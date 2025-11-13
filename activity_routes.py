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
            url TEXT,
            ip_address TEXT,
            timestamp TEXT,
            duration INTEGER
        )
    """)

    cursor.execute("""
        INSERT INTO user_activity (user_id, activity_type, details, image_url, url, ip_address, timestamp, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        activity_type,
        details,
        image_url,
        details if activity_type == "view_article" else None,
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

    log_activity(session['user_id'], 'view_article', details=details, image_url=image, duration=data.get('duration'))

    return jsonify({'success': True})

# --- Route for activity page ---
@activity_bp.route('/my_activity')
def my_activity():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect("newsphere.db")
    cursor = conn.cursor()

    # Fetch all activities
    cursor.execute("""
        SELECT activity_type, details, timestamp
        FROM user_activity
        WHERE user_id=?
        ORDER BY id DESC
    """, (user_id,))
    all_activities = cursor.fetchall()
    conn.close()

    activities = []
    for activity in all_activities:
        activities.append({
            "type": activity[0],
            "details": activity[1],
            "timestamp": format_datetime(activity[2])
        })

    return render_template(
        "my_activity.html",
        username=session.get('username'),
        activities=activities
    )
