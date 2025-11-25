"""
Seed the database with deterministic test data via SQLAlchemy ORM.

Usage:
    python seed_test_data.py
"""
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import text

from api.database import SessionLocal, engine
from api.db_models import (
    EmailQueue,
    Base,
    EmailTemplate,
    Professor,
    ProfessorContact,
    SendLog,
    SendingRules,
    TemplateFile,
    User,
)


TEST_USER_EMAIL = "test.user@example.com"


def upsert_user(session):
    user = session.get(User, TEST_USER_EMAIL)
    if user:
        return user

    user = User(
        email=TEST_USER_EMAIL,
        password_hash="",
        is_active=True,
        display_name="Test User",
    )
    session.add(user)
    session.flush()
    return user


def create_templates(session, user_email) -> List[EmailTemplate]:
    existing = (
        session.query(EmailTemplate)
        .filter(EmailTemplate.user_email == user_email)
        .order_by(EmailTemplate.created_at.desc())
        .all()
    )
    if existing:
        return existing

    templates = []
    subjects = [
        "Initial Outreach",
        "First Reminder",
        "Second Reminder",
        "Third Reminder",
    ]
    bodies = [
        "<p>Hello Professor, this is the initial email.</p>",
        "<p>Following up on my previous message.</p>",
        "<p>Second reminder with additional details.</p>",
        "<p>Final reminder before closing the loop.</p>",
    ]

    for idx, subject in enumerate(subjects):
        template = EmailTemplate(
            user_email=user_email,
            subject=subject,
            template_body=bodies[idx],
            template_type=idx,
        )
        session.add(template)
        session.flush()

        attachment = TemplateFile(
            email_template_id=template.id,
            file_path=f"C:/attachments/{subject.replace(' ', '_').lower()}.pdf",
        )
        session.add(attachment)
        templates.append(template)

    session.flush()
    return templates


def ensure_sending_rules(session, user_email):
    existing = (
        session.query(SendingRules)
        .filter(SendingRules.user_email == user_email)
        .first()
    )
    if existing:
        return existing

    rules = SendingRules(
        user_email=user_email,
        main_mail_number=5,
        reminder_one=3,
        reminder_two=2,
        reminder_three=1,
        local_professor_time=True,
        max_email_per_university=2,
        send_working_day_only=True,
        period_between_reminders=5,
        delay_sending_mail=1,
    )
    session.add(rules)
    session.flush()
    return rules


def create_professor_contacts(session, user_email):
    professors = [
        ("dr.emma@university.edu", "Emma Stone"),
        ("prof.jackson@campus.edu", "Michael Jackson"),
        ("advisor.lee@college.edu", "Sophie Lee"),
    ]

    for email, name in professors:
        professor = session.get(Professor, email)
        if not professor:
            professor = Professor(
                email=email,
                name=name,
                major="Computer Science",
            )
            session.add(professor)
            session.flush()

        contact = (
            session.query(ProfessorContact)
            .filter(
                ProfessorContact.professor_email == email,
                ProfessorContact.user_email == user_email,
            )
            .first()
        )
        if contact:
            continue

        contact = ProfessorContact(
            professor_email=email,
            user_email=user_email,

            contact_status=3,  # replied
        )
        session.add(contact)


def create_queue_and_logs(session, user_email, templates):
    now = datetime.now(timezone.utc)

    # Email queue entries
    for idx in range(3):
        queue_item = EmailQueue(
            user_email=user_email,
            to_email=f"prospect{idx + 1}@example.com",
            subject=f"Queued Email {idx + 1}",
            body=f"<p>This is queued email #{idx + 1}.</p>",
            template_id=templates[idx % len(templates)].id,
            scheduled_at=now + timedelta(days=idx),
            status=0,
        )
        session.add(queue_item)

    # Send log entries
    for idx in range(3):
        log = SendLog(
            user_email=user_email,
            sent_to=f"sent{idx + 1}@example.com",
            subject=f"Sent Email {idx + 1}",
            body=f"<p>This is sent email #{idx + 1}.</p>",
            template_id=templates[idx % len(templates)].id,
            send_type=idx % 4,
            delivery_status=1,
        )
        session.add(log)


def main():
    # Ensure tables exist before attempting to insert data
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        user = upsert_user(session)
        templates = create_templates(session, user.email)
        ensure_sending_rules(session, user.email)
        create_professor_contacts(session, user.email)
        create_queue_and_logs(session, user.email, templates)

        session.commit()
        print("✅ Seed data inserted successfully.")
    except Exception as exc:
        session.rollback()
        print(f"❌ Failed to seed data: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

