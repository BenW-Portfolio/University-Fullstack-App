DROP TABLE IF EXISTS APPLICATIONS;
DROP TABLE IF EXISTS ACADEMIC_INFO;
DROP TABLE IF EXISTS RECOMMENDATION;
DROP TABLE IF EXISTS DEGREES;
DROP TABLE IF EXISTS TRANSCRIPT;
DROP TABLE IF EXISTS REVIEW;
DROP TABLE IF EXISTS DECISION;


-- USERS table (already correct for SQLite)

/* CREATE TABLE USERS (
    user_id INTEGER PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    password VARCHAR(255) NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('applicant', 'reviewer', 'gs', 'cac', 'admin')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP;
);
*/


-- Application table 
CREATE TABLE APPLICATIONS (
    application_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    ssn VARCHAR(11) UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    address TEXT,
    phone VARCHAR(15),
    email VARCHAR(100),
    
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
            'Rejected',
            'Offer Accepted',
            'Offer Declined'
        )),

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Academic details 
CREATE TABLE ACADEMIC_INFO (
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

-- Recommendation
CREATE TABLE RECOMMENDATION (
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

-- Degrees
CREATE TABLE DEGREES (
    degree_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    degree_type TEXT NOT NULL CHECK (degree_type IN ('BS', 'MS')),
    gpa REAL,
    major TEXT,
    year INTEGER,
    university TEXT,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id) ON DELETE CASCADE
);

-- Transcript tracking 
CREATE TABLE TRANSCRIPT (
    transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    received INTEGER DEFAULT 0,
    received_date TEXT,
    received_by INTEGER,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id) ON DELETE CASCADE,
    FOREIGN KEY (received_by) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Reviews table 
CREATE TABLE REVIEW (
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
    FOREIGN KEY (faculty_id) REFERENCES users(user_id),
    FOREIGN KEY (recommended_advisor) REFERENCES users(user_id)
);

-- Decision table 
CREATE TABLE DECISION (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('Admit with Aid', 'Admit', 'Reject')),
    decided_by INTEGER NOT NULL,  
    decision_date TEXT NOT NULL,
    FOREIGN KEY (application_id) REFERENCES APPLICATIONS(application_id),
    FOREIGN KEY (decided_by) REFERENCES users(user_id)
);


DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS prerequisites;
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS rooms;


-- Users Table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    passcode VARCHAR(255) NOT NULL,

    email TEXT UNIQUE,
 --   password TEXT,
    role TEXT CHECK (role IN ('alumni','instructor','student', 'advisor', 'gradSec', 'admin', 'applicant', 'reviewer', 'gs', 'cac', 'advisor/instructor', 'advisor/instructor/reviewer')),

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    address VARCHAR(255),
    program VARCHAR(50),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP

    -- user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- username VARCHAR(255) UNIQUE NOT NULL,
    -- passcode VARCHAR(255) NOT NULL,
    -- role VARCHAR(50) NOT NULL,
    -- first_name VARCHAR(255) NOT NULL,
    -- last_name VARCHAR(255) NOT NULL,
    -- address VARCHAR(255),
    -- program VARCHAR(50)
);

-- Courses Table (Course Catalog)
CREATE TABLE courses (
    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code VARCHAR(10) NOT NULL,
    course_number VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    credits INT NOT NULL,
    UNIQUE (dept_code, course_number)
);

-- Prerequisites Table
CREATE TABLE prerequisites (
    prerequisite_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INT,
    prerequisite_course_id INT,
    type VARCHAR(50), -- 'main', 'secondary'
    FOREIGN KEY (course_id) REFERENCES Courses(course_id),
    FOREIGN KEY (prerequisite_course_id) REFERENCES Courses(course_id)
);

CREATE TABLE rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT NOT NULL UNIQUE, -- e.g., 'Tompkins Hall 405', 'SEH B1220'
    capacity INTEGER NOT NULL CHECK (capacity > 0)
);

-- Sections Table (Course Schedule/Offerings)
CREATE TABLE sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INT,
    semester VARCHAR(50) NOT NULL, -- e.g., 'Fall'
    year INT NOT NULL, -- e.g., 2024
    day VARCHAR(10) NOT NULL, -- 'M', 'T', 'W', 'R', 'F'
    time_slot VARCHAR(20) NOT NULL, -- '1500-1730'
    instructor_id INT, -- Foreign Key referencing Users (instructors)
    room_id INT,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id),
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

