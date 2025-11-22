"""
Dashboard API routes
"""
from fastapi import APIRouter, HTTPException
from api.database import db
from api.models import DashboardStats
from typing import Dict

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats/{user_email}", response_model=DashboardStats)
async def get_dashboard_stats(user_email: str):
    """
    Get dashboard statistics for a user
    """
    column_storage = {
        "main_mail": "is_main_mail_send",
        "first_reminder": "is_first_reminder_send",
        "second_reminder": "is_second_reminder_send",
        "third_reminder": "is_third_reminder_send"
    }
    
    try:
        with db.get_cursor() as cur:
            stats = {}
            
            # Count main emails sent
            cur.execute("""
                SELECT COUNT(*) 
                FROM send_log 
                WHERE user_email = %s AND send_type = 0
            """, (user_email,))
            stats['email_you_send'] = cur.fetchone()[0] or 0
            
            # Count first reminder sent
            cur.execute("""
                SELECT COUNT(*) 
                FROM send_log 
                WHERE user_email = %s AND send_type = 1
            """, (user_email,))
            stats['first_reminder_send'] = cur.fetchone()[0] or 0
            
            # Count second reminder sent
            cur.execute("""
                SELECT COUNT(*) 
                FROM send_log 
                WHERE user_email = %s AND send_type = 2
            """, (user_email,))
            stats['second_reminder_send'] = cur.fetchone()[0] or 0
            
            # Count third reminder sent
            cur.execute("""
                SELECT COUNT(*) 
                FROM send_log 
                WHERE user_email = %s AND send_type = 3
            """, (user_email,))
            stats['third_reminder_send'] = cur.fetchone()[0] or 0
            
            # Count emails answered (replied status)
            cur.execute("""
                SELECT COUNT(*) 
                FROM professor_contact 
                WHERE user_email = %s AND contact_status = 3
            """, (user_email,))
            stats['number_of_email_professor_answered'] = cur.fetchone()[0] or 0
            
            # Count emails remaining (pending in queue)
            cur.execute("""
                SELECT COUNT(*) 
                FROM email_queue 
                WHERE user_email = %s AND status = 0
            """, (user_email,))
            stats['emails_remaining'] = cur.fetchone()[0] or 0
            
            return DashboardStats(**stats)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


@router.get("/email-analysis/{user_email}")
async def get_email_analysis(user_email: str, email_type: str):
    """
    Get email analysis by type (main_mail, first_reminder, second_reminder, third_reminder)
    """
    column_mapping = {
        "main_mail": 0,
        "first_reminder": 1,
        "second_reminder": 2,
        "third_reminder": 3
    }
    
    if email_type not in column_mapping:
        raise HTTPException(status_code=400, detail="Invalid email_type. Must be one of: main_mail, first_reminder, second_reminder, third_reminder")
    
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM send_log 
                WHERE user_email = %s AND send_type = %s
            """, (user_email, column_mapping[email_type]))
            count = cur.fetchone()[0] or 0
            return {"email_type": email_type, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email analysis: {str(e)}")


