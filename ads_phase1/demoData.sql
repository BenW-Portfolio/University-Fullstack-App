
-- reset
DELETE FROM advising;
DELETE FROM alumni;
DELETE FROM enroll;
DELETE FROM form1_courses;
DELETE FROM form1;
DELETE FROM students;
DELETE FROM users;
DELETE FROM courses;
DELETE FROM form1ApprovalQueue;
DELETE FROM graduateApplicationQueue;


-- Advisors
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES
(1010, 'narahari', 'password', 'Narahari', 'N.', 'advisor'),
(1011, 'parmer', 'password', 'Parmer', 'P.', 'advisor');


-- admins (also stored in users table)
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES
(1012, 'choi', 'password', 'Choi', 'C.', 'admin');

-- grad secretary user
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES
(1013, 'gsadmin', 'password', 'Grace', 'Hopper', 'gradSec');


-- MS Students (paul, george, billie, diana)
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES
(55555555, 'paul', 'password', 'Paul', 'McCartney', 'student'),
(66666666, 'george', 'password', 'George', 'Harrison', 'student'),
(88888888, 'holiday', 'password', 'Billie', 'Holiday', 'student'),
(99999999, 'krall', 'password', 'Diana', 'Krall', 'student');

INSERT INTO students (userID, address, program, graduationDate, approved)
VALUES
(55555555, '987 Wash Rd', 'ms', 'S 2028', 0),
(66666666, '345 Wash Rd', 'ms', 'S 2028', 0),
(88888888, '202 South St', 'ms', 'S 2028', 0),
(99999999, '303 North Ave', 'ms', 'S 2028', 0);

-- PhD Students
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES
(77777778, 'ringo', 'password', 'Ringo', 'Starr', 'student');

INSERT INTO students (userID, address, program, graduationDate, approved)
VALUES
(77777778, '789 Abbey Rd', 'phd', 'S 2028', 0);

-- Advisor-Student Links
INSERT INTO advising (advisorID, studentID)
VALUES
(1010, 55555555), -- Narahari -> Paul
(1011, 66666666), -- Parmer -> George
(1011, 77777778); -- Parmer -> Ringo

-- alumni user
INSERT INTO users (userID, username, password, fname, lname, role)
VALUES
(77777777, 'clapton', 'password', 'Eric', 'Clapton', 'alumni');

INSERT INTO alumni (userID, program, graduationDate)
VALUES
(77777777, 'ms', 'F 2014');


-- course schedule 
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



-- course enrollments

-- Paul McCartney courses
INSERT INTO enroll (studentID, courseID, grade, semester)
VALUES
(55555555, 1, 'A', 'F2023'),
(55555555, 2, 'A', 'F2023'),
(55555555, 3, 'A', 'F2023'),
(55555555, 4, 'A', 'F2023'),
(55555555, 5, 'A', 'F2023'),
(55555555, 6, 'B', 'S2024'),
(55555555, 8, 'B', 'S2024'),
(55555555, 9, 'B', 'S2024'),
(55555555, 10, 'B', 'S2024'),
(55555555, 7, 'B', 'S2024');

-- George Harrison courses
INSERT INTO enroll (studentID, courseID, grade, semester)
VALUES
(66666666, 15, 'C', 'F2023'),
(66666666, 1, 'B', 'F2023'),
(66666666, 2, 'B', 'F2023'),
(66666666, 3, 'B', 'F2023'),
(66666666, 4, 'B', 'F2023'),
(66666666, 5, 'B', 'F2023'),
(66666666, 6, 'B', 'S2024'),
(66666666, 7, 'B', 'S2024'),
(66666666, 10, 'B', 'S2024'),
(66666666, 11, 'B', 'S2024');

-- Ringo Starr (PhD)
INSERT INTO enroll (studentID, courseID, grade, semester)
VALUES
(77777778, 1, 'A', 'F2023'),
(77777778, 2, 'A', 'F2023'),
(77777778, 3, 'A', 'F2023'),
(77777778, 4, 'A', 'F2023'),
(77777778, 5, 'A', 'F2023'),
(77777778, 6, 'A', 'S2024'),
(77777778, 7, 'A', 'S2024'),
(77777778, 10, 'A', 'S2024'),
(77777778, 11, 'A', 'S2024'),
(77777778, 12, 'A', 'S2024'),
(77777778, 13, 'A', 'S2024'),
(77777778, 14, 'A', 'S2024');

-- Eric Clapton (alumni)
INSERT INTO enroll (studentID, courseID, grade, semester)
VALUES
(77777777, 1, 'B', 'F2013'),
(77777777, 2, 'B', 'F2013'),
(77777777, 3, 'B', 'F2013'),
(77777777, 4, 'B', 'F2013'),
(77777777, 5, 'B', 'F2013'),
(77777777, 6, 'B', 'S2014'),
(77777777, 7, 'B', 'S2014'),
(77777777, 10, 'A', 'S2014'),
(77777777, 11, 'A', 'S2014'),
(77777777, 12, 'A', 'S2014');

