import re, pprint
import smtplib
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plot
import matplotlib.dates as plotdates
from matplotlib.font_manager import FontProperties
import random
import StringIO
import cStringIO
import urllib, base64
from slimmer import html_slimmer

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta, datetime
from collections import OrderedDict, defaultdict

import config
from analytics import get_analytics, StatsRange
from renderer import render_template
from dateutils import subtract_one_month, add_one_month

from data_aggregator import DataAggregator

import logging

analytics = get_analytics()

get_data = DataAggregator()

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

    def send_email(self, recipients, subject, html, images):
        """
        Send an html email to a list of recipients.
        """

        html= html_slimmer(html)
        msg = MIMEMultipart('alternative')
        msg.set_charset('utf8')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = ', '.join(recipients)
        text_part = MIMEText("Please open with an HTML-enabled Email client.", 'plain')
        html_part = MIMEText(html.encode('utf-8'), 'html')


        for img in images:
            img_string = img['string']
            label = img['name'] 
            img_part = MIMEImage(img_string, 'png')
            img_part.add_header('Content-ID', '<%s>' % label)
            msg.attach(img_part)       
            
        
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

    def __init__(self, recipients, subject, sites, period):
        self.recipients = recipients
        self.sites = sites
        self.period = period
        self.emailer = Emailer()
        self.subject = subject

    def get_subject(self):
        return self.subject

    def data_available(self):
        """
        Iterate through all sites and check that their data is available.
        """
        
        for site in self.sites:
            site_ga_id = config.TABLES[site]
            site_data_available = analytics.data_available_for_site(site_ga_id, 
                self.period.get_end())
            if site_data_available == False:
                print "Data for %s is missing" % site
                return False
        return True

    def generate_report(self):
        """
        Marshall the data needed and use it to render the HTML report.
        """
        raise NotImplementedError()

    def send_report(self):
        """
        Generate and send the report to the recipients.
        """
        results = self.generate_report()
        html = results['html']
        images = results['images']
        subject = self.get_subject()
        recipients = self.recipients
        self.emailer.send_email(recipients, subject, html, images)
        print "Sent '%s' Report for site %s" % (self.subject, ','.join(self.sites))


