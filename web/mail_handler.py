import os
import smtplib
import ssl
from email.message import EmailMessage

GMAIL_USER = os.getenv('GMAIL_USER', "trolley_user")
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', "trolley_password")


class MailSender:
    def __init__(self, user_email: str = "", confirmation_url: str = "",
                 invitation_url: str = "http://localhost/register"):
        self.user_email = user_email
        self.confirmation_url = confirmation_url
        self.invitation_url = invitation_url

    def send_confirmation_mail(self):
        subject = "Welcome to Trolley!"
        body = f"Welcome to Trolley!" \
               f"To finish the registration please click on: {self.confirmation_url}"

        em = EmailMessage()
        em['From'] = GMAIL_USER
        em['To'] = self.user_email
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_USER, self.user_email, em.as_string())

    def send_invitation_mail(self):
        subject = "You have been invited to Trolley!"
        body = f"Congratulations! You have been invited to use Trolley!" \
               f" To start the registration please click on: {self.invitation_url}"

        em = EmailMessage()
        em['From'] = GMAIL_USER
        em['To'] = self.user_email
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_USER, self.user_email, em.as_string())
