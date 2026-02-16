# Technical Design Document: B2B Inventory & Order Management System

**Status:** Draft
**Date:** February 15, 2026

## 1. Project Overview

We are building a robust, production-grade B2B Inventory and Order Management System. The primary goal is reliability and correctness. This system will handle inventory tracking, order processing, and user management with strict adherence to data integrity.

### Core Engineering Principles

- **Data Integrity:** Correctness > Speed. Orders must never be placed for out-of-stock items.
- **Safety:** ACID compliance is mandatory for all transactions.
- **Observability:** Structured logging (JSON) and health checks from Day 1.
- **Maintainability:** Strict Layered Architecture to decouple business logic from the database.

### MVP

- Headless B2B Inventory System (backend API only. for now)
- User Roles
  - Admin: Can create products, update inventory stock, and view all orders.
  - Customer: Can view products, place orders, and view their own order history.
- **In-scope (The "Must Haves"):**
  - Authentication: Users must log in to do anything. We will use JWT (JSON Web Tokens).
  - Inventory Management: Admins can add/edit products. Stock must decrease automatically when an order is placed.
  - Order Processing: A Customer can buy multiple distinct items in one "Order."
  - Data Consistency: If User A buys the last item, User B must get an error immediately.
  - Status Workflow: Orders move from PENDING -> PAID -> SHIPPED.
- **Out-of-scope (The "Distractions"):**
  - Payment Gateway: We will not integrate Stripe/PayPal yet. We will mock the payment step (e.g., a function that always returns True).
  - Email Notifications: We will log "Email sent to user" to the console, but not actually send emails.
  - Frontend UI: We will test everything via cURL or Postman.
  - Shipping Integrations: We won't calculate real shipping costs (FedEx/UPS API). We'll use a flat rate.

### API Interface (High Level Spec)

- We will adhere to RESTful standards. This means we use HTTP verbs (GET, POST, PUT, DELETE) meaningfully.
- Common Response Format:
  - Success: 200 OK or 201 Created with JSON data.
  - Client Error: 400 Bad Request (Invalid input), 401 Unauthorized (Not logged in), 403 Forbidden (Logged in but wrong role).
  - Server Error: 500 Internal Server Error (Our fault).

- **Authentication (/auth):**
  - `POST /auth/register`
  - Payload: { "email": "user@example.com", "password": "securePass123", "role": "customer" }
  - Response: 201 Created -> { "id": "uuid...", "email": "..." }
  - Note: In a real app, you might disable self-registration for Admins, but for MVP we allow it.

  - `POST /auth/login`
  - Payload: { "email": "user@example.com", "password": "securePass123" }
  - Response: 200 OK -> { "access_token": "eyJhbGciOi...", "token_type": "bearer" }
  - Why: The client must send this token in the Authorization header for all subsequent requests.

- **Products (/products):**
  - `GET /products`
  - Auth: Public (or Authenticated Users only).
  - Response: 200 OK -> List of products.
  - Filter: Support query params like `?in_stock=true`.

  - `POST /products`
  - Auth: Admin Only.
  - Payload:

  ```
  {
      "name": "Industrial Widget A",
      "sku": "WIDGET-A-001",
      "price": 150.00,
      "stock_quantity": 500
  }
  ```

  - Response: 201 Created -> { "id": 1, ...}.

  - `PATCH /products/{id}`
  - Auth: Admin Only.
  - Why PATCH? We only want to update one field (e.g., price) without sending the whole object again.
  - Payload: { "price": 160.00 }

- **Orders (/orders) - The Core Logic:**
  - `POST /orders`
  - Auth: Authenticated Customer.
  - The "Senior" Payload: We accept a list of items.

  ```
  {
      "items": [
          { "product_id": 1, "quantity": 5 },
          { "product_id": 4, "quantity": 1 }
      ]
  }
  ```

  - The "Senior" Logic:
    - Start DB Transaction.
    - Lock Product 1 and Product 4.
    - Check Stock. If insufficient -> Rollback & Return 400.
    - Deduct Stock.
    - Create Order & OrderItems (Snapshot Price).
    - Commit Transaction.
  - Response: 201 Created -> { "id": "order-uuid", "status": "PENDING", "total_amount": 900.00 }

  - `GET /orders/{id}`
  - Auth: Owner of the order OR Admin.
  - Response:

  ```
  {
  "id": "order-uuid",
  "status": "PAID",
  "created_at": "2026-02-15T10:00:00Z",
  "items": [
      {
      "product_name": "Industrial Widget A",
      "quantity": 5,
      "unit_price_at_purchase": 150.00  // <--- The Snapshot!
      }
  ]
  }
  ```

