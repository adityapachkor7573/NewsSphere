from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3

app = Flask(__name__, template_folder='frontend', static_folder='static')
app.secret_key = 'your_secret_key_here' 

DB_PATH = 'users.db'

# --- Admin Login ---
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Admin credentials
        if username == 'admin' and password == 'admin':
            session['admin_logged_in'] = True
            return redirect(url_for('view_users'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')

    return render_template('admin_login.html')


# --- Admin Panel  ---
@app.route('/')
def view_users():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('view-users.html', users=users)


# --- Logout ---
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


if __name__ == '__main__':
    app.run(debug=True)
