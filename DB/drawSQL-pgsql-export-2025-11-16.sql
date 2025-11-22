-- extensions
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE user_education_information (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    major TEXT NOT NULL,
    university_id INT REFERENCES universities(id) ON DELETE SET NULL,
    education_level SMALLINT NOT NULL,        -- 0=BSc,1=MSc,2=PhD, etc.
    grade NUMERIC(4,2),                       -- GPA or percentage
    IELTS NUMERIC(3,1),                        -- e.g., 7.5
    GRE NUMERIC(4,1),                          -- e.g., 320.5
    google_scholar_link TEXT,
    CV_path TEXT,
    SOP_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
Alter table user_education_information add column university_department text;

-- Optional: index for fast lookups per user
CREATE INDEX idx_user_education_email ON user_education_information(user_email);

----------------------------
-- USERS / AUTH
----------------------------
CREATE TABLE users (
    email CITEXT PRIMARY KEY,                 -- case-insensitive unique user id
    password_hash TEXT NOT NULL,              -- store salted+hashed password (bcrypt/argon2)
    password_salt TEXT,                       -- optional, if your scheme uses explicit salt
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts SMALLINT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_name TEXT,
    profile_image TEXT,
    personal_website TEXT,
    backup_email CITEXT UNIQUE,               -- optional backup, validated at app level
    CHECK (email <> '')                       -- basic sanity
);
-- reference index (fast lookup by email domain or lower)
CREATE INDEX idx_users_created_at ON users(created_at);

----------------------------
-- UNIVERSITY / DEPARTMENT (normalized)
----------------------------
CREATE TABLE universities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    country CHAR(2),               -- ISO 3166-1 alpha-2 code (nullable if unknown)
    website TEXT
);
CREATE UNIQUE INDEX unique_name_lower_idx
ON universities ((LOWER(name)));

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
    university_deparment_name TEXT NOT NULL UNIQUE
);

----------------------------
-- PREMIUM / SUBSCRIPTIONS
----------------------------
-- current active subscription (one per user typically)
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status SMALLINT NOT NULL DEFAULT 1,  -- 1=active,2=cancelled,3=expired
    UNIQUE(user_email)                   -- ensure one active subscription row per user (if desired)
);

