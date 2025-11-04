DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS prerequisites;
DROP TABLE IF EXISTS sections;
DROP TABLE IF EXISTS enrollments;


-- Users Table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    passcode VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    address VARCHAR(255),
    program VARCHAR(50)
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

-- Sections Table (Course Schedule/Offerings)
CREATE TABLE sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INT,
    semester VARCHAR(50) NOT NULL, -- e.g., 'Fall'
    year INT NOT NULL, -- e.g., 2024
    day VARCHAR(10) NOT NULL, -- 'M', 'T', 'W', 'R', 'F'
    time_slot VARCHAR(20) NOT NULL, -- '1500-1730'
    instructor_id INT, -- Foreign Key referencing Users (instructors)
    FOREIGN KEY (course_id) REFERENCES Courses(course_id),
    FOREIGN KEY (instructor_id) REFERENCES Users(user_id)
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
INSERT INTO Users (user_id, username, passcode, role, first_name, last_name, program) VALUES
('77777777', 'akhil', 'akhilpass', 'student', 'Akhil', 'Vanka', 'PHD'),  
('88888888', 'billie', 'billiepass', 'student', 'Billie', 'Holiday', 'MASTERS'), 
('99999999', 'diana', 'dianapass', 'student', 'Diana', 'Krall', 'MASTERS'); 

INSERT INTO Users (username, passcode, role, first_name, last_name) VALUES
('gsuser', 'testpass', 'gs', 'Grad', 'Secretary'),
('narahari', 'testpass', 'instructor', 'Narahari', 'Instructor'),
('choi', 'testpass', 'instructor', 'Choi', 'Instructor'),
('admin', 'testpass', 'admin', 'System', 'Admin');

-- Populate Sections Table
INSERT INTO Sections (course_id, semester, year, day, time_slot) VALUES
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6221'), 'Fall', 2024, 'M', '1500-1730'), -- CourseID 1
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'Fall', 2024, 'T', '1500-1730'), -- CourseID 2
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6212'), 'Fall', 2024, 'W', '1500-1730'), -- CourseID 3
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6232'), 'Fall', 2024, 'M', '1800-2030'), -- CourseID 4
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6233'), 'Fall', 2024, 'T', '1800-2030'), -- CourseID 5
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6241'), 'Fall', 2024, 'W', '1800-2030'), -- CourseID 6
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6242'), 'Fall', 2024, 'R', '1800-2030'), -- CourseID 7
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6246'), 'Fall', 2024, 'T', '1500-1730'), -- CourseID 8
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6251'), 'Fall', 2024, 'M', '1800-2030'), -- CourseID 9
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6254'), 'Fall', 2024, 'M', '1530-1800'), -- CourseID 10
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6260'), 'Fall', 2024, 'R', '1800-2030'), -- CourseID 11
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6262'), 'Fall', 2024, 'W', '1800-2030'), -- CourseID 12
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6283'), 'Fall', 2024, 'T', '1800-2030'), -- CourseID 13
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6284'), 'Fall', 2024, 'M', '1800-2030'), -- CourseID 14
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6286'), 'Fall', 2024, 'W', '1800-2030'), -- CourseID 15
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6384'), 'Fall', 2024, 'W', '1500-1730'), -- CourseID 16
((SELECT course_id FROM Courses WHERE dept_code = 'ECE' AND course_number = '6241'), 'Fall', 2024, 'M', '1800-2030'), -- CourseID 17
((SELECT course_id FROM Courses WHERE dept_code = 'ECE' AND course_number = '6242'), 'Fall', 2024, 'T', '1800-2030'), -- CourseID 18
((SELECT course_id FROM Courses WHERE dept_code = 'MATH' AND course_number = '6210'), 'Fall', 2024, 'W', '1800-2030'), -- CourseID 19
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6339'), 'Fall', 2024, 'R', '1600-1830'); -- CourseID 20

-- Populate Section Table (Choi's classes)
INSERT INTO Sections (course_id, semester, year, day, time_slot, instructor_id) VALUES
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6221'), 'Fall', 2024, 'M', '1500-1730', (SELECT user_id FROM Users WHERE username = 'choi')), -- CSCI 6221 assigned to choi
((SELECT course_id FROM Courses WHERE dept_code = 'CSCI' AND course_number = '6461'), 'Fall', 2024, 'T', '1500-1730', (SELECT user_id FROM Users WHERE username = 'choi')); -- CSCI 6461 assigned to choi

-- Populate Enrollments Table (Billie Holiday's Registrations)
INSERT INTO Enrollments (student_id, section_id, grade) VALUES
((SELECT user_id FROM Users WHERE username = 'billie'), 22, NULL), -- Enroll Billie in section 22 (CSCI 6461)
((SELECT user_id FROM Users WHERE username = 'diana'),  21, NULL); -- Enroll Diana in section 21 (CSCI 6221)
