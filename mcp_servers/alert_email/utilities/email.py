import os
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class EmailService:
    """
    A reusable email service for sending emails via SendGrid.
    Designed for MCP servers and agent delegation.
    """

    def __init__(self):
        load_dotenv()

        self.sender_email = os.getenv("SENDER_EMAIL")
        self.api_key = os.getenv("SENDGRID_API_KEY")

        if not self.sender_email:
            raise ValueError("SENDER_EMAIL is missing in .env")
        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY is missing in .env")

        self.client = SendGridAPIClient(self.api_key)

    def send_email(self, receiver_email: str, subject: str, message: str) -> str:
        """
        Sends an email to the specified receiver using SendGrid.

        Args:
            receiver_email: Target email address
            subject: Email subject
            message: Body content (supports HTML)

        Returns:
            str: Success message with status code
        """
        try:
            mail = Mail(
                from_email=self.sender_email,
                to_emails=receiver_email,
                subject=subject,
                html_content=f"<p>{message}</p>"
            )

            response = self.client.send(mail)

            return f"Email successfully sent to {receiver_email} (status: {response.status_code})"

        except Exception as e:
            error_msg = getattr(e, 'message', str(e))
            return f"Failed to send email: {error_msg}"
