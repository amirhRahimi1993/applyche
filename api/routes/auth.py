"""
Authentication routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.db_models import User
from api.models import LoginRequest, LoginResponse
from api.security import verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """
    Validate user credentials against the Users table.
    """
    try:
        # Query user by email
        user = db.query(User).filter(User.email == credentials.email).first()
        
        # Check if user exists before accessing attributes
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not verify_password(credentials.password, user.password_hash or ""):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        return LoginResponse(
            email=user.email,
            display_name=user.display_name or user.email,
            message="Login successful",
        )
    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Catch any unexpected errors and return a safe error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login. Please try again.",
        )