---

## 2. Tech Stack & Infrastructure

- **Language:** Python 3.11+ (FastAPI)
  - _Rationale:_ Strong typing (Pydantic), high velocity, standard for data-heavy backends.
- **Database:** PostgreSQL 16+
  - _Rationale:_ Essential for ACID transactions and row-level locking.
- **Migration Tool:** Alembic
  - _Rationale:_ Infrastructure-as-Code for database schemas.
- **Containerization:** Docker & Docker Compose
  - _Rationale:_ Ensures identical environments for Dev, Test, and Prod.

---

## 3. Data Design (Schema)

### Key Pattern: The "Snapshot" (Immutable History)

To adhere to accounting standards, we do not link Orders directly to dynamic Product prices. We snapshot the data at the moment of purchase into `OrderItems`.

### Core Entities

**1. Users**

- `id` (UUID): Primary Key
- `email` (String, Unique)
- `password_hash` (String)
- `role` (Enum): `ADMIN`, `CUSTOMER`, `INVENTORY_MANAGER`

**2. Products**

- `id` (Integer): Primary Key
- `sku` (String, Unique): Stock Keeping Unit
- `name` (String)
- `current_price` (Decimal): The _current_ listing price.
- `stock_quantity` (Integer): The source of truth for inventory.
- `version` (Integer): Used for optimistic locking.

**3. Orders**

- `id` (UUID): Public Order ID.
- `user_id` (ForeignKey -> Users)
- `status` (Enum): `PENDING`, `PAID`, `SHIPPED`, `CANCELLED`
- `total_amount` (Decimal)
- `created_at` (Timestamp)

**4. OrderItems (The Snapshot)**

- `id` (Integer)
- `order_id` (ForeignKey -> Orders)
- `product_id` (ForeignKey -> Products)
- `quantity` (Integer)
- `unit_price_at_purchase` (Decimal): **CRITICAL.** Copies `Products.current_price` at moment of purchase.

---

## 4. Key Engineering Challenges

### Risk: Race Conditions (Overselling Inventory)

**Scenario:** Two users buy the last item simultaneously.
**Mitigation:** Database-Level Atomicity.
We strictly avoid "Read-Modify-Write" in application code. We use conditional atomic updates:

```sql
UPDATE products
SET stock_quantity = stock_quantity - :requested_qty
WHERE id = :product_id AND stock_quantity >= :requested_qty;
```

## 5. Implementation Roadmap

### Phase 1: The Walking Skeleton (Days 1-2)

- **Goal:** A "Hello World" API running in Docker with a database connection.
- Set up git repository & directory structure.
- Configure Docker & Docker Compose (FastAPI + PostgreSQL).
- Create a `Makefile` for common commands (e.g., `make up`, `make test`).
- Configure Linting & Formatting (Ruff) to enforce code style automatically.

### Phase 2: The Core Domain (Days 3-5)

- **Goal:** The ability to talk to the database.
- Implement Database Models (SQLAlchemy).
- Set up Alembic Migrations (version control for DB schema).
- Implement the **Repository Layer** (CRUD operations for Users and Products).
- **Deliverable:** Working Integration Tests for database interactions.

### Phase 3: Business Logic & Auth (Days 6-10)

- **Goal:** The rules of the business are enforced.
- Implement the **Service Layer** (The "Brain").
  - _Focus:_ The `place_order` function (Transaction management, Inventory checks).
- Implement JWT Authentication.
- Implement RBAC (Role-Based Access Control) decorators.

### Phase 4: API & Integration (Days 11-14)

- **Goal:** The outside world can talk to us.
- Build REST Endpoints (FastAPI Routers).
- Connect Layers: API -> Service -> Repository.
- **Deliverable:** End-to-End (E2E) tests running in Docker.

### Phase 5: Hardening (Days 15+)

- **Goal:** Production readiness.
- Add Structured Logging (JSON format for observability).
- Build CI/CD Pipeline (GitHub Actions) to run tests on every push.
- Stress test the concurrency logic to prove safety.
