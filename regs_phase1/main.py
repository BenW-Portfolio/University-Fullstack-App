from flask import Flask, session, render_template, redirect, url_for, request
import sqlite3
import random

app = Flask('app')
app.secret_key = "secret_key"
app.debug = True


'''
Helper functions
'''
@app.route('/reset_db', methods=['GET', 'POST'])
def reset_db():
    if request.method == 'POST':
        try:
            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                with open('create.sql', 'r') as f:
                    sql_script = f.read()
                cursor.executescript(sql_script)
                conn.commit()
            
            session.clear()
            return redirect(url_for('login'))
        except Exception as e:
            print("error resetting db")
            return redirect(url_for('home'))


# Returns connection to database
def get_connection():
	connection = sqlite3.connect('database.db')
	connection.row_factory = sqlite3.Row
	return connection


# Returns whether a user is logged in
def user_logged_in() -> bool:
    # Should be safe to just check for entered user+pass
    return 'user_id' in session


def run_query(query : str):
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    cur = connection.cursor()
    cur.execute(query)
    
    res = cur.fetchall()
    connection.close()
    return res
    
    
# For single operations/existential check
def run_single_query(query : str):
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    cur = connection.cursor()
    cur.execute(query)
    
    res = cur.fetchone()
    connection.close()
    return res


# Runs an insert statement
def run_insert(insert_statement : str):
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    cur = connection.cursor()
    cur.execute(insert_statement)

    connection.commit()
    connection.close()


def run_update(query: str, params: tuple):
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    cur = connection.cursor()
    cur.execute(query, params)

    connection.commit()
    connection.close()

'''
ROUTING
'''

# Home page, displays 
@app.route('/')
def home():
    if not user_logged_in():
        return redirect(url_for('login'))

    return render_template('home.html', user_type = session['user_type'])


# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Goto home if already logged in (requires user to log out to log in as a different user)
    if user_logged_in():
        print("user already logged in")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        try:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND passcode = ?',
                (username, password)
            ).fetchone()
            
            if user:
                # Set all required session variables
                session['user_id'] = user['user_id']
                session['user_type'] = user['role']
                session['username'] = user['username']
                session['password'] = user['passcode']

                return redirect(url_for('home'))
            else:
                return redirect(url_for('login'))
        
        finally:
            conn.close()

    return render_template('login.html')

# Account creation
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        if 'user_type' not in session or session['user_type'] != 'admin':
            return redirect(url_for('login'))
        
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        program = request.form['program']
        address = request.form.get('address', '')
        
        # Create the new user account if the username is not already taken
        username_taken = run_single_query(f"SELECT * FROM users u WHERE u.username LIKE '{username}'")
        if (username_taken is None):
            conn = sqlite3.connect('database.db')
            conn.row_factory = sqlite3.Row
            conn.execute(
                'INSERT INTO users (username, passcode, role, first_name, last_name, program, address) '
                'VALUES (?, ?, "student", ?, ?, ?, ?)',
                (username, password, first_name, last_name, program, address)
            )
            conn.commit()
            conn.close()

            return redirect(url_for('home'))
        else:
            print("tried to create account with username that already exists")
            return render_template('create_account.html', error_message = "Username already taken")

    return render_template('create_account.html')


# Logout page
@app.route('/logout')
def logout():
	# Log the user out and redirect them to the login page
	session.clear()
	return redirect(url_for('login'))


