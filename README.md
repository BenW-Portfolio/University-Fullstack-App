# University-Fullstack-App

University Fullstack App Project Summary

This project is developing the Application, Registration, and Graduation (ARG) system. The primary goal of this project is to integrate the three standalone modules: Application Processing (APS), Registration (REGS), and Advising/Degree Audit (ADS)—into a single, cohesive platform. Your team will build a complete, end-to-end workflow that manages the entire student lifecycle, from an initial application, through matriculation, course registration, academic advising, and finally to graduation and alumni status. Key focus areas for this project include ensuring seamless data flow between modules, implementing new critical features like online recommendations and advising holds, refining the user interface for a professional user experience, and robustly testing the integrated system.

Project Core Objectives
1. System Integration

The immediate priority is to integrate the separate modules into a functional skeleton of the complete system. This involves establishing clear data pathways and state transitions.

    Applicant to Student Transition: Define the process for an applicant to become a student. This occurs when they matriculate, which involves (1) accepting their admission offer and (2) submitting their acceptance fee. You must implement a mechanism for this, whether it's an action performed by the Graduate Secretary (GS) or a feature for the applicant.

    Data Flow: Once an applicant becomes a student, their data (originating from the Application module) must become immediately available to the Registration and Advising systems.

    Data Consistency: Ensure data is not unnecessarily replicated across systems. A student's registration information (courses, grades) should be directly accessible to the Advising system. Personal data should be sourced from a single point of truth established in the Application module.

2. Workflow Analysis and Refinement

Once the initial integration is complete, you must diligently review the entire system workflow against the project specifications.

    Validate Workflow: Go through the complete user journey, from application to graduation, to identify gaps or inconsistencies.

    Meet Final Specifications: Ensure your integrated system meets every requirement detailed in this document.

3. New Feature Implementation

This requires building new functionality to create a complete product.

    Online Recommendation Letters: Implement a system where applicants can list references, who are then automatically emailed a link to submit their letters online. These letters must be accessible to faculty reviewers.

    Advising Hold: New students must submit an advising form for their first semester. An "advising hold" must prevent them from registering until a faculty advisor electronically approves their form.

    Queries & Reports: Implement the specific reports and queries listed later in this document.

4. User Interface (UI) Enhancement

Critically evaluate and improve your user interface.

    Usability: Create an intuitive and easy-to-use interface.

    Seamless Navigation: Users should be able to move between different parts of the system smoothly.

    Role-Based Access: The UI must strictly enforce user permissions. For example, an applicant should never see student-only functions.

    Copyright: Do not use commercial banners or assets without a license. Your project's main page should clearly state that it is a class project.

5. Final System Testing

Thoroughly test the integrated system to catch common errors before the final demo. Populate your database with a sufficient number of diverse sample cases to demonstrate all functionalities.
End-to-End System Workflow

The ARG system must support the following workflow for managing the student lifecycle.

    Application Submission:

        A prospective graduate student applies online. Their data (personal, academic, GRE, GPA) is stored in the database.

        Online Recommendations: The applicant enters up to three references. The system emails the references, tracks submissions, and makes letters available to faculty.

        Online Transcripts: Applicants can choose to have transcripts mailed (GS marks as received) or submitted via a secure online link.

    Application Review:

        The Graduate Admissions Committee (faculty) reviews applications using an online form to enter scores and recommendations (Admit, Admit with Aid, Reject).

        The system must support multiple faculty reviews and calculate an average score for the Chair of the Admissions Committee (CAC).

        The CAC or GS makes the final admission decision.

    Application Status Check:

        Applicants can log in to check their status, which can be: "Application Received and Decision Pending," "Application Materials Missing," "Admission Decision: Accepted," or "Admission Decision: Rejected."

    Matriculation:

        An admitted applicant accepts their offer and pays a deposit to matriculate, officially becoming a current student.

        Upon matriculation, the GS assigns a faculty advisor to the new student.

        A matriculated student gains access to the registration system.

    Course Registration:

        A student registers for courses using the registration system.

        Advising Hold: For their first semester, a new student is on an "advising hold." They must submit an advising form (similar to Form 1) which their advisor must electronically approve before the hold is lifted and they can register.

    Academic Progress and Graduation:

        A current student must fill out a Form 1.

        A student can apply for graduation. The system performs a degree audit to check if requirements are met. The GS gives final clearance.

    Transition to Alumni:

        Once cleared for graduation, the student's status changes to "Alumni."

    Alumni Access:

        Alumni can log in to view their transcript and update personal contact information, but cannot register for courses.

Required Queries and Reports

Your system must provide the following reports and search functions, accessible to authorized users.

    Search for an applicant by last name or student number (GS, Faculty Reviewer).

    Update an applicant's academic/personal information (Applicant, GS).

    Update personal information for any user type (Applicant, Student, Alumni).

    Generate a list of applicants filtered by Semester, Year, or Degree program (GS).

    Generate a list of admitted students filtered by Semester, Year, or Degree program (GS).

    Generate application statistics (total applicants, admitted, rejected, average GRE) filtered by Semester, Year, or Degree program (GS).

    Generate a list of graduating students filtered by Semester, Year, or Degree program (GS).

    Generate a list of alumni with their email addresses (GS).

    Generate a list of all current students filtered by Degree or Admit Year (GS).

    Change a student's advisor given their student number (GS).

    Generate a student's transcript (courses, credits, GPA) given their student number (Student, Faculty Advisor, GS).

    Generate a list of all advisees for a faculty member (Faculty Advisor, GS).

    Generate a course roster for an instructor (Faculty Instructor).

User Roles and Permissions
The system must enforce a strict, role-based access control model.

System Administrator

    Has complete access to the system.

    Can create, modify, and delete all user accounts.

Grad Secretary (GS)

    Has full access to applicant and student data.

    Can update application status, matriculate students, and clear students for graduation.

    Cannot review applications or create new user accounts.

Chair of Admissions (CAC)

    A faculty member with full access to applicant data.

    Can enter reviews and make the final admission decision.

Faculty Reviewer

    A faculty member who can view all applicant information.

    Can submit application reviews via the review form.

Faculty Advisor

    A faculty member who can view their advisees' transcripts (but not other students').

    Can lift the "advising hold" for new advisees.

    Cannot enter application reviews.

Faculty Instructor

    A faculty member who can enter grades for students in the courses they are teaching.

    Can view their course rosters.

Applicant

    Can submit and edit their application information.

    Can update their personal/contact information.

    Can only check their own application status.

Current Student

    Can view their own transcript (read-only).

    Can register for classes, submit Form 1, and apply for graduation.

    Can update their personal information.

Alumni

    Can view their own transcript (read-only).

    Can update their personal information.
