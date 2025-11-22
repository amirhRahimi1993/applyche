"""
Email Queue and Send Log API routes
"""
from fastapi import APIRouter, HTTPException, Query
from api.database import db
from api.models import (
    EmailQueueCreate,
    EmailQueueResponse,
    SendLogResponse,
    MessageResponse
)
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/email-queue", tags=["email-queue"])


@router.post("/", response_model=EmailQueueResponse)
async def create_email_queue_item(item: EmailQueueCreate):
    """
    Add an email to the queue
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                INSERT INTO email_queue (
                    user_email, to_email, subject, body, template_id, scheduled_at, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 0)
                RETURNING id, user_email, to_email, subject, body, template_id,
                         scheduled_at, status, retry_count, created_at
            """, (
                item.user_email,
                item.to_email,
                item.subject,
                item.body,
                item.template_id,
                item.scheduled_at
            ))
            result = cur.fetchone()
            return EmailQueueResponse(
                id=result[0],
                user_email=result[1],
                to_email=result[2],
                subject=result[3],
                body=result[4],
                template_id=result[5],
                scheduled_at=result[6],
                status=result[7],
                retry_count=result[8],
                created_at=result[9]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating queue item: {str(e)}")


@router.get("/{user_email}", response_model=List[EmailQueueResponse])
async def get_email_queue(
    user_email: str,
    status: Optional[int] = Query(None, description="Filter by status (0=pending, 1=sent, 2=failed, 3=retrying)"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Get email queue items for a user
    """
    try:
        with db.get_cursor() as cur:
            query = """
                SELECT id, user_email, to_email, subject, body, template_id,
                       scheduled_at, status, retry_count, created_at
                FROM email_queue
                WHERE user_email = %s
            """
            params = [user_email]
            
            if status is not None:
                query += " AND status = %s"
                params.append(status)
            
            query += " ORDER BY scheduled_at ASC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            results = cur.fetchall()
            return [
                EmailQueueResponse(
                    id=row[0],
                    user_email=row[1],
                    to_email=row[2],
                    subject=row[3],
                    body=row[4],
                    template_id=row[5],
                    scheduled_at=row[6],
                    status=row[7],
                    retry_count=row[8],
                    created_at=row[9]
                )
                for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching queue items: {str(e)}")


@router.patch("/{queue_id}/status", response_model=MessageResponse)
async def update_queue_status(queue_id: int, status: int = Query(...), user_email: str = Query(...)):
    """
    Update the status of a queue item
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                UPDATE email_queue
                SET status = %s, last_attempt_at = %s
                WHERE id = %s AND user_email = %s
            """, (status, datetime.now(), queue_id, user_email))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Queue item not found")
            return MessageResponse(message="Status updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}")


@router.get("/logs/{user_email}", response_model=List[SendLogResponse])
async def get_send_logs(
    user_email: str,
    limit: int = Query(100, ge=1, le=1000),
    send_type: Optional[int] = Query(None, description="Filter by send type")
):
    """
    Get send logs for a user
    """
    try:
        with db.get_cursor() as cur:
            query = """
                SELECT id, user_email, sent_to, sent_time, subject, send_type, delivery_status
                FROM send_log
                WHERE user_email = %s
            """
            params = [user_email]
            
            if send_type is not None:
                query += " AND send_type = %s"
                params.append(send_type)
            
            query += " ORDER BY sent_time DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            results = cur.fetchall()
            return [
                SendLogResponse(
                    id=row[0],
                    user_email=row[1],
                    sent_to=row[2],
                    sent_time=row[3],
                    subject=row[4],
                    send_type=row[5],
                    delivery_status=row[6]
                )
                for row in results
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching send logs: {str(e)}")