# --- Define Valid Grades ---
VALID_GRADES = {'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'F'}


@app.route('/transcript', methods=['GET', 'POST'])
def view_transcript():
    conn = None
    if 'user_id' not in session or 'user_type' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_role = session['user_type']

    search_query = request.args.get('search_query', '')
    if request.method == 'POST':
        search_query = request.form.get('search_query_hidden', '')

    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if request.method == 'POST':
            if user_role == 'student':
                print(f"Attempt by student {user_id} to POST to /transcript.")
                return redirect(url_for('view_transcript'))

            try:
                enrollment_id = int(request.form['enrollment_id'])
                section_id = int(request.form['section_id'])
                new_grade = request.form.get('grade', '').strip().upper()
            except (KeyError, ValueError):
                print(f"Error: Invalid form data received for grade submission via /transcript.")
                return redirect(url_for('view_transcript', search_query=search_query))

            if new_grade and new_grade not in VALID_GRADES:
                print(f"Error: Invalid grade '{new_grade}' submitted for enrollment {enrollment_id}.")
                return redirect(url_for('view_transcript', search_query=search_query))

            can_update = False
            try:
                cursor.execute("SELECT instructor_id FROM sections WHERE section_id = ?", (section_id,))
                section_info = cursor.fetchone()
                cursor.execute("SELECT grade FROM enrollments WHERE enrollment_id = ?", (enrollment_id,))
                enrollment_info = cursor.fetchone()

                if not section_info or not enrollment_info:
                     print(f"Error: Section {section_id} or Enrollment {enrollment_id} not found during grade POST.")
                     can_update = False
                else:
                    current_grade = enrollment_info['grade']
                    section_instructor_id = section_info['instructor_id']

                    if user_role == 'gs' or user_role == 'admin':
                        can_update = True
                    elif user_role == 'instructor':
                        if str(section_instructor_id) == str(user_id):
                            if current_grade is None or current_grade == 'IP':
                                can_update = True
                            else:
                                print(f"Info: Instructor {user_id} attempted to change submitted grade for enrollment {enrollment_id}.")
                                can_update = False
                        else:
                            print(f"Permission Denied: Instructor {user_id} cannot grade section {section_id}.")
                            can_update = False

            except sqlite3.Error as e:
                 print(f"Database error during permission check for grade update: {e}")
                 can_update = False

            if can_update:
                grade_to_set = new_grade if new_grade else None
                try:
                    cursor.execute("UPDATE enrollments SET grade = ? WHERE enrollment_id = ?", (grade_to_set, enrollment_id))
                    conn.commit()
                    print(f"Success: Grade updated for enrollment {enrollment_id} by user {user_id} via /transcript.")
                except sqlite3.Error as e:
                    conn.rollback()
                    print(f"Database error during grade update commit: {e}")
            else:
                 print(f"Grade update denied or failed for enrollment {enrollment_id} by user {user_id}.")

            redirect_url = url_for('view_transcript')
            if search_query:
                redirect_url = url_for('view_transcript', search_query=search_query)
            return redirect(redirect_url)

        elif request.method == 'GET':
            template_data = {
                "user_role": user_role,
                "student_transcript": None,
                "instructor_sections": None,
                "gs_sections": None,
                "search_query": search_query
            }

            if user_role == 'student':
                cursor.execute("""
                    SELECT s.semester, s.year, c.dept_code, c.course_number, c.title, c.credits, e.grade
                    FROM enrollments e
                    JOIN sections s ON e.section_id = s.section_id
                    JOIN courses c ON s.course_id = c.course_id
                    WHERE e.student_id = ? ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
                """, (user_id,))
                template_data['student_transcript'] = cursor.fetchall()

            elif user_role == 'instructor':
                #print(f"--- Processing GET request for instructor {user_id} ---")
                cursor.execute("""
                    SELECT s.section_id, s.semester, s.year, s.day, s.time_slot, c.dept_code, c.course_number, c.title
                    FROM sections s JOIN courses c ON s.course_id = c.course_id
                    WHERE s.instructor_id = ? ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
                """, (user_id,))
                sections = cursor.fetchall()
                instructor_sections_data = []
                for section in sections:
                    #current_section_id = section['section_id'] 
                    #print(f"Querying students for section_id: {current_section_id}")
                    cursor.execute("""
                        SELECT e.enrollment_id, e.grade, u.user_id AS student_id, u.first_name, u.last_name
                        FROM enrollments e JOIN users u ON e.student_id = u.user_id
                        WHERE e.section_id = ? ORDER BY u.last_name, u.first_name
                    """, (section['section_id'],))
                    students = cursor.fetchall()
                    #print(f"Students found for section {current_section_id}: {[dict(row) for row in students]}") # Print student details found
                    instructor_sections_data.append({"details": section, "students": students})
                template_data['instructor_sections'] = instructor_sections_data

            elif user_role == 'gs' or user_role == 'admin':
                base_section_query = """
                    SELECT s.section_id, s.semester, s.year, s.day, s.time_slot, c.dept_code, c.course_number, c.title,
                           GROUP_CONCAT(DISTINCT sec_instr.first_name || ' ' || sec_instr.last_name) AS instructor_names
                    FROM sections s JOIN courses c ON s.course_id = c.course_id LEFT JOIN users sec_instr ON s.instructor_id = sec_instr.user_id
                """
                student_query = """
                    SELECT e.enrollment_id, e.grade, e.section_id, u.user_id AS student_id, u.first_name, u.last_name
                    FROM enrollments e JOIN users u ON e.student_id = u.user_id
                """
                params = []
                section_where_clause = ""
                student_where_clause = ""
                search_term = template_data['search_query'].strip()
                matching_student_ids = []
                matching_section_ids = []

                if search_term:
                    search_like = f"%{search_term}%"
                    cursor.execute("""
                        SELECT user_id FROM users WHERE role = 'student' AND
                              (first_name LIKE ? OR last_name LIKE ? OR username LIKE ? OR CAST(user_id AS TEXT) LIKE ?)
                    """, (search_like, search_like, search_like, search_like))
                    matching_student_ids = [row['user_id'] for row in cursor.fetchall()]
                    if matching_student_ids:
                        id_placeholders = ','.join('?' for _ in matching_student_ids)
                        student_where_clause = f" WHERE e.student_id IN ({id_placeholders})"
                        params.extend(matching_student_ids)
                        cursor.execute(f"SELECT DISTINCT section_id FROM enrollments WHERE student_id IN ({id_placeholders})", matching_student_ids)
                        matching_section_ids = [row['section_id'] for row in cursor.fetchall()]
                        if matching_section_ids:
                            sec_id_placeholders = ','.join('?' for _ in matching_section_ids)
                            section_where_clause = f" WHERE s.section_id IN ({sec_id_placeholders})"
                            params.extend(matching_section_ids)
                        else: section_where_clause = " WHERE 1=0"
                    else:
                        student_where_clause = " WHERE 1=0"
                        section_where_clause = " WHERE 1=0"

                full_section_query = base_section_query + section_where_clause + " GROUP BY s.section_id ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number"
                full_student_query = student_query + student_where_clause + " ORDER BY u.last_name, u.first_name"
                section_params = []
                student_params = []
                if "s.section_id IN" in section_where_clause: section_params = params[len(matching_student_ids):]
                if "e.student_id IN" in student_where_clause: student_params = params[:len(matching_student_ids)]

                cursor.execute(full_section_query, section_params)
                all_sections = cursor.fetchall()
                cursor.execute(full_student_query, student_params)
                all_students = cursor.fetchall()
                students_by_section = {}
                for student in all_students:
                    sec_id = student['section_id']
                    if sec_id not in students_by_section: students_by_section[sec_id] = []
                    students_by_section[sec_id].append(student)
                gs_sections_data = []
                for section in all_sections:
                     sec_id = section['section_id']
                     gs_sections_data.append({"details": section, "students": students_by_section.get(sec_id, [])})
                template_data['gs_sections'] = gs_sections_data

            return render_template('view_transcript.html', **template_data, valid_grades=VALID_GRADES)

    except sqlite3.Error as e:
        print(f"Database error processing /transcript request: {e}")
        if conn: conn.rollback()
        return redirect(url_for('home'))
    except Exception as e:
        print(f"An unexpected error occurred processing /transcript request: {e}")
        if conn: conn.rollback()
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

# Allows student to update personal info
#   - Relevant functs - Personal 
@app.route('/personal_info', methods=['GET', 'POST'])
def personal_info():
    if not user_logged_in():
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        new_username = request.form['username']
        new_firstname = request.form['first_name']
        new_lastname = request.form['last_name']
        new_address = request.form['address']
        new_program = request.form['program']

        # run_insert(f"UPDATE users SET username = {new_username} WHERE user_id = {user_id}")
        # run_insert(f"UPDATE users SET first_name = {new_firstname} WHERE user_id = {user_id}")
        # run_insert(f"UPDATE users SET last_name = {new_lastname} WHERE user_id = {user_id}")
        # run_insert(f"UPDATE users SET address = {new_address} WHERE user_id = {user_id}")
        # run_insert(f"UPDATE users SET program = {new_program} WHERE user_id = {user_id}")


        update_query = """
            UPDATE users
            SET username = ?, first_name = ?, last_name = ?, address = ?, program = ?
            WHERE user_id = ?
        """
        params = (new_username, new_firstname, new_lastname, new_address, new_program, user_id)

        run_update(update_query, params)

    
    username = session['username']
    password = session['password']
    user = run_single_query(f"SELECT * FROM users WHERE username LIKE '{username}' AND passcode LIKE '{password}'")
    print(type(user))
    return render_template('personal_info.html', user_id = session['user_id'],
                                                 user = user)


# Displays course list + registration functionality 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if not user_logged_in():
        return redirect(url_for('login'))
    
    # Get course list
    course_list = run_query(f"SELECT *, c.title FROM sections s JOIN courses c ON c.course_id = s.course_id")

    if request.method == 'POST':
        section_id = request.form['section_id']
        # Don't allow registration for non-students
        if (session['user_type'] != 'student'):
            return render_template('register.html', UID = session['user_id'],
                                                    user_type = session['user_type'],
                                                    courses = course_list,
                                                    display_message = "ERROR: User is not a student cannot register for course")
        
        # Redirect to same page if already enrolled
        existing_query = run_single_query(f"SELECT * FROM enrollments e WHERE e.section_id = {section_id} AND e.student_id = {session['user_id']}")
        if (existing_query is not None):
            return render_template('register.html', UID = session['user_id'],
                                                    user_type = session['user_type'],
                                                    courses = course_list,
                                                    display_message = "ERROR: User is already enrolled in this course")

        # Get the course itself instead of section
        course_id_query = run_single_query(f"SELECT * FROM sections s WHERE s.section_id = {section_id}")
        course_id = course_id_query['course_id']
        # If course has a prerequisite, check if the student has those classes 
        prerequisites = run_query(f"SELECT p.prerequisite_course_id FROM prerequisites p WHERE p.course_id = {course_id}")
        for prereq in prerequisites:
            # Check if the student has the prereq 
            prereq_course_query = run_query(
                f"SELECT * FROM enrollments e JOIN sections s ON e.section_id = s.section_id "
                f"WHERE e.student_id = {session['user_id']} AND s.course_id = {prereq['prerequisite_course_id']} "
            )
            
            # Redirect to login page if student doesn't have the prereq (found 0 rows)
            if len(prereq_course_query) == 0:
                return render_template('register.html', UID = session['user_id'],
                                                        user_type = session['user_type'],
                                                        courses = course_list,
                                                        display_message = "ERROR: Prerequisite Not Satisfied, unable to add course")
        # Check for time conflicts
    
        new_day = course_id_query['day']
        new_time_slot = course_id_query['time_slot']
        new_semester = course_id_query['semester']
        new_year = course_id_query['year']
        
        # Parse the new section's start and end time.
        new_start_str, new_end_str = new_time_slot.split('-')
        new_start = int(new_start_str)
        new_end = int(new_end_str)
        
        # Query the student's current enrollments in the same semester and year.
        student_sections = run_query(
            f"SELECT s.day, s.time_slot FROM enrollments e JOIN sections s ON e.section_id = s.section_id "
            f"WHERE e.student_id = {session['user_id']} AND s.semester = '{new_semester}' AND s.year = {new_year}"
        )
        
        # Check each enrolled section for a day and time overlap.
        for sec in student_sections:
            if sec['day'] == new_day:
                student_start_str, student_end_str = sec['time_slot'].split('-')
                student_start = int(student_start_str)
                student_end = int(student_end_str)
                
                # If the intervals overlap, then a conflict exists.
                if new_start < student_end and student_start < new_end:
                    return render_template('register.html', 
                                           user_id=session['user_id'],
                                           user_type=session['user_type'],
                                           courses=course_list,
                                           display_message="ERROR: Time conflict exists, unable to add course.")

        # Now we can add the course, so insert it into the DB
        run_insert(f"INSERT INTO enrollments (student_id, section_id, grade) VALUES ({session['user_id']}, {section_id}, 'IP')") 


    return render_template('register.html', user_id = session['user_id'],
                                            user_type = session['user_type'],
                                            courses = course_list,
                                            display_message = None)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