-- Enrollments Table (Student Course Registrations)
CREATE TABLE enrollments (
    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INT,
    section_id INT,
    grade VARCHAR(10), -- 'A', 'B+', 'IP', etc.
    FOREIGN KEY (student_id) REFERENCES Users(user_id),
    FOREIGN KEY (section_id) REFERENCES Sections(section_id)
);


-- Populate Rooms Table
INSERT INTO rooms (location, capacity) VALUES
('Tompkins Hall 405', 30),
('Tompkins Hall 406', 25),
('SEH B1220', 50),
('SEH 4040', 40),
('SEH 1450', 10),
('Online', 30);

-- Populate Courses Table
INSERT INTO Courses (dept_code, course_number, title, credits) VALUES
('CSCI', '6221', 'SW Paradigms', 3),
('CSCI', '6461', 'Computer Architecture', 3),
('CSCI', '6212', 'Algorithms', 3),
('CSCI', '6220', 'Machine Learning', 3),
('CSCI', '6232', 'Networks 1', 3),
('CSCI', '6233', 'Networks 2', 3),
('CSCI', '6241', 'Database 1', 3),
('CSCI', '6242', 'Database 2', 3),
('CSCI', '6246', 'Compilers', 3),
('CSCI', '6260', 'Multimedia', 3),
('CSCI', '6251', 'Cloud Computing', 3),
('CSCI', '6254', 'SW Engineering', 3),
('CSCI', '6262', 'Graphics 1', 3),
('CSCI', '6283', 'Security 1', 3),
('CSCI', '6284', 'Cryptography', 3),
('CSCI', '6286', 'Network Security', 3),
('CSCI', '6325', 'Algorithms 2', 3),
('CSCI', '6339', 'Embedded Systems', 3),
('CSCI', '6384', 'Cryptography 2', 3),
('ECE', '6241', 'Communication Theory', 3),
('ECE', '6242', 'Information Theory 2', 2),
('MATH', '6210', 'Logic', 2);

-- Populate Prerequisites Table
INSERT INTO Prerequisites (course_id, prerequisite_course_id, type) VALUES
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6233'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6232'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6242'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6241'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6246'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6246'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'secondary'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6251'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6254'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6221'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6283'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6284'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6286'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6283'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6286'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6232'), 'secondary'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6325'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6339'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'main'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6339'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'secondary'),
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6384'), (SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6284'), 'main');

-- Populate Users Table
--INSERT INTO users (user_id, username, passcode, role, first_name, last_name, program) VALUES

INSERT INTO Users (user_id, username, passcode, role, first_name, last_name, program) VALUES
--('77777777', 'akhil', 'akhilpass', 'student', 'Akhil', 'Vanka', 'PHD'),  
('88888888', 'billie', 'billiepass', 'student', 'Billie', 'Holiday', 'MASTERS'), 
('99999999', 'diana', 'dianapass', 'student', 'Diana', 'Krall', 'MASTERS'); 

-- 'applicant', 'reviewer', 'gs', 'cac'
INSERT INTO users (username, passcode, role, first_name, last_name) VALUES
('gsuser', 'testpass', 'gs', 'Grad', 'Secretary'),
--('narahari', 'testpass', 'advisor/instructor/reviewer', 'Narahari', '3role'),
--('parmer', 'testpass', 'advisor', 'Gabe', 'Parmer'),
('narahari2', 'testpass', 'advisor', 'Narahari2', 'Instructor2'),
('choi', 'testpass', 'instructor', 'Choi', 'Instructor'),
--('choi', 'testpass', 'advisor', 'Choi', 'Instructor'),--
('admin', 'testpass', 'admin', 'System', 'Admin'),
('applicant', 'testpass', 'applicant', 'applicant_first_name', 'applicant_last_name'),
('reviewer', 'testpass', 'reviewer', 'reviewer_first_name', 'Instructor_last_name'),
('cac', 'testpass', 'cac', 'cac_first_name', 'cac_last_name');

