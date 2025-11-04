
--Drop all of the tables if they exist
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS advisor; -- 
DROP TABLE IF EXISTS alumni;
DROP TABLE IF EXISTS form1;
DROP TABLE IF EXISTS form1_courses;
DROP TABLE IF EXISTS advising;
DROP TABLE IF EXISTS form1ApprovalQueue;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS enroll;
DROP TABLE IF EXISTS audit;
DROP TABLE IF EXISTS thesisApproval;
DROP TABLE IF EXISTS graduateApplicationQueue;


-- Define all of the tables
CREATE TABLE users (
    userID      INT PRIMARY KEY, 
    username    varchar(25) UNIQUE,
    password    varchar(50), -- Maybe make more restrictive than this? ie. More than 8 chars include a number/symbol --
    fname       varchar(25),
    lname       varchar(25),
    role        varchar(7) -- Either admin, student, advisor, gradSec, or none --
    
);

CREATE TABLE students ( 
    userID      INT PRIMARY KEY,  
    address     varchar(50), -- This is on the ER diagram but what are we using it for? --
    program     varchar(3), -- Either phd or md --
    graduationDate  varchar(8), -- Given in S ****(Year) or F ****(Year) --
    approved    TINYINT, -- 1 for true, 0 for false --
    suspended   TINYINT, -- 1 for true, 0 for false --
    FOREIGN KEY (userID) REFERENCES users(userID)   
);

CREATE TABLE alumni (
--Note that only a summary of their academic information should be kept in the Alumni table--
    userID      INT PRIMARY KEY, 
    address     varchar(50), -- This is on the ER diagram but what are we using it for? --
    program     varchar(3), -- Either phd or md --
    graduationDate  varchar(8), -- Given in S ****(Year) or F ****(Year) --
    
    FOREIGN KEY (userID) REFERENCES users(userID)

);

--fetch all students in sql
--check if they are in the advisor table
--if they are not, they appear in the gradsec screen
--also make list of possible advisors to assign
--gradsec can execute sql statements to update advisor table

CREATE TABLE courses (
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
);

CREATE TABLE audit (
    advisorID   INT, 
    studentID   INT,
    outcome     TINYINT, -- 1 for true, 0 for false --
    PRIMARY KEY(advisorID, studentID),
    FOREIGN KEY (advisorID) REFERENCES users(userID),
    FOREIGN KEY (studentID) REFERENCES users(userID)

);

CREATE TABLE thesisApproval(
    advisorID   INT,
    studentID   INT,
    PRIMARY KEY(advisorID, studentID),
    FOREIGN KEY (advisorID) REFERENCES users(userID),
    FOREIGN KEY (studentID) REFERENCES users(userID)

);

CREATE TABLE graduateApplicationQueue (
    userID INT PRIMARY KEY, 
    FOREIGN KEY (userID) REFERENCES users(userID)
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
    FOREIGN KEY (advisorID) REFERENCES users (userID),
    FOREIGN KEY (studentID) REFERENCES students(userID)
);


--WE CAN REMOVE UNIQUE CONSTRAINTS FOR THIS--
CREATE TABLE advising (
    advisorID INT,
    studentID INT,
    -- PRIMARY KEY (advisorID, studentID), --
    FOREIGN KEY (advisorID) REFERENCES users(userID), 
    FOREIGN KEY (studentID) REFERENCES students(userID)
);

-- Sample data for users
--CHANGED NAME FROM MDSTUDENT TO MSSTUDENT
INSERT INTO users VALUES (1, 'admin', 'password', 'Max', 'Eichholz', 'admin');
INSERT INTO users VALUES (2, 'PHDstudent', 'password', 'phd', 'student', 'student');
INSERT INTO users VALUES (5, 'MSstudent', 'password', 'ms', 'student', 'student');
INSERT INTO users VALUES (6, 'suspend_test', 'password', 'Test', 'Suspend', 'student');
INSERT INTO users VALUES (3, 'advisor', 'password', 'advisor', 'lastname', 'advisor');
INSERT INTO users VALUES (7, 'advisor2', 'password', 'Alice', 'Johnson', 'advisor');
INSERT INTO users VALUES (4, 'gradSec', 'password', 'grad', 'Sec', 'gradSec');

-- Sample data for students
INSERT INTO students VALUES (2, '2025 F Street', 'phd', 'S 2028',0, 0);
INSERT INTO students VALUES (5, '2025 F Street', 'ms', 'S 2028',1, 0);
INSERT INTO students VALUES (6, '2100 Eye Street', 'phd', 'S 2029', 0, 0);

--Sample data for graduating students--
--INSERT INTO graduateApplicationQueue VALUES (2);-
INSERT INTO graduateApplicationQueue VALUES (5);

-- Sample data for courses
INSERT INTO courses VALUES (1, 'SW Paradigms', 3, 6221, 'CSCI', NULL, NULL);
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
INSERT INTO advising VALUES (3,2);
INSERT INTO advising VALUES (3, 6);



INSERT INTO users (userID, username, password, fname, lname, role)
VALUES (8, 'noform1a', 'password', 'NoForm1', 'StudentA', 'student');

INSERT INTO students (userID, address, program, graduationDate, approved, suspended)
VALUES (8, '500 A Street', 'phd', 'F 2029', 0, 0);

INSERT INTO advising (advisorID, studentID)
VALUES (3, 8);

-- Add another student
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES (9, 'noform1b', 'password', 'NoForm1', 'StudentB', 'student');

INSERT INTO students (userID, address, program, graduationDate, approved, suspended)
VALUES (9, '600 B Street', 'ms', 'S 2030', 0, 0);

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

