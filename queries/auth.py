import sqlite3
import datetime
import random
import time
#from werkzeug.security import generate_password_hash

class AuthQuery:
    def __init__(self, db_path):
        self.db_path = db_path

    def authenticate_user(self, email, password):
        #hashed_pw = generate_password_hash(password)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND passcode = ?", 
                (email, password)  
            ).fetchone()
            if user:
                return dict(user)  
            return None

    def create_user(self, user_data):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                conn.execute("BEGIN IMMEDIATE")  # Start transaction with lock

                # Check email uniqueness first
                email_check = conn.execute(
                    "SELECT 1 FROM users WHERE email = ?", 
                    (user_data['email'],)
                ).fetchone()
                if email_check:
                    raise Exception("Email already exists")

                #hashed_pw = generate_password_hash(user_data['password'])
                # Insert user
                cursor = conn.execute("SELECT MAX(user_id) FROM users")
                values = cursor.fetchone()
                cursor = conn.execute("""
                    INSERT INTO users (user_id, username, passcode, email, role, first_name, last_name)
                    VALUES (?, ?, ?,?,?,?,?)
                """, (values[0] + 1,user_data['email'],user_data['password'],user_data['email'],user_data['role'],user_data['first_name'],user_data['last_name']))
                
                user_id = cursor.lastrowid

                # Generate student ID with retry logic
                student_id = self._generate_student_id(conn, max_attempts=10)
                '''
                # Insert application (updated for new schema)
                conn.execute("""
                    INSERT INTO APPLICATIONS (
                        user_id, user_id, ssn, first_name, last_name, address, phone,
                        status, degree_program, admission_semester, admission_year, email
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Application Incomplete', ?, ?, ?, ?)
                """, (
                    user_id,
                    student_id,  # This is the CHAR(8) student ID
                    user_data['ssn'],
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['address'],
                    user_data['phone'],
                    user_data.get('degree_program', 'MS'),  # Changed from degree_sought
                    user_data.get('admission_semester', 'Spring'),
                    user_data.get('admission_year', datetime.datetime.now().year + 1),
                    user_data.get('email', '')
                ))
                
                '''
                conn.commit()
                return {"user_id": user_id, "student_id": student_id}

        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed: APPLICATIONS.user_id" in str(e):
                raise Exception("Failed to generate unique student ID after multiple attempts")
            raise Exception("Database integrity error")
        except Exception as e:
            conn.rollback()
            raise Exception(f"Registration failed: {str(e)}")

    def _generate_student_id(self, conn, max_attempts=10):
        """Generates a unique 8-digit student ID"""
        attempts = 0
        while attempts < max_attempts:
            candidate = str(random.randint(10000000, 99999999))
            result = conn.execute(
                "SELECT 1 FROM APPLICATIONS WHERE user_id = ?", 
                (candidate,)
            ).fetchone()
            if not result:
                return candidate
            attempts += 1
            time.sleep(0.1)  # Small delay between attempts
        raise Exception("Failed to generate unique student ID after maximum attempts")