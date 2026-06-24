import os
import sqlite3
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='templates', static_folder='static')

DB_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.db')

def load_env():
    """Loads configuration variables from a local .env file if it exists."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

# Load environments variables
load_env()

# SMTP & Email Configurations
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', '').replace(' ', '')  # Google App Password (strips spaces)
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', 'gowrishankarponnusamyed1304@gmail.com')

def init_db():
    """Initializes the SQLite database and creates the messages table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

def send_email_notification(name, email, subject, message):
    """Sends a notification email for new contact form submissions. Fails gracefully."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("[WARNING] Email notifications are disabled because SENDER_EMAIL or SENDER_PASSWORD is not set in .env")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"Portfolio Contact: {subject}"

        body_content = f"""
        Hello Gowrishankar,

        You have received a new contact message from your portfolio website!

        Sender Details:
        - Name: {name}
        - Email: {email}
        - Subject: {subject}
        - Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Message:
        ----------------------------------------
        {message}
        ----------------------------------------

        This is an automated notification from your portfolio web application.
        """
        msg.attach(MIMEText(body_content, 'plain'))

        # Connect to SMTP server with TLS
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"[INFO] Email notification successfully sent to {RECEIVER_EMAIL}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email notification: {e}")
        return False

@app.route('/')
def home():
    """Renders the main portfolio page."""
    return render_template('index.html')

@app.route('/api/contact', methods=['POST'])
def contact_api():
    """Endpoint for receiving contact form submissions."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided.'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        
        # Simple validation
        if not all([name, email, subject, message]):
            return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
            
        # Store message in DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (name, email, subject, message))
        conn.commit()
        conn.close()
        
        # Trigger email notification (runs within try/except inside the function to avoid breaking form submission)
        send_email_notification(name, email, subject, message)
        
        return jsonify({
            'status': 'success',
            'message': 'Thank you! Your message has been saved in the SQLite database.'
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/messages')
def admin_messages():
    """Simple admin route to view contact submissions."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, subject, message, timestamp FROM messages ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Build a beautiful, styled dark-themed dashboard to view messages
        messages_html = ""
        for row in rows:
            messages_html += f"""
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed rgba(255, 255, 255, 0.08); padding-bottom: 10px; margin-bottom: 10px;">
                    <strong style="color: #00f2fe; font-size: 1.15rem;">{row[1]}</strong>
                    <span style="color: #6b7280; font-family: monospace; font-size: 0.9rem;">{row[5]}</span>
                </div>
                <div style="margin-bottom: 10px; font-size: 0.95rem;">
                    <span style="color: #9ca3af;">Email: </span><a href="mailto:{row[2]}" style="color: #8a2be2; text-decoration: none;">{row[2]}</a><br>
                    <span style="color: #9ca3af;">Subject: </span><strong style="color: #f3f4f6;">{row[3]}</strong>
                </div>
                <div style="background: rgba(0, 0, 0, 0.2); border-radius: 4px; padding: 12px; color: #d1d5db; font-size: 0.95rem; white-space: pre-wrap;">{row[4]}</div>
            </div>
            """
            
        if not messages_html:
            messages_html = "<p style='color: #9ca3af; text-align: center; margin-top: 40px;'>No contact submissions found in database.</p>"
            
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin - Contact Submissions</title>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
            <style>
                body {{
                    background-color: #080c14;
                    color: #f3f4f6;
                    font-family: 'Outfit', sans-serif;
                    margin: 0;
                    padding: 40px 20px;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h1 {{
                    font-size: 2.2rem;
                    margin-bottom: 30px;
                    background: linear-gradient(135deg, #8a2be2, #00f2fe);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    border-bottom: 2px solid rgba(255,255,255,0.08);
                    padding-bottom: 15px;
                }}
                .back-btn {{
                    display: inline-block;
                    margin-bottom: 20px;
                    color: #00f2fe;
                    text-decoration: none;
                    font-weight: 600;
                }}
                .back-btn:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">&larr; Back to Portfolio</a>
                <h1>Database Messages Dashboard</h1>
                {messages_html}
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"<h3>Error retrieving messages: {str(e)}</h3>", 500

if __name__ == '__main__':
    # Listen on all interfaces so it's accessible from host machine
    app.run(host='0.0.0.0', port=5000, debug=True)
