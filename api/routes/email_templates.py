"""
Email Templates API routes using SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import (
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    MessageResponse
)
from api.db_models import EmailTemplate
from typing import List

router = APIRouter(prefix="/api/email-templates", tags=["email-templates"])


@router.post("/", response_model=EmailTemplateResponse)
async def create_email_template(template: EmailTemplateCreate, db: Session = Depends(get_db)):
    """
    Create a new email template
    """
    try:
        db_template = EmailTemplate(
            user_email=template.user_email,
            template_body=template.template_body,
            template_type=template.template_type,
            subject=template.subject
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return EmailTemplateResponse(
            id=db_template.id,
            user_email=db_template.user_email,
            template_body=db_template.template_body,
            template_type=db_template.template_type,
            subject=db_template.subject,
            created_at=db_template.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.get("/{user_email}", response_model=List[EmailTemplateResponse])
async def get_email_templates(user_email: str, db: Session = Depends(get_db)):
    """
    Get all email templates for a user
    """
    try:
        templates = db.query(EmailTemplate).filter(
            EmailTemplate.user_email == user_email
        ).order_by(EmailTemplate.created_at.desc()).all()
        
        return [
            EmailTemplateResponse(
                id=t.id,
                user_email=t.user_email,
                template_body=t.template_body,
                template_type=t.template_type,
                subject=t.subject,
                created_at=t.created_at
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
        template = db.query(EmailTemplate).filter(
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
            created_at=template.created_at
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
        
        db.commit()
        db.refresh(db_template)
        
        return EmailTemplateResponse(
            id=db_template.id,
            user_email=db_template.user_email,
            template_body=db_template.template_body,
            template_type=db_template.template_type,
            subject=db_template.subject,
            created_at=db_template.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
