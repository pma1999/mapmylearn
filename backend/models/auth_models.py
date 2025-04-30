import uuid
import bcrypt
import os
import secrets
from datetime import datetime, timedelta
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON, func, Index, UniqueConstraint
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
    full_name = Column(String, nullable=True) # Explicitly nullable
    is_active = Column(Boolean, default=True, server_default='true') # Ensure server_default matches default
    is_admin = Column(Boolean, default=False, server_default='false') # Ensure server_default matches default
    is_email_verified = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_login = Column(DateTime, nullable=True) # Explicitly nullable
    
    # API Keys - Adding them back as they exist in production
    encrypted_google_api_key = Column(String, nullable=True)
    encrypted_perplexity_api_key = Column(String, nullable=True)
    
    credits = Column(Integer, nullable=False, server_default='0')
    last_monthly_credit_granted_at = Column(DateTime, nullable=True) # Explicitly nullable
    
    # Password reset fields
    password_reset_token_hash = Column(String, nullable=True, index=True)
    password_reset_token_expires_at = Column(DateTime, nullable=True) # Explicitly nullable

    # Relationships
    learning_paths = relationship("LearningPath", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    # Specify primaryjoin for CreditTransaction relationships to avoid ambiguity
    credit_transactions = relationship(
        "CreditTransaction", 
        primaryjoin="User.id==CreditTransaction.user_id", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    admin_transactions = relationship(
        "CreditTransaction", 
        primaryjoin="User.id==CreditTransaction.admin_user_id", 
        back_populates="admin"
    )
    

    # Index definitions
    __table_args__ = (
        Index('ix_users_email', email, unique=True), # Match inspected index name and uniqueness
        Index('ix_users_password_reset_token_hash', password_reset_token_hash), # Match inspected index name
        Index('idx_user_email', email), # Keep original for potential compatibility? Or remove?
        Index('idx_user_reset_token', password_reset_token_hash), # Keep original?
        # Add other potentially useful indexes if needed, e.g., on is_admin?
        # Index('idx_user_is_admin', is_admin),
    )


class Session(Base):
    """
    Session model for tracking user sessions with refresh tokens.
    """
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True) # Added index=True based on inspection
    refresh_token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_used_at = Column(DateTime, server_default=func.now(), nullable=False) # Inspection shows NOT NULL
    device_info = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)

    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index('ix_sessions_refresh_token', refresh_token, unique=True), # Match inspected index
        Index('idx_session_token', refresh_token), # Keep original?
        Index('idx_session_user_id', user_id), # Original index
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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True) # Added index=True
    admin_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True) # Added index=True
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False, index=True) # Added index=True
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True) # Added index=True
    balance_after = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    learning_path_id = Column(Integer, nullable=True) # Potentially add FK to learning_paths? And index?
    # Add Stripe related fields
    stripe_checkout_session_id = Column(String, nullable=True, index=True)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    purchase_metadata = Column(JSON, nullable=True) # Keep as standard JSON
    
    user = relationship("User", foreign_keys=[user_id], back_populates="credit_transactions")
    admin = relationship("User", foreign_keys=[admin_user_id], back_populates="admin_transactions")
    
    __table_args__ = (
        UniqueConstraint('stripe_checkout_session_id', name='credit_transactions_stripe_checkout_session_id_key'),
        UniqueConstraint('stripe_payment_intent_id', name='credit_transactions_stripe_payment_intent_id_key'),
        Index('idx_credit_transaction_user_id', user_id), 
        Index('idx_credit_transaction_admin_id', admin_user_id),
        Index('idx_credit_transaction_created_at', created_at.desc()), # Keep desc order?
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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True) # Added index=True
    path_id = Column(String, index=True, nullable=False)
    topic = Column(String, nullable=False, index=True) # Added index=True
    language = Column(String(10), nullable=False, index=True) # Added index=True
    path_data = Column(JSON, nullable=False)
    creation_date = Column(DateTime, default=func.now(), nullable=False)
    last_modified_date = Column(DateTime, default=func.now(), onupdate=func.now())
    favorite = Column(Boolean, default=False, server_default='false')
    tags = Column(JSON, default=list, server_default='[]')
    source = Column(String, default="generated", server_default='generated')
    last_visited_module_idx = Column(Integer, nullable=True)
    last_visited_submodule_idx = Column(Integer, nullable=True)
    
    # Sharing fields
    is_public = Column(Boolean, nullable=False, server_default='false', default=False, index=True)
    share_id = Column(String, unique=True, nullable=True, index=True)

    user = relationship("User", back_populates="learning_paths")

    __table_args__ = (
        Index('idx_learning_path_user_id', user_id),
        Index('idx_learning_path_path_id', path_id),
        Index('idx_learning_path_topic', topic),
        Index('idx_learning_path_language', language), # Match inspected index
        Index('idx_learning_path_user_date', user_id, creation_date.desc()),
        Index('idx_learning_path_user_favorite', user_id, favorite),
        Index('idx_learning_path_user_modified', user_id, last_modified_date.desc()),
        Index('idx_learning_path_user_source', user_id, source),
        Index('idx_learning_path_user_fav_date', user_id, favorite, creation_date.desc()),
        # Indices for sharing fields
        Index('idx_learning_path_share_id', share_id, unique=True),
        Index('idx_learning_path_is_public', is_public),
        # Index for querying public paths efficiently
        Index('idx_learning_path_public_share_id', share_id, is_public, unique=True, postgresql_where=(is_public == True)), # Use boolean True
    )


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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, index=True, default=GenerationTaskStatus.PENDING)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    request_topic = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)
    history_entry_id = Column(Integer, ForeignKey("learning_paths.id", ondelete="SET NULL"), nullable=True, index=True)
    
    user = relationship("User")
    history_entry = relationship("LearningPath")
    
    __table_args__ = (
        Index('ix_generation_tasks_task_id', task_id, unique=True), # Match inspected index
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
    is_completed = Column(Boolean, nullable=False, server_default='false', default=False)
    
    user = relationship("User") 
    learning_path = relationship("LearningPath") 
    
    __table_args__ = (
        Index('idx_lpp_user_path', user_id, learning_path_id), # Match inspected index
        UniqueConstraint(user_id, learning_path_id, module_index, submodule_index, name='uq_user_path_submodule'), # Match inspected constraint
        # Original Index('uq_user_path_submodule', ...) was trying to create an index with unique=True, using UniqueConstraint is cleaner
    )