INSERT INTO Users (user_id, username, passcode, role, first_name, last_name) VALUES
(14341231, 'narahari', 'testpass', 'advisor/instructor/reviewer', 'Narahari', '3role'),
(14341232, 'parmer', 'testpass', 'advisor', 'Gabe', 'Parmer');
--('choi', 'testpass', 'instructor', 'Choi', 'Instructor'),
--('admin', 'testpass', 'admin', 'System', 'Admin');

-- Populate Sections Table
INSERT INTO Sections (course_id, semester, year, day, time_slot, room_id) VALUES
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6221'), 'Fall', 2024, 'M', '1500-1730', 1), -- CourseID 1
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'Fall', 2024, 'T', '1500-1730', 2), -- CourseID 2
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'Fall', 2024, 'W', '1500-1730', 3), -- CourseID 3
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6232'), 'Fall', 2024, 'M', '1800-2030', 5), -- CourseID 4
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6233'), 'Fall', 2024, 'T', '1800-2030', 3), -- CourseID 5
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6241'), 'Fall', 2024, 'W', '1800-2030', 5), -- CourseID 6
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6242'), 'Fall', 2024, 'R', '1800-2030', 3), -- CourseID 7
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6246'), 'Fall', 2024, 'T', '1500-1730', 5), -- CourseID 8
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6251'), 'Fall', 2024, 'M', '1800-2030', 3), -- CourseID 9
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6254'), 'Fall', 2024, 'M', '1530-1800', 5), -- CourseID 10
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6260'), 'Fall', 2024, 'R', '1800-2030', 4), -- CourseID 11
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6262'), 'Fall', 2024, 'W', '1800-2030', 6), -- CourseID 12
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6283'), 'Fall', 2024, 'T', '1800-2030', 6), -- CourseID 13
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6284'), 'Fall', 2024, 'M', '1800-2030', 4), -- CourseID 14
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6286'), 'Fall', 2024, 'W', '1800-2030', 4), -- CourseID 15
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6384'), 'Fall', 2024, 'W', '1500-1730', 6), -- CourseID 16
((SELECT course_id FROM Courses WHERE dept_code = 'ECE' AND course_number = '6241'), 'Fall', 2024, 'M', '1800-2030', 4), -- CourseID 17
((SELECT course_id FROM Courses WHERE dept_code = 'ECE' AND course_number = '6242'), 'Fall', 2024, 'T', '1800-2030', 4), -- CourseID 18
((SELECT course_id FROM Courses WHERE dept_code = 'MATH' AND course_number = '6210'), 'Fall', 2024, 'W', '1800-2030', 6), -- CourseID 19
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6339'), 'Fall', 2024, 'R', '1600-1830', 6); -- CourseID 20

-- Populate Section Table (Choi's classes)
INSERT INTO Sections (course_id, semester, year, day, time_slot, instructor_id, room_id) VALUES
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6221'), 'Fall', 2024, 'M', '1500-1730', (SELECT user_id FROM Users WHERE username = 'choi'), 1), -- CSCI 6221 assigned to choi
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'Fall', 2024, 'T', '1500-1730', (SELECT user_id FROM Users WHERE username = 'choi'), 2); -- CSCI 6461 assigned to choi

-- Populate Enrollments Table (Billie Holiday's Registrations)
INSERT INTO Enrollments (student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'diana'),  21, NULL); -- Enroll Diana in section 21 (CSCI 6221)
--ADS SECTION FROM PHASE 1---
--Drop all of the tables if they exist
DROP TABLE IF EXISTS students;
--DROP TABLE IF EXISTS users;--
-- DROP TABLE IF EXISTS advisor; -- 
DROP TABLE IF EXISTS alumni;
DROP TABLE IF EXISTS form1;
DROP TABLE IF EXISTS form1_courses;
DROP TABLE IF EXISTS advising;
DROP TABLE IF EXISTS form1ApprovalQueue;
DROP TABLE IF EXISTS initialAdvisingQueue_courses;
DROP TABLE IF EXISTS initialAdvisingQueue;
DROP TABLE IF EXISTS enroll;
DROP TABLE IF EXISTS audit;
DROP TABLE IF EXISTS thesisApproval;
DROP TABLE IF EXISTS graduateApplicationQueue;


