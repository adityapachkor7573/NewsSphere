from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

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


# --- Admin Routes ---
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

@admin_bp.route('/admin/dashboard')
def admin_dashboard_view():
    # You can later replace these with actual database queries
    total_users = len(get_users())
    total_articles = 45      # TODO: Replace with real article count
    total_feedback = 32      # TODO: Replace with real feedback count

    return render_template('dashboard.html',
                           total_users=total_users,
                           total_articles=total_articles,
                           total_feedback=total_feedback)

@admin_bp.route('/admin/articles')
def admin_articles():
    return "<h3>Articles panel coming soon...</h3>"

@admin_bp.route('/admin/feedback')
def admin_feedback():
    return "<h3>Feedback panel coming soon...</h3>"

@admin_bp.route('/admin/settings')
def admin_settings():
    return "<h3>Settings panel coming soon...</h3>"