-- history of all subscription changes/payments
CREATE TABLE subscription_history (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    payment_reference TEXT,
    status SMALLINT NOT NULL,   -- same status codes
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_subscription_history_user ON subscription_history(user_email);

----------------------------
-- PROFESSORS, POSITIONS, CONTACTS
----------------------------
CREATE TABLE professors (
    email CITEXT PRIMARY KEY,
    name TEXT NOT NULL,
    major TEXT,
    university_id INTEGER REFERENCES universities(id) ON DELETE SET NULL,
    professor_img TEXT,
    meta_data JSONB
);
alter table professors add column department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL;

CREATE TABLE professor_research_interests (
    id SERIAL PRIMARY KEY,
    professor_email CITEXT NOT NULL REFERENCES professors(email) ON DELETE CASCADE,
    interest TEXT NOT NULL
);

CREATE INDEX idx_prof_interests_prof ON professor_research_interests(professor_email);
CREATE INDEX idx_prof_interest_text ON professor_research_interests(interest);

CREATE TABLE open_positions (
    id BIGSERIAL PRIMARY KEY,
    university_id INTEGER REFERENCES universities(id) ON DELETE SET NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    position_title TEXT NOT NULL,
    fund TEXT,
    min_ielts NUMERIC(3,1),
    min_gre NUMERIC(4,1),
    contact_email CITEXT,
    requirements JSONB,
    supervisor CITEXT,                    -- professor email or free-text
    deadline DATE,
    description TEXT,
    more_info_link TEXT,
    graduate_level SMALLINT,              -- e.g., 1 = MSc, 2 = PhD
    meta_data JSONB,
    country TEXT
);
ALTER TABLE open_positions
    ADD CONSTRAINT open_positions_supervisor_fk
    FOREIGN KEY (supervisor) REFERENCES professors(email) ON DELETE SET NULL;

alter table open_positions rename column supervisor to supervisor_email;

CREATE INDEX idx_open_positions_university ON open_positions(university_id);
CREATE INDEX idx_open_positions_deadline ON open_positions(deadline);

-- records of contact attempts to a professor (per user)
CREATE TABLE professor_contact (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    professor_email CITEXT REFERENCES professors(email) ON DELETE SET NULL,
    position_id BIGINT REFERENCES open_positions(id) ON DELETE SET NULL,
    last_contact_time TIMESTAMP WITH TIME ZONE,
    next_contact_time TIMESTAMP WITH TIME ZONE,
    contact_status SMALLINT NOT NULL DEFAULT 0,  -- 0=not_sent,1=sent,2=waiting_reply,3=replied,4=failed
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    attempts SMALLINT NOT NULL DEFAULT 0,
    UNIQUE(user_email, professor_email, position_id) -- prevent duplicate contact tracks
);
CREATE INDEX idx_prof_contact_user ON professor_contact(user_email);
CREATE INDEX idx_prof_contact_prof ON professor_contact(professor_email);

----------------------------
-- SAVED POSITIONS (user bookmarks & application status)
----------------------------
CREATE TABLE saved_positions (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    position_id BIGINT NOT NULL REFERENCES open_positions(id) ON DELETE CASCADE,
    status SMALLINT NOT NULL DEFAULT 0, -- 0=saved,1=applied,2=rejected,3=interviewing,4=offer
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE(user_email, position_id)
);
CREATE INDEX idx_saved_positions_user ON saved_positions(user_email);

----------------------------
-- EMAIL / TEMPLATE / FILES / SENDING RULES / QUEUE / LOG
----------------------------
CREATE TABLE email_templates (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    template_body TEXT NOT NULL,
    template_type SMALLINT NOT NULL,  -- e.g. 0=generic,1=followup...
    subject TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE TABLE template_files (
    id SERIAL PRIMARY KEY,
    email_template_id INTEGER NOT NULL REFERENCES email_templates(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL
);

CREATE TABLE sending_rules (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    main_mail_number SMALLINT NOT NULL DEFAULT 1,
    reminder_one SMALLINT NOT NULL DEFAULT 0,
    reminder_two SMALLINT NOT NULL DEFAULT 0,
    reminder_three SMALLINT NOT NULL DEFAULT 0,
    local_professor_time BOOLEAN NOT NULL DEFAULT TRUE,
    max_email_per_university SMALLINT NOT NULL DEFAULT 3,
    send_working_day_only BOOLEAN NOT NULL DEFAULT TRUE,
    period_between_reminders SMALLINT NOT NULL DEFAULT 7,  -- days
    delay_sending_mail SMALLINT NOT NULL DEFAULT 0,        -- minutes
    start_time_send TIME WITH TIME ZONE DEFAULT '09:00:00'::time,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_sending_rules_user ON sending_rules(user_email);

-- queue table used by worker to actually send emails
CREATE TABLE email_queue (
    id BIGSERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    to_email CITEXT NOT NULL,
    subject TEXT,
    body TEXT,
    template_id INTEGER REFERENCES email_templates(id) ON DELETE SET NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status SMALLINT NOT NULL DEFAULT 0, -- 0=pending,1=sent,2=failed,3=retrying
    retry_count SMALLINT NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX idx_email_queue_status_sched ON email_queue(status, scheduled_at);
CREATE INDEX idx_email_queue_user_sched ON email_queue(user_email, scheduled_at);

-- send log with many rows per user
CREATE TABLE send_log (
    id BIGSERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    sent_to CITEXT NOT NULL,
    sent_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    subject TEXT,
    body TEXT,
    template_id INTEGER REFERENCES email_templates(id) ON DELETE SET NULL,
    send_type SMALLINT NOT NULL,  -- enum describing type of email
    delivery_status SMALLINT NOT NULL, -- e.g. 0=queued,1=sent,2=bounced
    remote_message_id TEXT
);
CREATE INDEX idx_send_log_user_time ON send_log(user_email, sent_time DESC);

----------------------------
-- REVIEWS, COMMENTS, VOTES
----------------------------
CREATE TABLE professor_reviews (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    professor_email CITEXT NOT NULL REFERENCES professors(email) ON DELETE CASCADE,
    professor_name TEXT NOT NULL,
    review_text TEXT NOT NULL,
    interview_type SMALLINT,
    difficulty SMALLINT,
    stars SMALLINT,
    interview_date TIMESTAMP WITH TIME ZONE,
    status SMALLINT NOT NULL DEFAULT 1,
    visible BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    meta_data JSONB
);

CREATE INDEX idx_reviews_prof ON professor_reviews(professor_email);
CREATE INDEX idx_reviews_user ON professor_reviews(user_email);

CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES professor_reviews(id) ON DELETE CASCADE,
    commenter_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    parent_comment INTEGER REFERENCES comments(id) ON DELETE CASCADE, -- nullable for root comments
    comment_text TEXT NOT NULL,
    visible BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX idx_comments_review ON comments(review_id);

CREATE TABLE review_votes (
    id SERIAL PRIMARY KEY,
    review_id INTEGER NOT NULL REFERENCES professor_reviews(id) ON DELETE CASCADE,
    voter_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    vote SMALLINT NOT NULL,  -- 1=upvote, -1=downvote (or use boolean)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE(review_id, voter_email)
);
CREATE INDEX idx_review_votes_review ON review_votes(review_id);

CREATE TABLE comment_votes (
    id SERIAL PRIMARY KEY,
    comment_id INTEGER NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    voter_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    vote SMALLINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE(comment_id, voter_email)
);
CREATE INDEX idx_comment_votes_comment ON comment_votes(comment_id);

----------------------------
-- CHATBOT LOGS
----------------------------
CREATE TABLE chat_logs (
    id BIGSERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    model_name TEXT,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens_used INTEGER,
    latency_ms INTEGER,
    context_id TEXT,
    rating SMALLINT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX idx_chat_logs_user ON chat_logs(user_email);

----------------------------
-- API TOKENS (for app/api)
----------------------------
CREATE TABLE api_tokens (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    expires_at TIMESTAMP WITH TIME ZONE,
    name TEXT
);
CREATE INDEX idx_api_tokens_user ON api_tokens(user_email);

----------------------------
-- STATISTICS / METRICS (simple flexible store)
----------------------------
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    user_email CITEXT REFERENCES users(email) ON DELETE CASCADE,
    metric_key TEXT NOT NULL,
    metric_value NUMERIC,
    meta JSONB,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    UNIQUE(user_email, metric_key)
);

----------------------------
-- OTHER / MISC
----------------------------
-- professor lists (files uploaded by user)
CREATE TABLE professor_lists (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- email properties (app-specific credentials) - encrypted at app-level
CREATE TABLE email_properties (
    id SERIAL PRIMARY KEY,
    user_email CITEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    app_password TEXT NOT NULL,
    provider TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX idx_email_properties_user_provider ON email_properties(user_email, provider);

-- files generic (if you need global file registry)
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    owner_email CITEXT REFERENCES users(email) ON DELETE SET NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
-- conditions
-- Education level
CREATE TYPE education_level_enum AS ENUM ('BSc', 'MSc', 'PhD', 'PostDoc');

-- Subscription status
CREATE TYPE subscription_status_enum AS ENUM ('active', 'cancelled', 'expired');

-- Contact status
CREATE TYPE contact_status_enum AS ENUM ('not_sent', 'sent', 'waiting_reply', 'replied', 'failed');

-- Saved positions status
CREATE TYPE position_status_enum AS ENUM ('saved','applied','rejected','interviewing','offer');

-- Email queue status
CREATE TYPE email_queue_status_enum AS ENUM ('pending','sent','failed','retrying');

ALTER TABLE user_education_information
    ADD CONSTRAINT chk_ielts_range CHECK (IELTS IS NULL OR (IELTS >= 0 AND IELTS <= 9)),
    ADD CONSTRAINT chk_gre_range CHECK (GRE IS NULL OR (GRE >= 130 AND GRE <= 340)),
    ADD CONSTRAINT chk_grade CHECK (grade IS NULL OR grade BETWEEN 0 AND 100);

ALTER TABLE user_education_information
    ALTER COLUMN education_level TYPE education_level_enum
    USING
    CASE education_level
        WHEN 0 THEN 'BSc'::education_level_enum
        WHEN 1 THEN 'MSc'::education_level_enum
        WHEN 2 THEN 'PhD'::education_level_enum
        ELSE 'BSc'::education_level_enum
    END;
