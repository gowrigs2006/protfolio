import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()

SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', '').replace(' ', '')
RECEIVER_EMAIL = os.environ.get('RECEIVER_EMAIL', '')

print("--- PORTFOLIO EMAIL DIAGNOSTIC SYSTEM ---")
print(f"Connecting from: {SENDER_EMAIL}")
print(f"Sending alert to: {RECEIVER_EMAIL}")
print(f"Mail Server:     {SMTP_SERVER}:{SMTP_PORT}")
print("-----------------------------------------")

if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("❌ ERROR: SENDER_EMAIL or SENDER_PASSWORD is empty in your .env file.")
    exit(1)

try:
    print("1. Connecting to Gmail mail server...")
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.ehlo()
    
    print("2. Starting secure encryption (TLS)...")
    server.starttls()
    server.ehlo()
    
    print("3. Logging in with your App Password...")
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    
    print("4. Login success! Sending test email...")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "Portfolio SMTP Success Verification"
    msg.attach(MIMEText("Success! Your portfolio website email notifications are now fully working.", 'plain'))
    
    server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    server.quit()
    print("\n[SUCCESS] Test email sent successfully! Please check your inbox.")
except Exception as e:
    print(f"\n[FAIL] Gmail SMTP rejected login. Details:\n{str(e)}")
