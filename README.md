# Technical Design Document: B2B Inventory & Order Management System

**Status:** Draft
**Date:** February 15, 2026

## 1. Project Overview
We are building a robust, production-grade B2B Inventory and Order Management System. The primary goal is reliability and correctness. This system will handle inventory tracking, order processing, and user management with strict adherence to data integrity.

### Core Engineering Principles
* **Data Integrity:** Correctness > Speed. Orders must never be placed for out-of-stock items.
* **Safety:** ACID compliance is mandatory for all transactions.
* **Observability:** Structured logging (JSON) and health checks from Day 1.
* **Maintainability:** Strict Layered Architecture to decouple business logic from the database.

---

## 2. Tech Stack & Infrastructure
* **Language:** Python 3.11+ (FastAPI)
    * *Rationale:* Strong typing (Pydantic), high velocity, standard for data-heavy backends.
* **Database:** PostgreSQL 16+
    * *Rationale:* Essential for ACID transactions and row-level locking.
* **Migration Tool:** Alembic
    * *Rationale:* Infrastructure-as-Code for database schemas.
* **Containerization:** Docker & Docker Compose
    * *Rationale:* Ensures identical environments for Dev, Test, and Prod.

---

## 3. Data Design (Schema)

### Key Pattern: The "Snapshot" (Immutable History)
To adhere to accounting standards, we do not link Orders directly to dynamic Product prices. We snapshot the data at the moment of purchase into `OrderItems`.

### Core Entities

**1. Users**
* `id` (UUID): Primary Key
* `email` (String, Unique)
* `password_hash` (String)
* `role` (Enum): `ADMIN`, `CUSTOMER`, `INVENTORY_MANAGER`

**2. Products**
* `id` (Integer): Primary Key
* `sku` (String, Unique): Stock Keeping Unit
* `name` (String)
* `current_price` (Decimal): The *current* listing price.
* `stock_quantity` (Integer): The source of truth for inventory.
* `version` (Integer): Used for optimistic locking.

**3. Orders**
* `id` (UUID): Public Order ID.
* `user_id` (ForeignKey -> Users)
* `status` (Enum): `PENDING`, `PAID`, `SHIPPED`, `CANCELLED`
* `total_amount` (Decimal)
* `created_at` (Timestamp)

**4. OrderItems (The Snapshot)**
* `id` (Integer)
* `order_id` (ForeignKey -> Orders)
* `product_id` (ForeignKey -> Products)
* `quantity` (Integer)
* `unit_price_at_purchase` (Decimal): **CRITICAL.** Copies `Products.current_price` at moment of purchase.

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
* **Goal:** A "Hello World" API running in Docker with a database connection.
* Set up git repository & directory structure.
* Configure Docker & Docker Compose (FastAPI + PostgreSQL).
* Create a `Makefile` for common commands (e.g., `make up`, `make test`).
* Configure Linting & Formatting (Ruff) to enforce code style automatically.

### Phase 2: The Core Domain (Days 3-5)
* **Goal:** The ability to talk to the database.
* Implement Database Models (SQLAlchemy).
* Set up Alembic Migrations (version control for DB schema).
* Implement the **Repository Layer** (CRUD operations for Users and Products).
* **Deliverable:** Working Integration Tests for database interactions.

### Phase 3: Business Logic & Auth (Days 6-10)
* **Goal:** The rules of the business are enforced.
* Implement the **Service Layer** (The "Brain").
    * *Focus:* The `place_order` function (Transaction management, Inventory checks).
* Implement JWT Authentication.
* Implement RBAC (Role-Based Access Control) decorators.

### Phase 4: API & Integration (Days 11-14)
* **Goal:** The outside world can talk to us.
* Build REST Endpoints (FastAPI Routers).
* Connect Layers: API -> Service -> Repository.
* **Deliverable:** End-to-End (E2E) tests running in Docker.

### Phase 5: Hardening (Days 15+)
* **Goal:** Production readiness.
* Add Structured Logging (JSON format for observability).
* Build CI/CD Pipeline (GitHub Actions) to run tests on every push.
* Stress test the concurrency logic to prove safety.