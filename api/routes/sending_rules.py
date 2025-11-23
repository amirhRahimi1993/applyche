"""
Sending Rules API routes using SQLAlchemy ORM
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import (
    SendingRulesCreate,
    SendingRulesResponse,
    SendingRulesUpdate,
    MessageResponse
)
from api.db_models import SendingRules

router = APIRouter(prefix="/api/sending-rules", tags=["sending-rules"])


@router.post("/", response_model=SendingRulesResponse)
async def create_sending_rules(rules: SendingRulesCreate, db: Session = Depends(get_db)):
    """
    Create or update sending rules for a user
    """
    try:
        # Check if rules exist
        existing = db.query(SendingRules).filter(
            SendingRules.user_email == rules.user_email
        ).first()
        
        if existing:
            # Update existing
            existing.main_mail_number = rules.main_mail_number
            existing.reminder_one = rules.reminder_one
            existing.reminder_two = rules.reminder_two
            existing.reminder_three = rules.reminder_three
            existing.local_professor_time = rules.local_professor_time
            existing.max_email_per_university = rules.max_email_per_university
            existing.send_working_day_only = rules.send_working_day_only
            existing.period_between_reminders = rules.period_between_reminders
            existing.delay_sending_mail = rules.delay_sending_mail
            existing.start_time_send = rules.start_time_send
            db.commit()
            db.refresh(existing)
            result = existing
        else:
            # Insert new
            db_rules = SendingRules(
                user_email=rules.user_email,
                main_mail_number=rules.main_mail_number,
                reminder_one=rules.reminder_one,
                reminder_two=rules.reminder_two,
                reminder_three=rules.reminder_three,
                local_professor_time=rules.local_professor_time,
                max_email_per_university=rules.max_email_per_university,
                send_working_day_only=rules.send_working_day_only,
                period_between_reminders=rules.period_between_reminders,
                delay_sending_mail=rules.delay_sending_mail,
                start_time_send=rules.start_time_send
            )
            db.add(db_rules)
            db.commit()
            db.refresh(db_rules)
            result = db_rules
        
        return SendingRulesResponse(
            id=result.id,
            user_email=result.user_email,
            main_mail_number=result.main_mail_number,
            reminder_one=result.reminder_one,
            reminder_two=result.reminder_two,
            reminder_three=result.reminder_three,
            local_professor_time=result.local_professor_time,
            max_email_per_university=result.max_email_per_university,
            send_working_day_only=result.send_working_day_only,
            period_between_reminders=result.period_between_reminders,
            delay_sending_mail=result.delay_sending_mail,
            start_time_send=str(result.start_time_send) if result.start_time_send else None,
            created_at=result.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating/updating sending rules: {str(e)}")


@router.get("/{user_email}", response_model=SendingRulesResponse)
async def get_sending_rules(user_email: str, db: Session = Depends(get_db)):
    """
    Get sending rules for a user
    """
    try:
        rules = db.query(SendingRules).filter(
            SendingRules.user_email == user_email
        ).first()
        
        if not rules:
            raise HTTPException(status_code=404, detail="Sending rules not found")
        
        return SendingRulesResponse(
            id=rules.id,
            user_email=rules.user_email,
            main_mail_number=rules.main_mail_number,
            reminder_one=rules.reminder_one,
            reminder_two=rules.reminder_two,
            reminder_three=rules.reminder_three,
            local_professor_time=rules.local_professor_time,
            max_email_per_university=rules.max_email_per_university,
            send_working_day_only=rules.send_working_day_only,
            period_between_reminders=rules.period_between_reminders,
            delay_sending_mail=rules.delay_sending_mail,
            start_time_send=str(rules.start_time_send) if rules.start_time_send else None,
            created_at=rules.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sending rules: {str(e)}")


@router.patch("/{user_email}", response_model=SendingRulesResponse)
async def update_sending_rules(user_email: str, rules: SendingRulesUpdate, db: Session = Depends(get_db)):
    """
    Partially update sending rules for a user
    """
    try:
        db_rules = db.query(SendingRules).filter(
            SendingRules.user_email == user_email
        ).first()
        
        if not db_rules:
            raise HTTPException(status_code=404, detail="Sending rules not found")
        
        # Update only provided fields
        if rules.main_mail_number is not None:
            db_rules.main_mail_number = rules.main_mail_number
        if rules.reminder_one is not None:
            db_rules.reminder_one = rules.reminder_one
        if rules.reminder_two is not None:
            db_rules.reminder_two = rules.reminder_two
        if rules.reminder_three is not None:
            db_rules.reminder_three = rules.reminder_three
        if rules.local_professor_time is not None:
            db_rules.local_professor_time = rules.local_professor_time
        if rules.max_email_per_university is not None:
            db_rules.max_email_per_university = rules.max_email_per_university
        if rules.send_working_day_only is not None:
            db_rules.send_working_day_only = rules.send_working_day_only
        if rules.period_between_reminders is not None:
            db_rules.period_between_reminders = rules.period_between_reminders
        if rules.delay_sending_mail is not None:
            db_rules.delay_sending_mail = rules.delay_sending_mail
        if rules.start_time_send is not None:
            db_rules.start_time_send = rules.start_time_send
        
        db.commit()
        db.refresh(db_rules)
        
        return SendingRulesResponse(
            id=db_rules.id,
            user_email=db_rules.user_email,
            main_mail_number=db_rules.main_mail_number,
            reminder_one=db_rules.reminder_one,
            reminder_two=db_rules.reminder_two,
            reminder_three=db_rules.reminder_three,
            local_professor_time=db_rules.local_professor_time,
            max_email_per_university=db_rules.max_email_per_university,
            send_working_day_only=db_rules.send_working_day_only,
            period_between_reminders=db_rules.period_between_reminders,
            delay_sending_mail=db_rules.delay_sending_mail,
            start_time_send=str(db_rules.start_time_send) if db_rules.start_time_send else None,
            created_at=db_rules.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating sending rules: {str(e)}")
