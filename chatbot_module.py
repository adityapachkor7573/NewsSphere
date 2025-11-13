from flask import Blueprint, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import os, json, datetime, traceback, sqlite3

# ---------------------- Blueprint ----------------------
chatbot_bp = Blueprint("chatbot", __name__)

# ---------------------- Load Environment Variables ----------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# ---------------------- Chat Log ----------------------
os.makedirs("Data", exist_ok=True)
CHAT_LOG_PATH = "Data/ChatLog.json"

def load_chat_log():
    if not os.path.exists(CHAT_LOG_PATH):
        with open(CHAT_LOG_PATH, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(CHAT_LOG_PATH, "r") as f:
            return json.load(f)
    except:
        return []

def save_chat_log(messages):
    with open(CHAT_LOG_PATH, "w") as f:
        json.dump(messages, f, indent=4)

def clean_answer(answer):
    lines = [line.strip() for line in answer.split("\n") if line.strip()]
    return "\n".join(lines)

def time_info():
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %d %B %Y')} and time is {now.strftime('%H:%M:%S')}."

# ---------------------- DB Setup ----------------------
# ✅ Use the same DB file used by your admin panel
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

def init_db():
    """Initialize reported_issues table in users.db"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reported_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            issue TEXT NOT NULL,
            reply TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending',
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------- Report Issue Route ----------------------
@chatbot_bp.route("/report_issue", methods=["POST"])
def report_issue():
    """Handles issue report from chatbot"""
    data = request.get_json()
    email = data.get("email")
    issue = data.get("issue")

    if not email or not issue:
        return jsonify({"reply": "⚠️ Please provide both email and issue details."})

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reported_issues (email, issue, status)
            VALUES (?, ?, ?)
        """, (email, issue, "Pending"))
        conn.commit()
        conn.close()

        print(f"✅ Issue from {email} saved successfully in {DB_PATH}")
        return jsonify({"reply": "✅ Thank you! Your issue has been reported successfully. Our admin team will contact you soon."})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"⚠️ Failed to save issue: {str(e)}"})

# ---------------------- Chatbot AI Logic ----------------------
@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot_reply():
    """Handles general chatbot conversation"""
    user_input = request.json.get("message", "").strip().lower()
    if not user_input:
        return jsonify({"reply": "Please enter a message."})

    try:
        # --- Quick Replies ---
        quick_replies = {
            "latest news": "📰 Here are today's top headlines from NewsSphere! (Feature coming soon 🚀)",
            "contact support": "📩 You can reach us at support@newssphere.com or call +91-9876543210.",
            "about newssphere": "ℹ️ NewsSphere is your trusted AI-powered platform for unbiased, multi-source news.",
            "help": "💡 You can ask about news, contact info, or choose an option like 'report issue'."
        }

        if user_input in quick_replies:
            return jsonify({"reply": quick_replies[user_input]})

        # --- Detect Report Flow ---
        if "report issue" in user_input or "problem" in user_input or "bug" in user_input:
            return jsonify({"reply": "📝 Sure! Please enter your email address so we can contact you about the issue."})

        # --- AI Chat ---
        messages = load_chat_log()
        messages.append({"role": "user", "content": user_input})
        messages = messages[-15:]  # limit chat memory

        system_prompt = (
            f"You are NewsSphere Assistant, an AI chatbot for a news platform. "
            f"You can discuss news, answer queries, or assist users. "
            f"If a user wants to report an issue, guide them to provide their email and issue details. "
            f"Use this time info if needed: {time_info()}."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            max_tokens=500,
            temperature=0.5
        )

        reply = completion.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": reply})
        save_chat_log(messages)

        return jsonify({"reply": clean_answer(reply)})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"reply": f"⚠️ Error: {str(e)}"})


# ---------------------- Reset Chat ----------------------
@chatbot_bp.route("/chatbot/reset", methods=["POST"])
def reset_chat():
    """Resets chat history"""
    save_chat_log([])
    return jsonify({"reply": "Chat reset successfully."})
