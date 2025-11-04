import sqlite3
import logging

class ApplicationQuery:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_user_by_id(self, user_id):
        query = "SELECT first_name, last_name, email FROM users WHERE user_id = ?"
        return self._execute_query(query, (user_id,), fetch_one=True) or {}
        

    def get_application_by_user_id(self, user_id):
        return self._execute_query("SELECT * FROM applications WHERE user_id = ?", (user_id,), fetch_one=True) or {}

    def update_application(self, data):
        query = """
        UPDATE applications SET
            first_name = ?, last_name = ?, degree_program = ?, gre_verbal = ?, gre_quant = ?,
            gre_year = ?, toefl_score = ?, bs_gpa = ?, bs_major = ?, bs_year = ?, bs_university = ?,
            ms_gpa = ?, ms_major = ?, ms_year = ?, ms_university = ?, interests = ?, experience = ?,
            admission_semester = ?, admission_year = ?, email = ?
        WHERE application_id = ?
        """

        values = (
            data['first_name'], data['last_name'], data['degree_program'], data['gre_verbal'], data['gre_quant'],
            data['gre_year'], data['toefl_score'], data['bs_gpa'], data['bs_major'], data['bs_year'], data['bs_university'],
            data['ms_gpa'], data['ms_major'], data['ms_year'], data['ms_university'], data['interests'], data['experience'],
            data['admission_semester'], data['admission_year'], data['application_id'], data['email']
        )
        return self._execute_query(query, values)

    def insert_application(self, data):
        try:
            conn = sqlite3.connect(self.db_path)  # Assuming self.db_path stores your DB path
            cursor = conn.cursor()

            query = """
            INSERT INTO APPLICATIONS (
                user_id, first_name, last_name, degree_program,
                gre_verbal, gre_quant, gre_year, toefl_score,
                bs_gpa, bs_major, bs_year, bs_university,
                ms_gpa, ms_major, ms_year, ms_university,
                interests, experience, admission_semester, admission_year, status, email
            ) VALUES (
                :user_id, :first_name, :last_name, :degree_program,
                :gre_verbal, :gre_quant, :gre_year, :toefl_score,
                :bs_gpa, :bs_major, :bs_year, :bs_university,
                :ms_gpa, :ms_major, :ms_year, :ms_university,
                :interests, :experience, :admission_semester, :admission_year,
                'Application Submitted & Under Review', :email
            )
        """

            print("Executing query with data:", data)  # Debugging line
            cursor.execute(query, data)
            conn.commit()

            print("Insert successful")  # Debugging line
            return True

        except sqlite3.Error as e:
            print("Database error:", e)  # Debugging line
            return False

        finally:
            if conn:
                conn.close()

    def insert_recommendation_request(self, data):
        query = """
            INSERT INTO recommendation_requests (
                token,
                user_id,
                applicant_name,
                recommender_name,
                recommender_email,
                affiliation,
                status,
                letter
            ) VALUES (
                :token,
                :user_id,
                :applicant_name,
                :recommender_name,
                :recommender_email,
                :affiliation,
                :status,
                NULL
            )
        """
        return self._execute_query(query, data)

    def get_application_status(self, user_id):
        query = "SELECT status FROM APPLICATIONS WHERE user_id = :user_id"
        result = self._execute_query(query, {'user_id': user_id}, fetch_one=True)
        return result[0] if result else None

    def get_all_apps(self):
        query = "SELECT * FROM APPLICATIONS;"
        try:
            logging.info("Executing query to fetch all applications: %s", query)
            res = self._execute_query(query, fetch_one=False)
            if res is False:
                logging.warning("Query execution failed or returned False.")
                return []
            logging.info("Retrieved %d applications.", len(res))
            return res
        except Exception as e:
            logging.error("Error fetching applications: %s", str(e))
            return []

    def get_recommendation_by_token(self, token):
        query = "SELECT * FROM recommendation_requests WHERE token = ?"
        result = self._execute_query(query, (token,), fetch_one=True)
        return dict(result) if result else None

    def submit_recommendation_letter(self, token, letter):
        query = """
            UPDATE recommendation_requests
            SET letter = ?, submitted_at = CURRENT_TIMESTAMP, status = 'submitted'
            WHERE token = ?
        """
        return self._execute_query(query, (letter, token))

    def _execute_query(self, query, params=None, fetch_one=False):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params or ())
        
            if fetch_one:
                result = cursor.fetchone()
                conn.close()
                return result
        
            result = cursor.fetchall()  # Fetch all rows here
            conn.commit()
            conn.close()
            return result  # Return rows instead of True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            if 'conn' in locals():
                conn.close()
            return [] if not fetch_one else None
