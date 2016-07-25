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
            start_month = date(today.year-1, today.month, 1)
            end_month = date(today.year, today.month, 1)
            current = start_month
            month_stats_range = []
            months = []
            while current != end_month:
                start_date = current
                end_date = utils.add_one_month((current - timedelta(days=1)))
                name =  start_date.strftime("%b-%Y")
                month_stats_range.append(utils.StatsRange(name, start_date, end_date))
                months.append(name)
                current = utils.add_one_month(start_date)     
                
        
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
        
        logger.debug("Running analytics top social network report")      

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
            
                        
    def generate_html(self):
        
        today = self.period.end_date
        
        start_month = date(today.year-3, today.month, 1)
        end_month = today + timedelta(days=1) #first of next month so includes this month
        current = start_month
        month_stats_range = []
        while current != end_month:
            start_date = current
            end_date = utils.add_one_month((current - timedelta(days=1)))
            name =  start_date.strftime("%b-%Y")
            print name
            month_stats_range.append(utils.StatsRange(name, start_date, end_date))
            current = utils.add_one_month(start_date)     

        
        social = []  
        for month in month_stats_range:
            print month.get_start()
            new_row = {}
            new_row["month"] = month.name
            data = AnalyticsData(self.sites, month, "MONTHLY")
            new_row["data"] = data.social_network_table(0)
            #new_row["summary"] = data.summary_table()
            print new_row
            social.append(new_row)
        
        print social
        
        social_table = []
        for row in social:
            new_row = {}
            for data in row["data"]:
                try:
                    new_row[data["social_network"]].append(data)
                except KeyError:
                    new_row[data["social_network"]] = [data]
                    
            social_table.append(new_row)
        
        #top_networks_past_year = AnalyticsData(self.sites, utils.StatsRange("year", start_month, today), "YEARLY").social_network_table(0)
        top_networks_past_year =[{u'pageviews': 45648571.0, 'previous_figure_users': 7141077.0, 'yearly_figure_users': 7141077.0, 'yearly_figure_pageviews': 32913684.0, 'previous_figure_sessions': 18784191.0, 'yearly_percentage_pageviews': 38.69177026795299, 'yearly_change_users': 3250871.0, 'previous_change_users': 3250871.0, 'previous_percentage_users': 45.523539376483406, 'previous_percentage_sessions': 46.19580901833888, 'previous_figure_pageviews': 32913684.0, 'yearly_change_pageviews': 12734887.0, 'yearly_figure_sessions': 18784191.0, 'previous_percentage_pageviews': 38.69177026795299, 'previous_change_sessions': 8677509.0, u'users': 10391948.0, u'sessions': 27461700.0, 'social_network': u'Facebook', 'yearly_change_sessions': 8677509.0, 'yearly_percentage_users': 45.523539376483406, 'previous_change_pageviews': 12734887.0, 'articles': [], 'yearly_percentage_sessions': 46.19580901833888}, {u'pageviews': 13743402.0, 'previous_figure_users': 4644830.0, 'yearly_figure_users': 4644830.0, 'yearly_figure_pageviews': 12062636.0, 'previous_figure_sessions': 7703923.0, 'yearly_percentage_pageviews': 13.933654302426104, 'yearly_change_users': 6116.0, 'previous_change_users': 6116.0, 'previous_percentage_users': 0.13167327975404913, 'previous_percentage_sessions': 0.4009126259439509, 'previous_figure_pageviews': 12062636.0, 'yearly_change_pageviews': 1680766.0, 'yearly_figure_sessions': 7703923.0, 'previous_percentage_pageviews': 13.933654302426104, 'previous_change_sessions': 30886.0, u'users': 4650946.0, u'sessions': 7734809.0, 'social_network': u'reddit', 'yearly_change_sessions': 30886.0, 'yearly_percentage_users': 0.13167327975404913, 'previous_change_pageviews': 1680766.0, 'articles': [], 'yearly_percentage_sessions': 0.4009126259439509}, {u'pageviews': 23525306.0, 'previous_figure_users': 4091807.0, 'yearly_figure_users': 4091807.0, 'yearly_figure_pageviews': 28954416.0, 'previous_figure_sessions': 15812573.0, 'yearly_percentage_pageviews': -18.750542231623665, 'yearly_change_users': -971007.0, 'previous_change_users': -971007.0, 'previous_percentage_users': -23.730518081620176, 'previous_percentage_sessions': -16.69709920074361, 'previous_figure_pageviews': 28954416.0, 'yearly_change_pageviews': -5429110.0, 'yearly_figure_sessions': 15812573.0, 'previous_percentage_pageviews': -18.750542231623665, 'previous_change_sessions': -2640241.0, u'users': 3120800.0, u'sessions': 13172332.0, 'social_network': u'Twitter', 'yearly_change_sessions': -2640241.0, 'yearly_percentage_users': -23.730518081620176, 'previous_change_pageviews': -5429110.0, 'articles': [], 'yearly_percentage_sessions': -16.69709920074361}, {u'pageviews': 2098956.0, 'previous_figure_users': 773830.0, 'yearly_figure_users': 773830.0, 'yearly_figure_pageviews': 3628877.0, 'previous_figure_sessions': 1068907.0, 'yearly_percentage_pageviews': -42.1596267936334, 'yearly_change_users': -481987.0, 'previous_change_users': -481987.0, 'previous_percentage_users': -62.285902588423816, 'previous_percentage_sessions': -52.331774420038414, 'previous_figure_pageviews': 3628877.0, 'yearly_change_pageviews': -1529921.0, 'yearly_figure_sessions': 1068907.0, 'previous_percentage_pageviews': -42.1596267936334, 'previous_change_sessions': -559378.0, u'users': 291843.0, u'sessions': 509529.0, 'social_network': u'YouTube', 'yearly_change_sessions': -559378.0, 'yearly_percentage_users': -62.285902588423816, 'previous_change_pageviews': -1529921.0, 'articles': [], 'yearly_percentage_sessions': -52.331774420038414}, {u'pageviews': 2405530.0, 'previous_figure_users': 247223.0, 'yearly_figure_users': 247223.0, 'yearly_figure_pageviews': 2218851.0, 'previous_figure_sessions': 468934.0, 'yearly_percentage_pageviews': 8.413318424716214, 'yearly_change_users': -7059.0, 'previous_change_users': -7059.0, 'previous_percentage_users': -2.8553168596772953, 'previous_percentage_sessions': 3.9736935261678616, 'previous_figure_pageviews': 2218851.0, 'yearly_change_pageviews': 186679.0, 'yearly_figure_sessions': 468934.0, 'previous_percentage_pageviews': 8.413318424716214, 'previous_change_sessions': 18634.0, u'users': 240164.0, u'sessions': 487568.0, 'social_network': u'VKontakte', 'yearly_change_sessions': 18634.0, 'yearly_percentage_users': -2.8553168596772953, 'previous_change_pageviews': 186679.0, 'articles': [], 'yearly_percentage_sessions': 3.9736935261678616}, {u'pageviews': 282838.0, 'previous_figure_users': 180274.0, 'yearly_figure_users': 180274.0, 'yearly_figure_pageviews': 274271.0, 'previous_figure_sessions': 230537.0, 'yearly_percentage_pageviews': 3.123552982269361, 'yearly_change_users': 7826.0, 'previous_change_users': 7826.0, 'previous_percentage_users': 4.341169553013746, 'previous_percentage_sessions': -2.0265727410350616, 'previous_figure_pageviews': 274271.0, 'yearly_change_pageviews': 8567.0, 'yearly_figure_sessions': 230537.0, 'previous_percentage_pageviews': 3.123552982269361, 'previous_change_sessions': -4672.0, u'users': 188100.0, u'sessions': 225865.0, 'social_network': u'StumbleUpon', 'yearly_change_sessions': -4672.0, 'yearly_percentage_users': 4.341169553013746, 'previous_change_pageviews': 8567.0, 'articles': [], 'yearly_percentage_sessions': -2.0265727410350616}, {u'pageviews': 885966.0, 'previous_figure_users': 156619.0, 'yearly_figure_users': 156619.0, 'yearly_figure_pageviews': 827274.0, 'previous_figure_sessions': 218315.0, 'yearly_percentage_pageviews': 7.094626447827443, 'yearly_change_users': -8065.0, 'previous_change_users': -8065.0, 'previous_percentage_users': -5.149439084657673, 'previous_percentage_sessions': 0.4850788997549413, 'previous_figure_pageviews': 827274.0, 'yearly_change_pageviews': 58692.0, 'yearly_figure_sessions': 218315.0, 'previous_percentage_pageviews': 7.094626447827443, 'previous_change_sessions': 1059.0, u'users': 148554.0, u'sessions': 219374.0, 'social_network': u'Wikia', 'yearly_change_sessions': 1059.0, 'yearly_percentage_users': -5.149439084657673, 'previous_change_pageviews': 58692.0, 'articles': [], 'yearly_percentage_sessions': 0.4850788997549413}, {u'pageviews': 558336.0, 'previous_figure_users': 117717.0, 'yearly_figure_users': 117717.0, 'yearly_figure_pageviews': 465707.0, 'previous_figure_sessions': 173974.0, 'yearly_percentage_pageviews': 19.88997373885297, 'yearly_change_users': 1245.0, 'previous_change_users': 1245.0, 'previous_percentage_users': 1.0576212441703408, 'previous_percentage_sessions': 11.2654764505041, 'previous_figure_pageviews': 465707.0, 'yearly_change_pageviews': 92629.0, 'yearly_figure_sessions': 173974.0, 'previous_percentage_pageviews': 19.88997373885297, 'previous_change_sessions': 19599.0, u'users': 118962.0, u'sessions': 193573.0, 'social_network': u'Blogger', 'yearly_change_sessions': 19599.0, 'yearly_percentage_users': 1.0576212441703408, 'previous_change_pageviews': 92629.0, 'articles': [], 'yearly_percentage_sessions': 11.2654764505041}, {u'pageviews': 1012780.0, 'previous_figure_users': 122669.0, 'yearly_figure_users': 122669.0, 'yearly_figure_pageviews': 488528.0, 'previous_figure_sessions': 151539.0, 'yearly_percentage_pageviews': 107.31257983165756, 'yearly_change_users': -8447.0, 'previous_change_users': -8447.0, 'previous_percentage_users': -6.886010320455862, 'previous_percentage_sessions': 36.95418341153103, 'previous_figure_pageviews': 488528.0, 'yearly_change_pageviews': 524252.0, 'yearly_figure_sessions': 151539.0, 'previous_percentage_pageviews': 107.31257983165756, 'previous_change_sessions': 56000.0, u'users': 114222.0, u'sessions': 207539.0, 'social_network': u'Naver', 'yearly_change_sessions': 56000.0, 'yearly_percentage_users': -6.886010320455862, 'previous_change_pageviews': 524252.0, 'articles': [], 'yearly_percentage_sessions': 36.95418341153103}, {u'pageviews': 1110225.0, 'previous_figure_users': 224655.0, 'yearly_figure_users': 224655.0, 'yearly_figure_pageviews': 2708832.0, 'previous_figure_sessions': 1031237.0, 'yearly_percentage_pageviews': -59.014623276748054, 'yearly_change_users': -118424.0, 'previous_change_users': -118424.0, 'previous_percentage_users': -52.713716587656634, 'previous_percentage_sessions': -60.02732640508438, 'previous_figure_pageviews': 2708832.0, 'yearly_change_pageviews': -1598607.0, 'yearly_figure_sessions': 1031237.0, 'previous_percentage_pageviews': -59.014623276748054, 'previous_change_sessions': -619024.0, u'users': 106231.0, u'sessions': 412213.0, 'social_network': u'Disqus', 'yearly_change_sessions': -619024.0, 'yearly_percentage_users': -52.713716587656634, 'previous_change_pageviews': -1598607.0, 'articles': [], 'yearly_percentage_sessions': -60.02732640508438}, {u'pageviews': 115008.0, 'previous_figure_users': 0, 'yearly_figure_users': 0, 'yearly_figure_pageviews': 0, 'previous_figure_sessions': 0, 'yearly_percentage_pageviews': 0, 'yearly_change_users': 0, 'previous_change_users': 0, 'previous_percentage_users': 0, 'previous_percentage_sessions': 0, 'previous_figure_pageviews': 0, 'yearly_change_pageviews': 0, 'yearly_figure_sessions': 0, 'previous_percentage_pageviews': 0, 'previous_change_sessions': 0, u'users': 76010.0, u'sessions': 88379.0, 'social_network': u'Hacker News', 'yearly_change_sessions': 0, 'yearly_percentage_users': 0, 'previous_change_pageviews': 0, 'articles': [], 'yearly_percentage_sessions': 0}, {u'pageviews': 142346.0, 'previous_figure_users': 0, 'yearly_figure_users': 0, 'yearly_figure_pageviews': 0, 'previous_figure_sessions': 0, 'yearly_percentage_pageviews': 0, 'yearly_change_users': 0, 'previous_change_users': 0, 'previous_percentage_users': 0, 'previous_percentage_sessions': 0, 'previous_figure_pageviews': 0, 'yearly_change_pageviews': 0, 'yearly_figure_sessions': 0, 'previous_percentage_pageviews': 0, 'previous_change_sessions': 0, u'users': 68932.0, u'sessions': 92299.0, 'social_network': u'LinkedIn', 'yearly_change_sessions': 0, 'yearly_percentage_users': 0, 'previous_change_pageviews': 0, 'articles': [], 'yearly_percentage_sessions': 0}, {u'pageviews': 169305.0, 'previous_figure_users': 167970.0, 'yearly_figure_users': 167970.0, 'yearly_figure_pageviews': 1004569.0, 'previous_figure_sessions': 381033.0, 'yearly_percentage_pageviews': -83.14650362493767, 'yearly_change_users': -130530.0, 'previous_change_users': -130530.0, 'previous_percentage_users': -77.71030541168066, 'previous_percentage_sessions': -80.24186881451213, 'previous_figure_pageviews': 1004569.0, 'yearly_change_pageviews': -835264.0, 'yearly_figure_sessions': 381033.0, 'previous_percentage_pageviews': -83.14650362493767, 'previous_change_sessions': -305748.0, u'users': 37440.0, u'sessions': 75285.0, 'social_network': u'Google+', 'yearly_change_sessions': -305748.0, 'yearly_percentage_users': -77.71030541168066, 'previous_change_pageviews': -835264.0, 'articles': [], 'yearly_percentage_sessions': -80.24186881451213}, {u'pageviews': 78522.0, 'previous_figure_users': 66886.0, 'yearly_figure_users': 66886.0, 'yearly_figure_pageviews': 204589.0, 'previous_figure_sessions': 102151.0, 'yearly_percentage_pageviews': -61.619637419411596, 'yearly_change_users': -32702.0, 'previous_change_users': -32702.0, 'previous_percentage_users': -48.892144843465005, 'previous_percentage_sessions': -58.80706013646465, 'previous_figure_pageviews': 204589.0, 'yearly_change_pageviews': -126067.0, 'yearly_figure_sessions': 102151.0, 'previous_percentage_pageviews': -61.619637419411596, 'previous_change_sessions': -60072.0, u'users': 34184.0, u'sessions': 42079.0, 'social_network': u'Tumblr', 'yearly_change_sessions': -60072.0, 'yearly_percentage_users': -48.892144843465005, 'previous_change_pageviews': -126067.0, 'articles': [], 'yearly_percentage_sessions': -58.80706013646465}, {u'pageviews': 53258.0, 'previous_figure_users': 0, 'yearly_figure_users': 0, 'yearly_figure_pageviews': 0, 'previous_figure_sessions': 0, 'yearly_percentage_pageviews': 0, 'yearly_change_users': 0, 'previous_change_users': 0, 'previous_percentage_users': 0, 'previous_percentage_sessions': 0, 'previous_figure_pageviews': 0, 'yearly_change_pageviews': 0, 'yearly_figure_sessions': 0, 'previous_percentage_pageviews': 0, 'previous_change_sessions': 0, u'users': 27636.0, u'sessions': 31170.0, 'social_network': u'Pinterest', 'yearly_change_sessions': 0, 'yearly_percentage_users': 0, 'previous_change_pageviews': 0, 'articles': [], 'yearly_percentage_sessions': 0}]
        
        top_network = ["Facebook", "Twitter", "reddit"]
        for row in top_networks_past_year:
            if row["social_network"] not in top_network:            
                top_network.append(row["social_network"])
            else:
                continue
        top_network = top_network[:6]
        print top_network
        
        social_table = []
        for network in top_network:
            new_row = {}
            new_row["network"] = network
            new_row["data"] = []
            for row in social:
                #in row["Data"] find matching network row
                try:
                    match = utils.list_search(row["data"], "social_network", network)
                except KeyError:
                    match = {"pageviews":0, "sessions":0 }#put in full exception zero case dictionary
                new_row["data"].append({"month":row["month"], "monthly_data":match}) #extend the match dictionary with month key? 
            social_table.append(new_row)

            
        print "SOCIAL TABLE : \n", social_table           
         
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

        start_month = date(self.period.start_date.year - 1, self.period.start_date.month, 01)
        end_month = date(self.period.start_date.year, self.period.start_date.month, 01)
        current = start_month
        month_stats_range = []
        months = []
        while current != end_month:
            start_date = current
            end_date = utils.add_one_month((current - timedelta(days=1)))
            name =  start_date.strftime("%b-%Y")
            month_stats_range.append(utils.StatsRange(name, start_date, end_date))
            months.append(name)
            current = utils.add_one_month(start_date)
         
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
		
