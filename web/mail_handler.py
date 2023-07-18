import logging
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

GMAIL_USER = os.getenv('GMAIL_USER', "trolley_user")
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD', "trolley_password")
DOCKER_ENV = os.getenv('DOCKER_ENV', False)

log_file_name = 'server.log'
if DOCKER_ENV:
    log_file_path = f'{os.getcwd()}/web/{log_file_name}'
else:
    log_file_path = f'{os.getcwd()}/{log_file_name}'

logger = logging.getLogger(__name__)

file_handler = logging.FileHandler(filename=log_file_path)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
handlers = [file_handler, stdout_handler]


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers
)


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
        logger.info(f'Sending an email to: {self.user_email} with')
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(GMAIL_USER, GMAIL_PASSWORD)
                smtp.sendmail(GMAIL_USER, self.user_email, em.as_string())
        except Exception as e:
            logger.error(f'Error sending out an email with {e} error')

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
