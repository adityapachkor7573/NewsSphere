from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
import sqlite3
from datetime import datetime

activity_bp = Blueprint("activity", __name__, template_folder="frontend")

# --- Helper functions ---
def format_datetime(dt_str):
    if not dt_str:
        return None
    try:
        dt_str = dt_str.split(".")[0]  # Handle microseconds
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %I:%M %p")
    except Exception:
        return dt_str

def log_activity(user_id, activity_type, details="", image_url=None, duration=None):
    conn = sqlite3.connect("newsphere.db")
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            activity_type TEXT,
            details TEXT,
            image_url TEXT,
            ip_address TEXT,
            timestamp TEXT,
            duration INTEGER
        )
    """)

    cursor.execute("""
        INSERT INTO user_activity (user_id, activity_type, details, image_url, ip_address, timestamp, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        activity_type,
        details,
        image_url,
        request.remote_addr,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        duration
    ))
    conn.commit()
    conn.close()

# --- Route to log article view ---
@activity_bp.route('/log-article-view', methods=['POST'])
def log_article_view():
    if 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    data = request.get_json()
    title = data.get('title')
    url = data.get('url')
    image = data.get('image')

    # Store only the title in `details` for display
    details = title  

    # Log article view including URL and image in separate columns
    log_activity(session['user_id'], 'view_article', details=details, duration=data.get('duration'))

    return jsonify({'success': True})


# --- Route for activity page ---
@activity_bp.route('/my_activity')
def my_activity():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect("newsphere.db")
    cursor = conn.cursor()

    # Last login
    cursor.execute("""
        SELECT timestamp FROM user_activity
        WHERE user_id=? AND activity_type='login'
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    last_login = cursor.fetchone()

    # Last article viewed
    cursor.execute("""
        SELECT details, timestamp, duration, image_url FROM user_activity
        WHERE user_id=? AND activity_type='view_article'
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    last_article = cursor.fetchone()

    # All article views
    cursor.execute("""
        SELECT details, timestamp, duration, image_url FROM user_activity
        WHERE user_id=? AND activity_type='view_article'
        ORDER BY id DESC
    """, (user_id,))
    all_articles = cursor.fetchall()

    conn.close()

    # Format timestamps
    last_login = format_datetime(last_login[0]) if last_login else None
    last_article = (
        last_article[0],
        format_datetime(last_article[1]),
        last_article[2] or 0,
        last_article[3]
    ) if last_article else None
    all_articles = [
        (a[0], format_datetime(a[1]), a[2] or 0, a[3]) for a in all_articles
    ]

    return render_template(
        "my_activity.html",
        username=session.get('username'),
        last_login=last_login,
        last_article=last_article,
        all_articles=all_articles
    )
