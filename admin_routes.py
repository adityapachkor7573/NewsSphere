from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

# Create blueprint
admin_bp = Blueprint('admin', __name__, template_folder='frontend')

# --- Database Helper ---
def get_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- User Management ---
def get_users():
    conn = get_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users

def get_user_by_id(user_id):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def update_user(user_id, name, email, role):
    conn = get_connection()
    conn.execute("UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?", (name, email, role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- Article Management ---
def get_articles():
    return 0

def get_articles_count():
   return 0

# --- Feedback Management ---
def get_feedback():
    return 0

def get_feedback_count():
    return 0

# --- Reported Issues Management ---

def get_all_issues():
    conn = get_connection()
    issues = conn.execute("SELECT * FROM reported_issues ORDER BY created_at DESC").fetchall()
    conn.close()
    return issues

def reply_to_issue(issue_id, reply_text):
    conn = get_connection()
    conn.execute("""
        UPDATE reported_issues
        SET reply = ?, status = 'Resolved', replied_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (reply_text, issue_id))
    conn.commit()
    conn.close()

def add_issue(user_email, issue_text):
    conn = get_connection()
    conn.execute("INSERT INTO reported_issues (user_email, issue) VALUES (?, ?)", (user_email, issue_text))
    conn.commit()
    conn.close()


def update_user(user_id, name, email, role):
    # Default password: username@1234
    default_password = f"{name}@1234"
    conn = get_connection()
    conn.execute(
        "UPDATE users SET username = ?, email = ?, role = ?, password = ? WHERE id = ?",
        (name, email, role, default_password, user_id)
    )
    conn.commit()
    conn.close()


# --- Admin Routes ---
@admin_bp.route('/admin/dashboard')
def admin_dashboard_view():
    total_users = len(get_users())
    total_articles = get_articles_count()
    total_feedback = get_feedback_count()

    return render_template('dashboard.html',
                           total_users=total_users,
                           total_articles=total_articles,
                           total_feedback=total_feedback)

@admin_bp.route('/admin/users')
def admin_panel():
    users = get_users()
    return render_template('admin_panel.html', users=users)



@admin_bp.route('/admin/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        update_user(user_id, name, email, role)
        return redirect(url_for('admin.admin_panel'))
    user = get_user_by_id(user_id)
    return render_template('edit_user.html', user=user)

@admin_bp.route('/admin/delete/<int:user_id>')
def delete_user_route(user_id):
    delete_user(user_id)
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin/articles')
def admin_articles():
    articles = get_articles()
    return render_template('articles.html', articles=articles)

@admin_bp.route('/admin/feedback')
def admin_feedback():
    feedback = get_feedback()
    return render_template('feedback.html', feedback=feedback)

# ------------------ Reported Issues ------------------

@admin_bp.route('/admin/issues')
def admin_issues():
    issues = get_all_issues()
    return render_template('admin_issues.html', issues=issues)

@admin_bp.route('/admin/reply_issue/<int:issue_id>', methods=['POST'])
def reply_issue(issue_id):
    reply_text = request.form['reply']
    reply_to_issue(issue_id, reply_text)
    return redirect(url_for('admin.admin_issues'))


@admin_bp.route('/admin/settings')
def admin_settings():
    return render_template('settings.html')



