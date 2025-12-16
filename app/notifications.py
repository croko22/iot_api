import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

def send_email_alert(subject: str, body: str):
    """
    Send an email alert using Mailtrap settings.
    """
    settings = get_settings()
    
    sender = settings.MAIL_FROM
    receiver = settings.MAIL_TO
    
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receiver
    
    message.attach(MIMEText(body, "plain"))
    
    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            # Mailtrap often requires starttls, but sometimes it depends on the port. 
            # Port 2525 usually works with starttls.
            # Only starttls if not using SSL port (465 usually SSL, 587/2525 usually TLS)
            # The user code sample showed starttls.
            server.starttls() 
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.sendmail(sender, receiver, message.as_string())
        logger.info(f"Email sent successfully to {receiver}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
