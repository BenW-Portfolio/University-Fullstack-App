# Phase I Report

## Entity-Relation Diagram

<img src = "Reports\ER diagram.jpg">

## Normal Form
    Most of the tables in our schema are in 3NF or BCNF, bar a few of the following:


    Courses: We are not in 1NF because there is repeated information in the prereq1 and prereq2 columns. To fix this, there should have been another table that would store courseIDs and their prerequisite courses.

    Advising: we got rid of the primary key(advisorID, studentID) because of a bug with unique constraints. However, we realized that this may have posed an issue with maintaining normal forms, and without this key, the advising table is not in 1NF.

    Generally, the rest of our schema satisfies 3NF. The following examples demonstrate 3NF:
    Folumns in tables contain atomic values—simple, indivisible data. For example, in the students table, fields like first_name, last_name, program, and graduation_date each contain a single, meaningful piece of information. 
    Moving to 2NF, we verified that all non-key attributes are fully dependent on the entire primary key. This is especially relevant for tables with composite keys, although in our implementation most tables rely on a single-column primary key. In the form1 table, which records a student’s proposed course history, the primary key is form_id. All other attributes in that table—such as student_id, course_id, semester, and grade depend entirely on form_id. Similarly, the advising table uses advising_id as its primary key, and fields like student_id, advisor_id, and thesis_approved are directly dependent on that key alone. 
    To ensure 3NF, we confirmed that there are no transitive dependencies between non-key attributes. Each non-key attribute is directly dependent on the primary key and not indirectly through another attribute. For instance, in the students table, all fields such as first_name, program, and graduation_date are directly dependent on student_id, and no field depends on another non-key field like program. Likewise, in the users table, which supports authentication, the fields username, password, and role all depend directly on user_id, and not on each other.
    After confirming 3NF, we ensured that some tables also meets the stricter requirements of BCNF. BCNF requires that for every functional dependency, the left-hand side (the determinant) must be a superkey. So every field that determines another must uniquely identify rows in the table.
    For example, in the students table, student_id uniquely determines all other columns, including first_name, program, and graduation_date. In the form1 table, form_id determines the course information and associated student. The advising table follows the same structure, with advising_id determining the student, advisor, and thesis approval status. In the users table, user_id determines the username, password, and role. We don't generally let a non-superkey attribute to functionally determine another, which would violate BCNF.
    The relationship between students and advisors is designed to avoid dependencies like student_id → advisor_id, which could arise if we assumed a student could only ever have one advisor. Instead, we use the advising table with a unique advising_id to model this relationship. This design preserves flexibility while maintaining BCNF. 

## Design Justification

    We want to have it so that we can store a total course history for everyone and then search for student IDs in order to get a specific students courses. The structure of our database was designed to reflect the real-world advising process while maintaining clarity and flexibility. The students table serves as the foundation, with related data such as course planning and advising stored in separate, focused tables. The form1 table handles student course submissions and allows us to track course history, semesters, and grades using a unique form_id. The advising table separately manages advisor assignments and thesis approval, making it easier to track advising relationships over time and preserve data integrity.

    To manage system access, we use a single users table with role-based permissions for students, advisors, and administrative staff. This centralized design supports scalable authentication while keeping permissions simple and consistent. Separating responsibilities across tables keeps our schema normalized and efficient, allowing us to support key advising functions like course tracking, thesis approvals, and graduation checks without redundancy or confusion.

    We had several specific site features which were implemented in unique ways. One of these which also came up in  the demo was the way we calculate student GPAs. We calculate the GPA every time a user loads their profile or it is displayed for advisors. This was because we wanted to make sure that this information was as current as possible and it is not a very costly operation because course history will only be a maximum of 12 classes, so even if it is an O(n) operation, n cannot be greater than 12, especially considering the benefits of saving memory and always having a current and accurate GPA displayed. 

    Another unique feature of our program was that admins are the only people who can create advisor, admin, and graduate secretary accounts. This adds a layer of security to our system so that the only people in these roles are those who have been given their accounts by a trusted source. Students are required to make their own accounts; this is not a dangerous operation because they are only able to see their own information, and they don’t pose a threat to revealing others information. 


## Testing

