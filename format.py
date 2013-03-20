#!/usr/bin/python

import sys
import json
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.template import Template, Context
import django.conf
django.conf.settings.configure()

msg = MIMEMultipart('alternative')
msg['Subject'] = "Daily Analytics summary"
me = "Mark Kennedy <mark@gamer-network.net>"
msg['From'] = me
you = "Mark Kennedy <mark@verynoisy.com>"
msg['To'] = you

part1 = MIMEText(html, 'html')

msg.attach(part1)
s = smtplib.SMTP('localhost')
s.sendmail(me, you, msg.as_string())

