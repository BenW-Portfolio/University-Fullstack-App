import sqlite3
from datetime import datetime

class reviewerQuery:
    def __init__(self, path):
        self.path = path
        print(f"[DEBUG] reviewerQuery initialized with DB path: {self.path}")

    def get_applications_for_decision(self, search_term=None, semester=None, year=None):
        print(f"[DEBUG] get_applications_for_decision called with, search_term={search_term}, semester={semester}, year={year}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                base_query = """
                SELECT a.application_id, a.user_id as student_id, 
                       a.first_name, a.last_name, a.degree_program,
                       a.admission_semester, a.admission_year, a.status,
                       COUNT(r.review_id) as review_count
                FROM APPLICATIONS a
                LEFT JOIN REVIEW r ON a.application_id = r.application_id
                WHERE a.application_id IS NOT NULL
                """

  

                where_clause = []
                params = []

               

                if search_term:
                    where_clause.append("""
                    (a.first_name LIKE ? OR a.last_name LIKE ? 
                    OR a.user_id LIKE ?)""")
                    params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])

                if semester:
                    where_clause.append("a.admission_semester = ?")
                    params.append(semester)

                if year:
                    where_clause.append("a.admission_year = ?")
                    params.append(year)

                query = base_query
                if where_clause:
                    query += " WHERE " + " AND ".join(where_clause)
                query += " GROUP BY a.application_id ORDER BY a.admission_year DESC, a.admission_semester"

                print(f"[DEBUG] Executing query: {query}")
                print(f"[DEBUG] With params: {params}")
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                print(f"[DEBUG] applications retrieved YIPPPP: {results}")
                print(f"[DEBUG] Retrieved {len(results)} applications")
                return results

        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return []

    def get_application_full(self, application_id):
        print(f"[DEBUG] get_application_full called for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                SELECT a.*, d.decision, d.decision_date, 
                       u.email as student_email,
                       u.created_at as created_at
                FROM APPLICATIONS a
                LEFT JOIN DECISION d ON a.application_id = d.application_id
                JOIN USERS u ON a.user_id = u.user_id
                WHERE a.application_id = ?
            """, (application_id,))
                application = cursor.fetchone()
                if not application:
                    print("[DEBUG] No application found")
                    return None

                app_data = dict(application)
                app_data['academic'] = self.get_academic_info(application_id)
                app_data['degrees'] = self.get_degrees(application_id)
                app_data['transcripts'] = self.get_transcript_status(application_id)
                app_data['recommendations'] = self.get_recommendations(application_id)
                app_data['reviews'] = self.get_reviews(application_id)
                print(f"[DEBUG] Full application data retrieved for ID {application_id}")
                return app_data
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return None

    def get_academic_info(self, application_id):
        print(f"[DEBUG] get_academic_info for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT gre_verbal, gre_quant, gre_year, gre_subject, gre_subject_score,
                           toefl_score, toefl_exam_date, interests, experience
                    FROM APPLICATIONS
                    WHERE application_id = ?
                """, (application_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return None

    def get_reviews(self, application_id):
        print(f"[DEBUG] get_reviews for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.*, u.first_name, u.last_name, u.email
                    FROM REVIEW r
                    JOIN USERS u ON r.faculty_id = u.user_id
                    WHERE r.application_id = ?
                    ORDER BY r.review_date DESC
                """, (application_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return []

    def get_degrees(self, application_id):
        print(f"[DEBUG] get_degrees for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT degree_type, gpa, major, year, university
                    FROM DEGREES
                    WHERE application_id = ?
                    ORDER BY degree_type DESC
                """, (application_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return []

    def get_transcript_status(self, application_id):
        print(f"[DEBUG] get_transcript_status for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT t.*, u.first_name as received_by_name
                    FROM TRANSCRIPT t
                    LEFT JOIN USERS u ON t.received_by = u.user_id
                    WHERE t.application_id = ?
                """, (application_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return None

    def get_recommendations(self, application_id):
        print(f"[DEBUG] get_recommendations for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT letter_id, recommender_name, recommender_email, 
                           rating, generic_flag, credible_flag, submitted
                    FROM RECOMMENDATION
                    WHERE application_id = ?
                    ORDER BY submitted DESC, rating DESC
                """, (application_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return []

    def submit_review(self, application_id, faculty_id, rating, deficiency_courses=None, reject_reason=None, comments=None, recommended_advisor=None):
        print(f"[DEBUG] submit_review called with application_id={application_id}, faculty_id={faculty_id}, rating={rating}")
        try:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO REVIEW (
                        application_id, faculty_id, rating, deficiency_courses,
                        reject_reason, comments, recommended_advisor, review_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    application_id, faculty_id, rating, deficiency_courses,
                    reject_reason, comments, recommended_advisor, datetime.now()
                ))
                conn.commit()
                print("[DEBUG] Review submitted successfully")
                return True
        except sqlite3.Error as e:
            print(f"[ERROR] Insert error: {e}")
            return False

    def submit_final_decision(self, application_id, decision, decided_by):
        print(f"[DEBUG] submit_final_decision called with application_id={application_id}, "
          f"decision={decision}, decided_by={decided_by}")
        try:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.cursor()

                # Format timestamp as string
                decision_date = datetime.now().isoformat(sep=' ', timespec='seconds')
                print(f"[DEBUG] decision_date string: {decision_date!r}")

                # Insert without comments/notes column
                cursor.execute("""
                INSERT INTO DECISION (
                    application_id, decision, decided_by, decision_date
                ) VALUES (?, ?, ?, ?)
            """, (
                application_id,
                decision,
                decided_by,
                decision_date
            ))

                new_status = 'Admitted' if 'Admit' in decision else 'Rejected'
                cursor.execute("""
                UPDATE APPLICATIONS 
                SET status = ?
                WHERE application_id = ?
            """, (new_status, application_id))

                conn.commit()
                print(f"[DEBUG] Decision submitted and status updated to {new_status}")
                return True

        except sqlite3.Error as e:
            print(f"[ERROR] Decision error: {e!r}")
            return False

    def update_application_status(self, application_id, new_status, updated_by, notes=None):
        print(f"[DEBUG] update_application_status called with application_id={application_id}, new_status={new_status}")
        try:
            with sqlite3.connect(self.path) as conn:
                cursor = conn.cursor()

                if new_status == 'Transcript Received':
                    cursor.execute("""
                        UPDATE TRANSCRIPT 
                        SET received = 1, received_date = ?, received_by = ?
                        WHERE application_id = ?
                    """, (datetime.now(), updated_by, application_id))

                cursor.execute("""
                    UPDATE APPLICATIONS 
                    SET status = ?
                    WHERE application_id = ?
                """, (new_status, application_id))

                conn.commit()
                print("[DEBUG] Status updated successfully")
                return True
        except sqlite3.Error as e:
            print(f"[ERROR] Status update error: {e}")
            return False

    def get_decision(self, application_id):
        print(f"[DEBUG] get_decision for application_id={application_id}")
        try:
            with sqlite3.connect(self.path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT d.*, u.first_name as decider_first, u.last_name as decider_last,
                           a.first_name, a.last_name, a.degree_program
                    FROM DECISION d
                    JOIN USERS u ON d.decided_by = u.user_id
                    JOIN APPLICATIONS a ON d.application_id = a.application_id
                    WHERE d.application_id = ?
                """, (application_id,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[ERROR] Query error: {e}")
            return None
        
    
