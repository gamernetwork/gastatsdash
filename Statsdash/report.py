from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import date, datetime, timedelta
from render import get_environment
import smtplib
from premailer import transform
import StringIO
import cStringIO
import urllib, base64
from Statsdash.config import LOGGING

import config
from Statsdash.Youtube.aggregate_data import YoutubeData
from Statsdash.GA.aggregate_data import AnalyticsData
import Statsdash.utilities as utils
import Statsdash.GA.config as ga_config
import logging, logging.config, logging.handlers

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

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
        html = transform(html) #inline css using premailer
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
        	
        logger.debug("Running youtube report")


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
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            logger.debug("Data not available for: %s" % check["channel"])
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
        self.imgdata = None
        
        if len(self.sites) == len(ga_config.TABLES.keys()):
            self.all_sites = True
        else:
            self.all_sites = False
        
        logger.debug("Running analytics core report")

    def check_data_availability(self, override=False):
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            logger.debug("Data not available for: %s" % check["site"])
            if override:
                self.warning_sites = check["site"]
                return True
            else:
                return False
                
                
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        elif len(self.sites) == len(ga_config.TABLES.keys()):
            return ga_config.ALL_SITES_NAME
    

    def generate_html(self):
        
        to_month_table = None
        num_days = None
        full_month_table = None
        network_summary_table = None
        network_month_summary_table = None
        device_img = None
        num_articles = 5
        today = self.period.end_date
        
        if self.frequency != "MONTHLY":
            num_articles = 1
            #today = self.period.end_date
            first = datetime(today.year, today.month, 1).date()
            month_range = utils.StatsRange("Month to date Aggregate", first, today)            
            to_month_data = AnalyticsData(self.sites, month_range, self.frequency)
            to_month_table = to_month_data.summary_table()
            
            last = utils.add_one_month((first-timedelta(days=1)))
            num_days = (last - self.period.end_date).days
            month_range = utils.StatsRange("Month to date Aggregate", first, last)           
            full_month_data = AnalyticsData(self.sites, month_range, self.frequency)
            full_month_table = full_month_data.summary_table()            
            
        elif self.frequency == "MONTHLY":

            month_stats_range = utils.list_of_months(today, 1)
        
            device = []  
            for month in month_stats_range:
                new_row = {}
                new_row["month"] = month.get_start()
                data = AnalyticsData(self.sites, month, "MONTHLY")
                new_row["data"] = data.device_table()
                new_row["summary"] = data.summary_table()
                device.append(new_row)
                
            self.imgdata = self.data.device_chart(device)


        if not self.all_sites:
            network_data = AnalyticsData(ga_config.TABLES.keys(), self.period, self.frequency)
            network_summary_table = network_data.summary_table()
            if self.frequency != "MONTHLY":
                network_month_data = AnalyticsData(ga_config.TABLES.keys(), month_range, self.frequency)
                network_month_summary_table = network_month_data.summary_table()
        
            
        summary_table = self.data.summary_table()    
        site_table = self.data.site_summary_table()
        country_table = self.data.country_table()
        article_table = self.data.article_table()
        traffic_table = self.data.traffic_source_table()
        referring_site_table = self.data.referring_sites_table(num_articles)
        device_table = self.data.device_table()
        social_table = self.data.social_network_table(num_articles)

        
        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            site = self.get_site(),
            all_sites = self.all_sites,
            report_span = self.frequency,
            warning_sites = self.warning_sites,
            month_summary_table = to_month_table,
            num_days = num_days,
            full_month_summary_table = full_month_table,
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
        
        
    def send_email(self, html):
        """
        Send html email using config parameters
        """
        html = transform(html) #inline css using premailer
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf8')
        msg['Subject'] = self.get_subject()
        msg['From'] = config.SEND_FROM
        msg['To'] = ', '.join(self.recipients)
        text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        html_part = MIMEText(html.encode("utf-8"), 'html')


        if self.imgdata:
            img_part = MIMEImage(self.imgdata, 'png')
            img_part.add_header('Content-ID', '<graph>')
            msg.attach(img_part)
                    
        msg.attach(text_part)
        msg.attach(html_part)
        
        sender = smtplib.SMTP(config.SMTP_ADDRESS)
        sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
    
        sender.quit()
        
        
        
			
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
        self.imgdata = None
        
        logger.debug("Running analytics social report")
        
        if len(self.sites) == len(ga_config.TABLES.keys()):
            self.all_sites = True
        else:
            self.all_sites = False
		
    def check_data_availability(self, override=False):
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            logger.debug("Data not available for: %s" % check["site"])
            if override:
                self.warning_sites = check["site"]
                return True
            else:
                return False	
                
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        elif len(self.sites) == len(ga_config.TABLES.keys()):
            return ga_config.ALL_SITES_NAME
    	
                
    def generate_html(self):
        #TO DO 
        
        summary_table = self.data.summary_table()
        network_data = AnalyticsData(ga_config.TABLES.keys(), self.period, self.frequency)
        network_summary_table = network_data.summary_table()
        
        social_table = self.data.social_network_table(10)
        self.imgdata = self.data.social_chart()

        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            site = self.get_site(),
            all_sites = self.all_sites,
            report_span = self.frequency,
            warning_sites = self.warning_sites,
            network_summary_table = network_summary_table,
            summary_table=summary_table,
            #top_articles=article_table,
            social_table=social_table, 		
        )
        return html		

    def send_email(self, html):
        """
        Send html email using config parameters
        """
        html = transform(html) #inline css using premailer
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf8')
        msg['Subject'] = self.get_subject()
        msg['From'] = config.SEND_FROM
        msg['To'] = ', '.join(self.recipients)
        text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        html_part = MIMEText(html.encode("utf-8"), 'html')


        if self.imgdata:
            img_part = MIMEImage(self.imgdata, 'png')
            img_part.add_header('Content-ID', '<graph>')
            msg.attach(img_part)
                    
        msg.attach(text_part)
        msg.attach(html_part)
        
        sender = smtplib.SMTP(config.SMTP_ADDRESS)
        sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
    
        sender.quit()



