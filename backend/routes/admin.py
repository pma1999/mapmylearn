from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, aliased
from sqlalchemy import or_, and_, desc, func
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import os

from backend.config.database import get_db
from backend.models.auth_models import User, CreditTransaction
from backend.schemas.auth_schemas import (
    UserResponse, UserListResponse, AdminUserUpdate, 
    AddCreditsRequest, CreditTransactionResponse,
    CreditTransactionListResponse, UserListFilters,
    CreditTransactionListFilters
)
from backend.utils.auth_middleware import get_admin_user, get_current_user, get_optional_user

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Special endpoint to create the first admin user
@router.get("/init-admin")
async def initialize_admin(request: Request, db: Session = Depends(get_db)):
    """
    Initialize the first admin user. This endpoint is protected by a secret admin code
    in the environment to ensure security.
    """
    # Get the admin code from the request
    admin_code = request.query_params.get("code")
    target_email = "pablomiguelargudo@gmail.com"
    
    # Verify the admin code against environment variable
    env_admin_code = os.environ.get("ADMIN_INIT_CODE")
    
    if not env_admin_code:
        # If no admin code is set, return 404 to hide the endpoint
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    if admin_code != env_admin_code:
        # If code doesn't match, return 403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin initialization code"
        )
    
    # Check if any admin users already exist
    existing_admin = db.query(User).filter(User.is_admin == True).first()
    if existing_admin:
        return {
            "status": "exists",
            "message": "Admin user already exists",
            "admin_email": existing_admin.email
        }
    
    # Find the user with the target email
    user = db.query(User).filter(User.email == target_email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {target_email} not found. User must register first."
        )
    
    # Make the user an admin
    user.is_admin = True
    
    # Also give them some initial credits
    user.credits += 50
    
    # Create a credit transaction
    transaction = CreditTransaction(
        user_id=user.id,
        amount=50,
        transaction_type="system_add",
        notes="Initial admin user setup",
        balance_after=user.credits
    )
    
    db.add(transaction)
    db.commit()
    
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Admin user initialized: {user.email} from IP {client_ip}")
    
    return {
        "status": "success",
        "message": "Admin user initialized successfully",
        "admin_email": user.email
    }


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Get dashboard statistics for the admin panel.
    Only accessible by admin users.
    """
    # Count all users
    total_users = db.query(func.count(User.id)).scalar()
    
    # Count active users
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # Count admin users
    admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
    
    # Sum of all credits currently assigned
    total_credits = db.query(func.sum(User.credits)).scalar() or 0
    
    # Total credits used (sum of negative transactions)
    credits_used = db.query(
        func.abs(func.sum(CreditTransaction.amount))
    ).filter(
        CreditTransaction.amount < 0
    ).scalar() or 0
    
    # Recent transactions (last 24 hours)
    day_ago = datetime.utcnow() - timedelta(days=1)
    recent_transactions = db.query(func.count(CreditTransaction.id)).filter(
        CreditTransaction.created_at >= day_ago
    ).scalar()
    
    # Users with credits
    users_with_credits = db.query(func.count(User.id)).filter(User.credits > 0).scalar()
    
    # Average credits per user
    avg_credits = db.query(func.avg(User.credits)).scalar() or 0
    
    logger.info(f"Admin user {admin.email} fetched dashboard statistics")
    
    return {
        "stats": {
            "totalUsers": total_users,
            "activeUsers": active_users,
            "adminUsers": admin_users,
            "totalCredits": total_credits,
            "creditsUsed": credits_used,
            "recentTransactions": recent_transactions,
            "usersWithCredits": users_with_credits,
            "averageCredits": round(float(avg_credits), 2)
        }
    }


@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    is_admin: Optional[bool] = None,
    is_active: Optional[bool] = None,
    has_credits: Optional[bool] = None,
    order: str = Query("email", regex="^(email|full_name|created_at|last_login|credits)$"),
    direction: str = Query("asc", regex="^(asc|desc)$")
):
    """
    Get a paginated list of users with optional filtering.
    Only accessible by admin users.
    """
    # Build the base query
    query = db.query(User)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if has_credits is not None:
        if has_credits:
            query = query.filter(User.credits > 0)
        else:
            query = query.filter(User.credits <= 0)
    
    # Apply ordering
    if order:
        order_column = getattr(User, order)
        if direction == "desc":
            order_column = desc(order_column)
        query = query.order_by(order_column)
    
    # Count total matching records
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Execute query
    users = query.all()
    
    # Log the action
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Admin user {admin.email} listed users from IP {client_ip}")
    
    # Convert SQLAlchemy models to Pydantic models
    user_responses = [UserResponse.model_validate(user, from_attributes=True) for user in users]
    
    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Get detailed information about a specific user.
    Only accessible by admin users.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    logger.info(f"Admin user {admin.email} viewed user {user.email}")
    
    # Convert SQLAlchemy model to Pydantic model
    return UserResponse.model_validate(user, from_attributes=True)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Update user details.
    Only accessible by admin users.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Prevent removing admin privileges from your own account
    if admin.id == user.id and user_update.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot remove their own admin privileges"
        )
    
    # Check which fields to update
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    logger.info(f"Admin user {admin.email} updated user {user.email}")
    
    # Convert SQLAlchemy model to Pydantic model
    return UserResponse.model_validate(user, from_attributes=True)


@router.post("/credits/add", response_model=CreditTransactionResponse)
async def add_credits(
    request: Request,
    credit_request: AddCreditsRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Add credits to a user account.
    Only accessible by admin users.
    """
    user = db.query(User).filter(User.id == credit_request.user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {credit_request.user_id} not found"
        )
    
    # Create a new credit transaction
    transaction = CreditTransaction(
        user_id=user.id,
        admin_user_id=admin.id,
        amount=credit_request.amount,
        transaction_type="admin_add",
        notes=credit_request.notes
    )
    
    # Update user's credit balance
    user.credits += credit_request.amount
    
    # Set the balance_after field
    transaction.balance_after = user.credits
    
    # Save both changes in a transaction
    try:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add credits. Please try again."
        )
    
    # Create response object with additional fields
    response_data = CreditTransactionResponse.model_validate(transaction, from_attributes=True)
    response_data.user_email = user.email
    response_data.admin_email = admin.email
    
    # Map transaction_type to action_type for frontend compatibility
    response_data.action_type = transaction.transaction_type
    
    # Ensure notes is set correctly
    response_data.notes = transaction.notes
    
    # Log the action with client IP
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Admin {admin.email} added {credit_request.amount} credits to user {user.email} from IP {client_ip}")
    
    return response_data


