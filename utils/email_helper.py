import os
import smtplib
from email.mime.text import MIMEText

def send_email(to, subject, body):
    smtp_server = os.getenv("MAIL_SERVER")
    smtp_port = int(os.getenv("MAIL_PORT"))
    smtp_user = os.getenv("MAIL_USERNAME")
    smtp_password = os.getenv("MAIL_PASSWORD")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, msg.as_string())

        print("Email sent successfully!")

    except Exception as e:
        print("Email failed:", e)
