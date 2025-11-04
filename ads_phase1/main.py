from flask import Flask, session, render_template, redirect, url_for, request, flash
import sqlite3
import random
app = Flask('app')
app.secret_key = "yikes"
app.debug = True

@app.route('/', methods = ['POST', 'GET'])
def login():
    #error = ""
    with getConnection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        if request.method == 'POST': 
            session['user'] = request.form["username"]
            session['pw'] = request.form["password"]
            cursor.execute("SELECT password FROM users WHERE username = ?", (session['user'],))
            values=cursor.fetchone()
            #print("pass = " + session['pw']) DEBUG
            #print("realpass = " + values['password']) DEBUG
            #print("comparison = " + str(session['pw'] == values['password'])) DEBUG
            if (values is None) or (session['pw'] != values['password']):
                flash("Username or password is not correct", 'error')
                return render_template("login.html")
            elif session['pw'] == values['password']:
                #Now that we have a sucsessful login, purge password from session and get user info
                session.pop('pw')

                cursor.execute("SELECT * FROM users WHERE username = ?", (session['user'],))
                values = cursor.fetchone()
                session['user_type'] = values['role']
                session['userID'] = values['userID']
                #print("role  = " + values['role'])

                #Redirects the user to their homepage
                if session['user_type'] == ('admin'):
                    return redirect('/adminHome')
                elif session['user_type'] == ('advisor'):
                    return redirect('/advisorHome')
                elif session['user_type'] == ('gradSec'):
                    return redirect('/gradSecHome')
                elif session['user_type'] == ('alumni'):
                    return redirect('/alumni')
                elif session['user_type'] == ('student'):
                    suspend(session['userID'])
                    return redirect('/studentHome')
            connection.commit()
            connection.close()
            
                
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
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if request.method == 'POST':
        fname = request.form["fname"]
        lname = request.form["lname"]
        username = request.form["username"]
        pw = request.form["pass"]
        address = request.form["address"]
        #NEEDS FIXING BECAUSE USERID IS A PRIMARY KEY
        cursor.execute("SELECT MAX(userID) FROM users")
        max_id = cursor.fetchone()[0]
        random_id = max_id + 1 if max_id is not None else 1000

        program = request.form['program']
        gradDate = request.form['gradSem'] + " " + request.form['gradYear']

        connection = sqlite3.connect("ADS database.db")
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
            connection = sqlite3.connect("ADS Database.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (userID, username, password, fname, lname, role) VALUES (?,?,?, ?, ?, ?)", (random_id, username, pw, fname, lname, 'student',))
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
    
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute("SELECT userID, fname, lname from users WHERE username = ?", (session['user'], ))
    userID = cursor.fetchone()

    cursor.execute("SELECT * FROM alumni WHERE userID = ? ", (userID[0],))
    values = cursor.fetchall()[0]

    cursor.execute("SELECT course.courseID, course.title, course.credits, course.code, course.department, outcome.grade, outcome.semester FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (userID[0],))
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

    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #print("UserID = " + str(session['userID']))
    if session['user_type'] == 'alumni' :
        cursor.execute("SELECT * FROM alumni JOIN users ON alumni.userID = users.userID WHERE users.userID = ?", (int(session['userID']), ))
    elif session['user_type'] == 'student':
        cursor.execute("SELECT * FROM students JOIN users ON students.userID = users.userID WHERE users.userID = ?", (int(session['userID']), ))

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

        cursor.execute("UPDATE users SET fname = ?, lname = ?, password = ? WHERE userID = ?", (newFName, newLName, newPass, session['userID'], ))

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
    
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute("SELECT userID from users WHERE username = ?", (session['user'], ))
    userID = cursor.fetchone()[0]

    cursor.execute("SELECT course.courseID, course.title, course.credits, course.code, course.department, outcome.grade, outcome.semester FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (userID,))
    courses = cursor.fetchall()

    cursor.execute("SELECT * FROM users use LEFT JOIN students stu ON use.userID = stu.userID WHERE stu.userID = ?", (userID,))
    studentInfo = cursor.fetchone()
    #for i in studentInfo:
        #print(i)
    
    cursor.execute("SELECT student.fname, student.lname, course.title, course.department, course.code, course.credits, f1.formID FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.courseID = f1Course.courseID LEFT JOIN users student ON student.userID = f1.studentID WHERE f1.studentID = ? AND (SELECT MAX(formID) FROM form1 WHERE studentID = ?) = f1.formID", (userID, userID, ))
    form1 = cursor.fetchall()
    
    #print(form1[5])

    cursor.execute("SELECT result FROM form1ApprovalQueue WHERE studentID = ? AND formID = (SELECT MAX(formID) FROM form1ApprovalQueue WHERE studentID = ?)", (int(userID), int(userID), ))
    result = cursor.fetchone()

    studentGPA = GPA(userID)

    cursor.execute("SELECT fname, lname FROM users WHERE userID = (SELECT advisorID FROM advising WHERE studentID = ?)", (userID, ))
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
    if session['user_type'] == 'student' or session['user_type'] == 'gradSec' or session['user_type'] == 'admin' or session['user_type'] == 'advisor':
        
        if request.method == 'POST':
            if session['user_type'] != 'student':
                student = int(request.form["auditID"])
            else:
                student = session['userID']
                               
            connection = sqlite3.connect("ADS database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            
            cursor.execute("SELECT userID FROM students")
            studentCheck = cursor.fetchall()
           
            cursor.execute("SELECT program FROM students WHERE userID = ?" , (student,))
            studentProgram = cursor.fetchone()[0]
            #print(studentProgram + "program")

            if (studentProgram == 'phd'):
                cursor.execute("SELECT approved FROM students WHERE userID = ?" , (student,))
                thesisApproved = cursor.fetchone()[0]
                
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
                connection = sqlite3.connect("ADS database.db")
                connection.row_factory = sqlite3.Row
                cursor = connection.cursor()
                #cursor.execute("SELECT * FROM enroll WHERE studentID = ?", (student))
                cursor.execute("SELECT course.courseID, course.title, course.credits, course.code, course.department, outcome.grade, outcome.semester FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (student,))
                studentHistory = cursor.fetchall()
                cursor.execute("SELECT course.courseID FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (student,))
                studentCID = cursor.fetchall()
                #print(studentCID)

                #cursor.execute("SELECT userID FROM students")
                cursor.execute("SELECT student.fname, student.lname, course.courseID, course.title, course.department, course.code, course.credits FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.courseID = f1Course.courseID LEFT JOIN users student ON student.userID = f1.studentID WHERE f1.studentID = ?", (student, ))
                form1 = cursor.fetchall()
                cursor.execute("SELECT course.courseID FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.courseID = f1Course.courseID LEFT JOIN users student ON student.userID = f1.studentID WHERE f1.studentID = ?", (student, ))
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
                cursor.execute("SELECT grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE enroll.studentID = ?", (student, ))
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
                    nonCS = getNonCS(student)
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
                            connection = sqlite3.connect("ADS database.db")
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
                            connection = sqlite3.connect("ADS database.db")
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

def getNonCS(studentID):
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

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
    return nonCS

def getCSHours(studentID):
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT credits, grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE department = 'CSCI' AND enroll.studentID = ?", (studentID, ))
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
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT credits, grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE enroll.studentID = ? ", (studentID, ))
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
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT credits, grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE enroll.studentID = ? ", (studentID, ))
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
        credits += grade[0]
    
    GPA = GPA / credits

    return (int(GPA * 100)) / 100.0

#fixed to adjust based on ms or phd program reqs 
def suspend(studentID):
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT grade FROM enroll LEFT JOIN courses ON enroll.courseID = courses.courseID WHERE enroll.studentID = ?", (studentID, ))
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


    #print("The length of grades is " + str(len(grades)) + " and isSuspended() = " + str(isSuspended(studentID))) DEBUG
    if len(grades) > 0 and not isSuspended(studentID) and count > 2:
        cursor.execute ("UPDATE students SET suspended = 1 WHERE userID = ?", (studentID, ))
    else :
        cursor.execute("UPDATE students SET suspended = 0 WHERE userID = ?", (studentID, ))
    
    cursor.close()
    connection.commit()
    connection.close()

def isSuspended(studentID) :
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute ("SELECT suspended FROM students WHERE userID = ?", (studentID, ))
    temp = cursor.fetchone()[0]

    cursor.close()
    connection.commit()
    connection.close()

    if temp == 0:
        return False
    else :
        return True


@app.route('/studentProf', methods = ['POST', 'GET']) 
def studentProf():
    suspend(request.form['studentID'])

    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    cursor.execute("SELECT course.courseID, course.title, course.credits, course.code, course.department, outcome.grade, outcome.semester FROM enroll outcome LEFT JOIN courses course ON outcome.courseID = course.courseID WHERE outcome.studentID = ?", (request.form['studentID'],))
    courses = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users use LEFT JOIN students stu ON use.userID = stu.userID WHERE stu.userID = ?", (request.form['studentID'],))
    studentInfo = cursor.fetchone()
    
    cursor.execute("SELECT student.fname, student.lname, course.title, course.department, course.code, course.credits FROM form1 f1 LEFT JOIN form1_courses f1Course ON f1.formID = f1Course.formID LEFT JOIN courses course ON course.courseID = f1Course.courseID LEFT JOIN users student ON student.userID = f1.studentID WHERE f1.studentID = ?", (request.form['studentID'], ))
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

    connection = sqlite3.connect("ADS Database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #select to display all students + info
    cursor.execute("SELECT student.userID AS student_userID, student.username AS student_username, student.fname AS student_fname, student.lname AS student_lname, students.address AS student_address, student.role AS student_role, students.program AS student_program, students.graduationDate AS student_graduationDate, students.approved AS student_approved, advisor.fname AS advisor_fname, advisor.lname AS advisor_lname FROM users student JOIN students ON student.userID = students.userID LEFT JOIN users advisor ON advisor.userID = (SELECT advisorID FROM advising WHERE studentID = student.userID) WHERE student.role = ?", ('student',)) 
    values = cursor.fetchall()
    connection.commit()
    connection.close()
    approvedGrad = "Yes"
    unapprovedGrad = "No"

    #select to display all students who need to graduate
    connection = sqlite3.connect("ADS Database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    #cursor.execute("SELECT * FROM graduateApplicationQueue JOIN users ON graduateApplicationQueue.userID = users.userID JOIN students ON graduateApplicationQueue.userID = students.userID WHERE students.approved = 1")
    cursor.execute("SELECT * FROM graduateApplicationQueue JOIN users ON graduateApplicationQueue.userID = users.userID")
    
    gradValues = cursor.fetchall()
    connection.commit()
    connection.close()
    if request.method == 'POST':
        if (gradValues is not None):
            gradName = request.form["userID"]
            connection = sqlite3.connect("ADS Database.db")
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM students WHERE userID = ?", (gradName, ))
            finalValues = cursor.fetchone()
            cursor.execute("DELETE FROM graduateApplicationQueue WHERE userID = ?", (gradName, ))
            
            #might need to be changed later based on how alumni table gets changed
            cursor.execute("DELETE FROM students WHERE userID = ?", (gradName, ))
            cursor.execute("INSERT INTO alumni VALUES (?, ?, ?, ?)" , (finalValues['userID'] , finalValues['address'], finalValues['program'], finalValues['graduationDate'],))
            cursor.execute("UPDATE users SET role = 'alumni' WHERE userID = ?", (gradName,))

            #could possibly be made nicer later, but not focus for now
            flash("Graduated " + gradName)
            cursor.close()
            connection.commit()
            connection.close()
            return redirect('/gradSecHome')
    return render_template("gradSecHome.html", values = values, approvedGrad = approvedGrad, unapprovedGrad = unapprovedGrad, gradValues = gradValues)

@app.route('/gradSecAssignAdv', methods = ['POST', 'GET'])
def gradSecAssignAdv():
    connection = sqlite3.connect("ADS Database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM students JOIN users ON students.userID = users.userID WHERE students.userID NOT IN (SELECT studentID FROM advising)")
    values = cursor.fetchall()
    cursor.execute("SELECT * FROM users WHERE role = 'advisor'")
    advisorValues = cursor.fetchall()
    #for advisor in advisorValues:
        #print("\n")
        #for element in advisor:
            #print(element)


    connection.commit()
    connection.close()
        #assigning a faculty advisor to students:
  #      connection = sqlite3.connect("ADS Database.db")
      #  connection.row_factory = sqlite3.Row
      #  cursor = connection.cursor()
    
    if request.method == 'POST':
        student = request.form["student"]
        advisor = request.form["advisor"]

        connection = sqlite3.connect("ADS Database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("INSERT INTO advising VALUES (?, ?)", (advisor, student))
        values = cursor.fetchall()

        connection.commit()
        connection.close()
        return redirect('gradSecAssignAdv')

    back = "/gradSecHome"

    return render_template("gradSecAssignAdv.html", values = values, advisorValues = advisorValues, back = back)

# shows the advisor's homepage with their advisees and the courses each student picked for form 1
@app.route('/advisorHome', methods=['POST', 'GET'])
def advisorHome():
    if 'user' not in session:
        return redirect('/login')

    advisor_id = session.get('userID')

    connection = sqlite3.connect("ADS Database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users WHERE userID = ?", (advisor_id,))
    advisor = cursor.fetchone()

    # get the list of students that are assigned to this advisor
    cursor.execute("""
        SELECT stu.*, use.fname, use.lname
        FROM advising adv
        JOIN users use ON adv.studentID = use.userID
        JOIN students stu ON stu.userID = use.userID
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

        if form_row:
            form_id = form_row['formID']
            cursor.execute("""
                SELECT c.department, c.code 
                FROM form1_courses fc 
                JOIN courses c ON fc.courseID = c.courseID 
                WHERE fc.formID = ?
            """, (form_id,))
            student['form1_courses'] = cursor.fetchall()
        else:
            student['form1_courses'] = []

        student_dicts.append(student)



    cursor.execute("SELECT * FROM form1ApprovalQueue JOIN users ON userID = studentID WHERE form1ApprovalQueue.advisorID = ? AND form1ApprovalQueue.result = 0", (session['userID'], ))
    formQueueUsers = cursor.fetchall()

    cursor.execute("SELECT title, department, code, form1ApprovalQueue.formID, form1ApprovalQueue.studentID, form1ApprovalQueue.advisorID FROM form1_courses JOIN courses ON courses.courseID = form1_courses.courseID JOIN form1ApprovalQueue on form1ApprovalQueue.formID = form1_courses.formID WHERE form1ApprovalQueue.advisorID = ? AND form1ApprovalQueue.result = 0 ORDER BY form1ApprovalQueue.formID", (session['userID'], ))
    formQueueClasses = cursor.fetchall()

    cursor.close()
    connection.commit()
    connection.close()
    
    return render_template("advisorHome.html", advisor=advisor, students=student_dicts, studentsQueue = formQueueUsers, coursesQueue = formQueueClasses)


@app.route('/approveForm1', methods = ['POST'])
def approveForm1():
    connection = sqlite3.connect("ADS Database.db")
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
    connection = sqlite3.connect("ADS Database.db")
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

    connection = sqlite3.connect("ADS Database.db")
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

    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # get a list of all available courses to display in the dropdowns
    cursor.execute("SELECT courseID, department, code, title FROM courses")
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
            request.form['course_id ' + str(i)]
            chosen.append(request.form['course_id ' + str(i)])
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
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    
    #Selects all courses
    cursor.execute("SELECT course.courseID, course.title, course.credits, course.code, course.department, pr1.title AS pre1, pr2.title AS pre2 FROM courses course LEFT JOIN courses pr1 ON course.preReq1 IS pr1.courseID LEFT JOIN courses pr2 ON course.preReq2 IS pr2.courseID")
    courses = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'gradSec'")
    gradSecs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'advisor'")
    advisors = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'student'")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE role = 'alumni'")
    alumni = cursor.fetchall()
    
    #print(courses)

    cursor.close()
    connection.commit()
    connection.close()

    return render_template("adminHome.html", courses = courses, admins = admins, gradSecs = gradSecs, advisors = advisors, students = students, Alumni = alumni)

@app.route('/adminCreateAccount', methods = ['POST', 'GET'])
def adminCreateAccount():
    if request.method == 'POST':
        fname = request.form["fname"]
        lname = request.form["lname"]
        username = request.form["username"]
        pw = request.form["pass"]


        connection = sqlite3.connect("ADS database.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        values = cursor.fetchall()

        cursor.execute("SELECT MAX(userID) FROM users")
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
            connection = sqlite3.connect("ADS Database.db")
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (userID, username, password, fname, lname, role) VALUES (?,?,?, ?, ?, ?)", (random_id, username, pw, fname, lname, request.form['type'],))
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
    connection = sqlite3.connect("ADS database.db")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    #This line needs to be able to select all studentIDs from the advising relationship table 
    cursor.execute("SELECT student.fname, student.lname, student.userID FROM advising LEFT JOIN users student ON student.userID = advising.studentID WHERE advising.advisorID = ?", (request.form['advisorID'], ))
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM users WHERE userID = ?", (request.form['advisorID'], ))
    advisor = cursor.fetchone()

    cursor.close()
    connection.commit()
    connection.close()

    back = request.referrer

    return render_template("advisorProf.html", advisor = advisor, students = students, back = back)

#Use this to avoid SQLite issues with concurrency
def getConnection() :
    return sqlite3.connect("ADS database.db")

app.run(host='0.0.0.0', port=8080)