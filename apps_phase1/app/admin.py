from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from db.queries.admin import AdminQuery

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
admin_db = AdminQuery("./db/app.db")

@admin_bp.route('/dashboard')
@admin_required
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

        return render_template('admin/dashboard.html',
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