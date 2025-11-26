"""
Pydantic models for request/response schemas
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from pydantic import BaseModel, EmailStr


# Dashboard Models
class DashboardStats(BaseModel):
    """Dashboard statistics response"""
    email_you_send: int
    first_reminder_send: int
    second_reminder_send: int
    third_reminder_send: int
    number_of_email_professor_answered: int
    emails_remaining: int


# Email Template Models
class EmailTemplateCreate(BaseModel):
    """Create email template request"""
    user_email: EmailStr
    template_body: str
    template_type: int  # 0=generic, 1=followup, etc.
    subject: Optional[str] = None


class EmailTemplateResponse(BaseModel):
    """Email template response"""
    id: int
    user_email: str
    template_body: str
    template_type: int
    subject: Optional[str]
    created_at: datetime
    file_paths: Optional[List[str]] = []  # List of file paths from template_files


class TemplateFileResponse(BaseModel):
    """Template file response"""
    id: int
    email_template_id: int
    file_path: str


class EmailTemplateUpdate(BaseModel):
    """Update email template request"""
    template_body: Optional[str] = None
    template_type: Optional[int] = None
    subject: Optional[str] = None


# Sending Rules Models
class SendingRulesCreate(BaseModel):
    """Create sending rules request"""
    user_email: EmailStr
    main_mail_number: int = 1
    reminder_one: int = 0
    reminder_two: int = 0
    reminder_three: int = 0
    local_professor_time: bool = True
    max_email_per_university: int = 3
    send_working_day_only: bool = True
    period_between_reminders: int = 7
    delay_sending_mail: int = 0
    start_time_send: Optional[str] = "09:00:00"


class SendingRulesResponse(BaseModel):
    """Sending rules response"""
    id: int
    user_email: str
    main_mail_number: int
    reminder_one: int
    reminder_two: int
    reminder_three: int
    local_professor_time: bool
    max_email_per_university: int
    send_working_day_only: bool
    period_between_reminders: int
    delay_sending_mail: int
    start_time_send: Optional[str]
    created_at: datetime


class SendingRulesUpdate(BaseModel):
    """Update sending rules request"""
    main_mail_number: Optional[int] = None
    reminder_one: Optional[int] = None
    reminder_two: Optional[int] = None
    reminder_three: Optional[int] = None
    local_professor_time: Optional[bool] = None
    max_email_per_university: Optional[int] = None
    send_working_day_only: Optional[bool] = None
    period_between_reminders: Optional[int] = None
    delay_sending_mail: Optional[int] = None
    start_time_send: Optional[str] = None


# Email Queue Models
class EmailQueueCreate(BaseModel):
    """Create email queue item request"""
    user_email: EmailStr
    to_email: EmailStr
    subject: Optional[str] = None
    body: str
    template_id: Optional[int] = None
    scheduled_at: datetime


class EmailQueueResponse(BaseModel):
    """Email queue item response"""
    id: int
    user_email: str
    to_email: str
    subject: Optional[str]
    body: str
    template_id: Optional[int]
    scheduled_at: datetime
    status: int
    retry_count: int
    created_at: datetime


# Send Log Models
class SendLogResponse(BaseModel):
    """Send log response"""
    id: int
    user_email: str
    sent_to: str
    sent_time: datetime
    subject: Optional[str]
    send_type: int
    delivery_status: int


# Professor Models
class ProfessorResponse(BaseModel):
    """Professor response"""
    email: str
    name: str
    major: Optional[str]
    university_id: Optional[int]
    department_id: Optional[int]
    professor_img: Optional[str]
    meta_data: Optional[Dict[str, Any]]


# User Models
class UserCreate(BaseModel):
    """Create user request"""
    email: EmailStr
    password_hash: str
    display_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response"""
    email: str
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
    display_name: Optional[str]
    profile_image: Optional[str]


class LoginRequest(BaseModel):
    """Login request payload"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response"""
    email: EmailStr
    display_name: Optional[str] = None
    message: str = "Login successful"


# Generic Response Models
class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