-- Define all of the tables
/*CREATE TABLE users (
    userID      INT PRIMARY KEY, 
    username    varchar(25) UNIQUE,
    password    varchar(50), -- Maybe make more restrictive than this? ie. More than 8 chars include a number/symbol --
    fname       varchar(25),
    lname       varchar(25),
    role        varchar(7) -- Either admin, student, advisor, gradSec, or none --
    
);*/

CREATE TABLE students ( 
    userID      INT PRIMARY KEY,  
    address     varchar(50), -- This is on the ER diagram but what are we using it for? --
    program     varchar(3), -- Either phd or md --
    graduationDate  varchar(8), -- Given in S ****(Year) or F ****(Year) --
    approved    TINYINT, -- 1 for true, 0 for false --
    suspended   TINYINT, -- 1 for true, 0 for false --
    initial_advising_complete INTEGER DEFAULT 0 NOT NULL,
    --FOREIGN KEY (userID) REFERENCES users(userID)--  
    FOREIGN KEY (userID) REFERENCES users(user_id)  
 
);

CREATE TABLE alumni (
--Note that only a summary of their academic information should be kept in the Alumni table--
    userID      INT PRIMARY KEY, 
    address     varchar(50), -- This is on the ER diagram but what are we using it for? --
    program     varchar(3), -- Either phd or md --
    graduationDate  varchar(8), -- Given in S ****(Year) or F ****(Year) --
    
    FOREIGN KEY (userID) REFERENCES users(user_id)

);

--fetch all students in sql
--check if they are in the advisor table
--if they are not, they appear in the gradsec screen
--also make list of possible advisors to assign
--gradsec can execute sql statements to update advisor table

/*CREATE TABLE courses (
    courseID   INT PRIMARY KEY, 
    title      varchar(25),  -- The name of a course ie. Regression modeling --
    credits    TINYINT,
    code       TINYINT, -- The number of a course ie. 6521 --
    department  varchar(5), -- Written as it is in the catalog. For this project itll be CSCI -- 
    preReq1     varchar(10),
    preReq2     varchar(10),
    FOREIGN KEY (preReq1) REFERENCES courses(courseID),
    FOREIGN KEY (preReq2) REFERENCES courses(courseID)
);


CREATE TABLE sections (
    sectionID   INT, 
    course      INT,
    -- could add meeting time + location here but I don't really want to and I don't think we need to --
    PRIMARY KEY(sectionID, course),
    FOREIGN KEY (course) REFERENCES courses(courseID)
);

CREATE TABLE enroll (
    studentID   INT, 
    courseID    INT, 
    grade       varchar(10), -- Letter grade --
    semester    varchar(10), -- In S ****(year) or F ****(year) -- 
    PRIMARY KEY (studentID, courseID),
    FOREIGN KEY (studentID) REFERENCES students(userID), 
    FOREIGN KEY (courseID) REFERENCES courses(courseID)
);*/

CREATE TABLE audit (
    advisorID   INT, 
    studentID   INT,
    outcome     TINYINT, -- 1 for true, 0 for false --
    PRIMARY KEY(advisorID, studentID),
    FOREIGN KEY (advisorID) REFERENCES users(user_id)  --users(userID),--
    FOREIGN KEY (studentID) REFERENCES users(user_id)  --users(userID)--

);

CREATE TABLE thesisApproval(
    advisorID   INT,
    studentID   INT,
    PRIMARY KEY(advisorID, studentID),
    FOREIGN KEY (advisorID) REFERENCES users(user_id),
    FOREIGN KEY (studentID) REFERENCES users(user_id)

);

CREATE TABLE graduateApplicationQueue (
    userID INT PRIMARY KEY, 
    FOREIGN KEY (userID) REFERENCES users(user_id)
);

CREATE TABLE form1 (
    formID INTEGER PRIMARY KEY, -- SHOULD NOT AUTOINCREMENT, WASTE OF DB RESOURCES --
    studentID INTEGER NOT NULL,
    FOREIGN KEY (studentID) REFERENCES students(userID)
);

CREATE TABLE form1_courses (
    formID INT,
    courseID INT, 
    -- PRIMARY KEY (formID, courseID), -- 
    FOREIGN KEY (formID) REFERENCES form1(formID),
    FOREIGN KEY (courseID) REFERENCES courses (courseID)
);