class ArticleBreakdown(Report):
    template = "article_dash.html"

    def __init__(self, recipients, subject, sites, period, second_period, topic, extra_filters="", article_limit=10):
        super(ArticleBreakdown, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
        self.topic = topic
        self.extra_filters = extra_filters
        self.article_limit = article_limit

    def get_subject(self):
        subject = ' - '.join([self.subject, self.period.get_end()])
        return subject

    def get_article_breakdown_for_site(self, site_id):
        data = analytics.get_article_breakdown_two_periods(site_id, 
            self.period, self.second_period, extra_filters=self.extra_filters,
            min_pageviews=250)
        return data

    def generate_report(self):
        site_ga_id = config.TABLES[self.sites[0]]
        data = self.get_article_breakdown_for_site(site_ga_id)
        data = list(data.items())[:self.article_limit]
        report_html = render_template(self.template, {
            'data': data,
            'site': self.sites[0],
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'topic': self.topic,
            'article_limit': self.article_limit,
        })
        
        results = {
            'html' : report_html,
            'images' : []
        }
        return results
	

class NetworkArticleBreakdown(ArticleBreakdown):
    template = "article_dash.html"

    def generate_report(self):
        
        formatted_network_data = get_data.get_article_breakdown(self.sites, self.period, self.second_period, self.article_limit)
        
        report_html = render_template(self.template, {
            'data': formatted_network_data,
            'site': "Gamer Network",
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'topic': self.topic,
            'article_limit': self.article_limit,
        })
        results = {
            'html' : report_html,
            'images' : []
        }
        return results

class NetworkBreakdown(Report):
    template = "dash.html"

    def __init__(self, recipients, subject, sites, period, second_period, report_span="1", extra_filters=""):
        super(NetworkBreakdown, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
        self.extra_filters = extra_filters
        self.report_span = report_span

    def get_subject(self):
        if self.report_span == '1':
            subject = ' for '.join([self.subject, self.period.get_end()])
        if self.report_span == '7':
            subject = ' for '.join([self.subject, '%s to %s' % 
                (self.period.get_start(), self.period.get_end())
            ])
        if self.report_span == 'month':
            subject = ' for '.join([self.subject, self.period.start_date.strftime("%B")])
        return subject

    
    def generate_report(self):
         
        data = get_data.get_site_totals(self.sites, self.period, self.second_period, True)   
        
        network_data = data['network_data']
        totals = {'pageviews': data['totals']['first_period']['pageviews'], 'visitors': data['totals']['first_period']['visitors']}
        
        country_metrics = get_data.get_country_metrics(self.sites, self.period, self.second_period)

        report_html = render_template(self.template, {
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'period': self.report_span,
            'totals': totals,
            'sites': network_data,
            'countries': country_metrics
        })
        results = {
            'html' : report_html,
            'images' : []
        }
        return results

class TrafficSourceBreakdown(Report):
    template='site_dash.html'
    
    #init
    def __init__(self, recipients, subject, sites, period, second_period, report_span, black_list):
        super(TrafficSourceBreakdown, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
        self.report_span = report_span
        self.black_list = black_list

    def get_subject(self):
        start = self.period.start_date
        end = self.period.end_date
        if self.report_span == 'daily':
            subject = ' '.join([self.subject, end.strftime("%a %d %b %Y")])
        elif self.report_span  == 'weekly':
            weekly_date = start.strftime("%a %d %b %Y") + ' - ' + end.strftime("%a %d %b %Y")
            subject = ' '.join([self.subject, weekly_date])
        elif self.report_span == 'monthly':
            subject = ' '.join([self.subject, start.strftime('%B')])
        return subject

    def data_available(self):
        """
        Iterate through all sites and check that their data is available.
        """        
        logger = logging.getLogger('report')
        for site in config.TABLES.keys():
            site_ga_id = config.TABLES[site]
            print site 
            site_data_available = analytics.data_available_for_site(site_ga_id, 
                self.period.get_end())
            if site_data_available == False:
                logger.info( "Data for %s is missing" % site)
                return False
        return True
                     
    def generate_report(self):
        """
        main function 
        gather data from analytics, call functions to aggregate/sort data and draw charts 
        template to html
        """

        logger = logging.getLogger('report')
        logger.info('%s', self.get_subject())
        
        image_strings = []              
               
        total_num_sites = len(config.TABLES)            
        num_sites = len(self.sites)
        site_names=[]
            
        #getting stat ranges for monthly accum
        today = self.period.end_date
        first = datetime(today.year, today.month, 1).date()
        month_range = StatsRange("Month to date Aggregate", first, today)
        prev_yr_first = first - timedelta(days=365)
        prev_yr_today = today - timedelta(days=365)
        #last_yr_range = StatsRange("Last Year Monthly Aggregate", prev_yr_first, prev_yr_today) 
        yesterday = self.period.start_date - timedelta(days=1)
        yesterday_period = StatsRange("yesterday", yesterday, yesterday)    
        
        prev_yr_end = add_one_month(prev_yr_first)
        last_yr_range = StatsRange("Last Year Whole Monthly Aggregate", prev_yr_first, prev_yr_end) 
        
        num_days = (prev_yr_end - prev_yr_today).days
        
        #get data for totals of the site and network if not network report
        period_data = get_data.get_site_totals(self.sites, self.period, self.second_period, True)
        period_totals = period_data['totals'] 
        monthly_totals = get_data.get_site_totals(self.sites, month_range, last_yr_range, True)['totals'] 
        
        network_period_totals = 0
        network_monthly_totals = 0
        if num_sites < total_num_sites:
            network_period_totals = get_data.get_site_totals(config.TABLES.keys(), self.period, self.second_period, True)['totals'] 
            network_monthly_totals = get_data.get_site_totals(config.TABLES.keys(), month_range, last_yr_range, True)['totals']
          
        #get data for traffic/devices/socials 
        results = get_data.get_traffic_device_social_data(self.sites, self.period, self.second_period)
        socials = results['social']['first_period']
        traffic = results['traffic']['first_period']
        devices = results['devices']['first_period']
        
        second_socials = results['social']['second_period']
        second_traffic = results['traffic']['second_period']
        second_devices = results['devices']['second_period']
        last_year_socials = results['social']['last_year_period']
                
        sorted_traffic = get_data.sort_data(traffic, 'visitors', 11)
        sorted_devices = get_data.sort_data(devices, 'visitors', 5)
        sorted_socials = get_data.sort_data(socials, 'visitors', 6)              
          
        top_traffic_results = get_data.add_change(sorted_traffic, second_traffic, ['visitors', 'pageviews'])
        top_device_results = get_data.add_change(sorted_devices, second_devices, ['visitors'])
        top_social_results = get_data.add_change(sorted_socials, second_socials, ['visitors', 'pageviews'])    
        
        #last_yr_social_results = get_data.add_change(sorted_socials, last_year_socials, ['visitors'])  
                
        #total number visitors use social networks
        period_totals['first_period']['social_visitors'] = 0
        for social in socials:
            visitors = social['metrics']['visitors']
            period_totals['first_period']['social_visitors'] += visitors   

        if self.report_span == 'daily':
            num_articles = 1
            num_referrals = 5
        elif self.report_span == 'weekly' or 'monthly':
            num_articles = 5
            num_referrals = 5
            
        top_sites = get_data.sort_data(traffic, 'visitors', 25)
            
        social_articles = get_data.get_social_referral_articles(self.sites, self.period, yesterday_period, top_social_results, num_articles)
        site_total = get_data.get_site_referral_articles(self.sites, self.period, yesterday_period, top_sites, self.black_list, num_articles, num_referrals)
        
        site_referrals = site_total['site_referrals']
        site_total_pvs = site_total['site_pvs']

        
        if self.report_span == 'daily':
            top_articles = get_data.get_top_articles(self.sites, self.period, yesterday_period, 10)
        else:
            top_articles = get_data.get_top_articles(self.sites, self.period, yesterday_period, 15)            
        
        country_metrics = 0
        network_data = 0
        metric_totals = 0
        
        if num_sites == total_num_sites:
            #NETWORK REPORT
                   
            #get country data 
            country_first = get_data.get_country_metrics(self.sites, self.period)
            country_second = get_data.get_country_metrics(self.sites, self.second_period)
            
            country_metrics = get_data.add_change(country_first, country_second, ['visitors', 'pageviews'])
            
            
            network_data = period_data['network_data']
            
            metric_totals = {'pageviews': period_data['totals']['first_period']['pageviews'], 'visitors': period_data['totals']['first_period']['visitors']}  
        elif num_sites == 1:
            country_first = get_data.get_country_metrics(self.sites, self.period)
            country_second = get_data.get_country_metrics(self.sites, self.second_period)
            
            country_metrics = get_data.add_change(country_first, country_second, ['visitors', 'pageviews'])  
            
            country_metrics = get_data.sort_data(country_metrics, 'visitors',limit = 5)    
            network_data = period_data['network_data']
            
            metric_totals = {'pageviews': period_data['totals']['first_period']['pageviews'], 'visitors': period_data['totals']['first_period']['visitors']}    
            
        device_img_name = 0     
        if self.report_span == 'monthly':
            #calculate device trend graph for 12 months
            month_list =[self.period]
            #find this month, get dates for prev months, actually should work as only monthly reports!
            end_date = self.period.start_date
            for month in range(0, 11):
                #get previous months
                start_date = subtract_one_month(end_date)
                month_list.append(StatsRange("month_%d" % month, start_date, end_date))
                end_date = start_date      
                
            results = get_data.get_monthly_device_data(self.sites, month_list)
            device_img = get_data.plot_device_line_graph(results, month_list)
            image_strings.append(device_img)
            device_img_name = device_img['name']

          
        #RENDER TEMPLATE                                         
        report_html = render_template(self.template, {
            'start_date': self.period.start_date,
            'end_date': self.period.end_date,
            'report_span': self.report_span,
            'subject': self.get_subject(),
            #'img_url': config.ASSETS_URL,
            'img_name' : {'device' : device_img_name},
            'traffic_list' : top_traffic_results,
            'devices_list' : top_device_results, 
            'social_list' : top_social_results,
            'social_articles': social_articles,
            'site_referrals': site_referrals,
            'site_total_pvs' : site_total_pvs,
            'top_articles' : top_articles,
            'num_sites': num_sites,
            'total_num_sites': total_num_sites,
            #'peak': peak,
            'period_totals': period_totals, 
            'monthly_totals': monthly_totals, 
            'network_period_totals': network_period_totals,
            'network_monthly_totals': network_monthly_totals,
            'country_data': country_metrics,
            'network_data': network_data,
            'metric_totals': metric_totals,
            'num_days': num_days
        })
        
        results = {
            'html': report_html,
            'images':image_strings
        }
        
        return results


class SocialReport(Report):
    template='social_dash.html'
  
    def __init__(self, recipients, subject, sites, period, second_period, report_span):
        super(SocialReport, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
        self.report_span = report_span

    def get_subject(self):
        start = self.period.start_date
        end = self.period.end_date
        if self.report_span == 'monthly':
            subject = ' '.join([self.subject, start.strftime('%B')])
        elif self.report_span == 'daily':
            subject = ' '.join([self.subject, end.strftime("%a %d %b %Y")])
        return subject
        
    def data_available(self):
        """
        Iterate through all sites and check that their data is available.
        """        
        for site in config.TABLES.keys():
            site_ga_id = config.TABLES[site]
            site_data_available = analytics.data_available_for_site(site_ga_id, 
                self.period.get_end())
            if site_data_available == False:
                return False
        return True
        
    def generate_report(self):

        logger = logging.getLogger('report')
        logger.info('%s', self.get_subject())        
        #some kind of historical data chart 
        
        #get site and network totals 
        period_data = get_data.get_site_totals(self.sites, self.period, self.second_period, True)
        period_totals = period_data['totals'] 
        network_data = get_data.get_site_totals(config.TABLES.keys(), self.period, self.second_period, True)
        network_totals = network_data['totals'] 
        
        #get social data 
        results = get_data.get_traffic_device_social_data(self.sites, self.period, self.second_period, data=['social'])
        socials = results['social']['first_period']
        second_socials = results['social']['second_period']
        last_year_socials = results['social']['last_year_period']
        
        #sorted_socials = get_data.sort_data(socials, 'visitors', 6)   
               
        socials = get_data.add_change(socials, second_socials, ['visitors', 'pageviews']) 
        
        #for social network in socials list: append and remove if facebook/twitter/reddit/youtube, then sort and find alternate top 3. get change for these 
        #top articles for each netowrk 
        top_social_results = []
        alternate_social_results =[]
        for soc in socials:
            network = soc['dimensions']['socialNetwork']
            if network in ['Facebook', 'Twitter', 'reddit', 'YouTube']:
                top_social_results.append(soc)
            else:
                alternate_social_results.append(soc)
            
            
        alternate_social_results = get_data.sort_data(alternate_social_results, 'visitors', 3)
        
        top_4_socials = top_social_results
        
        bottom_social_articles = get_data.get_social_referral_articles(self.sites, self.period, self.second_period, top_4_socials, 5, sort='ascending')
        
        top_social_results.extend(alternate_social_results)
        top_social_results = get_data.sort_data(top_social_results, 'visitors', 10)

        social_articles = get_data.get_social_referral_articles(self.sites, self.period, self.second_period, top_social_results, 10)
        

        start = self.period.start_date
        start_range = StatsRange("first", start, start)
        end = self.period.end_date
        day = start 
        
        period_list = [start_range]
        while day != end:
            day = day + timedelta(days=1)
            day_range = StatsRange("day", day, day)
            period_list.append(day_range)
                 

        total_dict = get_data.get_totals_over_period(period_list, self.sites)['site']
        network_total = get_data.get_totals_over_period(period_list, self.sites)['network']

        visitors = []
        pageviews = []
        sort_dates = []
        network_visitors = []
        network_pageviews = []
        for date in period_list:
            sort_dates.append(date.start_date)
            visitors.append(total_dict[date.start_date]['visitors'])
            network_visitors.append(network_total[date.start_date]['visitors'])
            pageviews.append(total_dict[date.start_date]['pageviews'])
            network_pageviews.append(network_total[date.start_date]['pageviews'])
                        
        #add more interesting looking things ya know, be able to all axis ticks, label axes, etc etc
        visitor_data = {'site visitors':visitors, 'network visitors':network_visitors}
        pageview_data = {'site pageviews':pageviews, 'network pageviews':network_pageviews}
        all_data = {'site visitors':visitors, 'network visitors':network_visitors, 'site pageviews':pageviews, 'network pageviews':network_pageviews}
        site_data = {'site visitors':visitors,'site pageviews':pageviews}
        network_data = {'network visitors':network_visitors, 'network pageviews':network_pageviews}
        
        
        #get returns of image string and add to image strings, then add into report!?
        get_data.plot_line_graph('visitors_test', sort_dates, visitor_data)
        get_data.plot_line_graph('pageviews_test', sort_dates, pageview_data)
        get_data.plot_line_graph('combined_test', sort_dates, all_data)
        get_data.plot_line_graph('site_test', sort_dates, site_data)
        get_data.plot_line_graph('network_test', sort_dates, network_data)


        image_strings = 0
        

        report_html = render_template(self.template, {  
            'start_date': self.period.start_date.strftime("%d/%m/%y"),
            'end_date': self.period.end_date.strftime("%d/%m/%y"),
            'report_span': self.report_span,
            'subject': self.get_subject(),   
            'top_socials': top_social_results,
            'site_totals': period_totals,
            'network_totals': network_totals,
            'social_articles': social_articles, 
            'bottom_social_articles': bottom_social_articles,       
        })
        
        results = {
            'html': report_html,
            'images':image_strings
        }
        
        return results                    

def create_report(report_class, config, run_date):
    """
    Factory function for instantiating report.
    """
    frequency = config['frequency']
    period = StatsRange.get_period(run_date, frequency)
    kwargs = config['kwargs']
    if config.get('second_period'):
        # Handle other second period types here
        if config['second_period'] == 'immediate_before':
            kwargs['second_period'] = StatsRange.get_previous_period(period, frequency)
        if config['second_period'] == 'week_before':
            kwargs['second_period'] = StatsRange.get_previous_period(period, 'WOW_DAILY')           

    report = report_class(config['recipients'], config['subject'], 
        config['sites'], period, **kwargs)
    return report


if __name__ == '__main__':
    all_sites = config.TABLES.keys()
    today = date.today() - timedelta(days=2)
    day_before = date.today() - timedelta(days=2)
    yesterday_stats_range = StatsRange("Yesterday", today, today)
    day_before_stats_range = StatsRange("Day Before", day_before, day_before)

    
    #network_breakdown = NetworkArticleBreakdown(['foo@example.net'], 'Network Article Breakdown', all_sites, 
        #yesterday_stats_range, day_before_stats_range, "Daily Summary", article_limit=25)
    network_breakdown = TrafficSourceBreakdown(['foo@example.net'], 'Network Article Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range, None, '.')
    generated_html = network_breakdown.generate_report()
    #print generated_html.encode("utf-8")