@router.get("/credits/transactions", response_model=CreditTransactionListResponse)
async def list_transactions(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    action_type: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    order: str = Query("created_at", regex="^(created_at|amount|action_type)$"),
    direction: str = Query("desc", regex="^(asc|desc)$")
):
    """
    Get a paginated list of credit transactions with optional filtering.
    Only accessible by admin users.
    """
    # Create alias for admin user
    admin_user = aliased(User)
    
    # Start with a join query to get user and admin emails
    query = db.query(
        CreditTransaction,
        User.email.label("user_email"),
        func.coalesce(admin_user.email, "System").label("admin_email")
    ).join(
        User, CreditTransaction.user_id == User.id
    ).outerjoin(
        admin_user, CreditTransaction.admin_user_id == admin_user.id
    )
    
    # Apply filters
    if user_id:
        query = query.filter(CreditTransaction.user_id == user_id)
    
    if admin_id:
        query = query.filter(CreditTransaction.admin_user_id == admin_id)
    
    if action_type:
        query = query.filter(CreditTransaction.transaction_type == action_type)
    
    if from_date:
        query = query.filter(CreditTransaction.created_at >= from_date)
    
    if to_date:
        query = query.filter(CreditTransaction.created_at <= to_date)
    
    # Apply ordering
    if order == "created_at":
        if direction == "desc":
            query = query.order_by(desc(CreditTransaction.created_at))
        else:
            query = query.order_by(CreditTransaction.created_at)
    elif order == "amount":
        if direction == "desc":
            query = query.order_by(desc(CreditTransaction.amount))
        else:
            query = query.order_by(CreditTransaction.amount)
    elif order == "action_type":
        if direction == "desc":
            query = query.order_by(desc(CreditTransaction.transaction_type))
        else:
            query = query.order_by(CreditTransaction.transaction_type)
    
    # Count total matching records
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Execute query
    results = query.all()
    
    # Process results to add the joined fields
    transactions = []
    for transaction, user_email, admin_email in results:
        transaction_dict = transaction.__dict__.copy()
        transaction_dict["user_email"] = user_email
        transaction_dict["admin_email"] = admin_email
        # Map transaction_type to action_type for frontend compatibility
        transaction_dict["action_type"] = transaction_dict["transaction_type"]
        # Map notes to description for frontend compatibility
        if "notes" in transaction_dict:
            transaction_dict["description"] = transaction_dict["notes"]
        else:
            transaction_dict["description"] = ""  # Default empty string if notes doesn't exist
        transactions.append(transaction_dict)
    
    logger.info(f"Admin {admin.email} listed credit transactions")
    
    return CreditTransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/credits/transactions/{user_id}", response_model=CreditTransactionListResponse)
async def get_user_transactions(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get credit transactions for a specific user.
    Only accessible by admin users.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Create alias for admin user
    admin_user = aliased(User)
    
    # Start with a join query to get admin emails
    query = db.query(
        CreditTransaction,
        func.coalesce(admin_user.email, "System").label("admin_email")
    ).outerjoin(
        admin_user, CreditTransaction.admin_user_id == admin_user.id
    ).filter(
        CreditTransaction.user_id == user_id
    ).order_by(
        desc(CreditTransaction.created_at)
    )
    
    # Count total matching records
    total = query.count()
    
    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)
    
    # Execute query
    results = query.all()
    
    # Process results to add the joined fields
    transactions = []
    for transaction, admin_email in results:
        transaction_dict = transaction.__dict__.copy()
        transaction_dict["user_email"] = user.email
        transaction_dict["admin_email"] = admin_email
        # Map transaction_type to action_type for frontend compatibility
        transaction_dict["action_type"] = transaction_dict["transaction_type"]
        # Map notes to description for frontend compatibility
        if "notes" in transaction_dict:
            transaction_dict["description"] = transaction_dict["notes"]
        else:
            transaction_dict["description"] = ""  # Default empty string if notes doesn't exist
        transactions.append(transaction_dict)
    
    logger.info(f"Admin {admin.email} viewed credit transactions for user {user.email}")
    
    return CreditTransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        per_page=per_page
    ) 