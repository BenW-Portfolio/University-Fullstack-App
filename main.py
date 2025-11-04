from flask import Flask, session, render_template, redirect, url_for, request, flash
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime

from queries.setup import init_db
from queries.admin import AdminQuery
from queries.applicant import ApplicationQuery
from queries.auth import AuthQuery
from queries.cac import CACQuery
from queries.gs import GSQuery
from queries.applicant import ApplicationQuery  # For recommender.py
from queries.reviewer import reviewerQuery

gs_query = GSQuery("database.db")

import sqlite3
import random


app = Flask(__name__)
app.secret_key = "yikes"
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
            return redirect(url_for('login'))


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

def get_admission_decision(user_id):
    """Gets the final admission decision for a user."""
    query = """
        SELECT d.decision
        FROM DECISION d
        JOIN APPLICATIONS a ON d.application_id = a.application_id
        WHERE a.user_id = ?
        ORDER BY d.decision_date DESC
        LIMIT 1;
    """
    conn = get_connection()
    result = conn.execute(query, (user_id,)).fetchone()
    conn.close()
    # Ensure you return None if no decision is found, or handle potential None result
    return result['decision'] if result else None

def get_application_status(user_id):
    """Fetches the current status of an application directly from APPLICATIONS table."""
    query = "SELECT status FROM APPLICATIONS WHERE user_id = ?"
    conn = get_connection()
    result = conn.execute(query, (user_id,)).fetchone()
    conn.close()
    # Ensure you return None if no application is found
    return result['status'] if result else None