class AnalyticsYearSocialReport(Report):
    def __init__(self, sites, period, recipients, frequency, subject):
        super(AnalyticsYearSocialReport, self).__init__(sites, period, recipients, frequency, subject)
        self.sites = sites
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject		 
        self.data = AnalyticsData(self.sites, self.period, self.frequency)    
        self.warning_sites = []
        self.template = self.env.get_template("GA/year_social_report.html")
        
        logger.debug("Running analytics top social network report for the year")      

        if len(self.sites) == len(ga_config.TABLES.keys()):
            self.all_sites = True
        else:
            self.all_sites = False

    def get_subject(self):
        """
        Return the subject of the email that includes the dates for this period
        """
        start_month = date(self.period.start_date.year-1, self.period.start_date.month, 1)
        dates = start_month.strftime("%B %Y") + " - " + self.period.start_date.strftime('%B %Y')
        subject = ' '.join([self.subject, dates])
        
        return subject

		
    def check_data_availability(self, override=False):
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            logger.debug("Data not available for: %s" % check["site"])
            if override:
                self.warning_sites = check["site"]
                return True
            else:
                return False	
                
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        elif len(self.sites) == len(ga_config.TABLES.keys()):
            return ga_config.ALL_SITES_NAME
          
    
    def _get_social_data(self):
        today = self.period.end_date
        month_stats_range = utils.list_of_months(today, 3)
  
        for month in month_stats_range:
            new_row = {}
            new_row["month"] = month.name
            data = AnalyticsData(self.sites, month, "MONTHLY")
            new_row["data"] = data.social_network_table(0)
            #new_row["summary"] = data.summary_table()
            social.append(new_row)            
        return social
    
    def _get_top_networks(self):
        top_networks_past_year = AnalyticsData(self.sites, utils.StatsRange("year", start_month, today), "YEARLY").social_network_table(0)

        top_network = ["Facebook", "Twitter", "reddit"]
        for row in top_networks_past_year:
            if row["social_network"] not in top_network:            
                top_network.append(row["social_network"])
            else:
                continue
        top_network = top_network[:6]
        return top_network                    
                        
    def generate_html(self):
        
        social = self._get_social_data()        
        top_network = self._get_top_networks()
        
        social_table = []
        for network in top_network:
            new_row = {}
            new_row["network"] = network
            new_row["data"] = []
            for row in social:
                #in row["data"] find matching network row
                try:
                    match = utils.list_search(row["data"], "social_network", network)
                except KeyError:
                    match = {"pageviews":0, "sessions":0 }#put in full exception zero case dictionary
                new_row["data"].append({"month":row["month"], "monthly_data":match}) #extend the match dictionary with month key? 
            social_table.append(new_row)
    
         
        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            site = self.get_site(),
            all_sites = self.all_sites,
            report_span = self.frequency,
            warning_sites = self.warning_sites,
            social_table = social_table
        
        )
        return html	        
        

class AnalyticsSocialExport(Report):
    def __init__(self, sites, period, recipients, frequency, subject):
        super(AnalyticsSocialExport, self).__init__(sites, period, recipients, frequency, subject)
        self.sites = sites
        self.period = period
        self.recipients = recipients
        self.frequency = frequency
        self.subject = subject		 
        self.data = AnalyticsData(self.sites, self.period, self.frequency)    
        self.warning_sites = []
        self.template = self.env.get_template("social.csv")
        
        logger.debug("Running analytics social export")   	

    def check_data_availability(self, override=False):
        check = self.data.check_available_data()
        if check["result"]:
            return True
        else:
            logger.debug("Data not available for: %s" % check["site"])
            if override:
                self.warning_sites = check["site"]
                return True
            else:
                return False	
        
    	
    def generate_html(self):

        month_stats_range = utils.list_of_months(self.period.end_date, 1)
        social_export = []   
        for month in month_stats_range:
            new_row = {}
            new_row["month"] = month.get_start()
            data = AnalyticsData(self.sites, month, self.frequency)
            new_row["data"] = data.social_network_table(0)
            social_export.append(new_row)
            

        csv = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            report_span = self.frequency,
            warning_sites = self.warning_sites,
            social_export = social_export	
        )
        return csv		
        
    def send_email(self, csv):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = self.get_subject()
        msg['From'] = config.SEND_FROM
        msg['To'] = ', '.join(self.recipients)
        
        attachment= MIMEText(csv)
        
        attachment.add_header("Content-Disposition", "attachment", filename="test.csv")
        msg.attach(attachment)
        
        sender = smtplib.SMTP(config.SMTP_ADDRESS)
        sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
    
        sender.quit()      		
		
