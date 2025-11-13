from flask import Blueprint, request, jsonify
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

approve_bp = Blueprint('approve', __name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "adityapachkor90@gmail.com"
SMTP_PASS = "odre anaz ctqk txhc"  # App password

@approve_bp.route('/approve_issue', methods=['POST'])
def approve_issue():
    try:
        data = request.get_json()
        issue_id = data.get("issue_id")
        user_email = data.get("email")

        if not issue_id or not user_email:
            return jsonify({"success": False, "message": "Missing issue ID or email."})

        conn = sqlite3.connect("Data/newssphere.db", check_same_thread=False)
        cursor = conn.cursor()

        # Fetch issue
        cursor.execute("SELECT issue FROM reported_issues WHERE id = ?", (issue_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "message": "Issue not found."})

        issue_text = row[0]

        # Create HTML email
        msg = MIMEMultipart("alternative")
        msg['Subject'] = "Your Reported Issue Has Been Resolved"
        msg['From'] = SMTP_USER
        msg['To'] = user_email

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <table style="max-width: 600px; margin: auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <tr style="background-color: #007bff; color: white;">
                    <td style="padding: 20px; text-align: center;">
                        <img src="https://i.imgur.com/yourlogo.png" alt="NewsSphere Logo" style="max-width: 120px; margin-bottom: 10px;">
                        <h2>NewsSphere</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 20px; color: #333;">
                        <p>Hello,</p>
                        <p>Your reported issue has been resolved:</p>
                        <blockquote style="background: #f8f8f8; border-left: 4px solid #007bff; padding: 10px; margin: 15px 0;">{issue_text}</blockquote>
                        <p>You can check our website for updates.</p>
                        <p>Thank you,<br><strong>NewsSphere Team</strong></p>
                    </td>
                </tr>
                <tr style="background-color: #f1f1f1; text-align: center; padding: 10px;">
                    <td style="padding: 10px; font-size: 12px; color: #555;">
                        &copy; 2025 NewsSphere. All rights reserved.
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        # Update status in DB
        cursor.execute("UPDATE reported_issues SET status = 'Completed' WHERE id = ?", (issue_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print(e)
        return jsonify({"success": False, "message": str(e)})
