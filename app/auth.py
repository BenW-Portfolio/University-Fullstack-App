import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db.queries.auth import AuthQuery

auth_bp = Blueprint('auth', __name__, template_folder='templates')

auth_db = AuthQuery("./db/app.db")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET': 
        return render_template('auth/login.html')

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
            return redirect(url_for('applicant.dashboard'))
        if user['role'] == 'gs': 
            return redirect(url_for('gs.dashboard'))
        if user['role'] == 'cac': 
            return redirect(url_for('cac.dashboard'))
        if user['role'] == 'admin': 
            return redirect(url_for('admin.dashboard'))
        if user['role'] == 'reviewer': 
            return redirect(url_for('reviewer.dashboard'))
        
    flash('Invalid credentials', 'danger')
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
    return render_template('auth/register.html', 
                         current_year=datetime.datetime.now().year,
                         next_year=datetime.datetime.now().year + 1)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))