from pprint import pprint
from datetime import date, datetime, timedelta
from email.mime.image import MIMEImage
import logging.config, logging.handlers
import smtplib

from Statsdash.config import LOGGING
from Statsdash.GA.aggregate_data import AnalyticsData
from Statsdash import aggregate_data
from Statsdash.render import get_environment
from Statsdash.Youtube.aggregate_data import YoutubeData
from Statsdash import config
import Statsdash.GA.config as ga_config
import Statsdash.utilities as utils

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')


class Report:
    """
    Report object
    Gathers data from analytics, renders and sends as an email
    """
    data = []

    def __init__(self, sites, period, frequency, subject):
        self.sites = sites
        self.period = period
        self.frequency = frequency
        self.subject = subject

        self.env = get_environment()
        self.template = self.env.get_template('base.html')
        
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

    # TODO test
    def get_freq_label(self):
        """
        Returns label for the period of change, e.g. where
        frequency == 'monthly', label == 'MoM'
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
        pass
        # html = transform(html) #inline css using premailer
        # msg = MIMEMultipart('alternative')
        # msg.set_charset('utf8')
        # msg['Subject'] = self.get_subject()
        # msg['From'] = config.SEND_FROM
        # msg['To'] = ', '.join(self.recipients)
        # text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        # html_part = MIMEText(html.encode("utf-8"), 'html')
        #
        # msg.attach(text_part)
        # msg.attach(html_part)
        #
        # sender = smtplib.SMTP(config.SMTP_ADDRESS)
        # sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
        #
        # sender.quit()

    # TODO test and docstring
    def _get_tables(self):
        args = [self.sites, self.period, self.frequency]
        return {d.table_label: d(*args).get_table() for d in self.data}



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
                
                return check["channel"]
            else:
                return False


class AnalyticsCoreReport(Report):
    """
    Google Analytics data report for a given collection of sites. Converts the
    report into HTML.
    """

    def __init__(self, sites, period, frequency, subject):
        super().__init__(sites, period, frequency, subject)
        self.sites = sites
        self.period = period
        self.frequency = frequency
        self.subject = subject
        self.data = AnalyticsData(self.sites, self.period, self.frequency)
        self.warning_sites = []
        self.imgdata = None
        self.template = self.env.get_template("GA/base.html")

        # NOTE maybe nicer way to handle this
        self.today = self.period.end_date
        self.first = datetime(self.today.year, self.today.month, 1).date()
        self.last = utils.add_one_month(self.first) - timedelta(days=1)
        self.num_days = (self.last - self.period.end_date).days

        if self.sites == ga_config.ALL_NETWORK_SITES:
            self.all_sites = True
        else:
            self.all_sites = False

        # TODO move outside init
        self.data = [
            aggregate_data.SummaryData,
            aggregate_data.SiteSummaryData,
            aggregate_data.CountryData,
            aggregate_data.ArticleData,
            aggregate_data.TrafficSourceData,
            aggregate_data.DeviceData,
            # TODO
            # referring_site_table = self.data.referring_sites_table(num_articles)
            # social_table = self.data.social_network_table(num_articles)
        ]
        logger.debug("Running analytics core report")
                
    # TODO sort this
    def get_site(self):
        if len(self.sites) == 1:
            return self.sites[0]
        elif self.all_sites:
            return ga_config.ALL_SITES_NAME

    def generate_html(self):
        tables = self._get_tables()

        html = self.template.render(
            subject=self.get_subject(),
            change=self.get_freq_label(),
            site=self.get_site(),
            all_sites=self.all_sites,
            report_span=self.frequency,
            warning_sites=self.warning_sites,
            num_days=self.num_days,
            **tables
        )
        return html

    def _get_tables(self):
        tables = super()._get_tables()
        tables['summary_table'] = tables['summary_table'][0]
        print(tables['summary_table'])
        tables['network_summary_table'] = self._get_network_summary_table()
        if self.frequency != 'MONTHLY':
            tables['network_month_summary_table'] = self._get_network_month_summary_table()
            tables['full_month_summary_table'] = self._get_full_month_summary_table()
            tables['month_summary_table'] = self._get_month_summary_table()
        return tables

    def _get_network_summary_table(self):
        network_data = aggregate_data.SummaryData(ga_config.TABLES.keys(), self.period, self.frequency)
        return network_data.get_table()

    def _get_month_summary_table(self):
        # TODO clean, test, mock
        if self.frequency != 'MONTHLY':
            # TODO does this need to use datetime method
            month_range = utils.StatsRange('Month to date Aggregate', self.first, self.today)
            month_summary_data = aggregate_data.SummaryData(self.sites, month_range, self.frequency)
            return month_summary_data.get_table()
        return None

    def _get_full_month_summary_table(self):
        # TODO clean, test, mock
        month_range = self._get_month_range()
        full_month_data = aggregate_data.SummaryData(self.sites, month_range, self.frequency)
        return full_month_data.get_table()

    def _get_network_month_summary_table(self):
        month_range = self._get_month_range()
        # TODO fix
        if not self.all_sites:
            network_month_data = aggregate_data.SummaryData(ga_config.TABLES, month_range, self.frequency)
            return network_month_data.get_table()
        return None

    def _get_month_range(self):
        # TODO docstring and test
        return utils.StatsRange('Month to date Aggregate', self.first, self.last)

        # # TODO not clear what the different frequency possibilities are.
        # else:
        #     month_stats_range = utils.list_of_months(today, 1)
        #
        #     device = []
        #     for month in month_stats_range:
        #         new_row = dict()
        #         new_row["month"] = month.get_start()
        #         device_data = aggregate_data.DeviceData(self.sites, month, "MONTHLY")
        #         summary_data = aggregate_data.SummaryData(self.sites, month, "MONTHLY")
        #         new_row['data'] = device_data.get_table()
        #         new_row['summary'] = summary_data.get_table()
        #         device.append(new_row)
        #
        #     # TODO add this back in
        #     # self.imgdata = self.data.device_chart(device)
        #

        
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
        
        if self.sites == len(ga_config.TABLES.keys()):
            self.all_sites = True
        else:
            self.all_sites = False
                
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
        pass
        # html = transform(html) #inline css using premailer
        # msg = MIMEMultipart('alternative')
        # msg.set_charset('utf8')
        # msg['Subject'] = self.get_subject()
        # msg['From'] = config.SEND_FROM
        # msg['To'] = ', '.join(self.recipients)
        # text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        # html_part = MIMEText(html.encode("utf-8"), 'html')


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
        pass
        # msg = MIMEMultipart('alternative')
        #
        # msg['Subject'] = self.get_subject()
        # msg['From'] = config.SEND_FROM
        # msg['To'] = ', '.join(self.recipients)
        #
        # attachment= MIMEText(csv)
        #
        # attachment.add_header("Content-Disposition", "attachment", filename="test.csv")
        # msg.attach(attachment)
        #
        # sender = smtplib.SMTP(config.SMTP_ADDRESS)
        # sender.sendmail(config.SEND_FROM, self.recipients, msg.as_string())
        #
        # sender.quit()
