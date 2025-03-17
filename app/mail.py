from flask_mail import Message
from app import mail


def send_email(subject, recipients, text_body):
    msg = Message(subject, recipients=recipients, body=text_body)
    mail.send(msg)
    return "Письмо отправлено!"
