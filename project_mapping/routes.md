
## Authentication Routes
- `**/register**` *(methods: GET, POST)*  --> Handles applicant account creation.

- `**/login**` *(methods: GET, POST)*  --> Manages login for all user roles.

- `**/logout**` *(methods: GET)* --> Logs out the current user and ends the session.

## Applicant Routes

- `**/dashboard**` *(methods: GET)*  --> Displays the applicant's dashboard with application status.

- `**/application**` *(methods: GET, POST)*  --> Allows applicants to start, edit, and submit their application.

- `**/application/status**` *(methods: GET)* --> Enables applicants to view the current status of their application.

## Graduate Secretary (GS) Routes

- `**/gs/dashboard**` *(methods: GET)*  --> Shows a list of all applications and their statuses.

- `**/gs/update_transcript/<user_id>**` *(methods: POST)*  --> Marks the receipt of an applicant's transcript.

## Reviewer Routes

- `**/reviewer/dashboard**` *(methods: GET)*  --> Lists applications pending review.

- `**/review/<user_id>**` *(methods: GET, POST)*  --> Provides access to the review form for a specific applicant.

## Chair of Admissions Committee (CAC) Routes

- `**/cac/final_decision/<user_id>**` *(methods: GET, POST)*  --> Allows entry of the final admission decision for an applicant.