The beginning phases of testing were done on specific functions and routes, usually through inserting sample data into our database. This was all done manually in SQL, and we were able to test unique edge cases for functions such as creating accounts and graduating students. We started our project with building the bulk of the backend infrastructure, so this was a natural way to test a lot of our functions. Once the functions were all verified to be working, we could then use them to test more complex things. 

As our project became more complete, we began using the frontend to generate and test our data. For example, the front end could be used to display changes made in our backend as soon as we verified that the backend updates were correct and the front end display worked as intended. This made testing much faster and allowed us to finally run through what we thought the demo would end up being. The final test that we ran was just walking through the demo, using the website to create the data and analyze it based on expected results. 

## Assumptions Made By Our Group

- Students can choose and update their own graduation date manually, without the approval of any admin (we do not check if it is possible for them to graduate in their chosen time frame, but there are restrictions put to ensure they cannot set their graduation date to before the current time).
- A student can only take a course once. If they try to take it again, then we need to have a different primary key in that table. 
- A student can only have one advisor
- The approval/denial of a Form1 does not depend on it meeting the graduation requirements. An advisor can approve a form1 that lacks the core class graduation requirements, but when an audit is run to apply for graduation, the audit will catch any and all missing graduation requirements, such as invalid course loads and not enough credits taken
- A student cannot take any action to fix an academic suspension (in this project’s current state)
- Never have to change/update available courses to take
- Never have to update graduation requirements across the school
- Information updated locally cannot be updated in all databases (explained in next section)
- We assume that all courses have been completed at the time that we are calculating the GPA. In progress courses do not affect GPA. 

## Things We Are Missing

We are missing a lot of the multiuser servicing that one would expect in a product like this. Only a single user can connect to the website at once, and only if they are also locally running the python code. That is probably the biggest gap between our project and something that might be deployed in the real world. The only feasible solution to this would have been to use a large scale database and purchase a url, but this requires monetary costs to maintain and didn’t make sense to implement for a class project like this. 

Another thing we are missing are password requirements and general security features as a whole. If this were to be released, we would require passwords to be 8 characters for example, as well as protect our database better. The HTML reveals a lot about how our backend works, which makes sense from a development perspective, but also probably reveals a lot of information that could be maliciously used to run unwanted SQL queries on our database. This would be problematic as we could lose data, lose the ability to run our program, or leak personal information. 

We are also missing any system to back up the database. If something happened to one of our laptops, we could lose the database and code forever. This wasn’t too much of a problem as students building this project for a class, but if this was the real world, we could lose the ability to verify academic records for alumni, as well as fail to properly graduate students who meet requirements. Most of our failures were a result of making this website for a class project, and while it met all requirements for that, it also means that we did not need to think about long term problems or what would happen if it was open to the general public. 

## Work Breakdown
We initially began by dividing the bulk of the work into “views.” Max was assigned the admin view, Katya was assigned the advisor view, and Y.G. was assigned the Graduate Secretary view. This way, we could naturally understand the functions required of the ADS system, and how to assign more tasks to others.

We agreed that having multiple people try to coordinate frontend design might be a struggle, so Max designed and implemented the majority, if not all, of CSS styling and html layouts. The other group members still worked with frontend displays such as retrieving and displaying information needed in the frontend from the backend. However, the styling choices were mostly Max’s. 

- Katya:
    - advisorHome (flask)
    - approveThesis (flask + html)
    - Was assigned to do form1
    - demoData.sql

- Shared Max and Y.G.:
    - Login (flask + html)
    - updateInfo (flask + html)
    - Alumni (flask + html)
    - createAccount(html + python)

- Majority Max: 
    - Organized the repository / initial setup of flask and files
    - CSS designing in styles.css
    - studentHome (flask + html)
    - GPA()
    - Suspend()
    - isSuspended()
    - studentProf (flask + html)
    - approveForm1 (flask )
    - rejectForm1 (flask )
    - adminHome (flask + html)
    - adminCreateAccount (flask + html)
    - adminCreateAccHelper (flask + html)
    - advisorProf (flask + html)
    - Everything in test.SQL, though note this was not used in front end and only for debugging / planning. 

- Majority Y.G.: 
    - Logout (flask)
    - createAccount (flask)
    - audit (flask + html)
    - getNonCS() 
    - getCSHours()
    - getCreditHours()
    - gradSecHome (flask)
    - gradSecAssignAdv (flask)


