from flask import Blueprint, render_template, request, redirect, url_for, flash
from db.queries.applicant import ApplicationQuery

recommender_bp = Blueprint('recommender', __name__, url_prefix='/recommendation', template_folder='../templates')

db = ApplicationQuery('./db/app.db')
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

    return render_template('recommender/submit.html', token=token, rec=rec)

@recommender_bp.route('/confirmation')
def confirmation(): return render_template('recommender/confirmation.html')

@recommender_bp.route('/invalid')
def invalid():
    return "Invalid recommendation token.", 404