-- Graduate-Ready MS Student (studentID 15)
INSERT INTO users VALUES (15, 'grad_ready', 'password', 'Grace', 'Grad', 'student');
INSERT INTO students VALUES (15, '123 Grad Ln', 'ms', 'S 2028', 0, 0);
INSERT INTO advising VALUES (1011, 15);
-- INSERT INTO graduateApplicationQueue VALUES (15);

INSERT INTO form1 VALUES (5, 15);
INSERT INTO form1ApprovalQueue VALUES (5, 3, 15, 1);
INSERT INTO form1_courses VALUES (5, 1), (5, 2), (5, 3), (5, 5), (5, 10), (5, 11), (5, 12);

INSERT INTO enroll VALUES 
(15, 1, 'A', 'F 2025'),
(15, 2, 'A', 'S 2026'),
(15, 3, 'A-', 'F 2026'),
(15, 5, 'B+', 'S 2027'),
(15, 10, 'A-', 'F 2027'),
(15, 11, 'A', 'S 2028'),
(15, 12, 'B+', 'S 2028');
--(15, 

-- Fail Case 1: Missing Form1 (studentID 16)
INSERT INTO users VALUES (16, 'no_form1', 'password', 'Nora', 'NoForm', 'student');
INSERT INTO students VALUES (16, '456 Missing Ln', 'ms', 'F 2029', 0, 0);
INSERT INTO advising VALUES (1011, 16);
-- INSERT INTO graduateApplicationQueue VALUES (16);

INSERT INTO enroll VALUES 
(16, 1, 'A', 'F 2025'),
(16, 2, 'A-', 'S 2026'),
(16, 3, 'B+', 'F 2026'),
(16, 5, 'A-', 'S 2027'),
(16, 10, 'B+', 'F 2027'),
(16, 11, 'A', 'S 2028'),
(16, 12, 'B', 'S 2028');

-- Fail Case 2: Form1 Rejected (studentID 17)
INSERT INTO users VALUES (17, 'rejected_form1', 'password', 'Rob', 'Reject', 'student');
INSERT INTO students VALUES (17, '789 Reject St', 'phd', 'S 2029', 0, 0);
INSERT INTO advising VALUES (1011, 17);
INSERT INTO form1 VALUES (6, 17);
INSERT INTO form1ApprovalQueue VALUES (6, 3, 17, -1);

INSERT INTO form1_courses VALUES (6, 1), (6, 3), (6, 4), (6, 7), (6, 8), (6, 14), (6, 15);

INSERT INTO enroll VALUES 
(17, 1, 'A', 'F 2025'),
(17, 3, 'B+', 'S 2026'),
(17, 4, 'A-', 'F 2026'),
(17, 7, 'A', 'S 2027'),
(17, 8, 'B', 'F 2027'),
(17, 14, 'A', 'S 2028'),
(17, 15, 'A-', 'S 2028');

-- Fail Case 3: Not Enough Credits (studentID 18)
INSERT INTO users VALUES (18, 'low_credits', 'password', 'Lara', 'Lite', 'student');
INSERT INTO students VALUES (18, '987 Short Rd', 'ms', 'S 2028', 0, 0);
INSERT INTO advising VALUES (1011, 18);
INSERT INTO form1 VALUES (7, 18);
INSERT INTO form1ApprovalQueue VALUES (7, 3, 18, 1);

INSERT INTO form1_courses VALUES (7, 1), (7, 2), (7, 3), (7, 5), (7, 10);

INSERT INTO enroll VALUES 
(18, 1, 'A', 'F 2025'),
(18, 2, 'A-', 'S 2026'),
(18, 3, 'A-', 'F 2026'),
(18, 5, 'B+', 'S 2027'),
(18, 10, 'A', 'F 2027');

-- Fail Case 4: Suspended Student (studentID 19)
INSERT INTO users VALUES (19, 'suspended_user', 'password', 'Sam', 'Suspended', 'student');
INSERT INTO students VALUES (19, '999 Suspend Ave', 'phd', 'F 2029', 0, 1);
INSERT INTO advising VALUES (1011, 19);
INSERT INTO form1 VALUES (8, 19);
INSERT INTO form1ApprovalQueue VALUES (8, 3, 19, 1);

INSERT INTO form1_courses VALUES (8, 1), (8, 3), (8, 4), (8, 7), (8, 8), (8, 14), (8, 15);

INSERT INTO enroll VALUES 
(19, 1, 'A', 'F 2025'),
(19, 3, 'A-', 'S 2026'),
(19, 4, 'B+', 'F 2026'),
(19, 7, 'B', 'S 2027'),
(19, 8, 'B+', 'F 2027'),
(19, 14, 'A-', 'S 2028'),
(19, 15, 'A', 'S 2028');


