import sqlite3
from datetime import datetime

class GSQuery:
    def __init__(self, db_path):
        self.db_path = db_path
        
    def _get_connection(self):
        """Create a new connection for each operation"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_applications(self, status_filter=None):
        """Retrieve all applications with optional status filter"""
        conn = self._get_connection()
        try:
            query = """
                SELECT a.*, 
                    t.received as transcript_received,
                    COUNT(r.letter_id) as letters_received
                FROM applications a
                LEFT JOIN transcript t ON a.application_id = t.application_id
                LEFT JOIN recommendation r ON a.application_id = r.application_id
            """
            
            params = ()
            if status_filter:
                query += " WHERE a.status = ?"
                params = (status_filter,)
            
            query += " GROUP BY a.application_id"
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def get_application_details(self, application_id):
        """Get complete application details"""
        conn = self._get_connection()
        try:
            return conn.execute("""
                SELECT a.*, ai.*, d.*, t.*, 
                    GROUP_CONCAT(r.recommender_name) as recommenders,
                    COUNT(r.letter_id) as letters_received
                FROM applications a
                LEFT JOIN academic_info ai ON a.application_id = ai.application_id
                LEFT JOIN degrees d ON a.application_id = d.application_id
                LEFT JOIN transcript t ON a.application_id = t.application_id
                LEFT JOIN recommendation r ON a.application_id = r.application_id
                WHERE a.application_id = ?
                GROUP BY a.application_id
            """, (application_id,)).fetchone()
        finally:
            conn.close()

    def update_application_status(self, application_id, new_status):
        """Update application status"""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE applications 
                    SET status = ?
                    WHERE application_id = ?
                """, (new_status, application_id))
                return conn.total_changes > 0
        finally:
            conn.close()

    def mark_transcript_received(self, application_id, received_by):
        conn = self._get_connection()
        try:
            with conn:
                # First, check if the record exists
                result = conn.execute("""
                    SELECT 1 FROM transcript WHERE application_id = ?
                """, (application_id,)).fetchone()

                if result:
                    # Update existing
                    conn.execute("""
                        UPDATE transcript
                        SET received = TRUE,
                            received_date = ?,
                            received_by = ?
                        WHERE application_id = ?
                    """, (datetime.now(), received_by, application_id))
                else:
                    # Insert new
                    conn.execute("""
                        INSERT INTO transcript (application_id, received, received_date, received_by)
                        VALUES (?, TRUE, ?, ?)
                    """, (application_id, datetime.now(), received_by))

                return True
        finally:
            conn.close()


    def update_personal_info(self, application_id, update_data):
        """Update applicant's personal information"""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE application
                    SET address = ?,
                        phone = ?,
                        ssn = ?
                    WHERE application_id = ?
                """, (
                    update_data.get('address'),
                    update_data.get('phone'),
                    update_data.get('ssn'),
                    application_id
                ))
                return conn.total_changes > 0
        finally:
            conn.close()

    def search_applications(self, search_term, search_type='name'):
        """Search applications with flexible criteria"""
        conn = self._get_connection()
        try:
            queries = {
            'name': """
                SELECT a.*, 
                    t.received as transcript_received,
                    COUNT(r.letter_id) as letters_received
                FROM applications a
                LEFT JOIN transcript t ON a.application_id = t.application_id
                LEFT JOIN recommendation r ON a.application_id = r.application_id
                WHERE a.first_name LIKE ? OR a.last_name LIKE ?
                GROUP BY a.application_id
            """,
            'uid': """
                SELECT a.*, 
                    t.received as transcript_received,
                    COUNT(r.letter_id) as letters_received
                FROM applications a
                LEFT JOIN transcript t ON a.application_id = t.application_id
                LEFT JOIN recommendation r ON a.application_id = r.application_id
                WHERE a.uid = ?
                GROUP BY a.application_id
            """,
            'ssn': """
                SELECT a.*, 
                    t.received as transcript_received,
                    COUNT(r.letter_id) as letters_received
                FROM applications a
                LEFT JOIN transcript t ON a.application_id = t.application_id
                LEFT JOIN recommendation r ON a.application_id = r.application_id
                WHERE a.ssn = ?
                GROUP BY a.application_id
            """
            }
        
            if search_type not in queries:
                raise ValueError("Invalid search type")

            if search_type == 'name':
                params = (f"%{search_term}%", f"%{search_term}%")
            else:
                params = (search_term,)

            return conn.execute(queries[search_type], params).fetchall()
        finally:
            conn.close()


    def get_statistics(self, semester=None, year=None, degree=None):
        conn = self._get_connection()
        try:
            query = """
                SELECT 
                    a.degree_program AS degree_sought,
                    a.admission_semester || ' ' || a.admission_year AS term,
                    COUNT(*) AS total_applications,
                    AVG(ai.gre_verbal) AS avg_verbal,
                    AVG(ai.gre_quant) AS avg_quant,
                    SUM(CASE WHEN a.status = 'Admitted' THEN 1 ELSE 0 END) AS admitted,
                    SUM(CASE WHEN a.status = 'Rejected' THEN 1 ELSE 0 END) AS rejected
                FROM applications a
                LEFT JOIN academic_info ai ON a.application_id = ai.application_id
                WHERE 1=1
            """
            params = []
            if semester:
                query += " AND a.admission_semester = ?"
                params.append(semester)
            if year:
                query += " AND a.admission_year = ?"
                params.append(year)
            if degree:
                query += " AND a.degree_program = ?"
                params.append(degree)

            query += " GROUP BY a.degree_program, a.admission_semester, a.admission_year"
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def filter_applicants(self, semester=None, year=None, degree=None):
        conn = self._get_connection()
        try:
            query = "SELECT * FROM applications WHERE 1=1"
            params = []
            if semester:
                query += " AND admission_semester = ?"
                params.append(semester)
            if year:
                query += " AND admission_year = ?"
                params.append(year)
            if degree:
                query += " AND degree_program = ?"
                params.append(degree)
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    def get_pending_recommendations(self):
        """Get applications with missing recommendations"""
        conn = self._get_connection()
        try:
            return conn.execute("""
                SELECT a.*, 
                    (SELECT COUNT(*) FROM recommendation r 
                    WHERE r.application_id = a.application_id 
                    AND r.submitted = FALSE) as pending_letters
                FROM applications a
                HAVING pending_letters > 0
            """).fetchall()
        finally:
            conn.close()

    def get_academic_info(self, application_id):
        """Get academic information for an application"""
        conn = self._get_connection()
        try:
            return conn.execute("""
                SELECT * FROM academic_info 
                WHERE application_id = ?
            """, (application_id,)).fetchone()
        finally:
            conn.close()

    def get_transcript_status(self, application_id):
        """Get transcript status for an application"""
        conn = self._get_connection()
        try:
            result = conn.execute("""
                SELECT received, received_date 
                FROM transcript 
                WHERE application_id = ?
            """, (application_id,)).fetchone()
            
            # Return empty dict if no transcript record found
            return dict(result) if result else {'received': False, 'received_date': None}
        finally:
            conn.close()

    def close(self):
        """Maintained for backward compatibility (no-op as connections are managed per method)"""
        pass