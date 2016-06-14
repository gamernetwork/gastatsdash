import sys
sys.path.append('/home/faye/src/gastatsdash/')


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from render import get_environment

import config
from Statsdash.Youtube.aggregate_data import YoutubeData
from Statsdash.GA.aggregate_data import AnalyticsData
import Statsdash.utilities as utils

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
        if self.frequency == 'daily':
        	subject = ' '.join([self.subject, self.period.end_date.strftime("%a %d %b %Y")])
        elif self.frequency  == 'weekly':
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
        msg['Subject'] = self.subject
        msg['From'] = config.SEND_FROM
        msg['To'] = self.recipients
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

    def generate_html(self):

        if self.frequency != "MONTHLY":
            today = self.period.end_date
            first = datetime(today.year, today.month, 1).date()
            month_range = StatsRange("Month to date Aggregate", first, today)            
            to_month_data = AnalyticsData(self.sites, month_range, self.frequency)
            to_month_table = to_month_data.summary_table()
            
        summary_table = self.data.summary_table()    
        country_table = self.data.country_table()
        site_table = self.data.site_summary_table()
        article_table = self.data.article_table()
        traffic_table = self.data.traffic_source_table()
        referring_site_table = self.data.referring_sites_table()
        device_table = self.data.device_table()
        social_table = self.data.social_network_table()
        
        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            warning_sites = self.warning_sites,
            month_summary_table = to_month_table,
            summary_table=summary_table,
            geo_table=country_table,
            top_articles=article_table,
            traffic=traffic_table,	
            referrals=referring_site_table,
            device=device_table,
            social=social_table, 		
        )
        return html		
			
class AnalyticsSocialReport(Report):
    
    def __init__(self, sites, start, end, recipients, frequency, subject):
        super(AnalyticsSocialReport, self).__init__(sites, start, end, recipients, frequency, subject)
        self.sites = sites
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject		
        self.data = AnalyticsData(self.sites, self.period, self.frequency)    
        self.warning_sites = []
		
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
                
    def generate_html(self):
        #TO DO 
        pass
		
		
if __name__ == '__main__':
    from datetime import datetime, timedelta, date
    import Statsdash.Youtube.config as yt_config
    
    period = utils.StatsRange("period", date(2016, 04, 01), date(2016, 04, 30))
    
    yt = YoutubeReport(yt_config.CHANNELS.keys(), period, ["test"], "MONTHLY", "Gamer Network Video Report for")
    html = yt.generate_html()
		
		
		
		
		