def accept_admission_offer(user_id):
    """Handles the process of accepting an admission offer."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Verify the user was actually admitted and hasn't already accepted/declined
        cursor.execute("""
            SELECT a.application_id, a.degree_program, a.status, u.address AS user_address, a.address AS app_address
            FROM APPLICATIONS a
            JOIN users u ON a.user_id = u.user_id
            LEFT JOIN DECISION d ON a.application_id = d.application_id
            WHERE a.user_id = ? AND d.decision LIKE 'Admit%' AND u.role = 'applicant'
            ORDER BY d.decision_date DESC
            LIMIT 1;
        """, (user_id,))
        app_info = cursor.fetchone()

        if not app_info:
            print(f"Acceptance failed: User {user_id} not found, not admitted, or already processed.")
            if conn: conn.close()
            return False, "Offer not available or already processed."

        application_id = app_info['application_id']
        degree_program_raw = app_info['degree_program']
        current_status = app_info['status']

        if current_status in ['Offer Accepted', 'Offer Declined']:
             print(f"Acceptance failed: User {user_id} application status is already '{current_status}'.")
             if conn: conn.close()
             return False, "You have already responded to this offer."

        address = app_info['user_address'] if app_info['user_address'] else app_info['app_address']
        program_for_student_table = 'ms' if degree_program_raw == 'MS' else ('phd' if degree_program_raw == 'PhD' else None)

        if not program_for_student_table:
            print(f"Acceptance failed: Invalid degree program '{degree_program_raw}' for user {user_id}.")
            if conn: conn.close()
            return False, "Invalid degree program found in application."

        cursor.execute("BEGIN TRANSACTION;")
        cursor.execute("UPDATE users SET role = 'student' WHERE user_id = ?", (user_id,))
        cursor.execute("""
            INSERT INTO students (userID, address, program, graduationDate, approved, suspended, initial_advising_complete)
            VALUES (?, ?, ?, NULL, 0, 0, 0);
        """, (user_id, address, program_for_student_table))
        # --- Make sure 'Offer Accepted' is valid in your APPLICATIONS status CHECK constraint ---
        cursor.execute("UPDATE APPLICATIONS SET status = 'Offer Accepted' WHERE application_id = ?;", (application_id,))
        conn.commit()
        print(f"User {user_id} accepted admission.")
        if conn: conn.close()
        return True, "Admission accepted successfully! Welcome."

    except sqlite3.Error as e:
        print(f"Database error during acceptance for user {user_id}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Database error occurred during acceptance."
    except Exception as e:
        print(f"Unexpected error during acceptance for user {user_id}: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False, f"An unexpected error occurred during acceptance."

def reject_admission_offer(user_id):
    """Handles the process of rejecting an admission offer."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.application_id, a.status
            FROM APPLICATIONS a
            JOIN users u ON a.user_id = u.user_id
            LEFT JOIN DECISION d ON a.application_id = d.application_id
            WHERE a.user_id = ? AND d.decision LIKE 'Admit%' AND u.role = 'applicant'
            ORDER BY d.decision_date DESC
            LIMIT 1;
        """, (user_id,))
        app_info = cursor.fetchone()

        if not app_info:
            print(f"Rejection failed: User {user_id} not found, not admitted, or already processed.")
            if conn: conn.close()
            return False, "Offer not available or already processed."

        application_id = app_info['application_id']
        current_status = app_info['status']

        if current_status in ['Offer Accepted', 'Offer Declined']:
             print(f"Rejection failed: User {user_id} application status is already '{current_status}'.")
             if conn: conn.close()
             return False, "You have already responded to this offer."

        # --- Make sure 'Offer Declined' is valid in your APPLICATIONS status CHECK constraint ---
        cursor.execute("UPDATE APPLICATIONS SET status = 'Offer Declined' WHERE application_id = ?;", (application_id,))
        conn.commit()
        print(f"User {user_id} rejected admission offer.")
        if conn: conn.close()
        return True, "Admission offer declined."

    except sqlite3.Error as e:
        print(f"Database error during rejection for user {user_id}: {e}")
        if conn: conn.close()
        return False, f"Database error occurred during rejection."
    except Exception as e:
        print(f"Unexpected error during rejection for user {user_id}: {e}")
        if conn: conn.close()
        return False, f"An unexpected error occurred during rejection."

@app.route('/', methods = ['POST', 'GET'])
def login():
    #error = ""
    with getConnection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if request.method == 'POST': 
            session['user'] = request.form["username"]
            session['pw'] = request.form["password"]
            cursor.execute("SELECT passcode FROM users WHERE username = ?", (session['user'],))
            values=cursor.fetchone()
            #print("pass = " + session['pw']) DEBUG
            #print("realpass = " + values['password']) DEBUG
            #print("comparison = " + str(session['pw'] == values['password'])) DEBUG
            if (values is None) or (session['pw'] != values['passcode']):
                flash("Username or password is not correct", 'error')
                return render_template("login.html")
            elif session['pw'] == values['passcode']:
                #Now that we have a sucsessful login, purge password from session and get user info
                session.pop('pw')

                cursor.execute("SELECT * FROM users WHERE username = ?", (session['user'],))
                values = cursor.fetchone()
                session['user_type'] = values['role']
                session['userID'] = values['user_id']
                session['user_id'] = values['user_id']
                session['role'] = values['role']
                print(user_logged_in())
                #print("role  = " + values['role'])

                #Redirects the user to their homepage
                if session['user_type'] == ('admin'):
                    return redirect('/adminHome')
                elif session['user_type'] == ('advisor'):
                    return redirect('/advisorHome')
                elif session['user_type'] == 'instructor':
                    return redirect('/instructorHome')
                elif session['user_type'] == ('gs'):
                    return redirect('/gradSecHome')
                elif session['user_type'] == ('alumni'):
                    return redirect('/alumni')
                elif session['user_type'] == ('reviewer'):
                    return redirect(url_for('reviewer.dashboard'))
                elif session['user_type'] == ('applicant'):
                    return redirect(url_for('applicant_dashboard'))
                elif session['user_type'] == ('cac'):
                    return redirect(url_for('cac.dashboard'))
                elif session['user_type'] == ('advisor/instructor'):
                    return redirect(url_for('advisor_instructor_home'))
                elif session['user_type'] == ('advisor/instructor/reviewer'):
                    return redirect(url_for('advisor_instructor_reviewer_home'))
                elif session['user_type'] == ('student'):
                    suspend(session['userID'])
                    return redirect('/studentHome')
                
            #connection.commit()
            #connection.close()
    return render_template("login.html")

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Log the user out and redirect them to the login page
    session.pop('user', None)
    session.pop('pw', None)
    session.pop('user_type', None)
    session.pop('userID', None)
    session.clear()
    return redirect('/')

@app.route('/createAccount', methods = ['POST', 'GET'] )
def createAccount():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if request.method == 'POST':
        fname = request.form["fname"]
        lname = request.form["lname"]
        username = request.form["username"]
        pw = request.form["pass"]
        address = request.form["address"]
        cursor.execute("SELECT MAX(user_id) FROM users")
        address = request.form.get('address', '')
        #NEEDS FIXING BECAUSE USERID IS A PRIMARY KEY
        max_id = cursor.fetchone()[0]
        random_id = max_id + 1 if max_id is not None else 1000

        program = request.form['program']
        gradDate = request.form['gradSem'] + " " + request.form['gradYear']

        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute("SELECT username FROM users")
        values = cursor.fetchall()
        connection.commit()
        connection.close()

        test = False
        #print(values)
        for i in range(len(values)):
            if (username == values[i][0]):
                #okay I still don't really know how flash works
                flash("Account already exists")
                test = True
                i = random_id
                return redirect('/createAccount')
        if (test == False):
            connection = sqlite3.connect("database.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (user_id, username, passcode, role, first_name, last_name) VALUES (?,?,?, ?, ?, ?)", (random_id, username, pw, 'student', fname, lname,))
            cursor.execute("INSERT INTO students (userID, address, program, graduationDate, approved, suspended) VALUES (?, ?, ?, ?, ?, ?)", (random_id , address, program, gradDate, 0, 0,))
            values = cursor.fetchall()
            cursor.close()
            connection.commit()
            connection.close()

            flash("Account created! Please log in.")
            return redirect('/')

    return render_template("createAccount.html")

@app.route('/alumni', methods = ['POST', 'GET'])
def alumni():
    
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute("SELECT user_id, first_name, last_name from users WHERE username = ?", (session['user'], ))
    userID = cursor.fetchone()

    cursor.execute("SELECT * FROM alumni WHERE userID = ? ", (userID[0],))
    values = cursor.fetchall()[0]

#-------------------------THIS IS GONNA GIVE AN ISSUE---------------------------------
    #cursor.execute("SELECT course.course_id, course.title, course.credits, course.course_number, course.dept_code, outcome.grade, outcome.semester FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (userID[0],))
    #COME BACK TOcursor.execute("SELECT course.course_id, course.title, course.credits, course.course_number, course.dept_code, outcome.grade FROM enrollments outcome LEFT JOIN courses course ON outcome.course_id = course.course_id WHERE outcome.studentID = ?", (userID[0],))
    cursor.execute("SELECT course.course_id, course.title, course.credits, course.dept_code, course.course_number, enrollments.grade FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id LEFT JOIN courses course ON sections.course_id = course.course_id WHERE enrollments.student_id = ?", (userID[0],))
    courses = cursor.fetchall()

    #for i in userID:
        #print(i)

    cursor.close()
    connection.commit()
    connection.close()

    return render_template("alumni.html", values = values, fname = userID[1], lname = userID[2], courses = courses)

@app.route('/updateInfo', methods = ['POST', 'GET'])
def updateInfo():

    back = request.referrer

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #print("UserID = " + str(session['userID']))
    if session['user_type'] == 'alumni' :
        cursor.execute("SELECT * FROM alumni JOIN users ON alumni.userID = users.user_id WHERE users.user_id = ?", (int(session['userID']), ))
    elif session['user_type'] == 'student':
        cursor.execute("SELECT * FROM students JOIN users ON students.userID = users.user_id WHERE users.user_id = ?", (int(session['userID']), ))

    user = cursor.fetchone()
    userGradYear = int(user[3][1:])
    #print(userGradYear)
    #print("user = " + str(user)) DEBUG

    if request.method == 'POST':
        #print("Form keys: ", list(request.form.keys()))
        newFName = request.form['fname']
        newLName = request.form['lname']
        newPass = request.form['password']
        newAddress = request.form['address']

        cursor.execute("UPDATE users SET first_name = ?, last_name = ?, passcode = ? WHERE user_id = ?", (newFName, newLName, newPass, session['userID'], ))

        if session['user_type'] == 'alumni':
            back = '/alumni'
            #cursor.execute("SELECT graduationDate FROM alumni WHERE userID = ?", (session['userID'], ))
            cursor.execute("UPDATE alumni SET address = ?, graduationDate = ? WHERE userID = ?", (newAddress, user[3], session['userID'], ))
        else:
            back = '/studentHome'
            newGradDate = str(request.form['gradSem']) + " " + str(request.form['gradYear'])
            cursor.execute("UPDATE students SET address = ?, graduationDate = ? WHERE userID = ?", (newAddress, newGradDate, session['userID'], ))

        flash("Update made sucsessfully!")
        cursor.close()
        connection.commit()
        connection.close()

    return render_template('updateInfo.html', back = back, user = user, gradYear = userGradYear)


@app.route('/studentHome', methods = ['POST', 'GET'])
def studentHome():
    if request.method == 'POST' :
        return redirect('/form1')
    
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute("SELECT user_id from users WHERE username = ?", (session['user'], ))
    userID = cursor.fetchone()[0]
    print(userID)

    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    cursor.execute("SELECT course.course_id, course.title, course.credits, course.dept_code, course.course_number, sections.semester, sections.year, enrollments.grade FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id LEFT JOIN courses course ON sections.course_id = course.course_id WHERE enrollments.student_id = ?", (userID,))
    courses = cursor.fetchall()

    cursor.execute("SELECT * FROM users use LEFT JOIN students stu ON use.user_id = stu.userID WHERE use.user_id = ?", (userID,))

    studentInfo = cursor.fetchone()

    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    cursor.execute("SELECT student.first_name, student.last_name, course.course_id, course.title, course.dept_code, course.course_number, course.credits, f1.formID FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.course_id = f1Course.courseID LEFT JOIN users student ON student.user_id = f1.studentID WHERE f1.studentID = ? AND (SELECT MAX(formID) FROM form1 WHERE studentID = ?) = f1.formID", (userID, userID, ))
    form1 = cursor.fetchall()
    
    if form1 is not None:
        for i in range(len(form1)):
            print("DEBUG" + form1[i][1])
    
    #print(form1[5])

    cursor.execute("SELECT result FROM form1ApprovalQueue WHERE studentID = ? AND formID = (SELECT MAX(formID) FROM form1ApprovalQueue WHERE studentID = ?)", (int(userID), int(userID), ))
    result = cursor.fetchone()

    studentGPA = GPA(userID)

    cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = (SELECT advisorID FROM advising WHERE studentID = ?)", (userID, ))
    advisor = cursor.fetchone()
    
    if advisor is None:
        advisor = "None"
    else:
        advisor = advisor[0] + " " + advisor[1]

    #print("Querying form1ApprovalQueue for studentID =", userID) DEBUG

    #print("Result = " + str(result[0])) DEBUG
    if result is not None:
        if(result[0] == -1):
            result = "Form was rejected"
        elif(result[0] == 0):
            result = "Advisor is still reviewing"
        elif(result[0] == 1):
            result = "Form was approved"
    else :
        result = "You have not yet submitted Form 1"
    #print(result)

    cursor.close()
    connection.commit()
    connection.close()

    return render_template("studentHome.html", student = studentInfo, courses = courses, form1 = form1, suspended = isSuspended(userID), form1Status = result, GPA = studentGPA, advisor = advisor)


@app.route('/audit', methods = ['POST', 'GET']) 
def audit():
    if session['user_type'] == 'student' or session['user_type'] == 'gs' or session['user_type'] == 'admin' or session['user_type'] == 'advisor' or session['user_type'] == 'advisor/instructor' or session['user_type'] == 'advisor/instructor/reviewer':
        
        if request.method == 'POST':
            if session['user_type'] != 'student':
                student = int(request.form["auditID"])
            else:
                student = session['userID']
                               
            connection = sqlite3.connect("database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            
            cursor.execute("SELECT userID FROM students")
            studentCheck = cursor.fetchall()
           
            cursor.close()
            connection.commit()
            connection.close()
            test = False

            #stupid way to check if accessing valid studentID
            for i in range(len(studentCheck)):
                if (int(studentCheck[i][0]) == int(student)):
                    test = True
                    i = len(studentCheck) + 10

            if test == True:
                connection = sqlite3.connect("database.db")
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                
                cursor.execute("SELECT program FROM students WHERE userID = ?" , (student,))
                studentProgram = cursor.fetchone()[0]
                #print(studentProgram + "program")

                if (studentProgram == 'phd'):
                    cursor.execute("SELECT approved FROM students WHERE userID = ?" , (student,))
                    thesisApproved = cursor.fetchone()[0]
                
                cursor.execute("SELECT course.course_id, course.title, course.credits, course.dept_code, course.course_number, enrollments.grade FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id LEFT JOIN courses course ON sections.course_id = course.course_id WHERE enrollments.student_id = ?", (student,))
                studentHistory = cursor.fetchall()

                cursor.execute("SELECT sections.course_id FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id WHERE enrollments.student_id = ?", (student,))
                studentCID = cursor.fetchall()

                cursor.execute("SELECT users.first_name, users.last_name, course.course_id, course.title, course.dept_code, course.course_number, course.credits FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.course_id = f1Course.courseID LEFT JOIN users ON users.user_id = f1.studentID WHERE f1.studentID = ?", (student, ))
                form1 = cursor.fetchall()

                cursor.execute("SELECT course.course_id FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.course_id = f1Course.courseID LEFT JOIN users student ON student.user_id = f1.studentID WHERE f1.studentID = ?", (student, ))
                form1CID = cursor.fetchall()
                #print(form1CID)

                counter = 0
                cscicounter = 0
                Algorithms = 0
                SWParadigms = 0
                Architecture = 0

                #before checking any courses: if the number of courses taken is 
                #less than the number of courses in the form1, obviously would fail audit
                if (GPA(student) == "N/A"):
                    flash("failed audit. You do not have a GPA.")
                    return render_template('audit.html',studentHistory = studentHistory, form1 = form1)

                if (len(studentHistory) < len(form1)):
                    flash("audit failed; not all courses taken in form 1")
                    return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                #checking if student is under academic suspension
                if (isSuspended(student)):
                    flash("audit failed; under academic suspension")
                    return render_template('audit.html',studentHistory = studentHistory, form1 = form1)


                #checking if courses in courseHistory is contained in form1
                for i in range(len(studentHistory)):
                    if (studentCID[i][0] == 3):
                        Algorithms = 1
                    if (studentCID[i][0] == 2):
                        Architecture = 1
                    if (studentCID[i][0] == 1):
                        SWParadigms = 1                    

                #If more than one grade below a B
                #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
                #cursor.execute("SELECT grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE enroll.studentID = ?", (student, ))
                cursor.execute("SELECT grade FROM enrollments WHERE enrollments.student_id = ?", (student, ))

                grades = cursor.fetchall()

                count = 0
                for grade in grades:
                    if grade[0] == 'B-':
                        count += 1
                    elif grade[0] == 'C+':
                        count += 1
                    elif grade[0] == 'C':
                        count += 1
                    elif grade[0] == 'C-':
                        count += 1
                    elif grade[0] == 'D+':
                        count += 1
                    elif grade[0] == 'D':
                        count += 1
                    elif grade[0] == 'D-':
                        count += 1
                    elif grade[0] == 'F':
                        count += 1

                if studentProgram == 'ms' and count > 2:
                    flash("audit failed; you have too many grades below a B")
                    return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                elif studentProgram == 'phd' and count > 1:
                    flash("audit failed; you have too many grades below a B")
                    return render_template('audit.html',studentHistory = studentHistory, form1 = form1)

                #checking if enough credit hours were taken
                if (studentProgram == 'phd'):
                    if (thesisApproved == 0):
                        flash("audit failed; thesis was not approved")
                        return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                   
                    if (getCreditHours(student) < 36):
                        flash("audit failed; you have only taken " + str(getCreditHours(student)) + " credit hours")
                        return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                    
                    if (getCSHours(student) < 30):
                        flash("failed audit. You have only taken " + str(getCSHours(student)) + " credit hours in CSCI." )
                    
                elif studentProgram == 'ms':
                    if (getCreditHours(student) < 30):
                        flash("audit failed; not enough credit hours taken")
                        return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                    #print("Alg = " + str(Algorithms))
                    #print("Para = " + str(SWParadigms))
                    #print("Arch = " + str(Architecture))
                    if (Algorithms + SWParadigms + Architecture != 3):
                        flash("audit failed; You are missing one or more required courses")
                        return render_template('audit.html',studentHistory = studentHistory, form1 = form1)

                    csHours = getCSHours(student)
                    csClasses = csHours / 3
                    #nonCS = getNonCS(student)
                   # print("DEBUG " + str(csClasses))
                    #print("DEBUG: LENGTH OF STHIS" + str(len(studentHistory)))
                    #print("DEBUG " + str(nonCS))

                    if (csHours < 27):
                        flash("audit failed; You have taken too many non-CS courses")
                        return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                    elif (len(studentHistory) - csClasses > 2):
                            flash("audit failed; You have taken too many non-CS courses")
                            return render_template('audit.html',studentHistory = studentHistory, form1 = form1)
                                   
                #all cases where all courses match the ones in the form 1
                if(len(studentCID) == len(form1CID)):
                    #IF STUDENT IS A phd STUDENT

                    if(studentProgram == 'phd'):
                        if (GPA(student) > 3.5):
                            flash("passed audit! you are now in queue to graduate.")
                            connection = sqlite3.connect("database.db")
                            connection.row_factory = sqlite3.Row
                            cursor = connection.cursor()
                            cursor.execute("INSERT INTO graduateApplicationQueue VALUES (?)", (student,))
                            #cursor.execute("UPDATE students SET approved = 1 WHERE userID = (?)", (student,))
                            cursor.close()
                            connection.commit()
                            connection.close()
                        else:
                            flash("failed audit. GPA is too low.")
                    #else, student is a ms student
                    else:

                        if (GPA(student) > 3):
                            flash("passed audit! you are now in queue to graduate.")
                            connection = sqlite3.connect("database.db")
                            connection.row_factory = sqlite3.Row
                            cursor = connection.cursor()
                            #cursor.execute("SELECT * FROM enroll WHERE studentID = ?", (student))
                            cursor.execute("INSERT INTO graduateApplicationQueue VALUES (?)", (student,))
                            #cursor.execute("UPDATE students SET approved = 1 WHERE userID = (?)", (student,))
                            cursor.close()
                            connection.commit()
                            connection.close()
                        else:
                            flash("failed audit. GPA is too low.")
                        
                    #NEED SQL STATEMENT TO 
                else:
                    flash("failed audit. one or more courses do not align")
                return render_template("audit.html", studentHistory = studentHistory, form1 = form1)
            else:
                flash("invalid studentID. please try again.")
                return redirect('/audit')
    else :
        flash("You cannot perform an audit")
        return redirect('/')

    return render_template("audit.html")

'''def getNonCS(studentID):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    cursor.execute("SELECT department FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE department = 'CSCI' AND enroll.studentID = ?", (studentID, ))
    department = cursor.fetchall()
    cursor.close()
    connection.commit()
    connection.close()

    nonCS = 0; 
    for dep in department:
        #print(dep[0])
        if (dep[0] != 'CSCI'):
            nonCS +=1
    return nonCS'''

def getCSHours(studentID):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    #cursor.execute("SELECT credits, grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE department = 'CSCI' AND enroll.studentID = ?", (studentID, ))
    cursor.execute("SELECT credits, grade FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id LEFT JOIN courses ON sections.course_id = courses.course_id WHERE dept_code = 'CSCI' AND enrollments.student_id = ?", (studentID, ))    
    grades = cursor.fetchall()
    cursor.close()
    connection.commit()
    connection.close()

    credits = 0; 
    for grade in grades:
        credits += grade[0]
    #print("DEBUG: " + credits)
    return credits

def getCreditHours(studentID):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    #cursor.execute("SELECT credits, grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE enroll.studentID = ? ", (studentID, ))
    cursor.execute("SELECT credits, grade FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id LEFT JOIN courses ON sections.course_id = courses.course_id WHERE enrollments.student_id = ?", (studentID, ))        
    grades = cursor.fetchall()
    cursor.close()
    connection.commit()
    connection.close()
    credits = 0; 
    for grade in grades:
        credits += grade[0]
    #print("DEBUG: " + credits)
    return credits
    
def GPA(studentID): 
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    #cursor.execute("SELECT credits, grade FROM enrollments INNER JOIN sections ON enrollments.section_id = sections.section_id INNER JOIN courses ON sections.course_id= courses.course_id WHERE enroll,ents.studentID = ? ", (studentID, ))
    cursor.execute("SELECT credits, grade FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id LEFT JOIN courses ON sections.course_id = courses.course_id WHERE enrollments.student_id = ?", (studentID, ))            
    grades = cursor.fetchall()


    cursor.close()
    connection.commit()
    connection.close()
    credits = 0; GPA = 0

    if len(grades) == 0 :
        return 'N/A'
    
    for grade in grades:
        #print("You got a " + grade[1] + "grade in a " + str(grade[0]) + " credit class") DEBUG
        if grade[1] == 'A':
            GPA += grade[0] * 4
        elif grade[1] == 'A-':
            GPA += grade[0] * 3.7
        elif grade[1] == 'B+':
            GPA += grade[0] * 3.3
        elif grade[1] == 'B':
            GPA += grade[0] * 3
        elif grade[1] == 'B-':
            GPA += grade[0] * 2.7
        elif grade[1] == 'C+':
            GPA += grade[0] * 2.3
        elif grade[1] == 'C':
            GPA += grade[0] * 2
        elif grade[1] == 'C-':
            GPA += grade[0] * 1.7
        elif grade[1] == 'D+':
            GPA += grade[0] * 1.3
        elif grade[1] == 'D':
            GPA += grade[0] * 1
        elif grade[1] == 'D-':
            GPA += grade[0] * 0.7
        elif grade[1] == 'F':
            GPA += grade[0] * 0
        elif grade[1] == 'IP':
            credits -= grade[0]
        credits += grade[0]
    if credits == 0:
        GPA = GPA
    else:
        GPA = GPA / credits

    return (int(GPA * 100)) / 100.0

#fixed to adjust based on ms or phd program reqs 
def suspend(studentID):
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    #.execute("SELECT enrollments.grade, sections.course_id FROM enrollments LEFT JOIN sections ON enrollments.section_id = sections.section_id WHERE enrollments.student_id = ?", (studentID, ))
    cursor.execute("SELECT grade FROM enrollments WHERE student_id = ?", (studentID, ))        
    grades = cursor.fetchall()

    count = 0
    for grade in grades:
        if grade[0] == 'B-':
            count += 1
        elif grade[0] == 'C+':
            count += 1
        elif grade[0] == 'C':
            count += 1
        elif grade[0] == 'C-':
            count += 1
        elif grade[0] == 'D+':
            count += 1
        elif grade[0] == 'D':
            count += 1
        elif grade[0] == 'D-':
            count += 1
        elif grade[0] == 'F':
            count += 1

    cursor.execute("SELECT program FROM students WHERE userID = ?" , (studentID,))
    program = cursor.fetchone()[0]
    #print(program) DEBUG
    #print("The number of grades below a B is " + str(count)) DEBUG


    print("The length of grades is " + str(len(grades)) + " and isSuspended() = " + str(isSuspended(studentID)) + "and count = " + str(count))
    if len(grades) > 0 and not isSuspended(studentID) and count > 2:
        print("DEBUG AM I IN THIS STATEMENT")
        cursor.execute ("UPDATE students SET suspended = 1 WHERE userID = ?", (studentID, ))
    else:
        cursor.execute("UPDATE students SET suspended = 0 WHERE userID = ?", (studentID, ))
    
    cursor.close()
    connection.commit()
    connection.close()

def isSuspended(studentID) :
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute ("SELECT suspended FROM students WHERE userID = ?", (studentID, ))
    temp = cursor.fetchone()[0]

    cursor.close()
    connection.commit()
    connection.close()

    if temp == 0:
        return False
    else:
        return True


@app.route('/studentProf', methods = ['POST', 'GET']) 
def studentProf():
    suspend(request.form['studentID'])

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------    
   # cursor.execute("SELECT course.course_id, course.title, course.credits, course.dept_code, course.course_number, outcome.grade, outcome.semester FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (request.form['studentID'],))
    cursor.execute("SELECT course.course_id, course.title, course.credits, course.dept_code, course.course_number, outcome.grade FROM enrollments outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (request.form['studentID'],))    
    courses = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users use LEFT JOIN students stu ON use.user_id = stu.userID WHERE stu.userID = ?", (request.form['studentID'],))
    studentInfo = cursor.fetchone()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------    
    cursor.execute("SELECT student.first_name, student.last_name, course.title, course.dept_code, course.course_number, course.credits FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.course_id = f1Course.courseID LEFT JOIN users student ON student.user_id = f1.studentID WHERE f1.studentID = ?", (request.form['studentID'], ))
    form1 = cursor.fetchall()
    
    cursor.close()
    connection.commit()
    connection.close()

    if(session['user_type'] == 'admin') :
        back = "/adminHome"
    elif(session['user_type'] == 'advisor'):
        back = "/advisorHome"

    return render_template("studentProf.html", student = studentInfo, courses = courses, form1 = form1, GPA = GPA(request.form['studentID']), suspended = isSuspended(request.form['studentID']), back = back)

#has complete access to current student's data
#responsible for assigning an advisor
#graduates a student
@app.route('/gradSecHome', methods = ['POST', 'GET'])
def gradSecHome():

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #select to display all students + info
    cursor.execute("SELECT student.user_id AS student_userID, student.username AS student_username, student.first_name AS student_fname, student.last_name AS student_lname, students.address AS student_address, student.role AS student_role, students.program AS student_program, students.graduationDate AS student_graduationDate, students.approved AS student_approved, advisor.first_name AS advisor_fname, advisor.last_name AS advisor_lname FROM users student JOIN students ON student.user_id = students.userID LEFT JOIN users advisor ON advisor.user_id = (SELECT advisorID FROM advising WHERE studentID = student.user_id) WHERE student.role = ?", ('student',)) 
    values = cursor.fetchall()
    connection.commit()
    connection.close()
    approvedGrad = "Yes"
    unapprovedGrad = "No"

    #select to display all students who need to graduate
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #cursor.execute("SELECT * FROM graduateApplicationQueue JOIN users ON graduateApplicationQueue.userID = users.userID JOIN students ON graduateApplicationQueue.userID = students.userID WHERE students.approved = 1")
    cursor.execute("SELECT * FROM graduateApplicationQueue JOIN users ON graduateApplicationQueue.userID = users.user_id")
    
    gradValues = cursor.fetchall()
    connection.commit()
    connection.close()
    if request.method == 'POST':
        if (gradValues is not None):
            gradName = request.form["userID"]
            connection = sqlite3.connect("database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM students WHERE userID = ?", (gradName, ))
            finalValues = cursor.fetchone()
            cursor.execute("DELETE FROM graduateApplicationQueue WHERE userID = ?", (gradName, ))
            
            #might need to be changed later based on how alumni table gets changed
            cursor.execute("DELETE FROM students WHERE userID = ?", (gradName, ))
            cursor.execute("INSERT INTO alumni VALUES (?, ?, ?, ?)" , (finalValues['userID'] , finalValues['address'], finalValues['program'], finalValues['graduationDate'],))
            cursor.execute("UPDATE users SET role = 'alumni' WHERE user_id = ?", (gradName,))

            #could possibly be made nicer later, but not focus for now
            flash("Graduated " + gradName)
            cursor.close()
            connection.commit()
            connection.close()
            return redirect('/gradSecHome')
    return render_template("gradSecHome.html", values = values, approvedGrad = approvedGrad, unapprovedGrad = unapprovedGrad, gradValues = gradValues)

@app.route('/gradSecAssignAdv', methods = ['POST', 'GET'])
def gradSecAssignAdv():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM students JOIN users ON students.userID = users.user_id WHERE students.userID NOT IN (SELECT studentID FROM advising)")
    values = cursor.fetchall()
    cursor.execute("SELECT * FROM users WHERE role = 'advisor' OR role = 'advisor/instructor/reviewer'")
    advisorValues = cursor.fetchall()

    connection.commit()
    connection.close()

    if request.method == 'POST':
        student = request.form["student"]
        advisor = request.form["advisor"]

        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("INSERT INTO advising VALUES (?, ?)", (advisor, student))
        values = cursor.fetchall()

        connection.commit()
        connection.close()
        return redirect('gradSecAssignAdv')

    back = "/gradSecHome"

    return render_template("gradSecAssignAdv.html", values = values, advisorValues = advisorValues, back = back)

@app.route('/gradSecReassign', methods = ['POST', 'GET'])
def gradSecReassign():
    value = ""
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE role = 'advisor'")
    advisorValues = cursor.fetchall()
    connection.commit()
    connection.close()

    #if request.method == 'GET':
    #print(student)
    if request.method == 'GET':
        student = request.args.get('studentID')
        if student:
            connection = sqlite3.connect("database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM students LEFT JOIN users ON students.userID = users.user_id WHERE students.userID = ?", (student,))
            value = cursor.fetchone()
            connection.commit()
            connection.close()

            
    
    if request.method == 'POST':
        advisor = request.form["advisor"]
        student = request.form["studentID"]  
        print("student" + student)  
        print("advisor" + advisor)      
    
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        #cursor.execute("SELECT * FROM students LEFT JOIN users on students.userID = users.user_id WHERE students.userID = ?", (student,))
        #value = cursor.fetchone()
        cursor.execute("SELECT * FROM users WHERE role = 'advisor'")
        advisorValues = cursor.fetchall()

        cursor.execute("SELECT studentID FROM advising")
        advising = cursor.fetchall()
        connection.commit()
        connection.close()

        temp = False
        for i in range(len(advising)):
            print("debug")
            print(advising[i][0])
            if int(student) == advising[i][0]:
                print("debug if in student loop")
                temp = True
                i = 349234023843
        print(temp)
        if temp == False:
            connection = sqlite3.connect("database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("INSERT INTO advising VALUES (?, ?)", (int(advisor), int(student) ))
            #session.pop('testStudent', None )
            connection.commit()
            connection.close()
            return redirect('/gradSecReassign')

        else:
            print("advisor" + advisor)
            #print(session['testStudent']  + student
            connection = sqlite3.connect("database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()            
            cursor.execute("UPDATE advising SET advisorID = ? WHERE studentID = ?", (int(advisor), int(student) ))
            connection.commit()
            connection.close()
            #session.pop('testStudent', None )
            return redirect('/gradSecReassign')


        return render_template("gradSecReassign.html", value = value, advisorValues = advisorValues)
    back = "/gradSecHome"

    return render_template("gradSecReassign.html", value = value, advisorValues = advisorValues,back = back)

@app.route('/alumniList', methods=['POST', 'GET'])
def alumniList():
    alumniInfo = ""
    back = "/gradSecHome"
    if request.method == 'POST':
        semester = request.form["semester"]
        year = request.form["year"]
        degree = request.form["degree"]

        if semester != "":
            semester = semester[0:1] + "%"
            
        if year != "":
            year = "%" + year + "%"
            
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()            
        cursor.execute("SELECT * FROM alumni JOIN users ON alumni.userID = users.user_id WHERE alumni.program = ? OR graduationDate LIKE ? OR graduationDate LIKE ?", (degree, semester, year))
        alumniInfo = cursor.fetchall()
        connection.commit()
        connection.close()
        return render_template("alumniList.html", alumniInfo = alumniInfo)
    return render_template("alumniList.html", alumniInfo = alumniInfo)
# shows the advisor's homepage with their advisees and the courses each student picked for form 1
@app.route('/advisorHome', methods=['POST', 'GET'])
def advisorHome():
    if 'user' not in session:
        return redirect('/login')

    advisor_id = session.get('userID')

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (advisor_id,))
    advisor = cursor.fetchone()

    # get the list of students that are assigned to this advisor
    cursor.execute("""
        SELECT stu.*, use.first_name, use.last_name
        FROM advising adv
        JOIN users use ON adv.studentID = use.user_id
        JOIN students stu ON stu.userID = use.user_id
        WHERE adv.advisorID = ?
    """, (advisor_id,))
    student_rows = cursor.fetchall()

    #this will hold the final list of students with all their info, including form1 data
    student_dicts = []
    #loop through each student 
    for student in student_rows:
        student = dict(student)  # make student mutable

        student_id = student['userID']
        #checks if the student submitted form1
        cursor.execute("SELECT formID FROM form1 WHERE studentID = ?", (student_id,))
        form_row = cursor.fetchone()

    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
        if form_row:
            form_id = form_row['formID']
            cursor.execute("""
                SELECT c.dept_code, c.course_number 
                FROM form1_courses fc 
                JOIN courses c ON fc.courseID = c.course_id 
                WHERE fc.formID = ?
            """, (form_id,))
            student['form1_courses'] = cursor.fetchall()
        else:
            student['form1_courses'] = []

        student_dicts.append(student)



    cursor.execute("SELECT * FROM form1ApprovalQueue JOIN users ON user_id = studentID WHERE form1ApprovalQueue.advisorID = ? AND form1ApprovalQueue.result = 0", (session['userID'], ))
    formQueueUsers = cursor.fetchall()
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    cursor.execute("SELECT course_id, title, dept_code, course_number, form1ApprovalQueue.formID, form1ApprovalQueue.studentID, form1ApprovalQueue.advisorID FROM form1_courses JOIN courses ON courses.course_id = form1_courses.courseID JOIN form1ApprovalQueue on form1ApprovalQueue.formID = form1_courses.formID WHERE form1ApprovalQueue.advisorID = ? AND form1ApprovalQueue.result = 0 ORDER BY form1ApprovalQueue.formID", (session['userID'], ))
    formQueueClasses = cursor.fetchall()
    print("Debug ???? true??")
    #for i in range(len(formQueueClasses)):
        #print("DEBUG" + formQueueClasses[i][0])

    cursor.close()
    connection.commit()
    connection.close()
    
    return render_template("advisorHome.html", advisor=advisor, students=student_dicts, studentsQueue = formQueueUsers, coursesQueue = formQueueClasses)

@app.route('/instructorHome')
def instructor_home():
    if 'user_id' not in session or session.get('user_type') != 'instructor':
        flash("Access denied. Please log in as an instructor.", "warning")
        return redirect(url_for('login'))

    instructor_id = session['user_id']
    conn = None
    sections = [] 

    try:
        conn = get_connection()
        sections = conn.execute("""
            SELECT s.section_id, c.dept_code, c.course_number, c.title, s.semester, s.year,
                   (SELECT COUNT(enrollment_id) FROM enrollments WHERE section_id = s.section_id) as enrollment_count
            FROM sections s
            JOIN courses c ON s.course_id = c.course_id
            WHERE s.instructor_id = ?
            ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
        """, (instructor_id,)).fetchall()

    except sqlite3.Error as e:
        print(f"Database error fetching instructor sections: {e}")
        flash("Error loading assigned sections.", "danger")
    except Exception as e:
        print(f"Unexpected error fetching instructor sections: {e}")
        flash("An unexpected error occurred.", "danger")
    finally:
        if conn:
            conn.close()

    return render_template('instructorHome.html', sections=sections)

@app.route('/advisor_instructor_home')
def advisor_instructor_home():
    # 1. Role Check
    allowed_roles = ['advisor/instructor'] # Could also include admin if desired
    if 'user_id' not in session or session.get('role') not in allowed_roles:
        flash("Access denied.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id'] # Use user_id consistently
    combined_data = {'role': session.get('role')} # Store data to pass to template

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 2. Fetch Advisor Data (Copied & Adapted from advisorHome)
        # -----------------------------------------------------
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        combined_data['advisor'] = cursor.fetchone() # Changed from 'advisor' to combined_data['advisor']

        cursor.execute("""
            SELECT stu.*, use.first_name, use.last_name
            FROM advising adv
            JOIN users use ON adv.studentID = use.user_id
            JOIN students stu ON stu.userID = use.user_id
            WHERE adv.advisorID = ?
        """, (user_id,))
        student_rows = cursor.fetchall()

        advisees_data = [] # Renamed from student_dicts
        for student_row in student_rows:
            student = dict(student_row)
            student_id = student['userID']
            # Fetch latest form1
            cursor.execute("SELECT formID FROM form1 WHERE studentID = ? ORDER BY formID DESC LIMIT 1", (student_id,))
            form_row = cursor.fetchone()

            if form_row:
                form_id = form_row['formID']
                cursor.execute("""
                    SELECT c.dept_code, c.course_number, c.title
                    FROM form1_courses fc
                    JOIN courses c ON fc.courseID = c.course_id
                    WHERE fc.formID = ?
                """, (form_id,))
                student['form1_courses'] = cursor.fetchall()
                # Check approval status for this specific form
                cursor.execute("SELECT result FROM form1ApprovalQueue WHERE formID = ?", (form_id,))
                approval_status = cursor.fetchone()
                student['form1_status_code'] = approval_status['result'] if approval_status else None # Use code
            else:
                student['form1_courses'] = []
                student['form1_status_code'] = None # No form submitted

            advisees_data.append(student)
        combined_data['advisees'] = advisees_data # Store advisor's students

        # Fetch pending forms for this advisor
        cursor.execute("""
            SELECT q.*, u.first_name, u.last_name
            FROM form1ApprovalQueue q JOIN users u ON u.user_id = q.studentID
            WHERE q.advisorID = ? AND q.result = 0
            """, (user_id,))
        combined_data['studentsQueue'] = cursor.fetchall() # Store pending form users

        # Fetch courses for pending forms
        pending_form_ids = [fq['formID'] for fq in combined_data['studentsQueue']]
        pending_form_courses = [] # Renamed from formQueueClasses
        if pending_form_ids:
            placeholders = ','.join('?' for _ in pending_form_ids)
            cursor.execute(f"""
                SELECT c.course_id, c.title, c.dept_code, c.course_number, q.formID, q.studentID, q.advisorID
                FROM form1_courses fc
                JOIN courses c ON c.course_id = fc.courseID
                JOIN form1ApprovalQueue q on q.formID = fc.formID
                WHERE q.formID IN ({placeholders}) AND q.result = 0
                ORDER BY q.formID, c.dept_code, c.course_number
            """, pending_form_ids)
            pending_form_courses = cursor.fetchall()
        combined_data['coursesQueue'] = pending_form_courses # Store pending form courses
        # -----------------------------------------------------

        # 3. Fetch Instructor Data (Copied & Adapted from instructor_home)
        # -----------------------------------------------------
        cursor.execute("""
            SELECT s.section_id, c.dept_code, c.course_number, c.title, s.semester, s.year,
                   (SELECT COUNT(enrollment_id) FROM enrollments WHERE section_id = s.section_id) as enrollment_count
            FROM sections s
            JOIN courses c ON s.course_id = c.course_id
            WHERE s.instructor_id = ?
            ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
        """, (user_id,))
        combined_data['instructor_sections'] = cursor.fetchall() # Store instructor sections
        # -----------------------------------------------------

    except sqlite3.Error as e:
        flash(f"Database error loading dashboard: {e}", "danger")
        print(f"Advisor/Instructor Home DB Error: {e}")
        # Set default empty values if error occurs before fetching all data
        combined_data.setdefault('advisor', None)
        combined_data.setdefault('advisees', [])
        combined_data.setdefault('studentsQueue', [])
        combined_data.setdefault('coursesQueue', [])
        combined_data.setdefault('instructor_sections', [])
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"Advisor/Instructor Home General Error: {e}")
        combined_data.setdefault('advisor', None)
        combined_data.setdefault('advisees', [])
        combined_data.setdefault('studentsQueue', [])
        combined_data.setdefault('coursesQueue', [])
        combined_data.setdefault('instructor_sections', [])
    finally:
        if conn:
            conn.close()

    # 4. Render Combined Template
    return render_template('advisor_instructor_home.html', **combined_data)


@app.route('/advisor_instructor_reviewer_home')
def advisor_instructor_reviewer_home():
    # 1. Role Check
    allowed_roles = ['advisor/instructor/reviewer'] # Could also include admin
    if 'user_id' not in session or session.get('role') not in allowed_roles:
        flash("Access denied.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    combined_data = {'role': session.get('role')}

    # Get search term for reviewer part (needed before DB connection)
    search_term = request.args.get('search', '').strip()
    search_term = search_term if search_term else None # Handle empty search
    combined_data['search_term'] = search_term
    combined_data['current_year'] = datetime.now().year # For reviewer date checks

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 2. Fetch Advisor Data (Same as advisor_instructor_home)
        # -----------------------------------------------------
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        combined_data['advisor'] = cursor.fetchone()

        cursor.execute("""
            SELECT stu.*, use.first_name, use.last_name
            FROM advising adv
            JOIN users use ON adv.studentID = use.user_id
            JOIN students stu ON stu.userID = use.user_id
            WHERE adv.advisorID = ?
        """, (user_id,))
        student_rows = cursor.fetchall()
        advisees_data = []
        for student_row in student_rows:
             student = dict(student_row)
             student_id = student['userID']
             cursor.execute("SELECT formID FROM form1 WHERE studentID = ? ORDER BY formID DESC LIMIT 1", (student_id,))
             form_row = cursor.fetchone()
             if form_row:
                 form_id = form_row['formID']
                 cursor.execute("SELECT c.dept_code, c.course_number, c.title FROM form1_courses fc JOIN courses c ON fc.courseID = c.course_id WHERE fc.formID = ?", (form_id,))
                 student['form1_courses'] = cursor.fetchall()
                 cursor.execute("SELECT result FROM form1ApprovalQueue WHERE formID = ?", (form_id,))
                 approval_status = cursor.fetchone()
                 student['form1_status_code'] = approval_status['result'] if approval_status else None
             else:
                 student['form1_courses'] = []
                 student['form1_status_code'] = None
             advisees_data.append(student)
        combined_data['advisees'] = advisees_data

        cursor.execute("SELECT q.*, u.first_name, u.last_name FROM form1ApprovalQueue q JOIN users u ON u.user_id = q.studentID WHERE q.advisorID = ? AND q.result = 0", (user_id,))
        combined_data['studentsQueue'] = cursor.fetchall()
        pending_form_ids = [fq['formID'] for fq in combined_data['studentsQueue']]
        pending_form_courses = []
        if pending_form_ids:
             placeholders = ','.join('?' for _ in pending_form_ids)
             cursor.execute(f"SELECT c.course_id, c.title, c.dept_code, c.course_number, q.formID, q.studentID, q.advisorID FROM form1_courses fc JOIN courses c ON c.course_id = fc.courseID JOIN form1ApprovalQueue q on q.formID = fc.formID WHERE q.formID IN ({placeholders}) AND q.result = 0 ORDER BY q.formID, c.dept_code, c.course_number", pending_form_ids)
             pending_form_courses = cursor.fetchall()
        combined_data['coursesQueue'] = pending_form_courses
        # -----------------------------------------------------

        # 3. Fetch Instructor Data (Same as advisor_instructor_home)
        # -----------------------------------------------------
        cursor.execute("""
            SELECT s.section_id, c.dept_code, c.course_number, c.title, s.semester, s.year,
                   (SELECT COUNT(enrollment_id) FROM enrollments WHERE section_id = s.section_id) as enrollment_count
            FROM sections s
            JOIN courses c ON s.course_id = c.course_id
            WHERE s.instructor_id = ?
            ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
        """, (user_id,))
        combined_data['instructor_sections'] = cursor.fetchall()
        # -----------------------------------------------------

        # 4. Fetch Reviewer Data (Copied & Adapted from reviewer_bp.dashboard)
        # -----------------------------------------------------
        # Use the existing reviewerQuery class instance if available and appropriate
        # Or replicate the query logic here
        # Assuming replication for simplicity based on the original reviewer code structure
        base_query = """
            SELECT
                a.application_id, a.user_id as student_id, a.first_name, a.last_name, a.email,
                a.degree_program, a.admission_semester, a.admission_year, a.status,
                a.transcript_received, a.recommendation_received,
                (SELECT COUNT(review_id) FROM REVIEW WHERE application_id = a.application_id) as review_count
            FROM APPLICATIONS a
            WHERE a.status NOT IN ('Admitted', 'Rejected', 'Offer Accepted', 'Offer Declined') -- Show only actionable items
            -- Additional condition: Only show applications *not* yet reviewed by *this* faculty member? Optional.
            -- AND a.application_id NOT IN (SELECT application_id FROM REVIEW WHERE faculty_id = ?)
            """
        params = []
        # if user_id: # If adding the optional condition above
        #     params.append(user_id)

        if search_term:
            search_like = f"%{search_term}%"
            base_query += """
                AND (
                    a.first_name LIKE ? OR
                    a.last_name LIKE ? OR
                    CAST(a.user_id AS TEXT) LIKE ? OR
                    a.degree_program LIKE ?
                )
            """
            params.extend([search_like] * 4)

        base_query += " ORDER BY a.last_name, a.first_name"

        cursor.execute(base_query, params)
        combined_data['review_applications'] = cursor.fetchall() # Renamed from 'applications'
        # -----------------------------------------------------

    except sqlite3.Error as e:
        flash(f"Database error loading dashboard: {e}", "danger")
        print(f"Advisor/Instructor/Reviewer Home DB Error: {e}")
        # Set defaults
        combined_data.setdefault('advisor', None)
        combined_data.setdefault('advisees', [])
        combined_data.setdefault('studentsQueue', [])
        combined_data.setdefault('coursesQueue', [])
        combined_data.setdefault('instructor_sections', [])
        combined_data.setdefault('review_applications', [])
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"Advisor/Instructor/Reviewer Home General Error: {e}")
        combined_data.setdefault('advisor', None)
        combined_data.setdefault('advisees', [])
        combined_data.setdefault('studentsQueue', [])
        combined_data.setdefault('coursesQueue', [])
        combined_data.setdefault('instructor_sections', [])
        combined_data.setdefault('review_applications', [])
    finally:
        if conn:
            conn.close()

    # 5. Render Combined Template
    return render_template('advisor_instructor_reviewer_home.html', **combined_data)

@app.route('/approveForm1', methods = ['POST'])
def approveForm1():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    formID = int(request.form['formID'])
    
    #Copy the values from the queue
    #print("Approving form '" + str(formID) + "'")
    #print (type(request.form['formID']))
    cursor.execute("SELECT * FROM form1ApprovalQueue WHERE formID = ?", (formID, ))
    copy = cursor.fetchone()
    #print(copy)

    #Update the queue to reflect our result
    cursor.execute("UPDATE form1ApprovalQueue SET result = 1 WHERE formID = ?", (formID, ))

    #Insert the values into form1
    cursor.execute("INSERT INTO form1 VALUES (?, ?)", (copy[0], copy[2], ))

    flash("Approved form")

    cursor.close()
    connection.commit()
    connection.close()

    return redirect('/advisorHome')

@app.route('/rejectForm1', methods = ['POST'])
def rejectForm1():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    formID = int(request.form['formID'])
    
    #Copy the values from the queue
    #print("Approving form '" + str(formID) + "'")
    #print (type(request.form['formID']))
    cursor.execute("SELECT * FROM form1ApprovalQueue WHERE formID = ?", (formID, ))
    copy = cursor.fetchone()
    #print(copy)

    #remove values from form1ApprovalQueue
    cursor.execute("UPDATE form1ApprovalQueue SET result = -1 WHERE formID = ?", (formID, ))
    
    flash("Rejected form")

    cursor.close()
    connection.commit()
    connection.close()

    return redirect('/advisorHome')

#this route approves thesis 
@app.route('/approveThesis', methods=['POST'])
def approveThesis():

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if 'user' not in session or session['user_type'] != 'advisor':
        return redirect('/login')

    #student_id = request.form.get('studentID')



    if request.method == 'POST' :
        #print("Updating thesis for student ID = " + request.form['studentID'])
        cursor.execute("UPDATE students SET approved = 1 WHERE userID = ?", (request.form['studentID'],))


    flash("Thesis approved successfully.")

    cursor.close()
    connection.commit()
    connection.close()

    return redirect('/advisorHome')



# this route lets students pick their form 1 courses and submit them to the system
@app.route('/form1', methods=['POST', 'GET'])
def form1():
    if 'user' not in session:
        return redirect('/login')

    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # get a list of all available courses to display in the dropdowns
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    cursor.execute("SELECT course_id, dept_code, course_number, title FROM courses")
    course_options = cursor.fetchall()

    cursor.execute("SELECT program FROM students WHERE userID = ?", (session['userID'], ))
    program = cursor.fetchone()[0]

    cursor.execute("SELECT advisorID FROM advising WHERE studentID = ?", (session['userID'], ))
    advisorId = cursor.fetchone()
    #print(advisorId) DEBUG
   
    if advisorId is None: 
        flash("You need to wait until you have an advisor in order to submit your Form1")
        return redirect("/studentHome")

    if request.method == 'POST':
        chosen = []; i = 0
        #print(request.form['course_id 0'])
        #print(request.form['course_id ' + str(i)])
        while i < 12 and request.form['course_id ' + str(i)] is not None:
            #request.form['course_id ' + str(i)]
            # chosen.append(request.form['course_id ' + str(i)])
            chosen.append(request.form['course_id ' + str(i)])
            print("DEBUG ADDING COURSES OT FORM1" + chosen[i])            
            i += 1
        

        if 1 <= len(chosen) <= 12:
            #cursor.execute("INSERT INTO form1 (studentID) VALUES (?)", (student_id, ))
            #connection.commit()
            #form_id = cursor.lastrowid


            cursor.execute("SELECT MAX(formID) FROM form1")
            maxForm1 = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(formID) FROM form1ApprovalQueue")
            maxQueue = cursor.fetchone()[0]

            # Handle None values (i.e., if the tables are empty)
            maxForm1 = maxForm1 if maxForm1 is not None else 0
            maxQueue = maxQueue if maxQueue is not None else 0

            # The next available formID would be the higher of the two + 1
            formID = max(maxForm1, maxQueue) + 1


            #print("FormID = " + str(formID))
            i = 0
            for course in chosen:
                #print("course (i = " + str(i) + " ) = "  + course)
                i += 1
                if course != "":
                    #print("INSERTING course (i = " + str(i) + " ) = "  + course)
                    cursor.execute("INSERT INTO form1_courses VALUES (?, ?)", (formID, course, ))
            connection.commit()

            cursor.execute("INSERT INTO form1ApprovalQueue VALUES (?, ?, ?, ?)", (formID, advisorId[0], session['userID'], 0, ))
            connection.commit()
            flash("Form 1 submitted successfully.")
            return redirect('/studentHome')
        else:
            flash("You must select between 1 and 12 courses.")

    cursor.close()
    connection.commit()
    connection.close()

    back = '/studentHome'

    return render_template("form1.html", courses=course_options, back = back, program = program)     
 
@app.route('/adminHome', methods = ['POST', 'GET'])
def adminHome():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute('''SELECT course.course_id, course.title, course.credits, course.dept_code, course.course_number,
    GROUP_CONCAT(CASE WHEN p.type = 'main' THEN pr.title END) AS pre1,
    GROUP_CONCAT(CASE WHEN p.type = 'secondary' THEN prs.title END) AS pre2
    FROM courses course
    LEFT JOIN prerequisites p ON p.course_id = course.course_id
    LEFT JOIN courses pr ON pr.course_id = p.prerequisite_course_id
    LEFT JOIN courses prs ON prs.course_id = p.prerequisite_course_id
    GROUP BY course.course_id
    ORDER BY course.course_id''')

    courses = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role = 'gs'")
    gradSecs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'advisor'")
    advisors = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role = 'instructor'")
    instructors = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'student'")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role = 'alumni'")
    alumni = cursor.fetchall()
    
    #print(courses)

    cursor.close()
    connection.commit()
    connection.close()

    return render_template("adminHome.html", courses = courses, admins = admins, gradSecs = gradSecs, advisors = advisors, instructors = instructors, students = students, Alumni = alumni)

@app.route('/adminCreateAccount', methods = ['POST', 'GET'])
def adminCreateAccount():
    if request.method == 'POST':
        fname = request.form["fname"]
        lname = request.form["lname"]
        username = request.form["username"]
        pw = request.form["pass"]


        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        values = cursor.fetchall()

        cursor.execute("SELECT MAX(user_id) FROM users")
        max_id = cursor.fetchone()[0]
        random_id = max_id + 1 if max_id is not None else 1000

        cursor.execute("SELECT username FROM users")
        values = cursor.fetchall()
        
        connection.commit()
        connection.close()

        test = False
        #print(values)
        for i in range(len(values)):
            if (username == values[i][0]):
                #okay I still don't really know how flash works
                flash("Account already exists")
                test = True
                i = random_id
                return redirect('/adminCreateAccount')
        if (test == False):
            connection = sqlite3.connect("database.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (user_id, username, passcode, first_name, last_name, role) VALUES (?,?,?, ?, ?, ?)", (random_id, username, pw, fname, lname, request.form['type'],))
            #values = cursor.fetchall()
            connection.commit()
            connection.close()
            #cursor.close()

            #I BELIEVE THIS NEEDS FIXING?
            flash("Account created! Please return to the login page")

    back = "/adminHome"

    return render_template('adminCreateAccount.html', type = request.form['type'], back = back)
    
@app.route('/adminCreateAccHelper', methods = ['POST', 'GET'])
def adminCreateHelper():
    if request.method == 'POST' :
        #flash("User type = " + request.form['type']) DEBUG
        return render_template('adminCreateAccount.html', type = request.form['type'])
    return redirect('/adminHome')

@app.route('/advisorProf', methods = ['POST', 'GET'])
def advisorProf():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #This line needs to be able to select all studentIDs from the advising relationship table 
    #---------------------------------ANOTHER ONE THAT WILL GIVE ERROR------------------------
    cursor.execute("SELECT student.first_name, student.last_name, student.user_id FROM advising LEFT JOIN users student ON student.user_id = advising.studentID WHERE advising.advisorID = ?", (request.form['advisorID'], ))
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (request.form['advisorID'], ))
    advisor = cursor.fetchone()

    cursor.close()
    connection.commit()
    connection.close()

    back = request.referrer

    return render_template("advisorProf.html", advisor = advisor, students = students, back = back)

@app.route('/search', methods = ['POST', 'GET'])
def search():
    results = []
    search_grad = ""
    back = '/gradSecHome'

    if request.method == 'GET':
        search_grad = request.args.get('search_grad')
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()        
        if search_grad == 'degreeMS':
            cursor.execute( '''
                SELECT user_id, first_name, last_name, users.program, graduationDate
                FROM graduateApplicationQueue g
                JOIN users ON user_id = g.userID
                JOIN students ON g.userID = students.userID
                WHERE users.program = 'ms' OR users.program = 'MASTERS'                                 
            ''')
            results = cursor.fetchall()

        elif search_grad == 'degreePHD':
            cursor.execute( '''
                SELECT user_id, first_name, last_name, users.program,graduationDate 
                FROM graduateApplicationQueue g
                JOIN users ON user_id = g.userID
                JOIN students ON g.userID = students.userID
                WHERE users.program = 'phd' OR users.program = 'PHD'                                 
            ''')
            results = cursor.fetchall()  

        elif search_grad == 'semester':
            if request.args.get('value') == 'S' or request.args.get('value') == 's' or request.args.get('value') == 'spring' or request.args.get('value') == 'Spring':
                cursor.execute( '''
                    SELECT user_id, first_name, last_name, users.program, graduationDate 
                    FROM graduateApplicationQueue g
                    JOIN users ON user_id = g.userID
                    JOIN students ON g.userID = students.userID
                    WHERE graduationDate LIKE 'S%'                              
                ''')
                results = cursor.fetchall()
    
            elif request.args.get('value') == 'F' or request.args.get('value') == 'f' or request.args.get('value') == 'fall' or request.args.get('value') == 'Fall':
                cursor.execute( '''
                    SELECT user_id, first_name, last_name, users.program, graduationDate 
                    FROM graduateApplicationQueue g
                    JOIN users ON user_id = g.userID
                    JOIN students ON g.userID = students.userID
                    WHERE graduationDate LIKE 'F%'                               
                ''')
                results = cursor.fetchall()    
            
        elif search_grad == 'year':
            year = request.args.get('value')
            if year is not None:
                cursor.execute( '''
                    SELECT user_id, first_name, last_name, users.program, graduationDate 
                    FROM graduateApplicationQueue g
                    JOIN users ON user_id = g.userID
                    JOIN students ON g.userID = students.userID
                    WHERE SUBSTRING(graduationDate,3,7) LIKE '%'+(?)''', (year,))
                results = cursor.fetchall()    

        connection.commit()
        connection.close()
    if request.method == 'POST':
        search_type = request.form['search_type']  # 'degree' or 'year'
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if search_type == 'degree':
            cursor.execute( '''
                SELECT program, COUNT(*) as total
                FROM users
                GROUP BY program;
            ''')
            results = cursor.fetchall()
        elif search_type == 'year':
            cursor.execute('''
                SELECT SUBSTRING(created_at, 1, 4) AS degree_year, COUNT(SUBSTRING(created_at, 1, 4)) AS Count
                FROM users
                GROUP BY degree_year''')
            results = cursor.fetchall()
        connection.commit()
        connection.close()
    return render_template('search.html', results=results, type = search_grad, back = back)

#Use this to avoid SQLite issues with concurrency
def getConnection() :
    return sqlite3.connect("database.db")


from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from queries.admin import AdminQuery

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates/admin')

def admin_required(f):
    """Custom decorator to ensure admin role"""
    def wrapper(*args, **kwargs):
        if session.get('role') not in ['admin', 'admin']:  # Allow admin access too
            flash('Unauthorized access - admin role required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Initialize admin query handler
admin_db = AdminQuery("database.db")

@admin_bp.route('/dashboard')
@admin_required
#@app.route('/dashboard')
def dashboard():
    """admin dashboard showing applications needing decisions"""
    try:
        search_term = request.args.get('search', '').strip()
        print(f"[DEBUG] dashboard, search_term: {search_term}")
        
        search_term = search_term if search_term else None
        print("[DEBUG] Before querying applications:")
        
    
        applications = admin_db.get_applications_for_decision(search_term=search_term)
    
        print("[DEBUG] After querying applications:")
        
        # Proper debug for SQLite Row objects
        print(f"[DEBUG] Number of applications retrieved: {len(applications)}")
        print("[DEBUG] Application IDs and structure:")
        for i, app in enumerate(applications, 1):
            print(f"  Application {i}:")
            print(f"    Type: {type(app)}")
            print(f"    Available fields: {list(app.keys())}")  # SQLite Row objects have .keys()
            print(f"    application_id: {app['application_id']}")  # Correct access method
            print(f"    Full object: {dict(app)}")  # Convert to dict for better readability

        return render_template('templates/admin/dashboard.html',
                           applications=applications,
                           search_term=search_term,
                           current_year=datetime.now().year)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        print(f"[ERROR] dashboard - Exception: {str(e)}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/application/<int:application_id>')
@admin_required
def application_detail(application_id):
    """Detailed application view with review form"""
    try:
        # Get all application data
        print(f"[DEBUG] application_detail - application_id: {application_id}")
        app_data = admin_db.get_application_full(application_id)
        if not app_data:
            flash('Application not found', 'danger')
            return redirect(url_for('admin.dashboard'))

        # Get all reviews
        reviews = admin_db.get_reviews(application_id)

        # Calculate average rating if multiple reviews exist
        avg_rating = None
        if reviews:
            ratings = [int(r['rating']) for r in reviews if r['rating'] is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None

        print(f"[DEBUG] application_detail - reviews: {reviews}, avg_rating: {avg_rating}")

        return render_template('admin/application_detail.html',
                               app=app_data,
                               reviews=reviews,
                               avg_rating=avg_rating,
                               reject_reasons=['A', 'B', 'C', 'D', 'E'])  # From document

    except Exception as e:
        flash(f'Error loading application: {str(e)}', 'danger')
        print(f"[ERROR] application_detail - Exception: {str(e)}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/submit-review/<int:application_id>', methods=['POST'])
@admin_required
def submit_review(application_id):
    """Handle review submission (admin can also review)"""
    try:
        review_data = {
            'rating': int(request.form.get('rating')),
            'deficiency_courses': request.form.get('deficiency_courses', ''),
            'reject_reason': request.form.get('reject_reason'),
            'comments': request.form.get('comments', '')[:40],  # Limit to 40 chars
            'recommended_advisor': request.form.get('recommended_advisor')
        }

        print(f"[DEBUG] submit_review - review_data: {review_data}")

        # Validate rating (1-4 as per document)
        if review_data['rating'] not in [1, 2, 3, 4]:
            flash('Invalid rating value', 'danger')
            return redirect(url_for('admin.application_detail', application_id=application_id))

        success = admin_db.submit_review(
            application_id=application_id,
            faculty_id=session['user_id'],
            **review_data
        )

        if success:
            flash('Review submitted successfully', 'success')
        else:
            flash('Failed to submit review', 'danger')

        return redirect(url_for('admin.application_detail', application_id=application_id))

    except ValueError:
        flash('Invalid rating format', 'danger')
        return redirect(url_for('admin.application_detail', application_id=application_id))
    except Exception as e:
        flash(f'Review submission error: {str(e)}', 'danger')
        print(f"[ERROR] submit_review - Exception: {str(e)}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/decision/<int:application_id>', methods=['POST'])
@admin_required
def submit_decision(application_id):
    """Handle final decision submission"""
    try:
        decision = request.form.get('decision')
        print(f"[DEBUG] submit_decision - decision: {decision}")

        # Validate decision
        if decision not in ['Admit with Aid', 'Admit', 'Reject']:
            flash('Invalid decision selection', 'danger')
            return redirect(url_for('admin.application_detail', application_id=application_id))

        # <-- call with only three args -->
        success = admin_db.submit_final_decision(
            application_id=application_id,
            decision=decision,
            decided_by=session['user_id']
        )

        if success:
            flash('Final decision recorded successfully', 'success')
            return redirect(url_for('admin.dashboard', application_id=application_id))

        flash('Failed to record decision', 'danger')
        return redirect(url_for('admin.application_detail', application_id=application_id))

    except Exception as e:
        flash(f'Decision error: {str(e)}', 'danger')
        print(f"[ERROR] submit_decision - Exception: {str(e)}")
        return redirect(url_for('admin.dashboard'))




@admin_bp.route('/update-status/<int:application_id>', methods=['POST'])
@admin_required
def update_status(application_id):
    """Manual status update (for transcripts, etc.)"""
    try:
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')

        print(f"[DEBUG] update_status - new_status: {new_status}, notes: {notes}")

        if not new_status:
            flash('Status update required', 'danger')
            return redirect(url_for('admin.application_detail', application_id=application_id))

        success = admin_db.update_application_status(
            application_id=application_id,
            new_status=new_status,
            updated_by=session['user_id'],
            notes=notes
        )

        if success:
            flash('Status updated successfully', 'success')
        else:
            flash('Failed to update status', 'danger')

        return redirect(url_for('admin.application_detail', application_id=application_id))

    except Exception as e:
        flash(f'Status update error: {str(e)}', 'danger')
        print(f"[ERROR] update_status - Exception: {str(e)}")
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/search')
@admin_required
def search_applicants():
    """Search functionality"""
    try:
        search_term = request.args.get('q', '')
        search_by = request.args.get('by', 'name')
        status = request.args.get('status', '')

        print(f"[DEBUG] search_applicants - search_term: {search_term}, search_by: {search_by}, status: {status}")

        results = admin_db.search_applications(
            search_term=search_term,
            search_type=search_by,
            status=status
        )

        return render_template('admin/dashboard.html',
                               applications=results,
                               search_term=search_term,
                               current_year=datetime.now().year)

    except Exception as e:
        flash(f'Search error: {str(e)}', 'danger')
        print(f"[ERROR] search_applicants - Exception: {str(e)}")
        return redirect(url_for('admin.dashboard'))
    

@admin_bp.route('/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        try:
            user_data = {
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'ssn': request.form.get('ssn'),
                'address': request.form.get('address'),
                'phone': request.form.get('phone'),
                'role': request.form.get('role', 'applicant'),  # Default role is applicant
            }

            result = admin_db.create_user(user_data)

            if result:
                flash(f"User created successfully! User ID: {result['user_id']}, Student ID: {result['student_id']}", 'success')
                return redirect(url_for('admin.add_user'))
            else:
                flash('Failed to create user', 'danger')

        except Exception as e:
            flash(f"Error: {str(e)}", 'danger')

    return render_template('admin/add_user.html')

import logging, uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from queries.applicant import ApplicationQuery


# ─── SETUP LOGGER ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── DATABASE AND BLUEPRINT SETUP ──────────────────────────────────────────────
db = ApplicationQuery('database.db')
applicant_bp = Blueprint('applicant', __name__, url_prefix='/applicant', template_folder='../templates')


# ─── DASHBOARD ─────────────────────────────────────────────────────────────────
# @applicant_bp.route('/dashboard')
# def dashboard():
#     logger.info("Accessing applicant dashboard for user_id=%s", session.get('user_id'))
#     return render_template('applicant/dashboard.html')

@app.route('/applicant_dashboard')
def applicant_dashboard():
    if 'user_id' not in session or session.get('role') != 'applicant':
        flash("Access denied. Please log in as an applicant.", "warning")
        return redirect(url_for('login'))
    user_id = session['user_id']
    admission_decision = get_admission_decision(user_id)
    application_status_val = get_application_status(user_id)
    show_offer_buttons = False
    if admission_decision and 'Admit' in admission_decision and application_status_val not in ['Offer Accepted', 'Offer Declined']:
        show_offer_buttons = True
    return render_template('applicant/dashboard.html',
                           admission_decision=admission_decision,
                           application_status=application_status_val,
                           show_offer_buttons=show_offer_buttons)

@app.route('/respond_offer', methods=['POST'])
def respond_offer_action():
    if 'user_id' not in session or session.get('role') != 'applicant':
        flash("Authentication required.", "warning")
        return redirect(url_for("login"))
    user_id = session['user_id']
    response = request.form.get('response')
    if response == 'accept':
        success, message = accept_admission_offer(user_id)
        if success:
            flash(message, 'success')
            session['role'] = 'student'
            session['user_type'] = 'student'
            return redirect(url_for('studentHome'))
        else:
            flash(message, 'danger')
            return redirect(url_for('applicant_dashboard'))
    elif response == 'reject':
        success, message = reject_admission_offer(user_id)
        flash(message, 'info' if success else 'danger')
        return redirect(url_for('applicant_dashboard'))
    else:
        flash("Invalid response.", 'warning')
        return redirect(url_for('applicant_dashboard'))
    

# ─── APPLICATION FORM ──────────────────────────────────────────────────────────
@applicant_bp.route('/application', methods=['GET', 'POST'])
def application():
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session['user_id']
    current_year = datetime.now().year

    application = dict(db.get_application_by_user_id(user_id))

    if request.method == 'GET':
        return render_template(
            'templates/applicant/application.html',
            current_year=current_year,
            first_name=application.get('first_name', ''),
            last_name=application.get('last_name', ''),
            email=application.get('email', ''),
            application=application
        )

    # ────── FORM DATA ──────
    data = {
        'user_id': user_id,
        'application_id': user_id,
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'degree_program': request.form['degree_program'],
        'gre_verbal': request.form.get('gre_verbal'),
        'gre_quant': request.form.get('gre_quant'),
        'gre_year': request.form.get('gre_year'),
        'toefl_score': request.form.get('toefl_score'),
        'bs_gpa': request.form.get('bs_gpa'),
        'bs_major': request.form.get('bs_major'),
        'bs_year': request.form.get('bs_year'),
        'bs_university': request.form.get('bs_university'),
        'ms_gpa': request.form.get('ms_gpa'),
        'ms_major': request.form.get('ms_major'),
        'ms_year': request.form.get('ms_year'),
        'ms_university': request.form.get('ms_university'),
        'interests': request.form.get('interests'),
        'experience': request.form.get('experience'),
        'admission_semester': request.form.get('admission_semester'),
        'admission_year': request.form.get('admission_year'),
        'email': request.form.get('email')
    }

    logger.info("Submitting application for user_id=%s with data=%s", user_id, data)

    if application:
        success = db.update_application(data)
        action = "updated"
    else:
            success = db.insert_application(data)
            action = "inserted"
    
    # Immediate verification
    print(f"[DEBUG] Immediately after {action} application:")
    
    
    if not success:
        flash("Failed to save application.", "danger")
        return redirect(url_for('applicant.application'))
    
    return redirect(url_for('applicant_dashboard'))

# ─── STATUS CHECK ──────────────────────────────────────────────────────────────
@applicant_bp.route('/application/status')
def application_status():
    if 'user_id' not in session:
        logger.warning("Unauthenticated access attempt to application status.")
        flash("Please log in to view status.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session['user_id']
    status = db.get_application_status(user_id)
    print(status, user_id)

    logger.info("Fetched application status for user_id=%s: %s", user_id, status)

    if status is None:
        flash("No application found.", "info")
        return redirect(url_for("applicant.application"))

    return render_template('templates/applicant/status.html', status=status)


# ─── RECOMMENDATION REQUEST ────────────────────────────────────────────────────
@applicant_bp.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    if 'user_id' not in session:
        logger.warning("Unauthenticated access attempt to recommendation request.")
        flash("Please log in.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == 'GET':
        logger.info("Rendering recommendation request form for user_id=%s", session['user_id'])
        return render_template('templates/applicant/recommendation_request.html')

    name = request.form['name']
    email = request.form['email']
    affiliation = request.form['affiliation']
    token = str(uuid.uuid4())[:8]

    user_id = session['user_id']
    applicant = db.get_application_by_user_id(user_id)  # assumes your query abstraction returns dict with name fields


    db.insert_recommendation_request({
        "token": token,
        "user_id": user_id,
        "applicant_name": f"{applicant['first_name']} {applicant['last_name']}",
        "recommender_name": name,
        "recommender_email": email,
        "affiliation": affiliation,
        "status": "pending"
    })

    logger.info(
        "Recommendation request created by user_id=%s | name=%s, email=%s, affiliation=%s, token=%s",
        user_id, name, email, affiliation, token
    )

    link = f"{request.host_url}recommendation/submit/{token}"

    message = f"""
    To: {email}
    Subject: Recommendation Request

    Dear {name},

    You have been requested to submit a recommendation letter.
    Please use this secure link:

    {link}

    Affiliation: {affiliation}
    """

    return render_template('templates/recommender/preview.html', message=message)

@applicant_bp.route('/recommendation/view')
def view_recommendations():
    if 'user_id' not in session:
        flash("Please log in to view your recommendation letters.", "warning")
        return redirect(url_for("auth.login"))

    user_id = session['user_id']
    letters = db._execute_query(
        "SELECT * FROM recommendation_requests WHERE user_id = ?",
        (user_id,),
        fetch_one=False
    )

    letters = db._execute_query(
        "SELECT * FROM recommendation_requests WHERE user_id = ?",
        (user_id,),
        fetch_one=False
    )

    print(letters)
    for letter in letters:
        print("Letter")
        print(letter)


    if not isinstance(letters, list):  # if it's False (error) or anything not iterable
        letters = []

    return render_template('templates/applicant/view_recommendations.html', letters=letters)
    
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from queries.auth import AuthQuery

auth_bp = Blueprint('auth', __name__, template_folder='templates')

auth_db = AuthQuery("database.db")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': 
        return render_template('templates/auth/login.html')

    email = request.form.get('email')
    password = request.form.get('password')
    
    user = auth_db.authenticate_user(email, password)

    if user:
        session['user_id'] = user['user_id']
        session['email'] = user['email']
        session['role'] = user['role']
        session['student_id'] = user.get('student_id')  # Store student_id if available

        # Redirect based on role (unchanged from original)
        if user['role'] == 'applicant': 
            return redirect(url_for('applicant_dashboard'))
        if user['role'] == 'gs': 
            return redirect(url_for('gs.dashboard'))
        if user['role'] == 'cac': 
            return redirect(url_for('cac.dashboard'))
        if user['role'] == 'admin': 
            return redirect(url_for('admin.dashboard'))
        if user['role'] == 'reviewer': 
            return redirect(url_for('reviewer.dashboard'))
        
    flash('Invalid credentials', 'danger')
    #print("debug" + url_for('auth.login'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Collect form data (updated with new schema fields)
            user_data = {
                'email': request.form.get('email'),
                'password': request.form.get('password'),
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'ssn': request.form.get('ssn'),
                'address': request.form.get('address'),
                'phone': request.form.get('phone'),
                'role': request.form.get('role', 'applicant'),  # Default to applicant
                # New fields for application
                #'degree_program': request.form.get('degree_program', 'MS'),  # Default to MS
                #'admission_semester': request.form.get('admission_semester', 'Spring'),  # Default to Spring
                #'admission_year': request.form.get('admission_year', datetime.datetime.now().year + 1)  # Default to next year
            }
            
            # Create user with new schema
            result = auth_db.create_user(user_data)
            if result:
                flash('Registration successful! Please login', 'success')
                return redirect(url_for('auth.login'))
            
            flash('Registration failed', 'danger')
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    # Render registration form with any needed new fields
    return render_template('templates/auth/register.html', 
                         current_year=datetime.now().year,
                         next_year=datetime.now().year + 1)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from queries.cac import CACQuery

cac_bp = Blueprint('cac', __name__, url_prefix='/cac', template_folder='templates/cac')

def cac_required(f):
    """Custom decorator to ensure CAC role"""
    def wrapper(*args, **kwargs):
        if session.get('role') not in ['cac', 'admin']:  # Allow admin access too
            flash('Unauthorized access - CAC role required', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Initialize CAC query handler
cac_db = CACQuery("database.db")

@cac_bp.route('/dashboard')
@cac_required
def dashboard():
    """CAC dashboard showing applications needing decisions"""
    try:
        search_term = request.args.get('search', '').strip()
        print(f"[DEBUG] dashboard, search_term: {search_term}")
        
        search_term = search_term if search_term else None
        print("[DEBUG] Before querying applications:")
        
    
        applications = cac_db.get_applications_for_decision(search_term=search_term)
    
        print("[DEBUG] After querying applications:")
        
        # Proper debug for SQLite Row objects
        print(f"[DEBUG] Number of applications retrieved: {len(applications)}")
        print("[DEBUG] Application IDs and structure:")
        for i, app in enumerate(applications, 1):
            print(f"  Application {i}:")
            print(f"    Type: {type(app)}")
            print(f"    Available fields: {list(app.keys())}")  # SQLite Row objects have .keys()
            print(f"    application_id: {app['application_id']}")  # Correct access method
            print(f"    Full object: {dict(app)}")  # Convert to dict for better readability

        return render_template('templates/cac/dashboard.html',
                           applications=applications,
                           search_term=search_term,
                           current_year=datetime.now().year)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        print(f"[ERROR] dashboard - Exception: {str(e)}")
        return redirect(url_for('templates/cac.dashboard'))

@cac_bp.route('/application/<int:application_id>')
@cac_required
def application_detail(application_id):
    """Detailed application view with review form"""
    try:
        # Get all application data
        print(f"[DEBUG] application_detail - application_id: {application_id}")
        app_data = cac_db.get_application_full(application_id)
        if not app_data:
            flash('Application not found', 'danger')
            return redirect(url_for('cac.dashboard'))

        # Get all reviews
        reviews = cac_db.get_reviews(application_id)

        # Calculate average rating if multiple reviews exist
        avg_rating = None
        if reviews:
            ratings = [int(r['rating']) for r in reviews if r['rating'] is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None

        print(f"[DEBUG] application_detail - reviews: {reviews}, avg_rating: {avg_rating}")

        return render_template('templates/cac/application_detail.html',
                               app=app_data,
                               reviews=reviews,
                               avg_rating=avg_rating,
                               reject_reasons=['A', 'B', 'C', 'D', 'E'])  # From document

    except Exception as e:
        flash(f'Error loading application: {str(e)}', 'danger')
        print(f"[ERROR] application_detail - Exception: {str(e)}")
        return redirect(url_for('cac.dashboard'))

@cac_bp.route('/submit-review/<int:application_id>', methods=['POST'])
@cac_required
def submit_review(application_id):
    """Handle review submission (CAC can also review)"""
    try:
        review_data = {
            'rating': int(request.form.get('rating')),
            'deficiency_courses': request.form.get('deficiency_courses', ''),
            'reject_reason': request.form.get('reject_reason'),
            'comments': request.form.get('comments', '')[:40],  # Limit to 40 chars
            'recommended_advisor': request.form.get('recommended_advisor')
        }

        print(f"[DEBUG] submit_review - review_data: {review_data}")

        # Validate rating (1-4 as per document)
        if review_data['rating'] not in [1, 2, 3, 4]:
            flash('Invalid rating value', 'danger')
            return redirect(url_for('cac.application_detail', application_id=application_id))

        success = cac_db.submit_review(
            application_id=application_id,
            faculty_id=session['user_id'],
            **review_data
        )

        if success:
            flash('Review submitted successfully', 'success')
        else:
            flash('Failed to submit review', 'danger')

        return redirect(url_for('cac.application_detail', application_id=application_id))

    except ValueError:
        flash('Invalid rating format', 'danger')
        return redirect(url_for('cac.application_detail', application_id=application_id))
    except Exception as e:
        flash(f'Review submission error: {str(e)}', 'danger')
        print(f"[ERROR] submit_review - Exception: {str(e)}")
        return redirect(url_for('cac.dashboard'))

@cac_bp.route('/decision/<int:application_id>', methods=['POST'])
@cac_required
def submit_decision(application_id):
    """Handle final decision submission"""
    try:
        decision = request.form.get('decision')
        print(f"[DEBUG] submit_decision - decision: {decision}")

        # Validate decision
        if decision not in ['Admit with Aid', 'Admit', 'Reject']:
            flash('Invalid decision selection', 'danger')
            return redirect(url_for('cac.application_detail', application_id=application_id))

        # <-- call with only three args -->
        success = cac_db.submit_final_decision(
            application_id=application_id,
            decision=decision,
            decided_by=session['user_id']
        )

        if success:
            flash('Final decision recorded successfully', 'success')
            return redirect(url_for('cac.dashboard', application_id=application_id))

        flash('Failed to record decision', 'danger')
        return redirect(url_for('cac.application_detail', application_id=application_id))

    except Exception as e:
        flash(f'Decision error: {str(e)}', 'danger')
        print(f"[ERROR] submit_decision - Exception: {str(e)}")
        return redirect(url_for('cac.dashboard'))




@cac_bp.route('/update-status/<int:application_id>', methods=['POST'])
@cac_required
def update_status(application_id):
    """Manual status update (for transcripts, etc.)"""
    try:
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')

        print(f"[DEBUG] update_status - new_status: {new_status}, notes: {notes}")

        if not new_status:
            flash('Status update required', 'danger')
            return redirect(url_for('cac.application_detail', application_id=application_id))

        success = cac_db.update_application_status(
            application_id=application_id,
            new_status=new_status,
            updated_by=session['user_id'],
            notes=notes
        )

        if success:
            flash('Status updated successfully', 'success')
        else:
            flash('Failed to update status', 'danger')

        return redirect(url_for('cac.application_detail', application_id=application_id))

    except Exception as e:
        flash(f'Status update error: {str(e)}', 'danger')
        print(f"[ERROR] update_status - Exception: {str(e)}")
        return redirect(url_for('cac.dashboard'))

@cac_bp.route('/search')
@cac_required
def search_applicants():
    """Search functionality"""
    try:
        search_term = request.args.get('q', '')
        search_by = request.args.get('by', 'name')
        status = request.args.get('status', '')

        print(f"[DEBUG] search_applicants - search_term: {search_term}, search_by: {search_by}, status: {status}")

        results = cac_db.search_applications(
            search_term=search_term,
            search_type=search_by,
            status=status
        )

        return render_template('templates/cac/dashboard.html',
                               applications=results,
                               search_term=search_term,
                               current_year=datetime.now().year)

    except Exception as e:
        flash(f'Search error: {str(e)}', 'danger')
        print(f"[ERROR] search_applicants - Exception: {str(e)}")
        return redirect(url_for('cac.dashboard'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from queries.gs import GSQuery

gs_bp = Blueprint('gs', __name__, url_prefix='/gs', template_folder='templates')

def gs_required(f):
    """Fixed GS role decorator without redirect loops"""
    def wrapper(*args, **kwargs):
        # First check if user is logged in at all
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        # Then verify GS role
        if session.get('role') != 'gs':
            session.clear()  # Destroy invalid session
            flash('GS access required', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Initialize GS query handler (NO CHANGES)
gs_db = GSQuery("database.db")

@gs_bp.route('/dashboard')
@gs_required
def dashboard():
    try:
        status_filter = request.args.get('status', 'all')
        semester = request.args.get('semester')
        year = request.args.get('year')
        degree_program = request.args.get('degree_program')

        if semester or year or degree_program:
            applications = gs_db.filter_applicants(semester, year, degree_program)
        else:
            applications = gs_db.get_all_applications(
                None if status_filter == 'all' else status_filter
            )

        for app in applications:
            print(f"[DEBUG] App ID {app['application_id']} - transcript_received: {app['transcript_received']}")

        status_options = [
            'Application Incomplete',
            'Application Complete and Under Review', 
            'Admitted',
            'Rejected'
        ]
        return render_template('gs/dashboard.html',
                            applications=applications,
                            status_options=status_options,
                            current_filter=status_filter)
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return render_template('gs/dashboard.html', applications=[], status_options=[], current_filter="all")

@gs_bp.route('/search', methods=['GET'])
@gs_required
def search_applicants():
    try:
        search_term = request.args.get('q', '').strip()
        search_type = request.args.get('search_type', 'name')

        if not search_term:
            flash('Please enter a search term', 'info')
            return redirect(url_for('gs.dashboard'))

        results = gs_db.search_applications(search_term, search_type)
        return render_template('templates/gs/search_results.html',
                            results=results,
                            search_term=search_term)

    except Exception as e:
        flash(f'Search error: {str(e)}', 'danger')
        return redirect(url_for('gs.dashboard'))

@gs_bp.route('/application/<int:application_id>')
@gs_required
def application_detail(application_id):
    try:
        application = gs_db.get_application_details(application_id)
        if not application:
            flash('Application not found', 'danger')
            return redirect(url_for('gs.dashboard'))

        academic = gs_db.get_academic_info(application_id)
        transcripts = gs_db.get_transcript_status(application_id)
        status_options = [
            'Application Incomplete',
            'Application Complete and Under Review',
            'Admitted',
            'Rejected'
        ]

        return render_template('templates/gs/application_detail.html',
                            application=application,
                            academic=academic,
                            transcripts=transcripts,
                            status_options=status_options)
    except Exception as e:
        flash(f'Error loading application: {str(e)}', 'danger')
        return redirect(url_for('gs.dashboard'))

@app.route("/gs/stats", methods=["GET", "POST"])
def gs_statistics():
    statistics = []
    if request.method == "POST":
        semester = request.form.get("semester")
        year = request.form.get("year")
        degree = request.form.get("degree")
        statistics = gs_query.get_statistics(semester, year, degree)
    else:
        statistics = gs_query.get_statistics()
    return render_template("gs/stats.html", statistics=statistics)

@app.route("/gs/applicants", methods=["GET", "POST"])
def gs_applicants():
    if request.method == "POST":
        semester = request.form.get("semester")
        year = request.form.get("year")
        degree = request.form.get("degree")
        applicants = gs_query.filter_applicants(semester, year, degree)
        return render_template("gs/filter_applicants.html", applicants=applicants)
    return render_template("gs/filter_applicants.html", applicants=[])


@gs_bp.route('/update_personal/<int:application_id>', methods=['POST'])
@gs_required
def update_personal_info(application_id):
    try:
        update_data = {
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'ssn': request.form.get('ssn')
        }
        if gs_db.update_personal_info(application_id, update_data):
            flash('Personal information updated successfully', 'success')
        else:
            flash('No changes made', 'info')
    except Exception as e:
        flash(f'Update failed: {str(e)}', 'danger')
    return redirect(url_for('gs.application_detail', application_id=application_id))

@gs_bp.route('/mark_transcript/<int:application_id>', methods=['POST'])
@gs_required
def mark_transcript(application_id):
    try:
        if gs_db.mark_transcript_received(application_id, session.get('user_id')):
            flash('Transcript status updated', 'success')
        else:
            flash('Transcript update failed', 'danger')
    except Exception as e:
        flash(f'Transcript error: {str(e)}', 'danger')
    return redirect(url_for('gs.dashboard'))

@gs_bp.route('/update_status/<int:application_id>', methods=['POST'])
@gs_required
def update_status(application_id):
    try:
        new_status = request.form.get('new_status')

        valid_statuses = [
            'Application Incomplete',
            'Application Complete & Under Review',
            'Admitted',
            'Rejected'
        ]

        if new_status not in valid_statuses:
            flash(f"Invalid status selected: {new_status}", 'danger')
            return redirect(url_for('gs.application_detail', application_id=application_id))

        if gs_db.update_application_status(application_id, new_status):
            flash('Application status updated', 'success')
        else:
            flash('Status update failed', 'danger')
    except Exception as e:
        flash(f'Status error: {str(e)}', 'danger')
    return redirect(url_for('gs.application_detail', application_id=application_id))

@gs_bp.route('/stats')
@gs_required
def stats():
    try:
        statistics = gs_db.generate_statistics()
        return render_template('gs/stats.html', statistics=statistics)
    except Exception as e:
        flash(f'Failed to generate stats: {str(e)}', 'danger')
        return redirect(url_for('gs.dashboard'))


from flask import Blueprint, render_template, request, redirect, url_for, flash
from queries.applicant import ApplicationQuery

recommender_bp = Blueprint('recommender', __name__, url_prefix='/recommendation', template_folder='../templates')

db = ApplicationQuery('database.db')
submitted_letters = {} #* replaced by db in ph2

@recommender_bp.route('/submit/<token>', methods=['GET', 'POST'])
def submit_letter(token):
    rec = db.get_recommendation_by_token(token)

    if not rec:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for('recommender.invalid'))

    if request.method == 'POST':
        letter = request.form['letter']
        db.submit_recommendation_letter(token, letter)
        flash("Letter submitted successfully!", "success")
        return redirect(url_for('recommender.confirmation'))

    return render_template('templates/recommender/submit.html', token=token, rec=rec)

@recommender_bp.route('/confirmation')
def confirmation(): return render_template('templates/recommender/confirmation.html')

@recommender_bp.route('/invalid')
def invalid():
    return "Invalid recommendation token.", 404


from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from queries.reviewer import reviewerQuery

reviewer_bp = Blueprint('reviewer', __name__, url_prefix='/reviewer', template_folder='templates/reviewer')

def reviewer_required(f):
    """Custom decorator to ensure reviewer role"""
    def wrapper(*args, **kwargs):
        if session.get('user_type') not in ['reviewer', 'admin']:  # Allow admin access too
            flash('Unauthorized access - reviewer role required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Initialize reviewer query handler
reviewer_db = reviewerQuery("database.db")

@reviewer_bp.route('/dashboard')
@reviewer_required
def dashboard():
    """reviewer dashboard showing applications needing decisions"""
    try:
        search_term = request.args.get('search', '').strip()
        print(f"[DEBUG] dashboard, search_term: {search_term}")
        
        search_term = search_term if search_term else None
        print("[DEBUG] Before querying applications:")
        
    
        applications = reviewer_db.get_applications_for_decision(search_term=search_term)
    
        print("[DEBUG] After querying applications:")
        
        # Proper debug for SQLite Row objects
        print(f"[DEBUG] Number of applications retrieved: {len(applications)}")
        print("[DEBUG] Application IDs and structure:")
        for i, app in enumerate(applications, 1):
            print(f"  Application {i}:")
            print(f"    Type: {type(app)}")
            print(f"    Available fields: {list(app.keys())}")  # SQLite Row objects have .keys()
            print(f"    application_id: {app['application_id']}")  # Correct access method
            print(f"    Full object: {dict(app)}")  # Convert to dict for better readability

        return render_template('templates/reviewer/dashboard.html',
                           applications=applications,
                           search_term=search_term,
                           current_year=datetime.now().year)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        print(f"[ERROR] dashboard - Exception: {str(e)}")
        return redirect(url_for('login'))

@reviewer_bp.route('/application/<int:application_id>')
@reviewer_required
def application_detail(application_id):
    """Detailed application view with review form"""
    try:
        # Get all application data
        print(f"[DEBUG] application_detail - application_id: {application_id}")
        app_data = reviewer_db.get_application_full(application_id)
        if not app_data:
            flash('Application not found', 'danger')
            return redirect(url_for('reviewer.dashboard'))

        # Get all reviews
        reviews = reviewer_db.get_reviews(application_id)

        # Calculate average rating if multiple reviews exist
        avg_rating = None
        if reviews:
            ratings = [int(r['rating']) for r in reviews if r['rating'] is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None

        print(f"[DEBUG] application_detail - reviews: {reviews}, avg_rating: {avg_rating}")

        return render_template('templates/reviewer/application_detail.html',
                               app=app_data,
                               reviews=reviews,
                               avg_rating=avg_rating,
                               reject_reasons=['A', 'B', 'C', 'D', 'E'])  # From document

    except Exception as e:
        flash(f'Error loading application: {str(e)}', 'danger')
        print(f"[ERROR] application_detail - Exception: {str(e)}")
        return redirect(url_for('reviewer.dashboard'))

@reviewer_bp.route('/submit-review/<int:application_id>', methods=['POST'])
@reviewer_required
def submit_review(application_id):
    """Handle review submission (reviewer can also review)"""
    try:
        review_data = {
            'rating': int(request.form.get('rating')),
            'deficiency_courses': request.form.get('deficiency_courses', ''),
            'reject_reason': request.form.get('reject_reason'),
            'comments': request.form.get('comments', '')[:40],  # Limit to 40 chars
            'recommended_advisor': request.form.get('recommended_advisor')
        }

        print(f"[DEBUG] submit_review - review_data: {review_data}")

        # Validate rating (1-4 as per document)
        if review_data['rating'] not in [1, 2, 3, 4]:
            flash('Invalid rating value', 'danger')
            return redirect(url_for('reviewer.application_detail', application_id=application_id))

        success = reviewer_db.submit_review(
            application_id=application_id,
            faculty_id=session['user_id'],
            **review_data
        )

        if success:
            flash('Review submitted successfully', 'success')
        else:
            flash('Failed to submit review', 'danger')

        return redirect(url_for('reviewer.application_detail', application_id=application_id))

    except ValueError:
        flash('Invalid rating format', 'danger')
        return redirect(url_for('reviewer.application_detail', application_id=application_id))
    except Exception as e:
        flash(f'Review submission error: {str(e)}', 'danger')
        print(f"[ERROR] submit_review - Exception: {str(e)}")
        return redirect(url_for('reviewer.dashboard'))

@reviewer_bp.route('/decision/<int:application_id>', methods=['POST'])
@reviewer_required
def submit_decision(application_id):
    """Handle final decision submission"""
    try:
        decision = request.form.get('decision')
        print(f"[DEBUG] submit_decision - decision: {decision}")

        # Validate decision
        if decision not in ['Admit with Aid', 'Admit', 'Reject']:
            flash('Invalid decision selection', 'danger')
            return redirect(url_for('reviewer.application_detail', application_id=application_id))

        # <-- call with only three args -->
        success = reviewer_db.submit_final_decision(
            application_id=application_id,
            decision=decision,
            decided_by=session['user_id']
        )

        if success:
            flash('Final decision recorded successfully', 'success')
            return redirect(url_for('reviewer.dashboard', application_id=application_id))

        flash('Failed to record decision', 'danger')
        return redirect(url_for('reviewer.application_detail', application_id=application_id))

    except Exception as e:
        flash(f'Decision error: {str(e)}', 'danger')
        print(f"[ERROR] submit_decision - Exception: {str(e)}")
        return redirect(url_for('reviewer.dashboard'))


@reviewer_bp.route('/update-status/<int:application_id>', methods=['POST'])
@reviewer_required
def update_status(application_id):
    """Manual status update (for transcripts, etc.)"""
    try:
        new_status = request.form.get('status')
        notes = request.form.get('notes', '')

        print(f"[DEBUG] update_status - new_status: {new_status}, notes: {notes}")

        if not new_status:
            flash('Status update required', 'danger')
            return redirect(url_for('reviewer.application_detail', application_id=application_id))

        success = reviewer_db.update_application_status(
            application_id=application_id,
            new_status=new_status,
            updated_by=session['user_id'],
            notes=notes
        )

        if success:
            flash('Status updated successfully', 'success')
        else:
            flash('Failed to update status', 'danger')

        return redirect(url_for('reviewer.application_detail', application_id=application_id))

    except Exception as e:
        flash(f'Status update error: {str(e)}', 'danger')
        print(f"[ERROR] update_status - Exception: {str(e)}")
        return redirect(url_for('reviewer.dashboard'))

@reviewer_bp.route('/search')
@reviewer_required
def search_applicants():
    """Search functionality"""
    try:
        search_term = request.args.get('q', '')
        search_by = request.args.get('by', 'name')
        status = request.args.get('status', '')

        print(f"[DEBUG] search_applicants - search_term: {search_term}, search_by: {search_by}, status: {status}")

        results = reviewer_db.search_applications(
            search_term=search_term,
            search_type=search_by,
            status=status
        )

        return render_template('templates/reviewer/dashboard.html',
                               applications=results,
                               search_term=search_term,
                               current_year=datetime.now().year)

    except Exception as e:
        flash(f'Search error: {str(e)}', 'danger')
        print(f"[ERROR] search_applicants - Exception: {str(e)}")
        return redirect(url_for('login'))
    
# --- Define Valid Grades ---
VALID_GRADES = {'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'F'}




@app.route('/transcript', methods=['GET', 'POST'])
def view_transcript():
    conn = None
    if 'user_id' not in session or 'role' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user_role = session['role']

    search_query = request.args.get('search_query', '')
    if request.method == 'POST' and ('grade' in request.form or 'search_query_hidden' in request.form):
        search_query = request.form.get('search_query_hidden', search_query)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if request.method == 'POST' and 'enrollment_id' in request.form and 'grade' in request.form:

            if user_role == 'student':
                 flash("Students cannot update grades.", "warning")
                 return redirect(request.referrer or url_for('view_transcript', search_query=search_query))

            try:
                enrollment_id = int(request.form['enrollment_id'])
                section_id = int(request.form['section_id'])
                new_grade_input = request.form.get('grade')
                new_grade = new_grade_input.strip().upper() if new_grade_input and new_grade_input.strip() else None

            except (KeyError, ValueError) as e:
                flash(f"Invalid form data submitted for grade update: {e}", "danger")
                return redirect(request.referrer or url_for('view_transcript', search_query=search_query))

            if new_grade is not None and new_grade not in VALID_GRADES and new_grade not in ('W', 'IP'):
                 flash(f"Invalid grade value '{new_grade or 'empty'}' submitted.", "danger")
                 return redirect(request.referrer or url_for('view_transcript', search_query=search_query))


            can_update = False
            try:
                cursor.execute("SELECT instructor_id FROM sections WHERE section_id = ?", (section_id,))
                section_info = cursor.fetchone()
                cursor.execute("SELECT grade FROM enrollments WHERE enrollment_id = ?", (enrollment_id,))
                enrollment_info = cursor.fetchone()

                if not section_info or not enrollment_info:
                     flash("Could not find section or enrollment record.", "warning")
                else:
                    current_grade = enrollment_info['grade']
                    section_instructor_id = section_info['instructor_id']

                    instructor_capable_roles = ['instructor', 'advisor/instructor', 'advisor/instructor/reviewer']
                    is_assigned_instructor_or_combined = (user_role in instructor_capable_roles and str(section_instructor_id) == str(user_id))

                    if user_role in ['gs', 'admin']:
                        can_update = True
                    elif is_assigned_instructor_or_combined:

                        if current_grade is None or current_grade == 'IP':
                             can_update = True
                        else:
                            flash("Cannot change a grade that has already been submitted.", "warning")
                    else:
                        flash("Permission Denied: You cannot grade this section.", "danger")

            except sqlite3.Error as e:
                 print(f"Database error during permission check for grade update: {e}")
                 flash("Database error checking permissions.", "danger")


            if can_update:
                grade_to_set = new_grade
                try:
                    cursor.execute("UPDATE enrollments SET grade = ? WHERE enrollment_id = ?", (grade_to_set, enrollment_id))
                    conn.commit()
                    flash("Grade updated successfully.", "success")
                except sqlite3.Error as e:
                    conn.rollback()
                    print(f"Database error during grade update commit: {e}")
                    flash("Database error saving grade update.", "danger")

            return redirect(url_for('view_transcript', search_query=search_query))


        elif request.method == 'GET':

            template_data = {
                "user_role": user_role,
                "student_transcript": None,
                "instructor_sections": None,
                "advisor_advisees": None,
                "gs_sections": None,
                "search_query": search_query,
                "valid_grades": VALID_GRADES
            }

            is_student = (user_role == 'student')
            is_instructor_capable = user_role in ['instructor', 'advisor/instructor', 'advisor/instructor/reviewer']
            is_advisor_capable = user_role in ['advisor', 'advisor/instructor', 'advisor/instructor/reviewer']
            is_gs_or_admin = user_role in ['gs', 'admin']


            if is_student:
                cursor.execute("""
                    SELECT e.enrollment_id, s.section_id, s.semester, s.year, c.dept_code, c.course_number, c.title, c.credits, e.grade
                    FROM enrollments e JOIN sections s ON e.section_id = s.section_id JOIN courses c ON s.course_id = c.course_id
                    WHERE e.student_id = ? ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
                """, (user_id,))
                template_data['student_transcript'] = cursor.fetchall()

            if is_instructor_capable:

                section_focus_id = None
                section_focus_str = request.args.get('section_focus')
                if section_focus_str:
                    try:
                        section_focus_id = int(section_focus_str)
                    except ValueError:
                        flash("Invalid section focus ID.", "warning")

                sql_sections = """
                    SELECT s.section_id, s.semester, s.year, s.day, s.time_slot, c.dept_code, c.course_number, c.title
                    FROM sections s JOIN courses c ON s.course_id = c.course_id
                    WHERE s.instructor_id = ?
                """
                params_sections = [user_id]
                if section_focus_id is not None:
                    sql_sections += " AND s.section_id = ?"
                    params_sections.append(section_focus_id)
                sql_sections += " ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number"

                cursor.execute(sql_sections, tuple(params_sections))
                sections_raw = cursor.fetchall()
                instructor_sections_data = []
                for section_dict_raw in sections_raw:
                    section_dict = dict(section_dict_raw)
                    cursor.execute("""
                        SELECT e.enrollment_id, e.grade, u.user_id AS student_id, u.first_name, u.last_name
                        FROM enrollments e JOIN users u ON e.student_id = u.user_id
                        WHERE e.section_id = ? ORDER BY u.last_name, u.first_name
                    """, (section_dict['section_id'],))
                    students = cursor.fetchall()
                    instructor_sections_data.append({"details": section_dict, "students": students})
                template_data['instructor_sections'] = instructor_sections_data
                template_data['section_focus_id'] = section_focus_id

            if is_advisor_capable:

                cursor.execute("""
                    SELECT u.user_id, u.first_name, u.last_name
                    FROM advising a JOIN users u ON a.studentID = u.user_id
                    WHERE a.advisorID = ? ORDER BY u.last_name, u.first_name
                """, (user_id,))
                advisees_raw = cursor.fetchall()
                advisor_advisees_data = []
                for advisee_raw in advisees_raw:
                    advisee = dict(advisee_raw)
                    cursor.execute("""
                        SELECT e.enrollment_id, s.section_id, s.semester, s.year, c.dept_code, c.course_number, c.title, c.credits, e.grade
                        FROM enrollments e
                        JOIN sections s ON e.section_id = s.section_id
                        JOIN courses c ON s.course_id = c.course_id
                        WHERE e.student_id = ? ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number
                    """, (advisee['user_id'],))
                    transcript = cursor.fetchall()
                    advisor_advisees_data.append({
                        "advisee_details": advisee,
                        "transcript": transcript
                    })
                template_data['advisor_advisees'] = advisor_advisees_data

            if is_gs_or_admin:

                base_section_query = """
                    SELECT s.section_id, s.semester, s.year, s.day, s.time_slot, c.dept_code, c.course_number, c.title,
                           GROUP_CONCAT(DISTINCT sec_instr.first_name || ' ' || sec_instr.last_name) AS instructor_names,
                           r.location as room_location, r.capacity as room_capacity
                    FROM sections s JOIN courses c ON s.course_id = c.course_id LEFT JOIN users sec_instr ON s.instructor_id = sec_instr.user_id LEFT JOIN rooms r ON s.room_id = r.room_id
                """
                student_query = """
                    SELECT e.enrollment_id, e.grade, e.section_id, u.user_id AS student_id, u.first_name, u.last_name
                    FROM enrollments e JOIN users u ON e.student_id = u.user_id
                """
                params = []
                section_where_clause = " WHERE 1=1 "
                student_where_clause = " WHERE 1=1 "
                search_term = template_data['search_query'].strip()
                matching_student_ids = []

                if search_term:
                    search_like = f"%{search_term}%"
                    cursor.execute("""
                        SELECT user_id FROM users WHERE role = 'student' AND
                              (first_name LIKE ? OR last_name LIKE ? OR username LIKE ? OR CAST(user_id AS TEXT) LIKE ?)
                    """, (search_like, search_like, search_like, search_like))
                    matching_student_ids = [row['user_id'] for row in cursor.fetchall()]

                    if matching_student_ids:
                        id_placeholders_stu = ','.join('?' for _ in matching_student_ids)
                        student_where_clause += f" AND e.student_id IN ({id_placeholders_stu})"

                        cursor.execute(f"SELECT DISTINCT section_id FROM enrollments WHERE student_id IN ({id_placeholders_stu})", matching_student_ids)
                        matching_section_ids = [row['section_id'] for row in cursor.fetchall()]
                        if matching_section_ids:
                             id_placeholders_sec = ','.join('?' for _ in matching_section_ids)
                             section_where_clause += f" AND s.section_id IN ({id_placeholders_sec})"
                             params.extend(matching_student_ids)
                             params.extend(matching_section_ids)
                        else:
                            section_where_clause += " AND 1=0 "
                            student_where_clause += " AND 1=0 "
                            params.extend(matching_student_ids)
                    else:
                        student_where_clause += " AND 1=0 "; section_where_clause += " AND 1=0 "

                else:
                    params = []

                num_student_params = len(matching_student_ids) if search_term else 0
                student_params = params[:num_student_params]
                section_params = params[num_student_params:]

                full_section_query = base_section_query + section_where_clause + " GROUP BY s.section_id ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number"
                full_student_query = student_query + student_where_clause + " ORDER BY u.last_name, u.first_name"


                cursor.execute(full_section_query, section_params); all_sections = cursor.fetchall()
                cursor.execute(full_student_query, student_params); all_students = cursor.fetchall()

                students_by_section = {};
                for student in all_students:
                    sec_id = student['section_id'];
                    if sec_id not in students_by_section: students_by_section[sec_id] = []
                    students_by_section[sec_id].append(dict(student))

                gs_sections_data = []
                for section in all_sections:
                     sec_id = section['section_id']
                     gs_sections_data.append({"details": dict(section), "students": students_by_section.get(sec_id, [])})
                template_data['gs_sections'] = gs_sections_data


            return render_template('view_transcript.html', **template_data)

        else:

             flash("Unsupported request method.", "warning")
             return redirect(url_for('login'))


    except sqlite3.Error as e:
        print(f"DATABASE ERROR in /transcript: {e}")
        if conn: conn.rollback()
        flash(f"A database error occurred: {e}. Please try again later.", "danger")

        return redirect(url_for('login'))
    except Exception as e:
        print(f"UNEXPECTED ERROR in /transcript: {e}")
        import traceback
        traceback.print_exc()
        if conn: conn.rollback()
        flash("An unexpected error occurred. Please try again later.", "danger")
        return redirect(url_for('login'))
    finally:
        if conn:
            conn.close()

@app.route('/drop_class', methods=['POST'])
def drop_class():
    if 'user_id' not in session:
        flash("Authentication required to drop classes.", "warning")
        return redirect(url_for('login'))

    enrollment_id_str = request.form.get('enrollment_id')
    if not enrollment_id_str:
        flash("Invalid request: Missing enrollment ID.", "danger")
        return redirect(request.referrer or url_for('view_transcript')) 

    try:
        enrollment_id = int(enrollment_id_str)
    except ValueError:
        flash("Invalid enrollment ID format.", "danger")
        return redirect(request.referrer or url_for('view_transcript'))

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT student_id, grade FROM enrollments WHERE enrollment_id = ?", (enrollment_id,))
        enrollment_info = cursor.fetchone()

        if not enrollment_info:
            flash(f"Enrollment record {enrollment_id} not found.", "danger")
            return redirect(request.referrer or url_for('view_transcript'))

        enrolled_student_id = enrollment_info['student_id']
        current_grade = enrollment_info['grade']
        logged_in_user_id = session['user_id']
        logged_in_role = session.get('user_type') 

        can_drop = False
        if logged_in_role == 'student' and enrolled_student_id == logged_in_user_id:
            can_drop = True
        elif logged_in_role in ['gs', 'admin']:
            can_drop = True

        if not can_drop:
            flash("Permission denied to drop this enrollment.", "danger")
            return redirect(request.referrer or url_for('view_transcript'))

        if current_grade != 'IP':
            flash(f"Cannot drop class. Current grade is '{current_grade}'. Only 'In Progress' classes can be dropped.", "warning")
            return redirect(request.referrer or url_for('view_transcript'))

        cursor.execute("UPDATE enrollments SET grade = 'W' WHERE enrollment_id = ?", (enrollment_id,))
        conn.commit()

        flash("Class dropped successfully (Grade set to 'W').", "success")
        return redirect(request.referrer or url_for('view_transcript')) 

    except sqlite3.Error as e:
        if conn: conn.rollback()
        print(f"Database error during drop class for enrollment {enrollment_id}: {e}")
        flash(f"Database error occurred while dropping class: {e}", "danger")
        return redirect(request.referrer or url_for('view_transcript'))
    except Exception as e:
        if conn: conn.rollback()
        print(f"Unexpected error during drop class for enrollment {enrollment_id}: {e}")
        flash("An unexpected error occurred while dropping the class.", "danger")
        return redirect(request.referrer or url_for('view_transcript'))
    finally:
        if conn:
            conn.close()

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
@app.route('/register_class', methods=['GET', 'POST'])
def register_class():
    if not user_logged_in():
        return redirect(url_for('login'))

    conn = None
    cursor = None

    try: 

        if request.method == 'POST':
            conn = get_connection() 
            cursor = conn.cursor() 

            section_id_str = request.form.get('section_id')
            if not section_id_str:
                 flash("Invalid section selected.", "warning")
                 return redirect(url_for('register_class'))

            try:
                section_id = int(section_id_str)
            except ValueError:
                flash("Invalid section ID.", "warning")
                return redirect(url_for('register_class'))

            student_id = session['user_id']

            if session['user_type'] != 'student':
                flash("ERROR: Only students can register for courses.", "danger")
                return redirect(url_for('register_class'))
            
            cursor.execute("SELECT initial_advising_complete FROM students WHERE userID = ?", (student_id,))
            advising_status_row = cursor.fetchone()

            if advising_status_row['initial_advising_complete'] == 0:
                flash("ERROR: Registration Blocked. You must complete your initial advising appointment before registering for classes.", "warning")
                return redirect(url_for('register_class'))

            # --- Check if already enrolled ---
            cursor.execute("SELECT 1 FROM enrollments WHERE section_id = ? AND student_id = ?", (section_id, student_id))
            if cursor.fetchone():
                flash("ERROR: You are already enrolled in this section.", "warning")
                return redirect(url_for('register_class'))

            # --- Get Section and Room Info ---
            cursor.execute("""
                SELECT s.course_id, s.day, s.time_slot, s.semester, s.year, s.room_id, r.capacity
                FROM sections s LEFT JOIN rooms r ON s.room_id = r.room_id WHERE s.section_id = ?
            """, (section_id,))
            section_info = cursor.fetchone()
            if not section_info:
                flash("ERROR: Selected section not found.", "danger")
                return redirect(url_for('register_class'))

            # --- Check Room Capacity ---
            room_capacity = section_info['capacity']
            if room_capacity is None:
                flash("ERROR: Registration closed. Room information unavailable.", "danger")
                return redirect(url_for('register_class'))
            cursor.execute("SELECT COUNT(enrollment_id) as count FROM enrollments WHERE section_id = ?", (section_id,))
            enrollment_count = cursor.fetchone()['count']
            if enrollment_count >= room_capacity:
                flash(f"ERROR: Registration failed. Section is full (Capacity: {room_capacity}).", "danger")
                return redirect(url_for('register_class'))

            # --- Check Prerequisites ---
            course_id = section_info['course_id']
            cursor.execute("SELECT prerequisite_course_id FROM prerequisites WHERE course_id = ?", (course_id,))
            prerequisites = cursor.fetchall()
            for prereq in prerequisites:
                 prereq_course_id = prereq['prerequisite_course_id']
                 cursor.execute("SELECT 1 FROM enrollments e JOIN sections s ON e.section_id = s.section_id WHERE e.student_id = ? AND s.course_id = ? AND e.grade NOT IN ('F', 'W', 'IP') LIMIT 1", (student_id, prereq_course_id))
                 if not cursor.fetchone():
                     cursor.execute("SELECT dept_code, course_number FROM courses WHERE course_id = ?", (prereq_course_id,))
                     prereq_course_info = cursor.fetchone()
                     prereq_name = f"{prereq_course_info['dept_code']} {prereq_course_info['course_number']}" if prereq_course_info else f"ID {prereq_course_id}"
                     flash(f"ERROR: Prerequisite ({prereq_name}) not met.", "danger")
                     return redirect(url_for('register_class'))


            # --- Check Time Conflicts ---
            new_day = section_info['day']
            new_time_slot = section_info['time_slot']
            new_semester = section_info['semester']
            new_year = section_info['year']
            try:
                new_start_str, new_end_str = new_time_slot.split('-')
                new_start = int(new_start_str)
                new_end = int(new_end_str)
            except ValueError:
                 flash("ERROR: Invalid time slot format for the selected section.", "danger")
                 return redirect(url_for('register_class'))
            cursor.execute("""
                SELECT s.day, s.time_slot, c.dept_code, c.course_number
                FROM enrollments e
                JOIN sections s ON e.section_id = s.section_id
                JOIN courses c ON s.course_id = c.course_id
                WHERE e.student_id = ? AND s.semester = ? AND s.year = ?
            """, (student_id, new_semester, new_year))
            student_sections = cursor.fetchall()
            for sec in student_sections:
                if sec['day'] == new_day:
                    try:
                        student_start_str, student_end_str = sec['time_slot'].split('-')
                        student_start = int(student_start_str)
                        student_end = int(student_end_str)
                        if new_start < student_end and student_start < new_end:
                            conflict_course = f"{sec['dept_code']} {sec['course_number']} ({sec['day']} {sec['time_slot']})"
                            flash(f"ERROR: Time conflict with {conflict_course}. Cannot register.", "danger")
                            return redirect(url_for('register_class'))
                    except ValueError:
                        print(f"Warning: Skipping time conflict check due to invalid format {sec['time_slot']}")
                        continue


            # --- If all checks pass, insert enrollment ---
            cursor.execute("INSERT INTO enrollments (student_id, section_id, grade) VALUES (?, ?, 'IP')",
                           (student_id, section_id))
            conn.commit()
            flash("Successfully registered for the course!", "success")
            return redirect(url_for('register_class')) 

        else: 
            conn = get_connection() 
            cursor = conn.cursor() 

            cursor.execute("""
                SELECT
                    s.section_id, s.semester, s.year, s.day, s.time_slot,
                    c.dept_code, c.course_number, c.title, c.credits,
                    i.first_name as instructor_fname, i.last_name as instructor_lname,
                    r.location as room_location, r.capacity as room_capacity,
                    (SELECT COUNT(enrollment_id) FROM enrollments WHERE section_id = s.section_id) as enrolled_count
                FROM sections s
                JOIN courses c ON c.course_id = s.course_id
                LEFT JOIN users i ON s.instructor_id = i.user_id
                LEFT JOIN rooms r ON s.room_id = r.room_id
                ORDER BY s.year DESC, s.semester, c.dept_code, c.course_number, s.section_id
            """)
            raw_courses = cursor.fetchall()
            course_list = []
            for course in raw_courses:
                course_dict = dict(course)
                capacity = course_dict.get('room_capacity')
                enrolled = course_dict.get('enrolled_count', 0)
                course_dict['seats_available'] = max(0, capacity - enrolled) if capacity is not None else 'N/A'
                course_list.append(course_dict)

            return render_template('register_class.html',
                                   user_id=session.get('user_id'),
                                   user_type=session.get('user_type'),
                                   courses=course_list,
                                   display_message=None)

    except sqlite3.Error as e:
        flash(f"Database error: {e}", "danger")
        print(f"Database Error in register_class: {e}")
        return redirect(url_for('login')) 
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"Unexpected Error in register_class: {e}")
        return redirect(url_for('login'))
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")



@app.route('/initial_advising_form', methods=['GET'])
def view_initial_advising_form():
    if not session.get('user_id') or session.get('user_type') != 'student':
        flash("Please log in as a student.", "warning")
        return redirect(url_for('login'))

    student_id = session['user_id']
    conn = None
    courses = []
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT initial_advising_complete FROM students WHERE userID = ?", (student_id,))
        status = cursor.fetchone()
        if status and status['initial_advising_complete'] == 1:
            flash("Your initial advising requirement is already complete.", "info")
            return redirect(url_for('studentHome'))


        cursor.execute("""
            SELECT 1 FROM initialAdvisingQueue
            WHERE studentID = ? AND status = 0
        """, (student_id,))
        pending = cursor.fetchone()
        if pending:
            flash("You already have an initial advising plan pending review.", "info")
            return redirect(url_for('studentHome'))

        cursor.execute("SELECT course_id, dept_code, course_number, title FROM courses ORDER BY dept_code, course_number")
        courses = cursor.fetchall()

    except sqlite3.Error as e:
        flash(f"Database error preparing form: {e}", "danger")
        print(f"[ERROR] view_initial_advising_form DB - {e}")
        return redirect(url_for('studentHome'))
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"[ERROR] view_initial_advising_form General - {e}")
        return redirect(url_for('studentHome'))
    finally:
        if conn:
            conn.close()

    return render_template('initial_advising_form.html', courses=courses)


@app.route('/submit_initial_advising_form', methods=['POST'])
def submit_initial_advising_form():
    if not session.get('user_id') or session.get('user_type') != 'student':
        flash("Please log in as a student.", "warning")
        return redirect(url_for('login')) 

    student_id = session['user_id']
    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT initial_advising_complete FROM students WHERE userID = ?", (student_id,))
        status = cursor.fetchone()
        if status and status['initial_advising_complete'] == 1:
            flash("Your initial advising requirement is already complete.", "info")
            return redirect(url_for('studentHome'))

        cursor.execute("SELECT 1 FROM initialAdvisingQueue WHERE studentID = ? AND status = 0", (student_id,))
        pending = cursor.fetchone()
        if pending:
            flash("You already have an initial advising plan pending review.", "info")
            return redirect(url_for('studentHome'))

        cursor.execute("SELECT advisorID FROM advising WHERE studentID = ?", (student_id,))
        advisor_info = cursor.fetchone()
        if not advisor_info:
            flash("You must be assigned an advisor before submitting this form. Please contact the Graduate Secretary.", "warning")
            return redirect(url_for('studentHome'))
        advisor_id = advisor_info['advisorID']

        chosen_courses = []
        for i in range(6):
            course_id_str = request.form.get(f'initial_course_id_{i}')
            if course_id_str: 
                try:
                     course_id = int(course_id_str)
                     cursor.execute("SELECT 1 FROM courses WHERE course_id = ?", (course_id,))
                     if cursor.fetchone():
                         if course_id not in chosen_courses: 
                             chosen_courses.append(course_id)
                except ValueError:
                    flash(f"Invalid course ID submitted: {course_id_str}", "warning")

        if not chosen_courses:
            flash("You must select at least one course for your initial plan.", "warning")
            return redirect(url_for('view_initial_advising_form'))

        cursor.execute("BEGIN TRANSACTION")

        cursor.execute("""
            INSERT INTO initialAdvisingQueue (studentID, advisorID, status)
            VALUES (?, ?, 0)
        """, (student_id, advisor_id))

        submission_id = cursor.lastrowid

        courses_to_insert = [(submission_id, course_id) for course_id in chosen_courses]
        cursor.executemany("""
            INSERT INTO initialAdvisingQueue_courses (submissionID, courseID)
            VALUES (?, ?)
        """, courses_to_insert)

        conn.commit() 
        flash("Initial advising plan submitted successfully for review.", "success")

    except sqlite3.Error as e:
        if conn: conn.rollback() 
        flash(f"Database error submitting form: {e}", "danger")
        print(f"[ERROR] submit_initial_advising_form DB - {e}")
    except Exception as e:
        if conn: conn.rollback() 
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"[ERROR] submit_initial_advising_form General - {e}")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('studentHome'))

@app.route('/view_pending_initial_forms', methods=['GET'])
def view_pending_initial_forms():
    user_role = session.get('user_type')
    if not session.get('user_id') or user_role not in ['advisor', 'gs', 'advisor/instructor', 'advisor/instructor/reviewer']:
        flash("Access restricted to Advisors and Graduate Secretaries.", "warning")
        return redirect(url_for('login'))

    conn = None
    pending_submissions = []
    try:
        conn = get_connection()
        cursor = conn.cursor()

        base_query = """
            SELECT q.submissionID, q.studentID, q.advisorID, q.submission_timestamp,
                   stu.first_name AS student_fname, stu.last_name AS student_lname,
                   adv.first_name AS advisor_fname, adv.last_name AS advisor_lname
            FROM initialAdvisingQueue q
            JOIN users stu ON q.studentID = stu.user_id
            JOIN users adv ON q.advisorID = adv.user_id
            WHERE q.status = 0
        """
        params = []

        if user_role == 'advisor':
            base_query += " AND q.advisorID = ?"
            params.append(session['user_id'])

        base_query += " ORDER BY q.submission_timestamp ASC"

        cursor.execute(base_query, params)
        submissions_raw = cursor.fetchall()

        for sub_raw in submissions_raw:
            submission = dict(sub_raw) 
            cursor.execute("""
                SELECT c.dept_code, c.course_number, c.title
                FROM initialAdvisingQueue_courses qc
                JOIN courses c ON qc.courseID = c.course_id
                WHERE qc.submissionID = ?
                ORDER BY c.dept_code, c.course_number
            """, (submission['submissionID'],))
            submission['courses'] = cursor.fetchall()
            pending_submissions.append(submission)

    except sqlite3.Error as e:
        flash(f"Database error fetching pending forms: {e}", "danger")
        print(f"[ERROR] view_pending_initial_forms DB - {e}")
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"[ERROR] view_pending_initial_forms General - {e}")
    finally:
        if conn:
            conn.close()

    return render_template('view_pending_initial_forms.html', pending_submissions=pending_submissions)


@app.route('/process_initial_advising_form', methods=['POST'])
def process_initial_advising_form():
    user_role = session.get('user_type')
    user_id = session.get('user_id')
    if not user_id or user_role not in ['advisor', 'gs']:
        flash("Access restricted.", "warning")
        return redirect(url_for('login'))

    submission_id_str = request.form.get('submissionID')
    action = request.form.get('action') 

    if not submission_id_str or action not in ['approve', 'reject']:
        flash("Invalid request data.", "warning")
        return redirect(url_for('view_pending_initial_forms'))
    try:
        submission_id = int(submission_id_str)
    except ValueError:
        flash("Invalid Submission ID.", "warning")
        return redirect(url_for('view_pending_initial_forms'))

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT studentID, advisorID, status
            FROM initialAdvisingQueue
            WHERE submissionID = ?
        """, (submission_id,))
        submission_info = cursor.fetchone()

        if not submission_info:
            flash(f"Submission ID {submission_id} not found.", "warning")
            return redirect(url_for('view_pending_initial_forms'))

        if submission_info['status'] != 0:
            flash(f"Submission {submission_id} has already been processed.", "info")
            return redirect(url_for('view_pending_initial_forms'))

        if user_role == 'advisor' and submission_info['advisorID'] != user_id:
            flash("You are not authorized to process this specific submission.", "danger")
            return redirect(url_for('view_pending_initial_forms'))

        student_id_to_update = submission_info['studentID']
        new_status = 0 
        success_message = ""


        cursor.execute("BEGIN TRANSACTION")

        if action == 'approve':
            new_status = 1
            cursor.execute("UPDATE initialAdvisingQueue SET status = ? WHERE submissionID = ?", (new_status, submission_id))
            cursor.execute("UPDATE students SET initial_advising_complete = 1 WHERE userID = ?", (student_id_to_update,))
            success_message = f"Submission {submission_id} approved. Registration hold lifted for student {student_id_to_update}."

        elif action == 'reject':
            new_status = -1
            cursor.execute("UPDATE initialAdvisingQueue SET status = ? WHERE submissionID = ?", (new_status, submission_id))
            success_message = f"Submission {submission_id} rejected."

        conn.commit() 
        flash(success_message, "success")

    except sqlite3.Error as e:
        if conn: conn.rollback()
        flash(f"Database error processing submission: {e}", "danger")
        print(f"[ERROR] process_initial_advising_form DB - {e}")
    except Exception as e:
        if conn: conn.rollback()
        flash(f"An unexpected error occurred: {e}", "danger")
        print(f"[ERROR] process_initial_advising_form General - {e}")
    finally:
        if conn:
            conn.close()

    return redirect(url_for('view_pending_initial_forms'))


