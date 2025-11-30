"""
Professor Lists API routes using SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import MessageResponse, ProfessorListCreate, ProfessorListResponse
from api.db_models import ProfessorList, User
from typing import Optional


router = APIRouter(prefix="/api/professor-lists", tags=["professor-lists"])


@router.post("/", response_model=ProfessorListResponse)
async def upsert_professor_list(
    data: ProfessorListCreate,
    db: Session = Depends(get_db)
):
    """
    Create or update professor list for a user.
    Only one row per user is allowed - updates existing if present.
    """
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == data.user_email).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User {data.user_email} not found"
            )
        
        # Check if professor list already exists for this user
        existing = db.query(ProfessorList).filter(
            ProfessorList.user_email == data.user_email
        ).first()
        
        if existing:
            # Update existing record
            existing.file_path = data.file_path
            db.commit()
            db.refresh(existing)
            return ProfessorListResponse(
                id=existing.id,
                user_email=existing.user_email,
                file_path=existing.file_path,
                created_at=existing.created_at.isoformat()
            )
        else:
            # Create new record
            new_list = ProfessorList(
                user_email=data.user_email,
                file_path=data.file_path
            )
            db.add(new_list)
            db.commit()
            db.refresh(new_list)
            return ProfessorListResponse(
                id=new_list.id,
                user_email=new_list.user_email,
                file_path=new_list.file_path,
                created_at=new_list.created_at.isoformat()
            )
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error saving professor list: {str(e)}"
        )


@router.get("/{user_email}", response_model=Optional[ProfessorListResponse])
async def get_professor_list(
    user_email: str,
    db: Session = Depends(get_db)
):
    """
    Get professor list for a user.
    Returns None if no list exists.
    """
    try:
        professor_list = db.query(ProfessorList).filter(
            ProfessorList.user_email == user_email
        ).first()
        
        if not professor_list:
            return None
        
        return ProfessorListResponse(
            id=professor_list.id,
            user_email=professor_list.user_email,
            file_path=professor_list.file_path,
            created_at=professor_list.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching professor list: {str(e)}"
        )


@router.delete("/{user_email}", response_model=MessageResponse)
async def delete_professor_list(
    user_email: str,
    db: Session = Depends(get_db)
):
    """
    Delete professor list for a user.
    """
    try:
        professor_list = db.query(ProfessorList).filter(
            ProfessorList.user_email == user_email
        ).first()
        
        if not professor_list:
            raise HTTPException(
                status_code=404,
                detail="Professor list not found"
            )
        
        db.delete(professor_list)
        db.commit()
        
        return MessageResponse(message="Professor list deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting professor list: {str(e)}"
        )