CREATE TABLE form1ApprovalQueue (
    formID INT, 
    advisorID INT, 
    studentID INT,
    result INT, -- -1 for rejected, 0 for no reply, 1 for approved --
    FOREIGN KEY (formID) REFERENCES form1 (formID),
    FOREIGN KEY (advisorID) REFERENCES users (user_id),
    FOREIGN KEY (studentID) REFERENCES students(userID)
);


--WE CAN REMOVE UNIQUE CONSTRAINTS FOR THIS--
CREATE TABLE advising (
    advisorID INT,
    studentID INT,
    -- PRIMARY KEY (advisorID, studentID), --
    FOREIGN KEY (advisorID) REFERENCES users(user_id), 
    FOREIGN KEY (studentID) REFERENCES students(userID)
);

-- Sample data for users
--CHANGED NAME FROM MDSTUDENT TO MSSTUDENT
-- INSERT INTO users VALUES (1, 'ads_admin', 'password', 'admin', 'max', 'eichholz', 'tompkins', null);
-- INSERT INTO users VALUES (2, 'PHDstudent', 'password','student', 'phd', 'student', 'seh', 'phd');
-- INSERT INTO users VALUES (5, 'MSstudent', 'password', 'student', 'ms', 'student', 'seh', 'ms');
/*INSERT INTO users VALUES (6, 'suspend_test', 'password', 'Test', 'Suspend', 'student');
INSERT INTO users VALUES (3, 'advisor', 'password', 'advisor', 'lastname', 'advisor');
INSERT INTO users VALUES (7, 'advisor2', 'password', 'Alice', 'Johnson', 'advisor');
INSERT INTO users VALUES (4, 'gradSec', 'password', 'grad', 'Sec', 'gradSec');
*/
-- Sample data for students
INSERT INTO students VALUES (2, '2025 F Street', 'phd', 'S 2028',0, 0, 0);
INSERT INTO students VALUES (5, '2025 F Street', 'ms', 'S 2028',1, 0, 0);
INSERT INTO students VALUES (88888888, '2025 F Street', 'ms', 'S 2028',0, 0, 0);
INSERT INTO students VALUES (99999999, '2025 F Street', 'ms', 'S 2028',0, 0, 0);

--INSERT INTO students VALUES (5, '2025 F Street', 'ms', 'S 2028',1, 0, 0);
--INSERT INTO students VALUES (6, '2100 Eye Street', 'phd', 'S 2029', 0, 0, 0);--

--Sample data for graduating students--
--INSERT INTO graduateApplicationQueue VALUES (2);-
INSERT INTO graduateApplicationQueue VALUES (88888888);

