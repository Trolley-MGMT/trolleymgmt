import os
import smtplib
import ssl
from email.message import EmailMessage

GMAIL_USER = os.getenv('GMAIL_USER', "trolley_user")
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', "trolley_password")


class MailSender:
    def __init__(self, user_email: str = "", confirm_url: str = ""):
        self.user_email = user_email
        self.confirm_url = confirm_url

    def send_mail(self):
        subject = "Welcome to Trolley"
        body = f"Welcome to Trolley! to finish the registration please click on: {self.confirm_url}"

        em = EmailMessage()
        em['From'] = GMAIL_USER
        em['To'] = self.user_email
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_USER, self.user_email, em.as_string())
