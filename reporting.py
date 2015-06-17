import re, pprint
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta
from collections import OrderedDict

import config
from analytics import get_analytics, StatsRange
from renderer import render_template

analytics = get_analytics()

class Emailer(object):
    """
    Responsible for sending HTMl emails to one or more recipients.
    """
    
    def __init__(self):
        #self.smtp_address = 'localhost:1055'
        self.smtp_address = config.SMTP_ADDRESS
        self.sender_email = config.SEND_FROM

    def get_smtp(self):
        sender = smtplib.SMTP(self.smtp_address)
        return sender

    def send_email(self, recipients, subject, html):
        """
        Send an html email to a list of recipients.
        """
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf8')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients)
        text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        html_part = MIMEText(html.encode('utf-8'), 'html')
        msg.attach(text_part)
        msg.attach(html_part)
        sender = self.get_smtp()
        sender.sendmail(self.sender_email, recipients, msg.as_string())
        sender.quit()


class Report(object):
    """
    Responsible for marshalling data from Analytics module, generating a rendered
    HTML report and sending this report to specified recipients.
    """
    template = ""

    def __init__(self, recipients, site, period):
        self.recipients = recipients
        self.site = site
        self.period = period
        self.emailer = Emailer()

    def get_site_gaid(self):
        return config.TABLES[self.site]

    def data_available(self):
        """
        Query GA to see if the data is available for this report.
        """
        return analytics.data_available_for_site(self.get_site_gaid(), 
            self.period.get_end())

    def get_subject(self):
        """
        Get the subject line for this report.
        """
        report_name_parts = re.findall('[A-Z][^A-Z]*', self.__class__.__name__)
        report_name = ' '.join(report_name_parts)
        subject = "%s - %s" % (report_name, self.period.get_start())
        return subject

    def generate_report(self):
        """
        Marshall the data needed and use it to render the HTML report.
        """
        raise NotImplementedError()

    def send_report(self):
        """
        Generate and send the report to the recipients.
        """
        html = self.generate_report()
        subject = self.get_subject()
        recipients = self.recipients
        self.emailer.send_email(recipients, subject, html)
        print "Sent '%s' Report for site %s" % (self.get_subject(), self.site)


class ArticleBreakdown(Report):
    template = "article_dash.html"

    def __init__(self, recipients, site, period, second_period, topic, extra_filters="", article_limit=10):
        super(ArticleBreakdown, self).__init__(recipients, site, period)
        self.second_period = second_period
        self.topic = topic
        self.extra_filters = extra_filters
        self.article_limit = article_limit

    def get_subject(self):
        subject = super(ArticleBreakdown, self).get_subject()
        if self.topic:
            subject += ' - Topic: %s' % self.topic
        return subject

    def get_article_breakdown_for_site(self, site_id):
        data = analytics.get_article_breakdown_two_periods(site_id, 
            self.period, self.second_period, extra_filters=self.extra_filters,
            min_pageviews=250)
        return data

    def generate_report(self):
        site_ga_id = config.TABLES[self.site]
        data = self.get_article_breakdown_for_site(site_ga_id)
        data = list(data.items())[:self.article_limit]
        report_html = render_template(self.template, {
            'data': data,
            'site': self.site,
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'topic': self.topic,
            'article_limit': self.article_limit,
        })
        return report_html


class NetworkArticleBreakdown(ArticleBreakdown):
    template = "article_dash.html"

    def __init__(self, recipients, site, period, second_period, topic, extra_filters="", article_limit=10):
        super(NetworkArticleBreakdown, self).__init__(
            recipients, site, period, 
            second_period, topic, extra_filters, article_limit
        )
        self.sites = site.split(',')

    def format_top_data(self, top_data):
        formatted = []
        for article in top_data:
            formatted.append((article['path'], article))
        return formatted

    def data_available(self):
        """
        Iterate through all sites and check that their data is available.
        """
        # TODO: move this up in to an AggregateReport mixin class which is aware
        #   of multiple sites
        for site in self.sites:
            site_ga_id = config.TABLES[site]
            site_data_available = analytics.data_available_for_site(site_ga_id, 
                self.period.get_end())
            if site_data_available == False:
                return False
        return True

    def generate_report(self):
        all_network_data = []
        for site in self.sites:
            site_ga_id = config.TABLES[site]
            data = self.get_article_breakdown_for_site(site_ga_id)
            all_network_data.extend(data.values())
        sorted_data = sorted(all_network_data, key=lambda article: article['pageviews'], reverse=True)
        top_network_data = list(sorted_data)[:self.article_limit]
        formatted_network_data = self.format_top_data(top_network_data)
        report_html = render_template(self.template, {
            'data': formatted_network_data,
            'site': "Gamer Network",
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'topic': self.topic,
            'article_limit': self.article_limit,
        })
        return report_html

if __name__ == '__main__':
    yesterday = date.today() - timedelta(days=1)
    yesterday_stats_range = StatsRange("Yesterday", yesterday, yesterday)
    day_before = yesterday - timedelta(days=1)
    day_before_stats_range = StatsRange("Day Before", day_before, day_before)
    article_breakdown = ArticleBreakdown(['foo@example.net'], 'vg247.com', yesterday_stats_range, day_before_stats_range, topic="E3", extra_filters="ga:dimension2=@e3", article_limit=10)
    data = article_breakdown.get_article_breakdown_for_site('ga:6872882')
