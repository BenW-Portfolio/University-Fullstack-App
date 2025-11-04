from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db.queries.gs import GSQuery

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
gs_db = GSQuery("./db/app.db")

@gs_bp.route('/dashboard')
@gs_required
def dashboard():
    try:
        status_filter = request.args.get('status', 'all')
        applications = gs_db.get_all_applications(
            None if status_filter == 'all' else status_filter
        )
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
        return render_template('gs/search_results.html',
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

        return render_template('gs/application_detail.html',
                            application=application,
                            academic=academic,
                            transcripts=transcripts,
                            status_options=status_options)
    except Exception as e:
        flash(f'Error loading application: {str(e)}', 'danger')
        return redirect(url_for('gs.dashboard'))

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
    return redirect(url_for('gs.application_detail', application_id=application_id))

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