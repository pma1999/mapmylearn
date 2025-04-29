import uuid
import bcrypt
import os
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON, func, Index
from sqlalchemy.orm import relationship
from backend.config.database import Base

# Transaction Type Constants
class TransactionType:
    ADMIN_ADD = "admin_add"
    SYSTEM_ADD = "system_add"
    GENERATION_USE = "generation_use"
    AUDIO_GENERATION_USE = "audio_generation_use" # New type
    REFUND = "refund"
    PURCHASE = "purchase"
    CHAT_ALLOWANCE_PURCHASE = "chat_allowance_purchase" # Added for chat limits

class User(Base):
    """
    User model for authentication.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # New field to identify admin users
    is_email_verified = Column(Boolean, nullable=False, server_default='false') # Added for email verification status
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_login = Column(DateTime)
    credits = Column(Integer, nullable=False, server_default='0')
    last_monthly_credit_granted_at = Column(DateTime, nullable=True) # Added for monthly credit tracking
    # Password reset fields
    password_reset_token_hash = Column(String, nullable=True, index=True)
    password_reset_token_expires_at = Column(DateTime, nullable=True)

    # Relationships
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", foreign_keys="[CreditTransaction.user_id]", back_populates="user", cascade="all, delete-orphan")

    # Index for email lookups during authentication
    __table_args__ = (
        Index('idx_user_email', email),
        # Index for password reset token hash
        Index('idx_user_reset_token', password_reset_token_hash),
    )


class Session(Base):
    """
    Session model for tracking user sessions with refresh tokens.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_used_at = Column(DateTime, server_default=func.now(), nullable=False)
    device_info = Column(String)
    ip_address = Column(String)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Index for token lookups
    __table_args__ = (
        Index('idx_session_token', refresh_token),
        Index('idx_session_user_id', user_id),
    )

    @classmethod
    def create_refresh_token(cls, user_id, expiry_days=30, device_info=None, ip_address=None):
        """
        Create a new session with refresh token.
        """
        refresh_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        return cls(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            last_used_at=datetime.utcnow(),
            device_info=device_info,
            ip_address=ip_address
        )


class CreditTransaction(Base):
    """
    Model for tracking credit transactions including admin assignments and usage.
    """
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Integer, nullable=False)  # Positive for additions, negative for usage
    transaction_type = Column(String, nullable=False)  # Use constants from TransactionType class
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # SQLite requires this column, used to store user's balance after the transaction
    balance_after = Column(Integer, nullable=True) # Making this nullable for flexibility, can be updated
    
    # Use 'notes' for PostgreSQL, 'description' was for SQLite
    notes = Column(String, nullable=True)
    
    # Optional field for tracking related learning paths (if applicable to purchase)
    learning_path_id = Column(Integer, nullable=True)
    
    # Add Stripe related fields
    stripe_checkout_session_id = Column(String, unique=True, nullable=True, index=True)
    stripe_payment_intent_id = Column(String, unique=True, nullable=True, index=True)
    purchase_metadata = Column(JSON, nullable=True) # Use JSONB for PostgreSQL, JSON for SQLite
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="credit_transactions")
    admin = relationship("User", foreign_keys=[admin_user_id])
    
    # Indexes for efficient querying (add indexes for Stripe columns)
    __table_args__ = (
        Index('idx_credit_transaction_user_id', user_id),
        Index('idx_credit_transaction_admin_id', admin_user_id),
        Index('idx_credit_transaction_created_at', created_at.desc()),
        Index('idx_credit_transaction_action_type', transaction_type),
        Index('idx_credit_transaction_checkout_session', stripe_checkout_session_id),
        Index('idx_credit_transaction_payment_intent', stripe_payment_intent_id),
    )


class LearningPath(Base):
    """
    Learning path model for storing user's learning paths.
    """
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    path_id = Column(String, index=True, nullable=False)  # UUID string for path identification
    topic = Column(String, nullable=False)
    language = Column(String(10), nullable=False, comment="ISO 639-1 language code for the learning path content")
    path_data = Column(JSON, nullable=False)  # Store the entire learning path data as JSON
    creation_date = Column(DateTime, default=func.now(), nullable=False)
    last_modified_date = Column(DateTime, default=func.now(), onupdate=func.now())
    favorite = Column(Boolean, default=False)
    tags = Column(JSON, default=list)  # Store tags as JSON array
    source = Column(String, default="generated")  # 'generated' or 'imported'

    # Relationships
    user = relationship("User", back_populates="learning_paths")

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_learning_path_user_id', user_id),
        Index('idx_learning_path_path_id', path_id),
        Index('idx_learning_path_topic', topic),
        # Composite indexes for common query patterns
        Index('idx_learning_path_user_date', user_id, creation_date.desc()),
        Index('idx_learning_path_user_favorite', user_id, favorite),
        Index('idx_learning_path_user_modified', user_id, last_modified_date.desc()),
        Index('idx_learning_path_user_source', user_id, source),
        # For frequently used sorting combinations
        Index('idx_learning_path_user_fav_date', user_id, favorite, creation_date.desc()),
    ) 

    # Add columns for last visited state
    last_visited_module_idx = Column(Integer, nullable=True)
    last_visited_submodule_idx = Column(Integer, nullable=True)


# New Model for Tracking Generation Tasks
class GenerationTaskStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class GenerationTask(Base):
    __tablename__ = "generation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False, comment="UUID string for task identification")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, index=True, default=GenerationTaskStatus.PENDING)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    request_topic = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    history_entry_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    user = relationship("User") # Relationship back to User
    history_entry = relationship("LearningPath") # Relationship to the saved history entry
    
    # Indexes
    __table_args__ = (
        Index('idx_generation_task_user_id', user_id),
        Index('idx_generation_task_status', status),
        Index('idx_generation_task_created_at', created_at.desc()),
        Index('idx_generation_task_user_status', user_id, status),
        Index('idx_generation_task_history_entry', history_entry_id), 
    ) 


# New Model for Tracking User Progress in Learning Paths
class LearningPathProgress(Base):
    __tablename__ = "learning_path_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    module_index = Column(Integer, nullable=False)
    submodule_index = Column(Integer, nullable=False)
    completed_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # New column to explicitly track completion status
    is_completed = Column(Boolean, nullable=False, server_default='false', default=False)
    
    # Relationships (optional, but can be useful)
    user = relationship("User") 
    learning_path = relationship("LearningPath") 
    
    # Indexes and Constraints
    __table_args__ = (
        # Index for efficient querying by user and path
        Index('idx_lp_progress_user_path', user_id, learning_path_id),
        # Unique constraint to prevent duplicate entries for the same submodule
        Index('uq_user_path_submodule', 
              user_id, 
              learning_path_id, 
              module_index, 
              submodule_index, 
              unique=True), 
    )