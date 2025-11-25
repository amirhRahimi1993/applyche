"""
Email Templates API routes using SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from api.database import get_db, DB_NAME
from api.models import (
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    MessageResponse
)
from api.db_models import EmailTemplate, TemplateFile, User
from typing import List, Optional

router = APIRouter(prefix="/api/email-templates", tags=["email-templates"])


@router.post("/", response_model=EmailTemplateResponse)
async def create_email_template(
    template: EmailTemplateCreate, 
    file_paths: Optional[List[str]] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Create a new email template with optional file paths
    """
    try:
        # Check if user exists, create if not (for development/testing)
        from api.db_models import User
        user = db.query(User).filter(User.email == template.user_email).first()
        if not user:
            # Auto-create user if it doesn't exist (for development)
            # In production, you might want to require user creation first
            user = User(
                email=template.user_email,
                password_hash="",  # Empty for auto-created users
                is_active=True
            )
            db.add(user)
            db.flush()
        
        db_template = EmailTemplate(
            user_email=template.user_email,
            template_body=template.template_body,
            template_type=template.template_type,
            subject=template.subject
        )
        db.add(db_template)
        db.flush()  # Get the ID without committing
        
        # Add template files if provided
        if file_paths:
            for file_path in file_paths:
                template_file = TemplateFile(
                    email_template_id=db_template.id,
                    file_path=file_path
                )
                db.add(template_file)
        
        db.commit()
        
        # Reload the template with relationships
        db.refresh(db_template)
        # Query again to get the relationship loaded
        db_template = db.query(EmailTemplate).options(
            joinedload(EmailTemplate.template_files)
        ).filter(EmailTemplate.id == db_template.id).first()
        
        # Get file paths
        file_paths_list = [tf.file_path for tf in db_template.template_files] if db_template.template_files else []
        
        return EmailTemplateResponse(
            id=db_template.id,
            user_email=db_template.user_email,
            template_body=db_template.template_body,
            template_type=db_template.template_type,
            subject=db_template.subject,
            created_at=db_template.created_at,
            file_paths=file_paths_list
        )
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        
        # Check for database connection errors
        error_str = str(e)
        if "does not exist" in error_str and "database" in error_str:
            raise HTTPException(
                status_code=500, 
                detail=f"Database '{DB_NAME}' does not exist. Please run 'python setup_database.py' to create it."
            )
        elif "connection" in error_str.lower() or "operationalerror" in error_str.lower():
            raise HTTPException(
                status_code=500,
                detail=f"Database connection failed. Please check your database configuration in model/server_info.env and ensure PostgreSQL is running."
            )
        
        # Log full error for debugging
        print(f"Error creating template: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.get("/{user_email}", response_model=List[EmailTemplateResponse])
async def get_email_templates(user_email: str, db: Session = Depends(get_db)):
    """
    Get all email templates for a user
    """
    try:
        # Use joinedload to eagerly load template_files relationship (prevents N+1 queries)
        templates = db.query(EmailTemplate).options(
            joinedload(EmailTemplate.template_files)
        ).filter(
            EmailTemplate.user_email == user_email
        ).order_by(EmailTemplate.created_at.desc()).all()
        
        return [
            EmailTemplateResponse(
                id=t.id,
                user_email=t.user_email,
                template_body=t.template_body,
                template_type=t.template_type,
                subject=t.subject,
                created_at=t.created_at,
                file_paths=[tf.file_path for tf in t.template_files]
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")


@router.get("/{user_email}/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(user_email: str, template_id: int, db: Session = Depends(get_db)):
    """
    Get a specific email template
    """
    try:
        # Use joinedload to eagerly load template_files relationship
        template = db.query(EmailTemplate).options(
            joinedload(EmailTemplate.template_files)
        ).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.user_email == user_email
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return EmailTemplateResponse(
            id=template.id,
            user_email=template.user_email,
            template_body=template.template_body,
            template_type=template.template_type,
            subject=template.subject,
            created_at=template.created_at,
            file_paths=[tf.file_path for tf in template.template_files]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: int, 
    template: EmailTemplateUpdate, 
    user_email: str = Query(...),
    file_paths: List[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Update an email template
    """
    try:
        db_template = db.query(EmailTemplate).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.user_email == user_email
        ).first()
        
        if not db_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update fields if provided
        if template.template_body is not None:
            db_template.template_body = template.template_body
        if template.template_type is not None:
            db_template.template_type = template.template_type
        if template.subject is not None:
            db_template.subject = template.subject
        
        # Update file paths if provided
        if file_paths is not None:
            # Delete existing files
            db.query(TemplateFile).filter(
                TemplateFile.email_template_id == template_id
            ).delete()
            # Add new files
            for file_path in file_paths:
                template_file = TemplateFile(
                    email_template_id=template_id,
                    file_path=file_path
                )
                db.add(template_file)
        
        db.commit()
        db.refresh(db_template)
        
        # Reload template_files relationship after commit
        db.refresh(db_template, ['template_files'])
        
        return EmailTemplateResponse(
            id=db_template.id,
            user_email=db_template.user_email,
            template_body=db_template.template_body,
            template_type=db_template.template_type,
            subject=db_template.subject,
            created_at=db_template.created_at,
            file_paths=[tf.file_path for tf in db_template.template_files]
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error updating template: {error_details}")  # Log full error
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")


@router.delete("/{template_id}", response_model=MessageResponse)
async def delete_email_template(
    template_id: int, 
    user_email: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Delete an email template
    """
    try:
        template = db.query(EmailTemplate).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.user_email == user_email
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        db.delete(template)
        db.commit()
        
        return MessageResponse(message="Template deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")


@router.get("/{user_email}/by-type/{template_type}", response_model=Optional[EmailTemplateResponse])
async def get_template_by_type(user_email: str, template_type: int, db: Session = Depends(get_db)):
    """
    Get the most recent template of a specific type for a user
    Useful for loading main_template (0), first_reminder (1), second_reminder (2), third_reminder (3)
    Returns None if no template found
    """
    try:
        # Use joinedload to eagerly load template_files relationship
        template = db.query(EmailTemplate).options(
            joinedload(EmailTemplate.template_files)
        ).filter(
            EmailTemplate.user_email == user_email,
            EmailTemplate.template_type == template_type
        ).order_by(EmailTemplate.created_at.desc()).first()
        
        if not template:
            return None
        
        return EmailTemplateResponse(
            id=template.id,
            user_email=template.user_email,
            template_body=template.template_body,
            template_type=template.template_type,
            subject=template.subject,
            created_at=template.created_at,
            file_paths=[tf.file_path for tf in template.template_files]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")


@router.get("/{user_email}/by-types", response_model=List[EmailTemplateResponse])
async def get_templates_by_types(
    user_email: str, 
    template_types: str = Query(..., alias="template_types", description="Comma-separated template types (e.g., '0,1,2,3')"),
    db: Session = Depends(get_db)
):
    """
    Get the most recent templates of multiple types for a user in a single query
    This is more efficient than making multiple separate API calls
    Returns a list of templates (may be empty or have fewer items than requested types)
    """
    try:
        # Parse template types from comma-separated string
        type_list = [int(t.strip()) for t in template_types.split(',') if t.strip().isdigit()]
        
        if not type_list:
            return []
        
        # Use joinedload to eagerly load template_files relationship
        # Get the most recent template for each type
        templates = []
        for template_type in type_list:
            template = db.query(EmailTemplate).options(
                joinedload(EmailTemplate.template_files)
            ).filter(
                EmailTemplate.user_email == user_email,
                EmailTemplate.template_type == template_type
            ).order_by(EmailTemplate.created_at.desc()).first()
            
            if template:
                templates.append(EmailTemplateResponse(
                    id=template.id,
                    user_email=template.user_email,
                    template_body=template.template_body,
                    template_type=template.template_type,
                    subject=template.subject,
                    created_at=template.created_at,
                    file_paths=[tf.file_path for tf in template.template_files]
                ))
        
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")