-- Sample data for courses
/*INSERT INTO courses VALUES (1, 'SW Paradigms', 3, 6221, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (2, 'Computer Architecture', 3, 6461, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (3, 'Algorithms', 3, 6212, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (4, 'Machine Learning', 3, 6220, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (5, 'Networks 1', 3, 6232, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (6, 'Networks 2', 3, 6233, 'CSCI', 5, NULL);
INSERT INTO courses VALUES (7, 'Database 1', 3, 6241, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (8, 'Database 2', 3, 6242, 'CSCI', 7, NULL);
INSERT INTO courses VALUES (9, 'Compilers', 3, 6246, 'CSCI', 2, 3);
INSERT INTO courses VALUES (10, 'Multimedia', 3, 6260, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (11, 'Cloud Computing', 3, 6251, 'CSCI', 2, NULL);
INSERT INTO courses VALUES (12, 'SW Engineering', 3, 6254, 'CSCI', 1, NULL);
INSERT INTO courses VALUES (13, 'Graphics 1', 3, 6262, 'CSCI', NULL, NULL);
INSERT INTO courses VALUES (14, 'Security 1', 3, 6283, 'CSCI', 3, NULL);
INSERT INTO courses VALUES (15, 'Cryptography', 3, 6284, 'CSCI', 3, NULL);
INSERT INTO courses VALUES (16, 'Network Security', 3, 6286, 'CSCI', 14, 5);
INSERT INTO courses VALUES (17, 'Algorithms 2', 3, 6235, 'CSCI', 3, NULL);
INSERT INTO courses VALUES (18, 'Embedded Systems', 3, 6339, 'CSCI', 2, 3);
INSERT INTO courses VALUES (19, 'Cryptography 2', 3, 6384, 'CSCI', 15, NULL);
INSERT INTO courses VALUES (20, 'Communication Theory', 3, 6241, 'ECE', NULL, NULL); 
INSERT INTO courses VALUES (21, 'Information Theory', 2, 6242, 'ECE', NULL, NULL);
INSERT INTO courses VALUES (22, 'Logic', 2, 6210, 'MATH', NULL, NULL);


-- Sample data for course -- 
INSERT INTO sections VALUES (10, 3);


--Sample data for enrolls --
-- Enrollments for PhD student (userID = 2)
INSERT INTO enroll VALUES (2, 1, 'B+', 'S 2025');
INSERT INTO enroll VALUES (2, 3, 'A', 'F 2025'); 
INSERT INTO enroll VALUES (2, 4, 'A-', 'S 2026');
INSERT INTO enroll VALUES (2, 7, 'B', 'F 2026'); 
INSERT INTO enroll VALUES (2, 8, 'B', 'S 2027'); 
INSERT INTO enroll VALUES (2, 14, 'B+', 'F 2027'); 
INSERT INTO enroll VALUES (2, 15, 'A-', 'S 2028');
INSERT INTO enroll VALUES (2, 16, 'A-', 'S 2028');
INSERT INTO enroll VALUES (2, 17, 'A-', 'S 2028');
INSERT INTO enroll VALUES (2, 18, 'A-', 'S 2028');

--INSERT INTO enroll VALUES (2, 22, 'B+', 'F 2027');-- 
INSERT INTO enroll VALUES (2, 21, 'A', 'S 2028');
INSERT INTO enroll VALUES (2, 20, 'A-', 'S 2028'); 

-- Enrollments for MD student (userID = 5)
INSERT INTO enroll VALUES (5, 1, 'A-', 'S 2025'); 
INSERT INTO enroll VALUES (5, 2, 'B+', 'F 2025'); 
INSERT INTO enroll VALUES (5, 3, 'B+', 'F 2025'); 
INSERT INTO enroll VALUES (5, 5, 'B', 'S 2026'); 
INSERT INTO enroll VALUES (5, 6, 'A', 'F 2026'); 
INSERT INTO enroll VALUES (5, 10, 'A-', 'S 2027'); 
INSERT INTO enroll VALUES (5, 11, 'B+', 'F 2027'); 
INSERT INTO enroll VALUES (5, 12, 'A', 'S 2028');
--INSERT INTO enroll VALUES (5, 13, 'A', 'S 2028');
--INSERT INTO enroll VALUES (5, 14, 'A', 'S 2028');

INSERT INTO enroll VALUES (5, 20, 'A-', 'S 2027'); 
INSERT INTO enroll VALUES (5, 21, 'B+', 'F 2027'); 
INSERT INTO enroll VALUES (5, 22, 'A', 'S 2028');
-- Enrollments for suspended student (userID = 6)
INSERT INTO enroll VALUES (6, 2, 'C', 'F 2025');
INSERT INTO enroll VALUES (6, 3, 'D+', 'S 2026');
INSERT INTO enroll VALUES (6, 4, 'F', 'F 2026');
INSERT INTO enroll VALUES (6, 5, 'B-', 'S 2027'); 
*/

-- Sample data for form 1
INSERT INTO form1 VALUES (1, 2); 
INSERT INTO form1 VALUES (2, 5); 


-- Sample courses for the PhD student
INSERT INTO form1_courses VALUES (1, 1);  
INSERT INTO form1_courses VALUES (1, 3);  
INSERT INTO form1_courses VALUES (1, 4);  
INSERT INTO form1_courses VALUES (1, 7);  
INSERT INTO form1_courses VALUES (1, 8); 
INSERT INTO form1_courses VALUES (1, 14); 
INSERT INTO form1_courses VALUES (1, 15); 

-- Sample courses for the MD student
INSERT INTO form1_courses VALUES (2, 1);  
INSERT INTO form1_courses VALUES (2, 3);  
INSERT INTO form1_courses VALUES (2, 5);  
INSERT INTO form1_courses VALUES (2, 6);  
INSERT INTO form1_courses VALUES (2, 10); 
INSERT INTO form1_courses VALUES (2, 11); 
INSERT INTO form1_courses VALUES (2, 12); 

