def send_email(self, html, subject, send_from, send_to):
    # TODO use mailcatcher smtp.
    """
    Send html email using config parameters
    """
    pass
    # html = transform(html)  # inline css using premailer
    # msg = MIMEMultipart('alternative')
    # msg.set_charset('utf8')
    # msg['Subject'] = self.get_subject()
    # msg['From'] = config.SEND_FROM
    # msg['To'] = ', '.join(self.recipients)

    # NOTE disabled for now
    # text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
    # html_part = MIMEText(html.encode("utf-8"), 'html')
    #
    # if self.imgdata:
    #     img_part = MIMEImage(self.imgdata, 'png')
    #     img_part.add_header('Content-ID', '<graph>')
    #     msg.attach(img_part)
    #
    # msg.attach(text_part)
    # msg.attach(html_part)
    #
    # sender = smtplib.SMTP(config.SMTP_ADDRESS)
    # sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
    #
    # sender.quit()
