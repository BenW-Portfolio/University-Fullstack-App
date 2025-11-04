import logging, uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db.queries.applicant import ApplicationQuery


# ─── SETUP LOGGER ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── DATABASE AND BLUEPRINT SETUP ──────────────────────────────────────────────
db = ApplicationQuery('./db/app.db')
applicant_bp = Blueprint('applicant', __name__, url_prefix='/applicant', template_folder='../templates')


# ─── DASHBOARD ─────────────────────────────────────────────────────────────────
@applicant_bp.route('/dashboard')
def dashboard():
    logger.info("Accessing applicant dashboard for user_id=%s", session.get('user_id'))
    return render_template('applicant/dashboard.html')


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
            'applicant/application.html',
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
    
    return redirect(url_for('applicant.dashboard'))

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

    return render_template('applicant/status.html', status=status)


# ─── RECOMMENDATION REQUEST ────────────────────────────────────────────────────
@applicant_bp.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    if 'user_id' not in session:
        logger.warning("Unauthenticated access attempt to recommendation request.")
        flash("Please log in.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == 'GET':
        logger.info("Rendering recommendation request form for user_id=%s", session['user_id'])
        return render_template('applicant/recommendation_request.html')

    name = request.form['name']
    email = request.form['email']
    affiliation = request.form['affiliation']
    token = str(uuid.uuid4())[:8]

    user_id = session['user_id']
    applicant = db.get_application_by_user_id(user_id)  # assumes your query abstraction returns dict with name fields


    db.insert_recommendation_request({
        "token": token,
        "user_id": user_id,
        "applicant_name": f"{applicant.get('first_name', '')} {applicant.get('last_name', '')}",
        "recommender_name": name,
        "recommender_email": email,
        "affiliation": affiliation,
        "status": "pending"
    })

    logger.info(
        "Recommendation request created by user_id=%s | name=%s, email=%s, affiliation=%s, token=%s",
        user_id, name, email, affiliation, token
    )

    message = f"""
    To: {email}
    Subject: Recommendation Request

    Dear {name},

    You have been requested to submit a recommendation letter.
    Please use this secure link:

    http://127.0.0.1:5000/recommendation/submit/{token} (Note --> Doesn't work in DEV)

    Affiliation: {affiliation}
    """

    return render_template('recommender/preview.html', message=message)

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

    return render_template('applicant/view_recommendations.html', letters=letters)
    