-- Sample advising relationships
INSERT INTO advising VALUES ((SELECT user_id FROM Users WHERE username = 'narahari'),55555555);
INSERT INTO advising VALUES ((SELECT user_id FROM Users WHERE username = 'parmer'),11111111);


/*INSERT INTO users (userID, username, password, fname, lname, role)
VALUES (8, 'noform1a', 'password', 'NoForm1', 'StudentA', 'student');

INSERT INTO students (userID, address, program, graduationDate, approved, suspended)
VALUES (8, '500 A Street', 'phd', 'F 2029', 0, 0);

INSERT INTO advising (advisorID, studentID)
VALUES (3, 8);

-- Add another student
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES (9, 'noform1b', 'password', 'NoForm1', 'StudentB', 'student');
*/
INSERT INTO students (userID, address, program, graduationDate, approved, suspended, initial_advising_complete)
VALUES (9, '600 B Street', 'ms', 'S 2030', 0, 0, 0);

INSERT INTO advising (advisorID, studentID)
VALUES (3, 9);

-- Queue entry for StudentA (formID = 3)
INSERT INTO form1ApprovalQueue (formID, advisorID, studentID, result)
VALUES (3, 3, 8, 0);

-- Queue entry for StudentB (formID = 4)
INSERT INTO form1ApprovalQueue (formID, advisorID, studentID, result)
VALUES (4, 3, 9, 0);

-- StudentA (userID = 8, formID = 3)
INSERT INTO form1_courses (formID, courseID) VALUES (3, 1);  -- SW Paradigms
INSERT INTO form1_courses (formID, courseID) VALUES (3, 3);  -- Algorithms
INSERT INTO form1_courses (formID, courseID) VALUES (3, 7);  -- Database 1

-- StudentB (userID = 9, formID = 4)
INSERT INTO form1_courses (formID, courseID) VALUES (4, 2);  -- Computer Architecture
INSERT INTO form1_courses (formID, courseID) VALUES (4, 5);  -- Networks 1
INSERT INTO form1_courses (formID, courseID) VALUES (4, 14); -- Security 1


CREATE TABLE initialAdvisingQueue (
    submissionID INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each submission
    studentID INTEGER NOT NULL,
    advisorID INTEGER NOT NULL, -- Advisor assigned when submitted
    status INTEGER DEFAULT 0 NOT NULL, -- 0=Pending, 1=Approved, -1=Rejected
    submission_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (studentID) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (advisorID) REFERENCES users(user_id) ON DELETE SET NULL -- Or CASCADE? Decide policy
);

-- Table to link courses to a specific initial advising submission
CREATE TABLE initialAdvisingQueue_courses (
    submissionID INTEGER NOT NULL,
    courseID INTEGER NOT NULL,
    FOREIGN KEY (submissionID) REFERENCES initialAdvisingQueue(submissionID) ON DELETE CASCADE,
    FOREIGN KEY (courseID) REFERENCES courses(course_id) -- Assuming courses table has course_id PK
    PRIMARY KEY (submissionID, courseID) -- Prevent duplicate courses per submission
);

-- ((SELECT user_id FROM Users WHERE username = 'billie'), 22, NULL), -- Enroll Billie in section 22 (CSCI 6461)
-- ((SELECT user_id FROM Users WHERE username = 'diana'),  21, NULL); -- Enroll Diana in section 21 (CSCI 6221)

--STARTING STATE: ADS--

INSERT INTO users (user_id, username, passcode, first_name, last_name, role, program) VALUES
(55555555, 'paul', 'password', 'Paul', 'McCartney', 'student', 'ms');
INSERT INTO students (userID, address, program, graduationDate, approved, suspended, initial_advising_complete) VALUES
(55555555, '987 Wash Rd', 'ms', 'S 2028', 0, 0,1);
INSERT INTO enrollments(student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'paul'), 1, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'paul'), 3, 'A'),
((SELECT user_id FROM Users WHERE username = 'paul'), 2, 'A'),
((SELECT user_id FROM Users WHERE username = 'paul'), 4, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'paul'), 5, 'A'),
((SELECT user_id FROM Users WHERE username = 'paul'), 6, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'paul'), 8, 'B'),
((SELECT user_id FROM Users WHERE username = 'paul'), 12, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'paul'), 13, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'paul'), 7, 'B');

