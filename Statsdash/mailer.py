import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from premailer import transform

from Statsdash import config

smtp_address = config.SMTP_ADDRESS


def send_email(html, text, subject, send_from, recipients, img_data=None):
    """
    Send email to `conf.SMTP_ADDRESS`.

    Args:
        * `html` - `str` - HTML to be included in the email.
        * `text` - `str` - Plain text to be included in the email.
        * `subject` - `str` - Subject line of the email.
        * `send_from` - `str` - Email address to appear as the sender.
        * `recipients` - `list` - Recipient email addresses.
        * `img_data` - `image`
    """
    msg = MIMEMultipart('alternative')
    msg.set_charset('utf8')
    msg['Subject'] = subject
    msg['From'] = send_from
    msg['To'] = ', '.join(recipients)

    if html:
        html = transform(html)  # inline css using premailer
        html_part = MIMEText(html, 'html')
        msg.attach(html_part)

    text_part = MIMEText(text, 'plain')
    msg.attach(text_part)

    if img_data:
        img_part = MIMEImage(img_data, 'png')
        img_part.add_header('Content-ID', '<graph>')
        msg.attach(img_part)

    sender = smtplib.SMTP(smtp_address)
    sender.sendmail(send_from, recipients, msg.as_string())

    sender.quit()
