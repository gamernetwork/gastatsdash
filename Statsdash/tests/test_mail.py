import unittest

from Statsdash.mailer import send_email


# TODO this needs to be automated somehow.
class TestMail(unittest.TestCase):

    def test_email_hits_mailcatcher(self):
        html = '<div>hi</div>'
        text = 'Some text'
        subject = 'Weekly Statsdash'
        send_from = 'The test suite'
        recipients = ['ness@fakesite.net', 'lucas@fakesite.net']
        send_email(html, text, subject, send_from, recipients)
