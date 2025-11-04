# Phase I Report

## Entity-Relation Diagram

![image](https://github.com/user-attachments/assets/70de671b-fb51-42ad-87db-70f6a1718e8d)


## Normal Form
  users Table
        Primary Key: {user_id}
        Candidate Keys: {user_id}, {username} 
        Functional Dependencies (FDs):
            user_id -> username, passcode, role, first_name, last_name, address, program (Determinant {user_id} is a superkey)
            username -> user_id, passcode, role, first_name, last_name, address, program (Determinant {username} is a candidate key, which makes it a superkey)
        BCNF Analysis: All identified non-trivial functional dependencies have a determinant (user_id or username) that is a superkey.
        Conclusion: The users table is in BCNF.
  
  courses Table
        Primary Key: {course_id}
        Candidate Keys: {course_id}, {dept_code, course_number} (due to UNIQUE constraint)
        Functional Dependencies (FDs):
            course_id -> dept_code, course_number, title, credits (Determinant {course_id} is a superkey)
            {dept_code, course_number} -> course_id, title, credits (Determinant {dept_code, course_number} is a candidate key, thus a superkey)
        BCNF Analysis: All identified non-trivial functional dependencies have a determinant that is a superkey.
        Conclusion: The courses table is in BCNF.
  
  prerequisites Table
        Primary Key: {prerequisite_id}
        Candidate Keys: {prerequisite_id}
        Functional Dependencies (FDs):
            prerequisite_id -> course_id, prerequisite_course_id, type (Determinant {prerequisite_id} is a superkey)
        BCNF Analysis: Only prerequisite_id is guaranteed unique so the only defined FD has prerequisite_id as the determinant, which is a superkey. Therefore, the table satisfies the BCNF condition based on its structure.
        Conclusion: The prerequisites table is in BCNF.
  
  sections Table
        Primary Key: {section_id}
        Candidate Keys: {section_id}
        Functional Dependencies (FDs):
            section_id -> course_id, semester, year, day, time_slot, instructor_id (Determinant {section_id} is a superkey)
        BCNF Analysis: The only determinant is the primary key (section_id), which is a superkey.
        Conclusion: The sections table is in BCNF.
  
  enrollments Table
        Primary Key: {enrollment_id}
        Candidate Keys: {enrollment_id}
        Functional Dependencies (FDs):
            enrollment_id -> student_id, section_id, grade (Determinant {enrollment_id} is a superkey)
        BCNF Analysis: All identified non-trivial functional dependencies have a determinant (enrollment_id) that is a superkey.
        Conclusion: The enrollments table is in BCNF.

Overall:
    All tables satisfy 1NF (atomic values, primary keys).
    All tables satisfy 2NF (no partial dependencies).
    All tables satisfy 3NF (no transitive dependencies among non-key attributes).
    All tables also satisfy BCNF. For every identified non-trivial functional dependency (X -> Y) within each table, the determinant (X) is a superkey for that table.

## Design Justification

The design for our entity-relation diagram was based on the attributes and relational tables we would need to support the features outlined in the spec sheet. We also ensured each table could be identified by a single 'id' attribute to simplify the design of our primary keys and queries. Three relational tables were used - 'prerequisites' to represent prerequisite relationships between courses, 'sections' as a bridge between specific courses and instructors to represent course sections, and 'enrollments' to represent student enrollment in a section of a course. As mentioned before, in general attributes for each of the tables were added as per the specs, with as little redundant information as possible. 

One thing to note is that in the users table, 'username' is labelled as a unique attribute as it is used to log in to the system.

The design of our site itself prioritizes function, listing every feature each user type may want to access as a tab at the top bar. Pages were also combined to support multiple features. 'View Transcripts' functions as both a transcript-view for students, a student enrollment info and grade change page for an instructor user's courses, and a universal student enrollment info and unrestricted grade change page for GS/Admin users. The 'Class Registration/View' page functions as both a current course section list for all users and a register/drop course page for students. As of now, a 'Register' or 'Drop' button appears next to each section for all users, but only functions for student users. 

Other page either only appears slightly different for each user (e.g. only Admin seeing 'Create Account' on the homepage), or features the same functionality for each user type and did not need to be modified.

Throughout our backend implementation, we make use of session variables to cache login info for the user. The general process for displaying queried data on each html page is similar overall, passing queried data, user id and type, and a display message if needed, as variables through a Flask render template. Helper functions for querying and insertion were also created to simplify querying and avoid long, confusing queries that are difficult to edit (although usage of these functions is not consistent in some sections), with a small tradeoff of redundant opening and closing of the database when multiple consecutive queries are made.

## Testing
We performed relatively thorough testing on general features and the varying features available to each user type. If we made any oversights on the backend logic, these will likely be edge cases and should be relatively simple to patch up through conditional checks, without any fundamental restructuring. 

To follow the test process we underwent, below is a list of the main features we verified to be functional. These are just an overview of the main testable features - more highly specific edge-case combinations we were aware of were tested as well, but won't be listed for redundancy.


(Universal User-Functionality)
Reset Database:
	- A reset database button displayed on all users' homepage for debug purposes. Clicking it will reset the database to default, clear session variables, and redirect to login page.


Login/Logout:
	- Users are able to sign in with username + password combination stored in the database
	- Once logged in, user is redirected to home page
	- If user enters wrong username/pass combination, the page is refreshed
	- Users are able to create a new account with (ONLY) the student role
	- Users can click 'Logout' button to log out, clearing all stored session variables and returning to the login page
	- Once logged in, users must log out to access the login page once again


Personal Info:
	- Users are able to change their username, first name, last name, address, and program
	- Users cannot change their username to an existing username

(Specific User-Functionality)
GS Functionality
- GS can view all student enrollment info via transcript/rosters menu (list individually for each student and class)
- GS can search for specific student enrollment info by username
- GS can update student grades for each of their enrolled courses
- GS can view, but not register, for courses

Admin Functionality
- Same functionality as GS
- Admin can create new faculty, gs, or student accounts 
- Admin cannot create accounts with existing usernames

Instructor Functionality
- Instructors can view students enrolled in their course sections 
- Instructors can change the grade of a student enrolled in their course from IP to any other grade (But not from a non 'IP' grade to another grade)

Student Functionality 
- Student can view their transcript (previous and in-progress classes)
- Students can register for a course if it does not introduce any prerequisite or time conflicts. 
- Student can drop courses they are enrolled in via the registration view. Note that it is assumed that all courses in this list are currently being offered and in-progress, so no check for an 'IP' grade is made when dropping a course.


Note - On the day of the demo, a few features like prerequisites had not been tested as thoroughly. Since then, more thorough testing has been performed.


## Assumptions Made By Our Group
In order to simplify the design process, there are multiple assumptions we make. 

For example, starting with authentication we assume a couple of things when considering how to store a user as well as what we expect from the login form during authentication. First, with the representation of a user, we assume that users do not have the ability to change their "student-id". We instead on creation auto-increment that field to ensure that each user has a unique id. The second with a user is that their program can be either a master's student or PHD, and they have that ability to change their program as they see fit. This was not clarified deeply within the documentation for REGS, and so we chose to include it apart of a user's personal info - meaning they can change it at will. Moving to the actual flow of authentication, we have a much simplier security assumption, which is that this is not a production level system and passwords are not only sent but stored in plaintext. We chose to ignore hashing the passwords to simplify the design of the route. 

Moving onwards, another design implementation is the entire registration system itself, which has more assumptions in it (of which some are defined in the documentation). The first is to assume that classes have no limits on how many students can register for the class, which is a deep assumption as our SQL has no consideration for class size. There are also other assumptions, such as only 3 possible time slots that can exist which is not reflective of real life application as well as a consideration that only PHD students can register for 6000 level courses (which as defined in the specifications means that masters students cannot register for any classes provided in Appendix A). Another consideration was that no class can have more than two prerequisite classes, which is also not reflective of real life application. This simplifies our design as we can acknoledge the prerequisites in one table while maintaing 3NF. However, in the future if necessary a seperate table would be needed to track pairs of classes and their prequisites. 

## Things We Are Missing
Few key elements are either missing, or have been modified as allowed in order to simplify the design. 

The first is the 8 digit UID for any student. We elected to AUTO_INCREMENT this field, which simplified the process, but this means that after adding a mandatory student whos UID is `999999` the SQL AUTO_INCREMENT feature starts all new users at 1,000,000. This will have to be modified to ensure 8 digits is enforced for all users in PHASE 2. 

The second is user account creation, where we had a small misunderstanding of the functionality outlined in the spec sheet (which will be aptly fixed). This lies in the documentation specifying two expected outcomes: the first was that users could self-register their own accounts. The second was under the roles of users, where it mentions only under the System Administrator account that it can create users, and makes a specific distinction that GS does not have those privelages. This led to a misunderstanding as commonly, students UID's are automatically generated by an administrator in real-life applications as well as their accounts, users only have to set passwords to move forward. This led to only the system administrator being allowed to create accounts (which is not the intended functionality).

The third is in consideration with the transcript, where we have no GPA calculation feature (as commonly present in a transcript). Since the functionality was listed under the scalability and phase 2, which will be implemnted as the integration process continues. This will require a new entry in the user's column if they are a student which will represent GPA, and will be recalculated any time a grade change occurs. This ensures no repeitition of recalculation. 

The fourth and trivial thing is simple flash messages when errors occur, instead of embeding them into the template HTML. This is just to ensure good UI/UX design philosphy. 

## Work Breakdown

Akhil: 
1. Layout Template and Login Template 
2. Implement entire functionality to allow user to change personal info 
3. Implemented the login flow for a user
4. Implemented creating of accounts route and template
5. Added original view_transcript routes (before new implementation)
6. Added route to reset the database on home page
7. Implemented the time check and assisted with the pre-requisite check
8. "QA" tested and fixed bugs in new transcript implementation

Benjamin:
1. Added tables to the create.sql(users, courses, pre-reqs, sections, enrollments)
2. Inserted class data into courses, sections, and prerequisites tables.
3. Added test users and enrolled them into the correct classes and sections.
4. Ran query to database.db and tested to make sure it loaded all the tables.
5. Created the new view_transcript(for students, gs, instructors, and admin) with the implmentation for gs, instructors, and admin to enter grades.
6. Created the view_transcripts.html and added styling with css for a nice UI.

Gilbert:
1. Implemented the prerequisite check for course registration and overall registration logic (aside from time check)
2. Created a few helper functions to aid in querying, insertion and login status
3. Assisted with backend logic and querying/insertion of personal_info 
4. Added sanity checks for page access based on user type (e.g. prevent page access without login, user) and error handling via redirection across flask routes
5. Added error message feedback to several html pages via backend render template
6. QA tested and implemented bug-fixes to login, transcript, registration, account creation, and personal info pages
