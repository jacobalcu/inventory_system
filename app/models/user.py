import uuid  # For generating unique user IDs
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
import enum  # For defining user roles

from app.core.database import Base


# Define Enum for Roles
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    # Primary Key: UUID
    # UUID is more secure than auto-incrementing integers and prevents enumeration attacks
    # Nobody can guess another user's ID by incrementing the number
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Email: Unique and indexed for fast lookups
    email = Column(String, unique=True, index=True, nullable=False)

    # Security: Store hashed passwords, not plain text
    hashed_password = Column(String, nullable=False)

    # Role-Based Access Control: Define user roles for permissions
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    # Soft Delete / Account Status: Instead of deleting users, we can mark them as inactive
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
