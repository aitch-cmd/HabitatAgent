import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


class EmailService:
    """
    A reusable email service for sending plain text emails.
    Designed for MCP servers and agent delegation.
    """

    def __init__(self):
        load_dotenv()

        self.sender_email = os.getenv("SENDER_EMAIL")
        self.app_password = os.getenv("EMAIL_APP_PASSWORD")

        if not self.sender_email:
            raise ValueError("SENDER_EMAIL is missing in .env")
        if not self.app_password:
            raise ValueError("EMAIL_APP_PASSWORD is missing in .env")

        self.smtp_server = "smtp.gmail.com"
        self.port = 587  

    def send_email(self, receiver_email: str, subject: str, message: str) -> str:
        """
        Sends an email to the specified receiver.

        Args:
            receiver_email: Target email address
            subject: Email subject
            message: Body content

        Returns:
            str: Success message
        """

        # MIME wrapper
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        # Connect and send
        try:
            server = smtplib.SMTP(self.smtp_server, self.port)
            server.starttls()
            server.login(self.sender_email, self.app_password)
            server.sendmail(self.sender_email, receiver_email, msg.as_string())
            server.quit()

            return f"Email successfully sent to {receiver_email}"

        except Exception as e:
            return f"Failed to send email: {str(e)}"
