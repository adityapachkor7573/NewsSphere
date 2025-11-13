from flask import Flask, render_template_string, request
import sqlite3
import os

app = Flask(__name__)

# Path to your SQLite .db file
DB_PATH = "Users.db"  # 👈 change to your .db file name

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SQLite DB Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f4f4f9; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; background: white; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #e0e0e0; }
        a { text-decoration: none; color: #007bff; }
        a:hover { text-decoration: underline; }
        .container { max-width: 1200px; margin: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 SQLite Database Viewer</h1>

        {% if tables %}
            <h2>Tables:</h2>
            <ul>
            {% for table in tables %}
                <li><a href="/view?table={{table}}">{{table}}</a></li>
            {% endfor %}
            </ul>
        {% endif %}

        {% if table_data %}
            <h2>Table: {{ current_table }}</h2>
            <table>
                <thead>
                    <tr>
                        {% for header in headers %}
                            <th>{{ header }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_data %}
                        <tr>
                            {% for cell in row %}
                                <td>{{ cell }}</td>
                            {% endfor %}
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
            <p><a href="/">← Back to Tables</a></p>
        {% endif %}
    </div>
</body>
</html>
"""

def get_tables():
    """Fetch all table names from the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name):
    """Fetch all data and headers from a table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    conn.close()
    return headers, rows

@app.route('/')
def home():
    if not os.path.exists(DB_PATH):
        return f"<h2 style='color:red;'>Error: Database file '{DB_PATH}' not found!</h2>"
    tables = get_tables()
    return render_template_string(HTML_TEMPLATE, tables=tables)

@app.route('/view')
def view_table():
    table_name = request.args.get('table')
    headers, data = get_table_data(table_name)
    return render_template_string(HTML_TEMPLATE, table_data=data, headers=headers, current_table=table_name, tables=None)

if __name__ == '__main__':
    app.run(debug=True)
