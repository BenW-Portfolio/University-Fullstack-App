# Phase I Report

## Entity-Relation Diagram

![ER Diagram](ERdiagram.png)

USERS to APPLICATION — 1:1

USERS to TRANSCRIPT — receives

USERS to REVIEW — faculty reviews

USERS to REVIEW — recommended advisor

USERS to DECISION — decides

APPLICATION to ACADEMIC_INFO — 1:1

APPLICATION to RECOMMENDATION — 1:N

APPLICATION to DEGREES — 1:N

APPLICATION to TRANSCRIPT — 1:1

APPLICATION to REVIEW — 1:N

APPLICATION to DECISION — 1:1

## Normal Form
The schema is in Third Normal Form (3NF). Each table is normalized to eliminate redundancy and ensure data integrity through primary and foreign keys.

## Design Justification
Normalization: The schema is designed to reduce redundancy and ensure data integrity, with each table focusing on a specific entity and relationships maintained via foreign keys.

Modularity: Data is divided into logical tables (e.g., USERS, APPLICATIONS, ACADEMIC_INFO), making it easier to maintain and scale.

Data Integrity: Constraints like UNIQUE, CHECK, and foreign key relationships ensure the consistency and correctness of the data across the system.

## Testing
Testing will include the following:

Integration Testing: Ensure that the foreign key relationships between tables (USERS, APPLICATIONS, etc.) maintain data integrity when performing operations across multiple tables.

Boundary Testing: Check that the constraints (e.g., for GPA, GRE scores, email format) are enforced correctly.

Performance Testing: Ensure that queries perform efficiently as the data grows.

---- AUTHOR: PG

Further testing will also include unit tests, performed via request.py
This will modularize the implementation of specific tests such as insert_application, request_rec, etc

This will be done to ensure the accuracy of queries + the reliability of services. 
---- *



## Assumptions Made By Our Group

Email Uniqueness: The email is unique across all users.

Role Constraints: The roles defined are fixed and will not change.

GRE and TOEFL Constraints: GRE scores and TOEFL scores are validated to fall within expected ranges.

Application Status: Only the predefined set of application statuses will be used.

Updating Personal Info is the GS's job

---- AUTHOR: PG

- Single rec letter sufficency for an application to be submitted
- Simulating the email delivery + rec letter generation via flask
---- *

## Things We Are Missing
BCNF (Boyce-Codd Normal Form): The schema can be further normalized to BCNF, where every determinant is a candidate key. This can address any anomalies arising from partial dependencies.
Application Materials Section of Application Detail

---- AUTHOR: PG

- No email / pw hashing
- Not super rigorous testing of the system

---- *

## Work Breakdown
We each took a different set of users:
JD: CAC, Reviewer, Admin
PG: Applicants
WR: GS


## Graduate Secretary (GS) Functionality

The Graduate Secretary serves a pivotal administrative role in the system. Their access includes:

- **Dashboard View**: An overview of all applicants and their statuses, pulled dynamically from the database.
- **Search Functionality**: Ability to search applicants by name, ID, program, or status via the GS dashboard. This is backed by flexible query logic in `db/queries/gs.py`.
- **Statistics View**: A statistics page that visualizes application trends, acceptance rates, and departmental distribution, enabling data-driven decisions.
- **Application Review Support**: GS can view detailed applicant data, transcripts, recommendation letters, and the current review status.

These features are implemented via Flask routes in `app/gs.py` and rendered through templates like `gs/dashboard.html`, `gs/stats.html`, and `gs/search_results.html`.

The GS module highlights the system’s goal to streamline workflows for non-technical administrative staff while maintaining secure access and efficient data navigation.
