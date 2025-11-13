from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3, os
from datetime import datetime

# Blueprint for reported issues
reported_issues_bp = Blueprint("reported_issues", __name__)

# ✅ Use same database file as your main app
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")


# ---------- Database Helper ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- Ensure Table Exists ----------
def init_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reported_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            issue TEXT NOT NULL,
            reply TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# ---------- Save New Report (Called from Chatbot) ----------
@reported_issues_bp.route("/api/report_issue", methods=["POST"])
def report_issue_api():
    data = request.get_json()
    email = data.get("email")
    issue = data.get("issue")

    if not email or not issue:
        return jsonify({"success": False, "message": "Email and issue are required."})

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO reported_issues (email, issue, status) VALUES (?, ?, 'Pending')",
            (email, issue),
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "✅ Report sent successfully!"})
    except Exception as e:
        print("❌ Error saving report:", e)
        return jsonify({"success": False, "message": "⚠️ Failed to save issue."})


# ---------- Admin Panel: View All Issues ----------
@reported_issues_bp.route("/admin/reported_issues")
def admin_issues():
    conn = get_db_connection()
    issues = conn.execute("SELECT * FROM reported_issues ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin_reported_issues.html", issues=issues)


# ---------- Admin: Reply to Issue ----------
@reported_issues_bp.route("/admin/reply_issue/<int:issue_id>", methods=["POST"])
def reply_issue(issue_id):
    reply_text = request.form.get("reply")

    conn = get_db_connection()
    conn.execute(
        "UPDATE reported_issues SET reply = ?, status = 'Resolved' WHERE id = ?",
        (reply_text, issue_id),
    )
    conn.commit()
    conn.close()

    flash("✅ Reply sent successfully!", "success")
    return redirect(url_for("reported_issues.admin_issues"))


# ---------- Initialize Table on Import ----------
init_table()