@app.route('/advisor_assignments')
def view_advisor_assignments():
    """Displays a list of advisors and their assigned advisees (for GS)."""

    if not session.get('user_id') or session.get('user_type') != 'gs':
        flash("Access restricted to Graduate Secretaries.", "warning")
        return redirect('/') 

    advisors_data = []
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, first_name, last_name
            FROM users
            WHERE role = 'advisor'
            ORDER BY last_name, first_name
        """)
        advisors = cursor.fetchall()

        for advisor_row in advisors:
            advisor_id = advisor_row['user_id']
            cursor.execute("""
                SELECT u.user_id, u.first_name, u.last_name
                FROM advising a
                JOIN users u ON a.studentID = u.user_id
                WHERE a.advisorID = ?
                ORDER BY u.last_name, u.first_name
            """, (advisor_id,))
            advisees_rows = cursor.fetchall()

            advisor_dict = {
                'advisor_id': advisor_row['user_id'],
                'advisor_first_name': advisor_row['first_name'],
                'advisor_last_name': advisor_row['last_name'],
                'advisees': [dict(student_row) for student_row in advisees_rows]
            }
            advisors_data.append(advisor_dict)

        template_path = 'advisor_assignments.html'

        return render_template(template_path, advisors_data=advisors_data)

    except sqlite3.Error as e:
        flash(f'Database error retrieving advisor assignments: {str(e)}', 'danger')
        print(f"[ERROR] view_advisor_assignments - DB Error: {str(e)}")
        return redirect('/gradSecHome') 
    except Exception as e:
        if isinstance(e, jinja2.exceptions.TemplateNotFound):
             flash(f'Template file not found: {e}', 'danger')
             print(f"[ERROR] view_advisor_assignments - Template Error: {e}")
        else:
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            print(f"[ERROR] view_advisor_assignments - General Error: {str(e)}")
        return redirect('/gradSecHome') 
    finally:
        if conn:
            conn.close()


app.register_blueprint(admin_bp)        # Uses url_prefix='/admin' from definition
app.register_blueprint(applicant_bp)    # Uses url_prefix='/applicant' from definition
app.register_blueprint(auth_bp)         # No url_prefix in definition
app.register_blueprint(cac_bp)          # Uses url_prefix='/cac' from definition
app.register_blueprint(gs_bp)           # Uses url_prefix='/gs' from definition
app.register_blueprint(recommender_bp)  # Uses url_prefix='/recommendation' from definition
app.register_blueprint(reviewer_bp)     # Uses url_prefix='/reviewer' from definition


app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    init_db()  # Only if safe to call again
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables in database.db:", [row[0] for row in cursor.fetchall()])
    conn.close()