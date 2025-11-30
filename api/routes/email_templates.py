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
    MessageResponse,
    TemplateFileResponse,
)
from api.db_models import EmailTemplate, TemplateFile, User, File
from typing import List, Optional

router = APIRouter(prefix="/api/email-templates", tags=["email-templates"])


@router.delete("/files/{file_id}", response_model=MessageResponse)
async def delete_template_file(
    file_id: int,
    user_email: str = Query(...),
    template_id: Optional[int] = Query(None, description="Optional template_id to remove file from specific template only"),
    db: Session = Depends(get_db)
):
    """
    Delete a file from template_files and optionally from files table.
    
    If template_id is provided, only removes the file from that specific template.
    If template_id is None, removes the file from all templates and deletes the File record.
    
    The File record is only deleted if it's not used by any other templates.
    """
    try:
        # First, verify the file exists and belongs to the user
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check ownership (if file has an owner)
        if file_record.owner_email and file_record.owner_email.lower() != user_email.lower():
            raise HTTPException(
                status_code=403, 
                detail="File does not belong to this user"
            )
        
        # Find all template_files that reference this file
        if template_id:
            # Remove from specific template only
            template_file = db.query(TemplateFile).filter(
                TemplateFile.file_id == file_id,
                TemplateFile.email_template_id == template_id
            ).first()
            
            if not template_file:
                raise HTTPException(
                    status_code=404, 
                    detail="File not found in this template"
                )
            
            # Verify template belongs to user
            template = db.query(EmailTemplate).filter(
                EmailTemplate.id == template_id,
                EmailTemplate.user_email == user_email
            ).first()
            
            if not template:
                raise HTTPException(
                    status_code=403,
                    detail="Template does not belong to this user"
                )
            
            # Delete the template_file relationship
            db.delete(template_file)
            db.flush()
            
            # Check if file is used by other templates
            remaining_links = db.query(TemplateFile).filter(
                TemplateFile.file_id == file_id
            ).count()
            
            # If no other templates use this file, delete the File record
            if remaining_links == 0:
                db.delete(file_record)
            
            db.commit()
            return MessageResponse(
                message=f"File removed from template. File record {'deleted' if remaining_links == 0 else 'kept'} (used by {remaining_links} other template(s))."
            )
        else:
            # Remove from all templates and delete File record
            template_files = db.query(TemplateFile).filter(
                TemplateFile.file_id == file_id
            ).all()
            
            if not template_files:
                # File exists but not linked to any templates - delete it anyway
                db.delete(file_record)
                db.commit()
                return MessageResponse(message="File deleted successfully")
            
            # Verify all templates belong to user
            template_ids = {tf.email_template_id for tf in template_files}
            user_templates = db.query(EmailTemplate).filter(
                EmailTemplate.id.in_(template_ids),
                EmailTemplate.user_email == user_email
            ).all()
            
            if len(user_templates) != len(template_ids):
                raise HTTPException(
                    status_code=403,
                    detail="Some templates using this file do not belong to this user"
                )
            
            # Delete all template_file relationships
            for tf in template_files:
                db.delete(tf)
            
            # Delete the File record
            db.delete(file_record)
            db.commit()
            
            return MessageResponse(
                message=f"File deleted successfully from {len(template_files)} template(s)."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error deleting file: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.post("/", response_model=EmailTemplateResponse)
async def create_email_template(
    template: EmailTemplateCreate,
    file_paths: Optional[List[str]] = Query(default=None),
    file_ids: Optional[List[int]] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Create a new email template with optional file paths
    """
    try:
        # Check if user exists, create if not (for development/testing)
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
        print("user created {user}".format(user=user))
        db_template = EmailTemplate(
            user_email=template.user_email,
            template_body=template.template_body,
            template_type=template.template_type,
            subject=template.subject
        )
        db.add(db_template)
        print("db template is {template}".format(template=db_template))
        db.flush()  # Get the ID without committing
        
        # Add template files if provided
        if file_paths or file_ids:
            _replace_template_files(
                db=db,
                db_template=db_template,
                user_email=template.user_email,
                file_paths=file_paths,
                file_ids=file_ids,
            )
        
        db.commit()
        
        # Reload the template with relationships
        db.refresh(db_template)
        # Query again to get the relationship loaded
        db_template = (
            db.query(EmailTemplate)
            .options(joinedload(EmailTemplate.template_files).joinedload(TemplateFile.file))
            .filter(EmailTemplate.id == db_template.id)
            .first()
        )
        
        return _build_template_response(db_template)
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


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: int,
    template: EmailTemplateUpdate,
    user_email: str = Query(...),
    file_paths: List[str] = Query(default=None),
    file_ids: List[int] = Query(default=None),
    db: Session = Depends(get_db),
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
        
        # Update file associations if provided
        if (file_paths is not None) or (file_ids is not None):
            _replace_template_files(
                db=db,
                db_template=db_template,
                user_email=user_email,
                file_paths=file_paths,
                file_ids=file_ids,
            )
        
        db.commit()
        db.refresh(db_template)
        
        # Reload template with relationships
        db_template = (
            db.query(EmailTemplate)
            .options(joinedload(EmailTemplate.template_files).joinedload(TemplateFile.file))
            .filter(EmailTemplate.id == template_id)
            .first()
        )
        
        return _build_template_response(db_template)
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
            joinedload(EmailTemplate.template_files).joinedload(TemplateFile.file)
        ).filter(
            EmailTemplate.user_email == user_email,
            EmailTemplate.template_type == template_type
        ).order_by(EmailTemplate.created_at.desc()).first()
        
        if not template:
            return None
        
        return _build_template_response(template)
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
                joinedload(EmailTemplate.template_files).joinedload(TemplateFile.file)
            ).filter(
                EmailTemplate.user_email == user_email,
                EmailTemplate.template_type == template_type
            ).order_by(EmailTemplate.created_at.desc()).first()
            
            if template:
                templates.append(_build_template_response(template))
        
        return templates
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
            joinedload(EmailTemplate.template_files).joinedload(TemplateFile.file)
        ).filter(
            EmailTemplate.id == template_id,
            EmailTemplate.user_email == user_email
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return _build_template_response(template)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")


@router.get("/{user_email}", response_model=List[EmailTemplateResponse])
async def get_email_templates(user_email: str, db: Session = Depends(get_db)):
    """
    Get all email templates for a user
    """
    try:
        # Use joinedload to eagerly load template_files relationship (prevents N+1 queries)
        print("get email templates is started")
        templates = db.query(EmailTemplate).options(
            joinedload(EmailTemplate.template_files).joinedload(TemplateFile.file)
        ).filter(
            EmailTemplate.user_email == user_email
        ).order_by(EmailTemplate.created_at.desc()).all()
        print("email templates {email_templates}".format(email_templates=templates))
        return [_build_template_response(t) for t in templates]
    except Exception as e:
        print("error")
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")


def _build_template_response(template: EmailTemplate) -> EmailTemplateResponse:
    file_responses: List[TemplateFileResponse] = []
    if template.template_files:
        for attachment in template.template_files:
            file_path = attachment.file.file_path if attachment.file else attachment.file_path
            file_responses.append(
                TemplateFileResponse(
                    id=attachment.id,
                    email_template_id=attachment.email_template_id,
                    file_id=attachment.file_id,
                    file_path=file_path,
                )
            )
    return EmailTemplateResponse(
        id=template.id,
        user_email=template.user_email,
        template_body=template.template_body,
        template_type=template.template_type,
        subject=template.subject,
        created_at=template.created_at,
        file_paths=[file.file_path for file in file_responses if file.file_path],
        files=file_responses,
    )


def _replace_template_files(
    db: Session,
    db_template: EmailTemplate,
    user_email: str,
    file_paths: Optional[List[str]],
    file_ids: Optional[List[int]],
):
    db.query(TemplateFile).filter(
        TemplateFile.email_template_id == db_template.id
    ).delete(synchronize_session=False)

    attachments: List[TemplateFile] = []

    if file_paths:
        for file_path in file_paths:
            new_file = File(owner_email=user_email, file_path=file_path)
            db.add(new_file)
            db.flush()
            attachments.append(
                TemplateFile(
                    email_template_id=db_template.id,
                    file_id=new_file.id,
                    file_path=file_path,
                )
            )

    if file_ids:
        files = (
            db.query(File)
            .filter(File.id.in_(file_ids))
            .all()
        )
        found_ids = {f.id for f in files}
        missing = set(file_ids) - found_ids
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"File(s) not found: {sorted(missing)}",
            )

        unauthorized = [
            f.id for f in files if f.owner_email and f.owner_email.lower() != user_email.lower()
        ]
        if unauthorized:
            raise HTTPException(
                status_code=403,
                detail=f"File(s) do not belong to user: {unauthorized}",
            )

        for file_record in files:
            attachments.append(
                TemplateFile(
                    email_template_id=db_template.id,
                    file_id=file_record.id,
                    file_path=file_record.file_path,
                )
            )

    for attachment in attachments:
        db.add(attachment)
