from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from render import get_environment
import smtplib

import config
from Statsdash.Youtube.aggregate_data import YoutubeData
from Statsdash.GA.aggregate_data import AnalyticsData
import Statsdash.utilities as utils
import Statsdash.GA.config as ga_config

class Report(object):
    #template = "Templates/base.html"
    """
    Report object
    Gathers data from analytics, renders and sends as an email
    """
    def __init__(self, sites, period, recipients, frequency, subject):
        self.sites = sites
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject
        
        self.env = get_environment()
        self.template = self.env.get_template("base.html")
        
    def get_subject(self):
        """
        Return the subject of the email that includes the dates for this period
        """
        if self.frequency == 'DAILY' or self.frequency == "WOW_DAILY":
        	subject = ' '.join([self.subject, self.period.end_date.strftime("%a %d %b %Y")])
        elif self.frequency  == 'WEEKLY':
        	weekly_date = self.period.start_date.strftime("%a %d %b %Y") + ' - ' + self.period.end_date.strftime("%a %d %b %Y")
        	subject = ' '.join([self.subject, weekly_date])
        elif self.frequency == 'MONTHLY':
        	subject = ' '.join([self.subject, self.period.start_date.strftime('%B %Y')])
        
        return subject
		
    def get_freq_label(self):
        """
        Returns label for the period of change 
        E.g. where frequency == "monthly", label == "MoM"
        """
        first_letter = self.frequency[0].upper()
        label = first_letter + "o" + first_letter
        return label
    

    def generate_html(self):
        """
        Get formatted data and render to template
        """
        raise NotImplementedError()       

    def send_email(self, html):
        """
        Send html email using config parameters
        """
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf8')
        msg['Subject'] = self.get_subject()
        msg['From'] = config.SEND_FROM
        msg['To'] = ', '.join(self.recipients)
        text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        html_part = MIMEText(html.encode("utf-8"), 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        sender = smtplib.SMTP(config.SMTP_ADDRESS)
        sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
        sender.quit()


class YoutubeReport(Report):
    
    def __init__(self, channels, period, recipients, frequency, subject):
        super(YoutubeReport, self).__init__(channels, period, recipients, frequency, subject)
        self.channels = channels
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject
        self.data = YoutubeData(self.channels, self.period, self.frequency)
        self.template = self.env.get_template("Youtube/base.html")
        #check = self.data.check_available_data()
        #if not check['result']:
        	#raise Exception("Data not available for %s" % check['channel'])


    def generate_html(self):   	
        tableone = self.data.channel_summary_table()
        tabletwo = self.data.channel_stats_table()
        tablethree = self.data.country_table()
        tablefour = self.data.video_table()
        tablefive = self.data.traffic_source_table()
        
        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            report_span = self.frequency,
            summary_table=tableone,
            stats_table=tabletwo,
            geo_table=tablethree,
            top_vids=tablefour,
            traffic=tablefive,	
        )
        
        return html
		
    def check_data_availability(self, override=False):
        """
        incomplete
        - could this be in main report
        - does it need override or in scheduler should it only be called if override is false? 
        - is there a better way than a function to call a function??
        """
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            if override:
                self.warning_sites = check["channel"]
                return True
            else:
                return False
		    

class AnalyticsCoreReport(Report):
    
    def __init__(self, sites, period, recipients, frequency, subject):
        super(AnalyticsCoreReport, self).__init__(sites, period, recipients, frequency, subject)
        self.sites = sites
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject
        self.data = AnalyticsData(self.sites, self.period, self.frequency)
        self.warning_sites = []
        self.template = self.env.get_template("GA/base.html")

    def check_data_availability(self, override=False):
        """
        incomplete
        - could this be in main report
        - does it need override or in scheduler should it only be called if override is false? 
        - is there a better way than a function to call a function??
        """
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            if override:
                self.warning_sites = check["sites"]
                return True
            else:
                return False
                
                
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        #TO DO: make this a check against total number of sites 
        elif len(self.sites) == len(ga_config.TABLES.keys()):
            return "Gamer Network"
    

    def generate_html(self):
        
        to_month_table = None
        network_summary_table = None
        network_month_summary_table = None
        

        if self.frequency != "MONTHLY":
            today = self.period.end_date
            first = datetime(today.year, today.month, 1).date()
            month_range = utils.StatsRange("Month to date Aggregate", first, today)            
            to_month_data = AnalyticsData(self.sites, month_range, self.frequency)
            to_month_table = to_month_data.summary_table()
        if self.get_site() != "Gamer Network":
            network_data = AnalyticsData(ga_config.TABLES.keys(), self.period, self.frequency)
            network_summary_table = network_data.summary_table()
            if self.frequency != "MONTHLY":
                network_month_data = AnalyticsData(ga_config.TABLES.keys(), month_range, self.frequency)
                network_month_summary_table = network_month_data.summary_table()
            
        summary_table = self.data.summary_table()    
        print "done summary table"
        country_table = self.data.country_table()
        print "done country table"
        site_table = self.data.site_summary_table()
        print "done site summary table"
        article_table = self.data.article_table()
        print "done article table"
        traffic_table = self.data.traffic_source_table()
        print "done traffic table"
        referring_site_table = self.data.referring_sites_table()
        print "done referral table"
        device_table = self.data.device_table()
        print "done device table"
        social_table = self.data.social_network_table()
        print "done social table"
        
        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            site = self.get_site(),
            report_span = self.frequency,
            warning_sites = self.warning_sites,
            month_summary_table = to_month_table,
            network_summary_table = network_summary_table,
            network_month_summary_table = network_month_summary_table,
            summary_table=summary_table,
            geo_table=country_table,
            site_summary=site_table,
            top_articles=article_table,
            traffic_table=traffic_table,	
            referrals=referring_site_table,
            device_table=device_table,
            social_table=social_table, 		
        )
        return html		
			
class AnalyticsSocialReport(Report):
    
    def __init__(self, sites, period, recipients, frequency, subject):
        super(AnalyticsSocialReport, self).__init__(sites, period, recipients, frequency, subject)
        self.sites = sites
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject		
        self.data = AnalyticsData(self.sites, self.period, self.frequency)    
        self.warning_sites = []
        self.template = self.env.get_template("GA/social_report.html")
		
    def check_data_availability(self, override=False):
        """
        incomplete
        - could this be in main report
        - does it need override or in scheduler should it only be called if override is false? 
        - is there a better way than a function to call a function??
        """
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            if override:
                self.warning_sites = check["sites"]
                return True
            else:
                return False	
                
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        #TO DO: make this a check against total number of sites 
        elif len(self.sites) == len(ga_config.TABLES.keys()):
            return "Gamer Network"
    	
                
    def generate_html(self):
        #TO DO 
        
        summary_table = self.data.summary_table()
        print "summary table done"
        network_data = AnalyticsData(ga_config.TABLES.keys(), self.period, self.frequency)
        network_summary_table = network_data.summary_table()
        print "network summary table done"
        
        social_table = self.data.social_network_table()
        print "social network table done"
        #article_table = self.data.article_table()
        #print "article table done"
        #image
        
        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            site = self.get_site(),
            report_span = self.frequency,
            warning_sites = self.warning_sites,
            network_summary_table = network_summary_table,
            summary_table=summary_table,
            #top_articles=article_table,
            social_table=social_table, 		
        )
        return html		

		
		
		
		
