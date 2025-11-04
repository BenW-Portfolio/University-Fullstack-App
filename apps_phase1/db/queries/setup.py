import sqlite3
import random
#from werkzeug.security import generate_password_hash

DROP_ALL_SQL = """
DROP TABLE IF EXISTS DECISION;
DROP TABLE IF EXISTS REVIEW;
DROP TABLE IF EXISTS TRANSCRIPT;
DROP TABLE IF EXISTS DEGREES;
DROP TABLE IF EXISTS RECOMMENDATION;
DROP TABLE IF EXISTS ACADEMIC_INFO;
DROP TABLE IF EXISTS APPLICATIONS;
DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS RECOMMENDATION_REQUESTS;
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS recommendation_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    applicant_name TEXT,
    recommender_name TEXT,
    recommender_email TEXT,
    affiliation TEXT,
    status TEXT DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP,
    letter TEXT
);

CREATE TABLE IF NOT EXISTS USERS (
    user_id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    role TEXT NOT NULL CHECK (role IN ('applicant', 'reviewer', 'gs', 'cac', 'admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE APPLICATIONS (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    ssn VARCHAR(11) UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    address TEXT,
    phone VARCHAR(15),
    email TEXT,
    
    degree_program TEXT NOT NULL CHECK (degree_program IN ('MS', 'PhD')),
    admission_semester TEXT NOT NULL CHECK (admission_semester IN ('Spring', 'Fall')),
    admission_year INTEGER NOT NULL CHECK (admission_year <= CAST(strftime('%Y', CURRENT_DATE) AS INTEGER) + 1),

    gre_verbal INTEGER CHECK (gre_verbal BETWEEN 130 AND 170),
    gre_quant INTEGER CHECK (gre_quant BETWEEN 130 AND 170),
    gre_year INTEGER,
    gre_subject_score INTEGER,
    gre_subject TEXT,

    toefl_score INTEGER,
    toefl_exam_date TEXT,

    bs_gpa REAL,
    bs_major TEXT,
    bs_year INTEGER,
    bs_university TEXT,

    ms_gpa REAL,
    ms_major TEXT,
    ms_year INTEGER,
    ms_university TEXT,

    interests TEXT,
    experience TEXT,

    transcript_received INTEGER DEFAULT 0, -- SQLite uses 0/1 for booleans
    recommendation_received INTEGER DEFAULT 0,

    status TEXT DEFAULT 'Application Incomplete' 
        CHECK (status IN (
            'Application Incomplete',
            'Application Submitted & Under Review',
            'Admitted',
            'Rejected'
        )),
    FOREIGN KEY (user_id) REFERENCES USERS(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ACADEMIC_INFO (
    application_id INTEGER PRIMARY KEY,
    gre_verbal INTEGER CHECK (gre_verbal BETWEEN 130 AND 170),
    gre_quant INTEGER CHECK (gre_quant BETWEEN 130 AND 170),
    gre_advanced INTEGER,
    gre_subject TEXT,
    toefl_score INTEGER,
    toefl_date TEXT,
    areas_of_interest TEXT,
    work_experience TEXT,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS RECOMMENDATION (
    letter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    recommender_name TEXT NOT NULL,
    recommender_email TEXT NOT NULL,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    generic_flag INTEGER DEFAULT 0,
    credible_flag INTEGER DEFAULT 0,
    submitted INTEGER DEFAULT 0,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS DEGREES (
    degree_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    degree_type TEXT NOT NULL CHECK (degree_type IN ('BS', 'MS')),
    gpa REAL,
    major TEXT,
    year INTEGER,
    university TEXT,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS TRANSCRIPT (
    transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    received INTEGER DEFAULT 0,
    received_date TEXT,
    received_by INTEGER,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id) ON DELETE CASCADE,
    FOREIGN KEY (received_by) REFERENCES USERS(user_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS REVIEW (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    rating TEXT NOT NULL CHECK (rating IN ('1', '2', '3', '4')),
    deficiency_courses TEXT,
    reject_reason TEXT CHECK (reject_reason IN ('A', 'B', 'C', 'D', 'E')),
    comments TEXT,
    recommended_advisor INTEGER,
    review_date TEXT NOT NULL,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id),
    FOREIGN KEY (faculty_id) REFERENCES USERS(user_id),
    FOREIGN KEY (recommended_advisor) REFERENCES USERS(user_id)
);

CREATE TABLE IF NOT EXISTS DECISION (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('Admit with Aid', 'Admit', 'Reject')),
    decided_by INTEGER NOT NULL,  
    decision_date TEXT NOT NULL,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id),
    FOREIGN KEY (decided_by) REFERENCES USERS(user_id)
);
"""

def generate_uid(conn):
    while True:
        candidate = str(random.randint(10000000, 99999999))
        exists = conn.execute("SELECT 1 FROM APPLICATIONS WHERE user_id = ?", (candidate,)).fetchone()
        if not exists:
            return candidate

def init_db():
    conn = sqlite3.connect("./db/app.db")
    cursor = conn.cursor()

    # Drop and recreate all tables
    cursor.executescript(DROP_ALL_SQL)
    cursor.executescript(SCHEMA_SQL)

    # Insert fake user
    cursor.execute("""
        INSERT INTO USERS (email, password, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("fake@gmail.com", "fakefake", "applicant", "f", "l"))
    cursor.execute("""
        INSERT INTO USERS (email, password, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("gs@gmail.com", "gggggggg", "gs", "g", "s"))
    cursor.execute("""
        INSERT INTO USERS (email, password, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("cac@gmail.com", "cccccccc", "cac", "c", "ac"))
    cursor.execute("""
        INSERT INTO USERS (email, password, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("admin@gmail.com", "aaaaaaaa", "admin", "a", "dmin"))
    cursor.execute("""
        INSERT INTO USERS (email, password, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
    """, ("reviewer@gmail.com", "rrrrrrrr", "reviewer", "r", "eviewer"))
    user_id = cursor.lastrowid

    conn.commit()
    conn.close()
