"""
Email Queue and Send Log API routes using SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from api.database import get_db
from api.models import (
    EmailQueueCreate,
    EmailQueueResponse,
    SendLogResponse,
    MessageResponse
)
from api.db_models import EmailQueue, SendLog
from typing import List, Optional

router = APIRouter(prefix="/api/email-queue", tags=["email-queue"])


@router.post("/", response_model=EmailQueueResponse)
async def create_email_queue_item(item: EmailQueueCreate, db: Session = Depends(get_db)):
    """
    Add an email to the queue
    """
    try:
        db_item = EmailQueue(
            user_email=item.user_email,
            to_email=item.to_email,
            subject=item.subject,
            body=item.body,
            template_id=item.template_id,
            scheduled_at=item.scheduled_at,
            status=0  # pending
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        return EmailQueueResponse(
            id=db_item.id,
            user_email=db_item.user_email,
            to_email=db_item.to_email,
            subject=db_item.subject,
            body=db_item.body,
            template_id=db_item.template_id,
            scheduled_at=db_item.scheduled_at,
            status=db_item.status,
            retry_count=db_item.retry_count,
            created_at=db_item.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating queue item: {str(e)}")


@router.get("/{user_email}", response_model=List[EmailQueueResponse])
async def get_email_queue(
    user_email: str,
    status: Optional[int] = Query(None, description="Filter by status (0=pending, 1=sent, 2=failed, 3=retrying)"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get email queue items for a user
    """
    try:
        query = db.query(EmailQueue).filter(EmailQueue.user_email == user_email)
        
        if status is not None:
            query = query.filter(EmailQueue.status == status)
        
        items = query.order_by(EmailQueue.scheduled_at.asc()).limit(limit).all()
        
        return [
            EmailQueueResponse(
                id=item.id,
                user_email=item.user_email,
                to_email=item.to_email,
                subject=item.subject,
                body=item.body,
                template_id=item.template_id,
                scheduled_at=item.scheduled_at,
                status=item.status,
                retry_count=item.retry_count,
                created_at=item.created_at
            )
            for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching queue items: {str(e)}")


@router.patch("/{queue_id}/status", response_model=MessageResponse)
async def update_queue_status(
    queue_id: int, 
    status: int = Query(...), 
    user_email: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Update the status of a queue item
    """
    try:
        queue_item = db.query(EmailQueue).filter(
            EmailQueue.id == queue_id,
            EmailQueue.user_email == user_email
        ).first()
        
        if not queue_item:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        queue_item.status = status
        queue_item.last_attempt_at = datetime.now(timezone.utc)
        db.commit()
        
        return MessageResponse(message="Status updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@router.get("/logs/{user_email}", response_model=List[SendLogResponse])
async def get_send_logs(
    user_email: str,
    limit: int = Query(100, ge=1, le=1000),
    send_type: Optional[int] = Query(None, description="Filter by send type"),
    db: Session = Depends(get_db)
):
    """
    Get send logs for a user
    """
    try:
        query = db.query(SendLog).filter(SendLog.user_email == user_email)
        
        if send_type is not None:
            query = query.filter(SendLog.send_type == send_type)
        
        logs = query.order_by(SendLog.sent_time.desc()).limit(limit).all()
        
        return [
            SendLogResponse(
                id=log.id,
                user_email=log.user_email,
                sent_to=log.sent_to,
                sent_time=log.sent_time,
                subject=log.subject,
                send_type=log.send_type,
                delivery_status=log.delivery_status
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching send logs: {str(e)}")
