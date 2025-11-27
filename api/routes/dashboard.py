"""
Dashboard API routes using SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.database import get_db
from api.models import DashboardStats
from api.db_models import SendLog, ProfessorContact, EmailQueue

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats/{user_email}", response_model=DashboardStats)
async def get_dashboard_stats(user_email: str, db: Session = Depends(get_db)):
    """
    Get dashboard statistics for a user
    """
    try:
        # Count main emails sent (send_type = 0)
        email_you_send = db.query(func.count(SendLog.id)).filter(
            SendLog.user_email == user_email,
            SendLog.send_type == 0
        ).scalar() or 0
        
        # Count first reminder sent (send_type = 1)
        first_reminder_send = db.query(func.count(SendLog.id)).filter(
            SendLog.user_email == user_email,
            SendLog.send_type == 1
        ).scalar() or 0
        
        # Count second reminder sent (send_type = 2)
        second_reminder_send = db.query(func.count(SendLog.id)).filter(
            SendLog.user_email == user_email,
            SendLog.send_type == 2
        ).scalar() or 0
        
        # Count third reminder sent (send_type = 3)
        third_reminder_send = db.query(func.count(SendLog.id)).filter(
            SendLog.user_email == user_email,
            SendLog.send_type == 3
        ).scalar() or 0
        
        # Count emails answered (contact_status = 3 means replied)
        number_of_email_professor_answered = db.query(func.count(ProfessorContact.id)).filter(
            ProfessorContact.user_email == user_email,
            ProfessorContact.contact_status == 3
        ).scalar() or 0
        
        # Count emails remaining (status = 0 means pending)
        emails_remaining = db.query(func.count(EmailQueue.id)).filter(
            EmailQueue.user_email == user_email,
            EmailQueue.status == 0
        ).scalar() or 0
        
        return DashboardStats(
            email_you_send=email_you_send,
            first_reminder_send=first_reminder_send,
            second_reminder_send=second_reminder_send,
            third_reminder_send=third_reminder_send,
            number_of_email_professor_answered=number_of_email_professor_answered,
            emails_remaining=emails_remaining
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


@router.get("/email-analysis/{user_email}")
async def get_email_analysis(user_email: str, email_type: str, db: Session = Depends(get_db)):
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
        raise HTTPException(
            status_code=400, 
            detail="Invalid email_type. Must be one of: main_mail, first_reminder, second_reminder, third_reminder"
        )
    
    try:
        count = db.query(func.count(SendLog.id)).filter(
            SendLog.user_email == user_email,
            SendLog.send_type == column_mapping[email_type]
        ).scalar() or 0
        
        return {"email_type": email_type, "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching email analysis: {str(e)}")
