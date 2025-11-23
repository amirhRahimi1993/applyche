"""
SQLAlchemy ORM models for ApplyChe database
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, SmallInteger,
    Numeric, Date, Time, DateTime, ForeignKey, UniqueConstraint, CheckConstraint,
    Index, JSON
)
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

class Base(DeclarativeBase):
    pass


# Note: Database enums are defined in PostgreSQL, but we use SmallInteger/String
# for compatibility. The actual enum values are handled at the application level.


# ============================================
# USERS / AUTH
# ============================================
class User(Base):
    __tablename__ = 'users'
    
    email = Column(CITEXT, primary_key=True)
    password_hash = Column(Text, nullable=False)
    password_salt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(SmallInteger, server_default='0', nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)
    display_name = Column(Text, nullable=True)
    profile_image = Column(Text, nullable=True)
    personal_website = Column(Text, nullable=True)
    backup_email = Column(CITEXT, unique=True, nullable=True)
    
    __table_args__ = (
        CheckConstraint("email <> ''", name='check_email_not_empty'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    # Relationships
    education_info = relationship('UserEducationInformation', back_populates='user', cascade='all, delete-orphan')
    subscriptions = relationship('Subscription', back_populates='user', cascade='all, delete-orphan')
    subscription_history = relationship('SubscriptionHistory', back_populates='user', cascade='all, delete-orphan')
    email_templates = relationship('EmailTemplate', back_populates='user', cascade='all, delete-orphan')
    sending_rules = relationship('SendingRules', back_populates='user', cascade='all, delete-orphan', uselist=False)
    email_queue = relationship('EmailQueue', back_populates='user', cascade='all, delete-orphan')
    send_logs = relationship('SendLog', back_populates='user', cascade='all, delete-orphan')
    professor_contacts = relationship('ProfessorContact', back_populates='user', cascade='all, delete-orphan')
    saved_positions = relationship('SavedPosition', back_populates='user', cascade='all, delete-orphan')
    professor_reviews = relationship('ProfessorReview', back_populates='user', cascade='all, delete-orphan')
    comments = relationship('Comment', back_populates='commenter', cascade='all, delete-orphan')
    review_votes = relationship('ReviewVote', back_populates='voter', cascade='all, delete-orphan')
    comment_votes = relationship('CommentVote', back_populates='voter', cascade='all, delete-orphan')
    chat_logs = relationship('ChatLog', back_populates='user', cascade='all, delete-orphan')
    api_tokens = relationship('APIToken', back_populates='user', cascade='all, delete-orphan')
    metrics = relationship('Metric', back_populates='user', cascade='all, delete-orphan')
    professor_lists = relationship('ProfessorList', back_populates='user', cascade='all, delete-orphan')
    email_properties = relationship('EmailProperty', back_populates='user', cascade='all, delete-orphan')
    files = relationship('File', back_populates='owner', cascade='all, delete-orphan')


# ============================================
# EDUCATION INFORMATION
# ============================================
class UserEducationInformation(Base):
    __tablename__ = 'user_education_information'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    major = Column(Text, nullable=False)
    university_id = Column(Integer, ForeignKey('universities.id', ondelete='SET NULL'), nullable=True)
    university_department = Column(Text, nullable=True)
    education_level = Column(String(20), nullable=False)  # 'BSc', 'MSc', 'PhD', 'PostDoc'
    grade = Column(Numeric(4, 2), nullable=True)
    ielts = Column(Numeric(3, 1), nullable=True)
    gre = Column(Numeric(4, 1), nullable=True)
    google_scholar_link = Column(Text, nullable=True)
    cv_path = Column('CV_path', Text, nullable=True)
    sop_path = Column('SOP_path', Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        CheckConstraint("ielts IS NULL OR (ielts >= 0 AND ielts <= 9)", name='chk_ielts_range'),
        CheckConstraint("gre IS NULL OR (gre >= 130 AND gre <= 340)", name='chk_gre_range'),
        CheckConstraint("grade IS NULL OR grade BETWEEN 0 AND 100", name='chk_grade'),
        Index('idx_user_education_email', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='education_info')
    university = relationship('University', back_populates='education_info')


# ============================================
# UNIVERSITIES / DEPARTMENTS
# ============================================
class University(Base):
    __tablename__ = 'universities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    country = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    website = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('unique_name_lower_idx', func.lower(name), unique=True),
    )
    
    # Relationships
    departments = relationship('Department', back_populates='university', cascade='all, delete-orphan')
    professors = relationship('Professor', back_populates='university')
    open_positions = relationship('OpenPosition', back_populates='university')
    education_info = relationship('UserEducationInformation', back_populates='university')


class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id', ondelete='CASCADE'), nullable=False)
    university_deparment_name = Column(Text, nullable=False, unique=True)
    
    # Relationships
    university = relationship('University', back_populates='departments')
    professors = relationship('Professor', back_populates='department')
    open_positions = relationship('OpenPosition', back_populates='department')


# ============================================
# SUBSCRIPTIONS
# ============================================
class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False, unique=True)
    plan_name = Column(String(255), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SmallInteger, server_default='1', nullable=False)  # 1=active, 2=cancelled, 3=expired
    
    # Relationships
    user = relationship('User', back_populates='subscriptions')


class SubscriptionHistory(Base):
    __tablename__ = 'subscription_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    plan_name = Column(String(255), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    payment_reference = Column(Text, nullable=True)
    status = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_subscription_history_user', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='subscription_history')


# ============================================
# PROFESSORS
# ============================================
class Professor(Base):
    __tablename__ = 'professors'
    
    email = Column(CITEXT, primary_key=True)
    name = Column(Text, nullable=False)
    major = Column(Text, nullable=True)
    university_id = Column(Integer, ForeignKey('universities.id', ondelete='SET NULL'), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    professor_img = Column(Text, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    
    # Relationships
    university = relationship('University', back_populates='professors')
    department = relationship('Department', back_populates='professors')
    research_interests = relationship('ProfessorResearchInterest', back_populates='professor', cascade='all, delete-orphan')
    open_positions = relationship('OpenPosition', back_populates='supervisor_prof')
    professor_contacts = relationship('ProfessorContact', back_populates='professor')
    reviews = relationship('ProfessorReview', back_populates='professor', cascade='all, delete-orphan')


class ProfessorResearchInterest(Base):
    __tablename__ = 'professor_research_interests'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    professor_email = Column(CITEXT, ForeignKey('professors.email', ondelete='CASCADE'), nullable=False)
    interest = Column(Text, nullable=False)
    
    __table_args__ = (
        Index('idx_prof_interests_prof', 'professor_email'),
        Index('idx_prof_interest_text', 'interest'),
    )
    
    # Relationships
    professor = relationship('Professor', back_populates='research_interests')


# ============================================
# OPEN POSITIONS
# ============================================
class OpenPosition(Base):
    __tablename__ = 'open_positions'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    university_id = Column(Integer, ForeignKey('universities.id', ondelete='SET NULL'), nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    position_title = Column(Text, nullable=False)
    fund = Column(Text, nullable=True)
    min_ielts = Column(Numeric(3, 1), nullable=True)
    min_gre = Column(Numeric(4, 1), nullable=True)
    contact_email = Column(CITEXT, nullable=True)
    requirements = Column(JSONB, nullable=True)
    supervisor_email = Column(CITEXT, ForeignKey('professors.email', ondelete='SET NULL'), nullable=True)
    deadline = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    more_info_link = Column(Text, nullable=True)
    graduate_level = Column(SmallInteger, nullable=True)
    meta_data = Column(JSONB, nullable=True)
    country = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_open_positions_university', 'university_id'),
        Index('idx_open_positions_deadline', 'deadline'),
    )
    
    # Relationships
    university = relationship('University', back_populates='open_positions')
    department = relationship('Department', back_populates='open_positions')
    supervisor_prof = relationship('Professor', back_populates='open_positions', foreign_keys=[supervisor_email])
    professor_contacts = relationship('ProfessorContact', back_populates='position')
    saved_positions = relationship('SavedPosition', back_populates='position', cascade='all, delete-orphan')


# ============================================
# PROFESSOR CONTACT
# ============================================
class ProfessorContact(Base):
    __tablename__ = 'professor_contact'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    professor_email = Column(CITEXT, ForeignKey('professors.email', ondelete='SET NULL'), nullable=True)
    position_id = Column(BigInteger, ForeignKey('open_positions.id', ondelete='SET NULL'), nullable=True)
    last_contact_time = Column(DateTime(timezone=True), nullable=True)
    next_contact_time = Column(DateTime(timezone=True), nullable=True)
    contact_status = Column(SmallInteger, server_default='0', nullable=False)
    is_active = Column(Boolean, server_default='true', nullable=False)
    attempts = Column(SmallInteger, server_default='0', nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_email', 'professor_email', 'position_id', name='uq_prof_contact'),
        Index('idx_prof_contact_user', 'user_email'),
        Index('idx_prof_contact_prof', 'professor_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='professor_contacts')
    professor = relationship('Professor', back_populates='professor_contacts')
    position = relationship('OpenPosition', back_populates='professor_contacts')


# ============================================
# SAVED POSITIONS
# ============================================
class SavedPosition(Base):
    __tablename__ = 'saved_positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    position_id = Column(BigInteger, ForeignKey('open_positions.id', ondelete='CASCADE'), nullable=False)
    status = Column(SmallInteger, server_default='0', nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_email', 'position_id', name='uq_saved_position'),
        Index('idx_saved_positions_user', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='saved_positions')
    position = relationship('OpenPosition', back_populates='saved_positions')


# ============================================
# EMAIL TEMPLATES
# ============================================
class EmailTemplate(Base):
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    template_body = Column(Text, nullable=False)
    template_type = Column(SmallInteger, nullable=False)
    subject = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='email_templates')
    template_files = relationship('TemplateFile', back_populates='email_template', cascade='all, delete-orphan')
    email_queue_items = relationship('EmailQueue', back_populates='template')
    send_logs = relationship('SendLog', back_populates='template')


class TemplateFile(Base):
    __tablename__ = 'template_files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email_template_id = Column(Integer, ForeignKey('email_templates.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(Text, nullable=False)
    
    # Relationships
    email_template = relationship('EmailTemplate', back_populates='template_files')


# ============================================
# SENDING RULES
# ============================================
class SendingRules(Base):
    __tablename__ = 'sending_rules'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False, unique=True)
    main_mail_number = Column(SmallInteger, server_default='1', nullable=False)
    reminder_one = Column(SmallInteger, server_default='0', nullable=False)
    reminder_two = Column(SmallInteger, server_default='0', nullable=False)
    reminder_three = Column(SmallInteger, server_default='0', nullable=False)
    local_professor_time = Column(Boolean, server_default='true', nullable=False)
    max_email_per_university = Column(SmallInteger, server_default='3', nullable=False)
    send_working_day_only = Column(Boolean, server_default='true', nullable=False)
    period_between_reminders = Column(SmallInteger, server_default='7', nullable=False)
    delay_sending_mail = Column(SmallInteger, server_default='0', nullable=False)
    start_time_send = Column(Time(timezone=True), server_default="'09:00:00'::time", nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_sending_rules_user', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='sending_rules')


# ============================================
# EMAIL QUEUE
# ============================================
class EmailQueue(Base):
    __tablename__ = 'email_queue'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    to_email = Column(CITEXT, nullable=False)
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    template_id = Column(Integer, ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SmallInteger, server_default='0', nullable=False)
    retry_count = Column(SmallInteger, server_default='0', nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_email_queue_status_sched', 'status', 'scheduled_at'),
        Index('idx_email_queue_user_sched', 'user_email', 'scheduled_at'),
    )
    
    # Relationships
    user = relationship('User', back_populates='email_queue')
    template = relationship('EmailTemplate', back_populates='email_queue_items')


# ============================================
# SEND LOG
# ============================================
class SendLog(Base):
    __tablename__ = 'send_log'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    sent_to = Column(CITEXT, nullable=False)
    sent_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    template_id = Column(Integer, ForeignKey('email_templates.id', ondelete='SET NULL'), nullable=True)
    send_type = Column(SmallInteger, nullable=False)
    delivery_status = Column(SmallInteger, nullable=False)
    remote_message_id = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_send_log_user_time', 'user_email', 'sent_time'),
    )
    
    # Relationships
    user = relationship('User', back_populates='send_logs')
    template = relationship('EmailTemplate', back_populates='send_logs')


# ============================================
# PROFESSOR REVIEWS
# ============================================
class ProfessorReview(Base):
    __tablename__ = 'professor_reviews'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    professor_email = Column(CITEXT, ForeignKey('professors.email', ondelete='CASCADE'), nullable=False)
    professor_name = Column(Text, nullable=False)
    review_text = Column(Text, nullable=False)
    interview_type = Column(SmallInteger, nullable=True)
    difficulty = Column(SmallInteger, nullable=True)
    stars = Column(SmallInteger, nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SmallInteger, server_default='1', nullable=False)
    visible = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meta_data = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_reviews_prof', 'professor_email'),
        Index('idx_reviews_user', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='professor_reviews')
    professor = relationship('Professor', back_populates='reviews')
    comments = relationship('Comment', back_populates='review', cascade='all, delete-orphan')
    votes = relationship('ReviewVote', back_populates='review', cascade='all, delete-orphan')


# ============================================
# COMMENTS
# ============================================
class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey('professor_reviews.id', ondelete='CASCADE'), nullable=False)
    commenter_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    parent_comment = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=True)
    comment_text = Column(Text, nullable=False)
    visible = Column(Boolean, server_default='true', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_comments_review', 'review_id'),
    )
    
    # Relationships
    review = relationship('ProfessorReview', back_populates='comments', foreign_keys=[review_id])
    commenter = relationship('User', back_populates='comments', foreign_keys=[commenter_email])
    parent = relationship('Comment', remote_side=[id], backref='replies')
    votes = relationship('CommentVote', back_populates='comment', cascade='all, delete-orphan')


# ============================================
# VOTES
# ============================================
class ReviewVote(Base):
    __tablename__ = 'review_votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey('professor_reviews.id', ondelete='CASCADE'), nullable=False)
    voter_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    vote = Column(SmallInteger, nullable=False)  # 1=upvote, -1=downvote
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('review_id', 'voter_email', name='uq_review_vote'),
        Index('idx_review_votes_review', 'review_id'),
    )
    
    # Relationships
    review = relationship('ProfessorReview', back_populates='votes')
    voter = relationship('User', back_populates='review_votes', foreign_keys=[voter_email])


class CommentVote(Base):
    __tablename__ = 'comment_votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey('comments.id', ondelete='CASCADE'), nullable=False)
    voter_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    vote = Column(SmallInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('comment_id', 'voter_email', name='uq_comment_vote'),
        Index('idx_comment_votes_comment', 'comment_id'),
    )
    
    # Relationships
    comment = relationship('Comment', back_populates='votes')
    voter = relationship('User', back_populates='comment_votes', foreign_keys=[voter_email])


# ============================================
# CHATBOT LOGS
# ============================================
class ChatLog(Base):
    __tablename__ = 'chat_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    model_name = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    context_id = Column(Text, nullable=True)
    rating = Column(SmallInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_chat_logs_user', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='chat_logs')


# ============================================
# API TOKENS
# ============================================
class APIToken(Base):
    __tablename__ = 'api_tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    token_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    name = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_api_tokens_user', 'user_email'),
    )
    
    # Relationships
    user = relationship('User', back_populates='api_tokens')


# ============================================
# METRICS
# ============================================
class Metric(Base):
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=True)
    metric_key = Column(Text, nullable=False)
    metric_value = Column(Numeric, nullable=True)
    meta = Column(JSONB, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_email', 'metric_key', name='uq_metric'),
    )
    
    # Relationships
    user = relationship('User', back_populates='metrics')


# ============================================
# MISC TABLES
# ============================================
class ProfessorList(Base):
    __tablename__ = 'professor_lists'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    file_path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='professor_lists')


class EmailProperty(Base):
    __tablename__ = 'email_properties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(CITEXT, ForeignKey('users.email', ondelete='CASCADE'), nullable=False)
    app_password = Column(Text, nullable=False)
    provider = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_email', 'provider', name='uq_email_property'),
    )
    
    # Relationships
    user = relationship('User', back_populates='email_properties')


class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_email = Column(CITEXT, ForeignKey('users.email', ondelete='SET NULL'), nullable=True)
    file_path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    owner = relationship('User', back_populates='files')

