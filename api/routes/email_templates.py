"""
Email Templates API routes
"""
from fastapi import APIRouter, HTTPException, Query
from api.database import db
from api.models import (
    EmailTemplateCreate,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    MessageResponse
)
from typing import List

router = APIRouter(prefix="/api/email-templates", tags=["email-templates"])


@router.post("/", response_model=EmailTemplateResponse)
async def create_email_template(template: EmailTemplateCreate):
    """
    Create a new email template
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                INSERT INTO email_templates (user_email, template_body, template_type, subject)
                VALUES (%s, %s, %s, %s)
                RETURNING id, user_email, template_body, template_type, subject, created_at
            """, (
                template.user_email,
                template.template_body,
                template.template_type,
                template.subject
            ))
            result = cur.fetchone()
            return EmailTemplateResponse(
                id=result[0],
                user_email=result[1],
                template_body=result[2],
                template_type=result[3],
                subject=result[4],
                created_at=result[5]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.get("/{user_email}", response_model=List[EmailTemplateResponse])
async def get_email_templates(user_email: str):
    """
    Get all email templates for a user
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT id, user_email, template_body, template_type, subject, created_at
                FROM email_templates
                WHERE user_email = %s
                ORDER BY created_at DESC
            """, (user_email,))
            results = cur.fetchall()
            return [
                EmailTemplateResponse(
                    id=row[0],
                    user_email=row[1],
                    template_body=row[2],
                    template_type=row[3],
                    subject=row[4],
                    created_at=row[5]
                )
                for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching templates: {str(e)}")


@router.get("/{user_email}/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(user_email: str, template_id: int):
    """
    Get a specific email template
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT id, user_email, template_body, template_type, subject, created_at
                FROM email_templates
                WHERE id = %s AND user_email = %s
            """, (template_id, user_email))
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Template not found")
            return EmailTemplateResponse(
                id=result[0],
                user_email=result[1],
                template_body=result[2],
                template_type=result[3],
                subject=result[4],
                created_at=result[5]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching template: {str(e)}")


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(template_id: int, template: EmailTemplateUpdate, user_email: str = Query(...)):
    """
    Update an email template
    """
    try:
        # Build update query dynamically
        updates = []
        values = []
        
        if template.template_body is not None:
            updates.append("template_body = %s")
            values.append(template.template_body)
        if template.template_type is not None:
            updates.append("template_type = %s")
            values.append(template.template_type)
        if template.subject is not None:
            updates.append("subject = %s")
            values.append(template.subject)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.extend([template_id, user_email])
        
        with db.get_cursor() as cur:
            cur.execute(f"""
                UPDATE email_templates
                SET {', '.join(updates)}
                WHERE id = %s AND user_email = %s
                RETURNING id, user_email, template_body, template_type, subject, created_at
            """, values)
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Template not found")
            return EmailTemplateResponse(
                id=result[0],
                user_email=result[1],
                template_body=result[2],
                template_type=result[3],
                subject=result[4],
                created_at=result[5]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")


@router.delete("/{template_id}", response_model=MessageResponse)
async def delete_email_template(template_id: int, user_email: str = Query(...)):
    """
    Delete an email template
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                DELETE FROM email_templates
                WHERE id = %s AND user_email = %s
            """, (template_id, user_email))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Template not found")
            return MessageResponse(message="Template deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")

