"""
Sending Rules API routes
"""
from fastapi import APIRouter, HTTPException
from api.database import db
from api.models import (
    SendingRulesCreate,
    SendingRulesResponse,
    SendingRulesUpdate,
    MessageResponse
)

router = APIRouter(prefix="/api/sending-rules", tags=["sending-rules"])


@router.post("/", response_model=SendingRulesResponse)
async def create_sending_rules(rules: SendingRulesCreate):
    """
    Create or update sending rules for a user
    """
    try:
        with db.get_cursor() as cur:
            # Check if rules exist
            cur.execute("""
                SELECT id FROM sending_rules WHERE user_email = %s
            """, (rules.user_email,))
            existing = cur.fetchone()
            
            if existing:
                # Update existing
                cur.execute("""
                    UPDATE sending_rules
                    SET main_mail_number = %s,
                        reminder_one = %s,
                        reminder_two = %s,
                        reminder_three = %s,
                        local_professor_time = %s,
                        max_email_per_university = %s,
                        send_working_day_only = %s,
                        period_between_reminders = %s,
                        delay_sending_mail = %s,
                        start_time_send = %s
                    WHERE user_email = %s
                    RETURNING id, user_email, main_mail_number, reminder_one, reminder_two,
                             reminder_three, local_professor_time, max_email_per_university,
                             send_working_day_only, period_between_reminders, delay_sending_mail,
                             start_time_send, created_at
                """, (
                    rules.main_mail_number,
                    rules.reminder_one,
                    rules.reminder_two,
                    rules.reminder_three,
                    rules.local_professor_time,
                    rules.max_email_per_university,
                    rules.send_working_day_only,
                    rules.period_between_reminders,
                    rules.delay_sending_mail,
                    rules.start_time_send,
                    rules.user_email
                ))
            else:
                # Insert new
                cur.execute("""
                    INSERT INTO sending_rules (
                        user_email, main_mail_number, reminder_one, reminder_two,
                        reminder_three, local_professor_time, max_email_per_university,
                        send_working_day_only, period_between_reminders, delay_sending_mail,
                        start_time_send
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_email, main_mail_number, reminder_one, reminder_two,
                             reminder_three, local_professor_time, max_email_per_university,
                             send_working_day_only, period_between_reminders, delay_sending_mail,
                             start_time_send, created_at
                """, (
                    rules.user_email,
                    rules.main_mail_number,
                    rules.reminder_one,
                    rules.reminder_two,
                    rules.reminder_three,
                    rules.local_professor_time,
                    rules.max_email_per_university,
                    rules.send_working_day_only,
                    rules.period_between_reminders,
                    rules.delay_sending_mail,
                    rules.start_time_send
                ))
            
            result = cur.fetchone()
            return SendingRulesResponse(
                id=result[0],
                user_email=result[1],
                main_mail_number=result[2],
                reminder_one=result[3],
                reminder_two=result[4],
                reminder_three=result[5],
                local_professor_time=result[6],
                max_email_per_university=result[7],
                send_working_day_only=result[8],
                period_between_reminders=result[9],
                delay_sending_mail=result[10],
                start_time_send=str(result[11]) if result[11] else None,
                created_at=result[12]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating/updating sending rules: {str(e)}")


@router.get("/{user_email}", response_model=SendingRulesResponse)
async def get_sending_rules(user_email: str):
    """
    Get sending rules for a user
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT id, user_email, main_mail_number, reminder_one, reminder_two,
                       reminder_three, local_professor_time, max_email_per_university,
                       send_working_day_only, period_between_reminders, delay_sending_mail,
                       start_time_send, created_at
                FROM sending_rules
                WHERE user_email = %s
            """, (user_email,))
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Sending rules not found")
            return SendingRulesResponse(
                id=result[0],
                user_email=result[1],
                main_mail_number=result[2],
                reminder_one=result[3],
                reminder_two=result[4],
                reminder_three=result[5],
                local_professor_time=result[6],
                max_email_per_university=result[7],
                send_working_day_only=result[8],
                period_between_reminders=result[9],
                delay_sending_mail=result[10],
                start_time_send=str(result[11]) if result[11] else None,
                created_at=result[12]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sending rules: {str(e)}")


@router.patch("/{user_email}", response_model=SendingRulesResponse)
async def update_sending_rules(user_email: str, rules: SendingRulesUpdate):
    """
    Partially update sending rules for a user
    """
    try:
        updates = []
        values = []
        
        if rules.main_mail_number is not None:
            updates.append("main_mail_number = %s")
            values.append(rules.main_mail_number)
        if rules.reminder_one is not None:
            updates.append("reminder_one = %s")
            values.append(rules.reminder_one)
        if rules.reminder_two is not None:
            updates.append("reminder_two = %s")
            values.append(rules.reminder_two)
        if rules.reminder_three is not None:
            updates.append("reminder_three = %s")
            values.append(rules.reminder_three)
        if rules.local_professor_time is not None:
            updates.append("local_professor_time = %s")
            values.append(rules.local_professor_time)
        if rules.max_email_per_university is not None:
            updates.append("max_email_per_university = %s")
            values.append(rules.max_email_per_university)
        if rules.send_working_day_only is not None:
            updates.append("send_working_day_only = %s")
            values.append(rules.send_working_day_only)
        if rules.period_between_reminders is not None:
            updates.append("period_between_reminders = %s")
            values.append(rules.period_between_reminders)
        if rules.delay_sending_mail is not None:
            updates.append("delay_sending_mail = %s")
            values.append(rules.delay_sending_mail)
        if rules.start_time_send is not None:
            updates.append("start_time_send = %s")
            values.append(rules.start_time_send)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(user_email)
        
        with db.get_cursor() as cur:
            cur.execute(f"""
                UPDATE sending_rules
                SET {', '.join(updates)}
                WHERE user_email = %s
                RETURNING id, user_email, main_mail_number, reminder_one, reminder_two,
                         reminder_three, local_professor_time, max_email_per_university,
                         send_working_day_only, period_between_reminders, delay_sending_mail,
                         start_time_send, created_at
            """, values)
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Sending rules not found")
            return SendingRulesResponse(
                id=result[0],
                user_email=result[1],
                main_mail_number=result[2],
                reminder_one=result[3],
                reminder_two=result[4],
                reminder_three=result[5],
                local_professor_time=result[6],
                max_email_per_university=result[7],
                send_working_day_only=result[8],
                period_between_reminders=result[9],
                delay_sending_mail=result[10],
                start_time_send=str(result[11]) if result[11] else None,
                created_at=result[12]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating sending rules: {str(e)}")


