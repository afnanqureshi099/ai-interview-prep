import os
import re
import secrets
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

import database
from ai_evaluator import AIEvaluator

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ai-interview-prep-secret-key-2026-secure')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ---------------------------------------------------------
# Authentication & Authorization Decorators
# ---------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Admin authentication required. Please log in.', 'warning')
            return redirect(url_for('login', next=request.path))
        if session.get('user_role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------
# Validation Helper Functions (Server-Side)
# ---------------------------------------------------------

def validate_registration(name, email, phone, password):
    """
    Validates candidate registration according to strict criteria:
    - Name: Letters and spaces only, min 3 chars
    - Email: RFC-compliant email regex
    - Phone: Exactly 10 digits (numeric only)
    - Password: Min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char (!@#$%^&*)
    """
    errors = []

    # Full Name validation
    if not name or not re.match(r'^[A-Za-z ]{3,60}$', name.strip()):
        errors.append('Full name must be at least 3 characters and contain only letters and spaces.')

    # Email validation
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not email or not re.match(email_regex, email.strip()):
        errors.append('Please provide a valid email address.')

    # Phone validation: exactly 10 digits
    if not phone or not re.match(r'^\d{10}$', phone.strip()):
        errors.append('Contact number must be exactly 10 digits without country code or special characters.')

    # Password criteria
    if not password:
        errors.append('Password is required.')
    else:
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must include at least one uppercase letter (A-Z).')
        if not re.search(r'[a-z]', password):
            errors.append('Password must include at least one lowercase letter (a-z).')
        if not re.search(r'\d', password):
            errors.append('Password must include at least one number (0-9).')
        if not re.search(r'[!@#$%^&*]', password):
            errors.append('Password must include at least one special character (!@#$%^&*).')

    return errors


# ---------------------------------------------------------
# Context Processors & Template Helpers
# ---------------------------------------------------------

@app.context_processor
def inject_user():
    return {
        'current_user': {
            'id': session.get('user_id'),
            'name': session.get('user_name'),
            'email': session.get('user_email'),
            'role': session.get('user_role')
        } if 'user_id' in session else None
    }


# ---------------------------------------------------------
# Public & Authentication Routes
# ---------------------------------------------------------

@app.route('/')
def index():
    """Landing Page showcasing platform features, stats, and mock domains."""
    total_interviews = database.query_one("SELECT COUNT(*) AS count FROM interview_sessions WHERE status='completed'")
    total_users = database.query_one("SELECT COUNT(*) AS count FROM users WHERE role='candidate'")
    avg_score = database.query_one("SELECT AVG(overall_score) AS avg FROM interview_sessions WHERE status='completed'")

    stats = {
        'total_interviews': total_interviews['count'] if total_interviews else 0,
        'total_users': total_users['count'] if total_users else 0,
        'avg_score': round(avg_score['avg'] or 78.4, 1) if avg_score else 78.4
    }
    return render_template('index.html', stats=stats)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Candidate Registration with client & server-side validation."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        errors = validate_registration(full_name, email, phone, password)
        if password != confirm_password:
            errors.append('Passwords do not match.')

        # Check existing email
        existing_user = database.query_one("SELECT id FROM users WHERE email = ?", (email,))
        if existing_user:
            errors.append('An account with this email address already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html', form_data={
                'full_name': full_name,
                'email': email,
                'phone': phone
            })

        # Secure password hashing
        password_hash = generate_password_hash(password)

        # Insert user into database
        result = database.execute_stmt(
            """INSERT INTO users (full_name, email, phone, password_hash, role, status)
               VALUES (?, ?, ?, ?, 'candidate', 'active')""",
            (full_name, email, phone, password_hash)
        )

        user_id = result['lastrowid']
        # Automatic session login
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['user_role'] = 'candidate'

        flash(f'Welcome aboard, {full_name}! Your account has been created successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html', form_data={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User & Admin Login with role-based routing and status check."""
    if 'user_id' in session:
        if session.get('user_role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html', email=email)

        user = database.query_one("SELECT * FROM users WHERE email = ?", (email,))

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('login.html', email=email)

        # Check active status
        if user['status'] != 'active':
            flash('Your account has been deactivated by the administrator. Please contact support.', 'danger')
            return render_template('login.html', email=email)

        # Set user session
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']
        session.permanent = remember

        flash(f'Welcome back, {user["full_name"]}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    return render_template('login.html', email='')


@app.route('/logout')
def logout():
    """Terminates session and logs user out."""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------
# Candidate Dashboard & Mock Interview Routes
# ---------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    """Candidate Dashboard showing metrics, recent sessions, and launch setup."""
    user_id = session['user_id']
    user = database.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    # Compute candidate statistics
    sessions_count = database.query_one(
        "SELECT COUNT(*) AS total FROM interview_sessions WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    )['total']

    avg_score_row = database.query_one(
        "SELECT AVG(overall_score) AS avg, MAX(overall_score) AS max FROM interview_sessions WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    )

    top_domain_row = database.query_one(
        """SELECT domain, COUNT(*) as count FROM interview_sessions
           WHERE user_id = ? AND status = 'completed'
           GROUP BY domain ORDER BY count DESC LIMIT 1""",
        (user_id,)
    )

    # Fetch recent attempts (up to 8)
    recent_sessions = database.query_all(
        """SELECT id, domain, difficulty, total_questions, overall_score,
                  technical_score, clarity_score, completeness_score, duration_seconds, created_at
           FROM interview_sessions
           WHERE user_id = ? AND status = 'completed'
           ORDER BY created_at DESC LIMIT 8""",
        (user_id,)
    )

    # Available domains and count of questions in each
    domains_meta = database.query_all(
        """SELECT domain, COUNT(*) as count FROM questions
           WHERE is_active = 1 GROUP BY domain"""
    )

    stats = {
        'total_interviews': sessions_count,
        'avg_score': round(avg_score_row['avg'], 1) if avg_score_row and avg_score_row['avg'] else 0.0,
        'highest_score': round(avg_score_row['max'], 1) if avg_score_row and avg_score_row['max'] else 0.0,
        'top_domain': top_domain_row['domain'] if top_domain_row else 'None yet'
    }

    return render_template(
        'dashboard.html',
        user=user,
        stats=stats,
        recent_sessions=recent_sessions,
        domains_meta=domains_meta
    )


@app.route('/interview/start', methods=['POST'])
@login_required
def start_interview():
    """Initializes a new interview session with selected domain and difficulty."""
    user_id = session['user_id']
    domain = request.form.get('domain', 'Software Engineering')
    difficulty = request.form.get('difficulty', 'Mid')
    question_count = int(request.form.get('question_count', 3))

    # Fetch random questions matching criteria
    questions = database.query_all(
        """SELECT id FROM questions
           WHERE domain = ? AND difficulty = ? AND is_active = 1
           ORDER BY RANDOM() LIMIT ?""",
        (domain, difficulty, question_count)
    )

    # Fallback to any difficulty in domain if specific difficulty count is low
    if len(questions) < question_count:
        questions = database.query_all(
            """SELECT id FROM questions
               WHERE domain = ? AND is_active = 1
               ORDER BY RANDOM() LIMIT ?""",
            (domain, question_count)
        )

    if not questions:
        flash(f'No active questions available for domain: {domain}. Please select another domain.', 'warning')
        return redirect(url_for('dashboard'))

    # Create new session record
    actual_count = len(questions)
    result = database.execute_stmt(
        """INSERT INTO interview_sessions (user_id, domain, difficulty, total_questions, status)
           VALUES (?, ?, ?, ?, 'in_progress')""",
        (user_id, domain, difficulty, actual_count)
    )
    session_id = result['lastrowid']

    # Store assigned question IDs in flask session for this interview run
    session[f'session_{session_id}_questions'] = [q['id'] for q in questions]

    return redirect(url_for('live_interview', session_id=session_id))


@app.route('/interview/<int:session_id>')
@login_required
def live_interview(session_id):
    """Live interactive interview environment."""
    user_id = session['user_id']
    interview = database.query_one(
        "SELECT * FROM interview_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )

    if not interview:
        flash('Interview session not found.', 'danger')
        return redirect(url_for('dashboard'))

    if interview['status'] == 'completed':
        flash('This interview has already been submitted and completed.', 'info')
        return redirect(url_for('view_results', session_id=session_id))

    # Retrieve assigned question IDs
    q_ids = session.get(f'session_{session_id}_questions')
    if not q_ids:
        # Fallback query matching domain and count
        fallback_qs = database.query_all(
            "SELECT id FROM questions WHERE domain = ? AND is_active = 1 LIMIT ?",
            (interview['domain'], interview['total_questions'])
        )
        q_ids = [q['id'] for q in fallback_qs]

    # Fetch question details (sanitized: no model answer sent in initial payload)
    placeholders = ','.join(['?'] * len(q_ids))
    questions_raw = database.query_all(
        f"SELECT id, domain, difficulty, question_text FROM questions WHERE id IN ({placeholders})",
        q_ids
    )

    # Maintain original randomized order
    id_map = {q['id']: q for q in questions_raw}
    questions = [id_map[qid] for qid in q_ids if qid in id_map]

    return render_template(
        'interview.html',
        interview=interview,
        questions=questions,
        total_questions=len(questions)
    )


@app.route('/api/interview/<int:session_id>/submit-answer', methods=['POST'])
@login_required
def submit_answer(session_id):
    """
    Evaluates a candidate's answer to a question in real-time.
    Uses AIEvaluator for multi-pillar analysis.
    """
    user_id = session['user_id']
    data = request.get_json() or {}

    question_id = data.get('question_id')
    user_answer = data.get('answer', '').strip()

    # Validate session ownership
    interview = database.query_one(
        "SELECT * FROM interview_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )
    if not interview:
        return jsonify({'error': 'Unauthorized or invalid session'}), 403

    # Fetch question details
    question = database.query_one("SELECT * FROM questions WHERE id = ?", (question_id,))
    if not question:
        return jsonify({'error': 'Question not found'}), 404

    # Run AI evaluation engine
    eval_result = AIEvaluator.evaluate_response(user_answer, question)

    matched_kw_str = ', '.join(eval_result['matched_keywords'])
    missing_kw_str = ', '.join(eval_result['missing_keywords'])

    # Save answer and scoring to database
    database.execute_stmt(
        """INSERT INTO session_answers
           (session_id, question_id, user_answer, technical_score, clarity_score,
            completeness_score, overall_score, feedback, strengths, improvements,
            matched_keywords, missing_keywords)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            question_id,
            user_answer,
            eval_result['technical_score'],
            eval_result['clarity_score'],
            eval_result['completeness_score'],
            eval_result['overall_score'],
            eval_result['feedback'],
            eval_result['strengths'],
            eval_result['improvements'],
            matched_kw_str,
            missing_kw_str
        )
    )

    return jsonify({
        'status': 'success',
        'scores': {
            'overall': eval_result['overall_score'],
            'technical': eval_result['technical_score'],
            'clarity': eval_result['clarity_score'],
            'completeness': eval_result['completeness_score']
        },
        'feedback': eval_result['feedback'],
        'strengths': eval_result['strengths'],
        'improvements': eval_result['improvements'],
        'matched_keywords': eval_result['matched_keywords'],
        'missing_keywords': eval_result['missing_keywords'],
        'model_answer': eval_result['model_answer'],
        'rating_label': eval_result['rating_label']
    })


@app.route('/api/interview/<int:session_id>/finish', methods=['POST'])
@login_required
def finish_interview(session_id):
    """
    Finalizes interview session: calculates aggregates and updates session status to completed.
    """
    user_id = session['user_id']
    data = request.get_json() or {}
    duration_seconds = int(data.get('duration_seconds', 0))

    interview = database.query_one(
        "SELECT * FROM interview_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )
    if not interview:
        return jsonify({'error': 'Session not found'}), 404

    # Compute averages across answered questions in this session
    score_agg = database.query_one(
        """SELECT
            AVG(overall_score) AS avg_overall,
            AVG(technical_score) AS avg_tech,
            AVG(clarity_score) AS avg_clarity,
            AVG(completeness_score) AS avg_comp
           FROM session_answers WHERE session_id = ?""",
        (session_id,)
    )

    avg_overall = round(score_agg['avg_overall'] or 0.0, 1)
    avg_tech = round(score_agg['avg_tech'] or 0.0, 1)
    avg_clarity = round(score_agg['avg_clarity'] or 0.0, 1)
    avg_comp = round(score_agg['avg_comp'] or 0.0, 1)

    database.execute_stmt(
        """UPDATE interview_sessions
           SET overall_score = ?, technical_score = ?, clarity_score = ?,
               completeness_score = ?, status = 'completed', duration_seconds = ?
           WHERE id = ?""",
        (avg_overall, avg_tech, avg_clarity, avg_comp, duration_seconds, session_id)
    )

    # Clean up temporary session key
    session.pop(f'session_{session_id}_questions', None)

    return jsonify({
        'status': 'completed',
        'redirect_url': url_for('view_results', session_id=session_id)
    })


@app.route('/results/<int:session_id>')
@login_required
def view_results(session_id):
    """Comprehensive performance feedback and scorecard breakdown."""
    user_id = session['user_id']
    user_role = session.get('user_role')

    # Allow admins to view any results, candidates only their own
    if user_role == 'admin':
        interview = database.query_one("SELECT * FROM interview_sessions WHERE id = ?", (session_id,))
    else:
        interview = database.query_one(
            "SELECT * FROM interview_sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id)
        )

    if not interview:
        flash('Scorecard not found or unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))

    candidate = database.query_one("SELECT * FROM users WHERE id = ?", (interview['user_id'],))

    # Fetch detailed answers joined with questions
    answers = database.query_all(
        """SELECT sa.*, q.question_text, q.model_answer, q.expected_keywords
           FROM session_answers sa
           JOIN questions q ON sa.question_id = q.id
           WHERE sa.session_id = ?
           ORDER BY sa.id ASC""",
        (session_id,)
    )

    # Calculate overall grade letter
    overall = interview['overall_score']
    if overall >= 90:
        grade = 'A+'
        verdict = 'Outstanding Performance - Ready for Senior Roles'
    elif overall >= 80:
        grade = 'A'
        verdict = 'Strong Hire - Demonstrates Great Technical Proficiency'
    elif overall >= 70:
        grade = 'B+'
        verdict = 'Solid Candidate - Meets Baseline Competency'
    elif overall >= 60:
        grade = 'B'
        verdict = 'Competent - Needs Polish on Technical Precision'
    else:
        grade = 'C'
        verdict = 'Foundational Knowledge Needed - Practice Recommended'

    return render_template(
        'results.html',
        interview=interview,
        candidate=candidate,
        answers=answers,
        grade=grade,
        verdict=verdict
    )


@app.route('/history')
@login_required
def history():
    """Complete candidate interview attempts history table with filtering."""
    user_id = session['user_id']
    domain_filter = request.args.get('domain', '').strip()

    if domain_filter:
        sessions_list = database.query_all(
            """SELECT * FROM interview_sessions
               WHERE user_id = ? AND domain = ? AND status = 'completed'
               ORDER BY created_at DESC""",
            (user_id, domain_filter)
        )
    else:
        sessions_list = database.query_all(
            """SELECT * FROM interview_sessions
               WHERE user_id = ? AND status = 'completed'
               ORDER BY created_at DESC""",
            (user_id,)
        )

    return render_template('history.html', sessions=sessions_list, selected_domain=domain_filter)


# ---------------------------------------------------------
# Administrator Module & Management Panel
# ---------------------------------------------------------

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin Dashboard: Metrics, User Management, Question Bank, Submissions."""
    # 1. System Metrics
    total_users = database.query_one("SELECT COUNT(*) as count FROM users WHERE role = 'candidate'")['count']
    active_users = database.query_one("SELECT COUNT(*) as count FROM users WHERE role = 'candidate' AND status = 'active'")['count']
    total_interviews = database.query_one("SELECT COUNT(*) as count FROM interview_sessions WHERE status = 'completed'")['count']
    avg_score_row = database.query_one("SELECT AVG(overall_score) as avg FROM interview_sessions WHERE status = 'completed'")
    total_questions = database.query_one("SELECT COUNT(*) as count FROM questions WHERE is_active = 1")['count']

    metrics = {
        'total_users': total_users,
        'active_users': active_users,
        'total_interviews': total_interviews,
        'avg_score': round(avg_score_row['avg'] or 0.0, 1) if avg_score_row else 0.0,
        'total_questions': total_questions
    }

    # 2. Candidate Users List with attempt counts
    users_list = database.query_all(
        """SELECT u.*, COUNT(s.id) as interview_count
           FROM users u
           LEFT JOIN interview_sessions s ON u.id = s.user_id AND s.status = 'completed'
           WHERE u.role = 'candidate'
           GROUP BY u.id
           ORDER BY u.created_at DESC"""
    )

    # 3. Question Bank List
    domain_filter = request.args.get('q_domain', '')
    if domain_filter:
        questions_list = database.query_all(
            "SELECT * FROM questions WHERE domain = ? ORDER BY id DESC",
            (domain_filter,)
        )
    else:
        questions_list = database.query_all("SELECT * FROM questions ORDER BY id DESC")

    # 4. Audit Log / Recent Submissions across all candidates
    submissions_list = database.query_all(
        """SELECT s.*, u.full_name, u.email
           FROM interview_sessions s
           JOIN users u ON s.user_id = u.id
           WHERE s.status = 'completed'
           ORDER BY s.created_at DESC LIMIT 30"""
    )

    return render_template(
        'admin.html',
        metrics=metrics,
        users=users_list,
        questions=questions_list,
        submissions=submissions_list,
        selected_q_domain=domain_filter
    )


@app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_user_status(user_id):
    """Toggles active/inactive status of a candidate user."""
    user = database.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if user['role'] == 'admin':
        flash('Cannot deactivate an administrator account.', 'warning')
        return redirect(url_for('admin_dashboard'))

    new_status = 'inactive' if user['status'] == 'active' else 'active'
    database.execute_stmt("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    flash(f"User '{user['full_name']}' is now {new_status}.", 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Deletes a candidate user and cascades their interview sessions."""
    user = database.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if user['role'] == 'admin':
        flash('Cannot delete an administrator account.', 'danger')
        return redirect(url_for('admin_dashboard'))

    database.execute_stmt("DELETE FROM users WHERE id = ?", (user_id,))
    flash(f"User '{user['full_name']}' has been permanently deleted.", 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/questions/add', methods=['POST'])
@admin_required
def admin_add_question():
    """Adds a new question to the question bank."""
    domain = request.form.get('domain', '').strip()
    difficulty = request.form.get('difficulty', '').strip()
    question_text = request.form.get('question_text', '').strip()
    expected_keywords = request.form.get('expected_keywords', '').strip()
    model_answer = request.form.get('model_answer', '').strip()

    if not all([domain, difficulty, question_text, expected_keywords, model_answer]):
        flash('All question fields are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    database.execute_stmt(
        """INSERT INTO questions (domain, difficulty, question_text, expected_keywords, model_answer, is_active)
           VALUES (?, ?, ?, ?, ?, 1)""",
        (domain, difficulty, question_text, expected_keywords, model_answer)
    )

    flash('New question successfully added to the question bank!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/questions/<int:question_id>/edit', methods=['POST'])
@admin_required
def admin_edit_question(question_id):
    """Edits an existing question in the bank."""
    question = database.query_one("SELECT id FROM questions WHERE id = ?", (question_id,))
    if not question:
        flash('Question not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    domain = request.form.get('domain', '').strip()
    difficulty = request.form.get('difficulty', '').strip()
    question_text = request.form.get('question_text', '').strip()
    expected_keywords = request.form.get('expected_keywords', '').strip()
    model_answer = request.form.get('model_answer', '').strip()
    is_active = 1 if request.form.get('is_active') == '1' else 0

    if not all([domain, difficulty, question_text, expected_keywords, model_answer]):
        flash('All fields are required when updating a question.', 'danger')
        return redirect(url_for('admin_dashboard'))

    database.execute_stmt(
        """UPDATE questions
           SET domain = ?, difficulty = ?, question_text = ?, expected_keywords = ?, model_answer = ?, is_active = ?
           WHERE id = ?""",
        (domain, difficulty, question_text, expected_keywords, model_answer, is_active, question_id)
    )

    flash('Question updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/questions/<int:question_id>/delete', methods=['POST'])
@admin_required
def admin_delete_question(question_id):
    """Deletes a question from the question bank."""
    database.execute_stmt("DELETE FROM questions WHERE id = ?", (question_id,))
    flash('Question removed from the question bank.', 'info')
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('base.html', not_found=True), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('base.html', server_error=True), 500


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------

if __name__ == '__main__':
    # Auto-initialize database if not already created
    if not os.path.exists(database.DB_PATH):
        import init_db
        init_db.seed_database()

    port = int(os.environ.get('PORT', 5050))
    print("\n" + "=" * 60)
    print("AI INTERVIEW PREPARATION PLATFORM")
    print(f"Server running at: http://127.0.0.1:{port}")
    print("Admin Portal:     admin@interviewprep.ai / Admin@12345")
    print("Candidate Demo:   candidate@interviewprep.ai / Candidate@123")
    print("=" * 60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=port)
