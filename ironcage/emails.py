from django.conf import settings
from django.core.mail import get_connection, EmailMultiAlternatives


def send_mail(subject, message, to_addr):
    connection = get_connection()

    mail = EmailMultiAlternatives(
        subject,
        message,
        settings.EMAIL_FROM_ADDR,
        [to_addr],
        reply_to=[settings.EMAIL_REPLY_TO_ADDR],
        connection=connection
    )

    return mail.send()


def send_mail_with_attachment(subject, message, to_addr, attachments):
    connection = get_connection()

    mail = EmailMultiAlternatives(
        subject,
        message,
        settings.EMAIL_FROM_ADDR,
        [to_addr],
        reply_to=[settings.EMAIL_REPLY_TO_ADDR],
        connection=connection,
        attachments=attachments,
    )

    return mail.send()