INSERT INTO users (user_id, username, passcode, first_name, last_name, role, program) VALUES
(66666666, 'george', 'password', 'George', 'Harrison', 'student', 'ms');
INSERT INTO students (userID, address, program, graduationDate, approved, suspended, initial_advising_complete) VALUES
(66666666, 'somewhere', 'ms', 'S 2028', 0, 0,1 );
INSERT INTO enrollments(student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'george'), 1, 'C'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'george'), 2, 'B'),
((SELECT user_id FROM Users WHERE username = 'george'), 3, 'B'),
((SELECT user_id FROM Users WHERE username = 'george'), 4, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'george'), 5, 'B'),
((SELECT user_id FROM Users WHERE username = 'george'), 6, 'B'), 
((SELECT user_id FROM Users WHERE username = 'george'), 7, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'george'), 13, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'george'), 14, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'george'), 18, 'B');


INSERT INTO users (user_id, username, passcode, first_name, last_name, role, program) VALUES
(11111111, 'ringo', 'password', 'Ringo', 'Starr', 'student', 'phd');
INSERT INTO students (userID, address, program, graduationDate, suspended, approved, initial_advising_complete) VALUES
(11111111, '789 Abbey Rd', 'phd', 'S 2028', 0, 0, 1);
INSERT INTO enrollments(student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'ringo'), 1, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'ringo'), 2, 'A'),
((SELECT user_id FROM Users WHERE username = 'ringo'), 3, 'A'),
((SELECT user_id FROM Users WHERE username = 'ringo'), 4, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'ringo'), 5, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'ringo'), 6, 'A'),
((SELECT user_id FROM Users WHERE username = 'ringo'), 7, 'A'),
((SELECT user_id FROM Users WHERE username = 'ringo'), 8, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'ringo'), 9, 'A'),
((SELECT user_id FROM Users WHERE username = 'ringo'), 10, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'ringo'), 11, 'A'),
((SELECT user_id FROM Users WHERE username = 'ringo'), 12, 'A');

INSERT INTO users (user_id, username, passcode, first_name, last_name, role) VALUES
(77777777, 'clapton', 'password', 'Eric', 'Clapton', 'alumni');
INSERT INTO enrollments(student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'clapton'), 13, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'clapton'), 14, 'A'),
((SELECT user_id FROM Users WHERE username = 'clapton'), 15, 'A'),
((SELECT user_id FROM Users WHERE username = 'clapton'), 1, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'clapton'), 3, 'B'),
((SELECT user_id FROM Users WHERE username = 'clapton'), 22, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'clapton'), 4, 'B'),
((SELECT user_id FROM Users WHERE username = 'clapton'), 5, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'clapton'), 6, 'B'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'clapton'), 7, 'B'); -- Enroll Billie in section 22 (CSCI 6461)
INSERT INTO alumni (userID, program, graduationDate) VALUES
(77777777, 'ms', 'F 2014');


/*
INSERT INTO users (user_id, username, passcode, first_name, last_name, role) VALUES
(55555555, 'paul', 'password', 'Paul', 'McCartney', 'student');
INSERT INTO students (userID, address, program, graduationDate, approved) VALUES
(55555555, '987 Wash Rd', 'ms', 'S 2028', 0);
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)






INSERT INTO users (user_id, username, passcode, first_name, last_name, role) VALUES
(77777778, 'ringo', 'password', 'Ringo', 'Starr', 'student');
INSERT INTO students (userID, address, program, graduationDate, approved) VALUES
(77777778, '789 Abbey Rd', 'phd', 'S 2028', 1);

INSERT INTO users (user_id, username, passcode, first_name, last_name, role) VALUES
(77777779, 'clapton', 'password', 'Eric', 'Clapton', 'alumni');
--INSERT INTO students(77777779, 'ms', 'S 2014');
INSERT INTO Enrollments (student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'billie'), 22, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 21, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 20, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'billie'), 19, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
(77777778, 2, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
(77777779, 3, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
(77777779, 15, 'A'), -- Enroll Billie in section 22 (CSCI 6461)
(77777779, 16, 'A'); -- Enroll Billie in section 22 (CSCI 6461)
INSERT INTO alumni (userID, program, graduationDate) VALUES
(77777779, 'ms', 'F 2014');*/
