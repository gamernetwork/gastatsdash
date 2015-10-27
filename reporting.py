import re, pprint
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta
from collections import OrderedDict, defaultdict

import config
from analytics import get_analytics, StatsRange
from renderer import render_template
from dateutils import subtract_one_month

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
        html = self.generate_report()
        subject = self.get_subject()
        recipients = self.recipients
        self.emailer.send_email(recipients, subject, html)
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
        return report_html
	

class NetworkArticleBreakdown(ArticleBreakdown):
    template = "article_dash.html"

    def format_top_data(self, top_data):
        formatted = []
        for article in top_data:
            formatted.append((article['path'], article))
        return formatted

    def generate_report(self):
        all_network_data = []
        for count, site in enumerate(self.sites):
            print "Calculating for %s..." % site           
            site_ga_id = config.TABLES[site]
            data = self.get_article_breakdown_for_site(site_ga_id)
            all_network_data.extend(data.values())
            print "%d/24 sites complete" % (count+1)
            
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

    def _get_change(self, first_period_totals, second_period_totals):
        """
        """
        change = {}
        current_visitors = first_period_totals.get('visitors', 0)
        previous_visitors = second_period_totals.get('visitors', 0)
        change['visitors'] = current_visitors - previous_visitors
        current_pageviews = first_period_totals.get('pageviews', 0)
        previous_pageviews = second_period_totals.get('pageviews', 0)
        change['pageviews'] = current_pageviews - previous_pageviews
        return change
        
    def generate_report(self):
        aggregate_pageviews = 0
        aggregate_visitors = 0
        site_data = []
        countries = ["Czec", "Germa", "Denma", "Spai", "Franc", "Italy", 
            "Portug", "Swede", "Polan", "Brazi", "Belgiu", "Netherl", 
            "United Ki", "Irela", "United St", "Canad", "Austral", "New Ze"]
        for site in self.sites:
            site_ga_id = config.TABLES[site]
            first_period_totals = analytics.get_site_totals_for_period(
                site_ga_id, self.period)[0]
            second_period_totals = analytics.get_site_totals_for_period(
                site_ga_id, self.second_period)[0]
            if self.report_span == 'month':
                start = self.period.start_date - timedelta(days=365)
                end = self.period.end_date - timedelta(days=365)
                last_year_period = StatsRange("This Month Last Year", start, end)
                last_year_totals = analytics.get_site_totals_for_period(
                    site_ga_id, last_year_period)[0]
            change_totals = self._get_change(first_period_totals, second_period_totals)
            country_data = analytics.get_country_breakdown_for_period(site_ga_id, self.period, countries)
            analytics.get
            data = {
                'name': site,
                'totals': first_period_totals,
                'previous_totals': second_period_totals,
                'change': change_totals,
                'country_metrics': country_data,
            }
            if self.report_span == 'month':
                data['yoy_totals'] = last_year_totals
                data['yoy_change'] = self._get_change(first_period_totals, last_year_totals)
            site_data.append(data)
            aggregate_pageviews += first_period_totals['pageviews']
            aggregate_visitors += first_period_totals['visitors']
        site_data = sorted(site_data, key=lambda k: k['totals']['pageviews'],
            reverse=True)

        country_data = {}
        for data in site_data:
            for country, metrics in data['country_metrics'].items():
                try:
                    country_data[country]['metrics']['pageviews'] += metrics['pageviews']
                    country_data[country]['metrics']['visitors'] += metrics['visitors']
                except KeyError:
                    country_data[country] = {
                        'name': country,
                        'metrics': {
                            'pageviews': metrics['pageviews'],
                            'visitors': metrics['visitors'],
                        }
                    }
        country_metrics = country_data.values()
        country_metrics = sorted(country_metrics, 
            key=lambda k: k['metrics']['pageviews'], reverse=True)
        cumulative_pageviews = 0
        cumulative_visitors = 0
        for country_stats in country_metrics:
            cumulative_pageviews += country_stats['metrics']['pageviews']
            cumulative_visitors += country_stats['metrics']['visitors']
            country_stats['cum'] = {
                'pageviews': cumulative_pageviews,
                'visitors': cumulative_visitors,
            }

        report_html = render_template(self.template, {
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'period': self.report_span,
            'totals': {'pageviews': aggregate_pageviews, 'visitors': aggregate_visitors},
            'sites': site_data,
            'countries': country_metrics
        })
        return report_html


class TrafficSourceBreakdown(Report):
    template='traffic_source.html'
    
    #init
    def __init__(self, recipients, subject, sites, period, second_period):
        super(TrafficSourceBreakdown, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
    
    #COULD I MERGE THESE FUNCTIONS AS A LOT OF REPITITION?
    """"
    def aggregate_site_traffic(self, results):
        compound_results = {}
        for source in results:
            source_label = source['source/medium']
            try:
                compound_results[source_label]['visitors'] += source['visitors']
                compound_results[source_label]['pageviews'] += source['pageviews']
            except KeyError:
                compound_results[source_label] = {'visitors': source['visitors'], 'pageviews': source['pageviews']}
        return compound_results        
                    
    def aggregate_site_socials(self, results):
        compound_socials = {}    
        for network in results:
            network_label = network['socialNetwork']
            try:
                compound_socials[network_label] += network['visitors']
            except KeyError:
                compound_socials[network_label] = network['visitors']                
        return compound_socials
        
    def aggregate_site_devices(self, results):
        compound_devices = {}
        for item in results:
            dev_category = item['deviceCategory']
            browser = item['browser']
            os = item['OS']
            number = item['visitors']
            try:#should it be if they all equal the same? 
                compound_devices[(dev_category, browser, os)] += number                     
            except KeyError:
                compound_devices[(dev_category, browser, os)] = number 
                
        return compound_devices         
    """
    #condensing functions       
     
    def aggregate_data(self, results, table_type):
        compound_results = {}  
        unsorted_list = []  
        if table_type == 'socials':
            for item in results:
                label = item['socialNetwork']
                try:
                    compound_results[label] += item['visitors']
                except KeyError:
                    compound_results[label] = item['visitors']   
            for key in compound_results.keys():              
                list_item = {'dimensions':{'socialNetwork': key},'metrics': {'visitors': compound_results[key]}}
                unsorted_list.append(list_item)      
            return unsorted_list 
            
        elif table_type == 'traffic':
            for item in results:
                label = item['source/medium']
                try:
                    compound_results[label]['visitors'] += item['visitors']
                    compound_results[label]['pageviews'] += item['pageviews']
                except KeyError:
                    compound_results[label] = {'visitors': item['visitors'], 'pageviews': item['pageviews']}  
                  
            for key in compound_results.keys():              
                list_item = {'dimensions':{'source': key}, 'metrics':{'visitors': compound_results[key]['visitors'], 'pageviews':compound_results[key]['pageviews']}}
                unsorted_list.append(list_item)      
            return unsorted_list 
                            
        elif table_type == 'devices':  
            for item in results:
                label = (item['deviceCategory'], item['browser'], item['OS'])
                try:
                    compound_results[label] += item['visitors']
                except KeyError:
                    compound_results[label] = item['visitors']
            for key in compound_results.keys():              
                list_item = {'dimensions':{'device_category': key[0], 'browser' : key[1], 'os' : key[2]}, 'metrics':{'visitors' : compound_results[key]}}
                unsorted_list.append(list_item)      
            return unsorted_list                               
    
    """"     
    def sort_site_traffic(self, compound_results):
        def sortKey(item):
            return item['visitors']
              
        compound_list = []
        for key in compound_results.keys():
            src = {'source': key, 'visitors': compound_results[key]['visitors'], 'pageviews':compound_results[key]['pageviews']}
            compound_list.append(src)       
        sorted_list = sorted(compound_list, key=sortKey, reverse=True)
        top_results = sorted_list[:26] 
        return top_results 
                 
    def sort_site_socials(self, compound_results):
        def sortSocial(item):
            return item['visitors']
                            
        social_list=[]
        for key in compound_results.keys():
            item = {'socialNetwork' : key, 'visitors' : compound_results[key]}
            social_list.append(item)
        sorted_social_list = sorted(social_list, key = sortSocial, reverse = True)
        top_results = sorted_social_list[:26]
        return top_results  
        
    def sort_site_devices(self, compound_results):
        def sortDev(item):
            return item['visitors']                
        device_list=[]
        for key in compound_results.keys():  
            item = {'device_category': key[0], 'browser' : key[1], 'os' : key[2], 'visitors' : compound_results[key]}
            device_list.append(item)
        sorted_device_list = sorted(device_list, key = sortDev, reverse = True)
        top_results = sorted_device_list[:26]      
        return top_results    
    """    
    def sort_data(self, unsorted_list, metric, limit = 26):
        def sortDev(item):
            return item['metrics'][metric]                
                    
        sorted_list = sorted(unsorted_list, key = sortDev, reverse = True)
        top_results = sorted_list[:limit]      
        return top_results  
        
    def add_change(self, top_results, second_period):
        for item in top_results:
            item['metrics']['change'] = 0            
            item['metrics']['second_visitors'] = 0
            for it in second_period:
                if item['dimensions'] == it['dimensions']:
                    change = item['metrics']['visitors'] - it['metrics']['visitors']
                    item['metrics']['change'] = change            
                    item['metrics']['second_visitors'] = it['metrics']['visitors']
        return top_results       
                 
    def generate_report(self):
        #still to do movement period-period 
        #refactor these into one, just pass in variable either traffic, social or device?
        tables = ['traffic', 'devices', 'socials']
        results_traffic = []
        results_device = []
        results_social = []
        second_results_traffic = []
        second_results_device = []
        second_results_social = []
        total_visitors = 0
        total_pageviews = 0
        total_social_visitors = 0
        second_total_visitors = 0
        second_total_pageviews = 0
        second_total_social_visitors = 0
        for count, site in enumerate(self.sites):
            site_ga_id = config.TABLES[site]
            print 'Calculation for %s ...' % site
            results_traffic += analytics.get_site_traffic_for_period(site_ga_id, self.period)
            second_results_traffic += analytics.get_site_traffic_for_period(site_ga_id, self.second_period)
            print '-- traffic'
            results_device += analytics.get_site_devices_for_period(site_ga_id, self.period)
            second_results_device += analytics.get_site_devices_for_period(site_ga_id, self.second_period)
            print '-- devices'
            results_social += analytics.get_site_socials_for_period(site_ga_id, self.period)
            second_results_social += analytics.get_site_socials_for_period(site_ga_id, self.second_period)
            print '-- social networks'
            totals = analytics.get_site_totals_for_period(site_ga_id, self.period)[0]
            total_visitors += totals['visitors']
            total_pageviews += totals['pageviews']
            
            second_totals = analytics.get_site_totals_for_period(site_ga_id, self.second_period)[0]
            second_total_visitors += second_totals['visitors']
            second_total_pageviews += second_totals['pageviews']
               
               
            print ' %d / 24 sites complete ' % (count+1)
            #if count ==4: break          
        
        unsorted_traffic = self.aggregate_data(results_traffic, 'traffic')
        unsorted_devices = self.aggregate_data(results_device, 'devices')
        unsorted_socials = self.aggregate_data(results_social, 'socials')
        
        second_traffic = self.aggregate_data(second_results_traffic, 'traffic')
        second_devices = self.aggregate_data(second_results_device, 'devices')
        second_socials = self.aggregate_data(second_results_social, 'socials')        
        
        sorted_traffic = self.sort_data(unsorted_traffic, 'visitors', 26)
        sorted_devices = self.sort_data(unsorted_devices, 'visitors', 26)
        sorted_socials = self.sort_data(unsorted_socials, 'visitors', 26)
        
        top_traffic_results = self.add_change(sorted_traffic, second_traffic)
        top_device_results = self.add_change(sorted_devices, second_devices)
        top_social_results = self.add_change(sorted_socials, second_socials)
        

        """"       
        compound_traffic = self.aggregate_site_traffic(results_traffic)
        compound_socials = self.aggregate_site_socials(results_social)
        compound_devices = self.aggregate_site_devices(results_device)
        
        second_compound_traffic = self.aggregate_site_traffic(second_results_traffic)
        second_compound_socials = self.aggregate_site_socials(second_results_social)
        second_compound_devices = self.aggregate_site_devices(second_results_device)
        print '-- aggregated'
        
        top_traffic_results = self.sort_site_traffic(compound_traffic)  
        top_social_results = self.sort_site_socials(compound_socials)         
        top_device_results = self.sort_site_devices(compound_devices) 
        """
        #sort the second period data tot he same order as first period, so correct comparison
        """"        
        for item in top_traffic_results:
            key = item['source']
            try:
                change = item['visitors'] - second_compound_traffic[key]['visitors']
                item['change'] = change
                item['second_visitors'] = second_compound_traffic[key]['visitors']
            except KeyError:
                item['change'] = 0
                item['second_visitors'] = 0  
                
        for item in top_social_results:
            key = item['socialNetwork']
            try:
                change = item['visitors'] - second_compound_socials[key]
                item['change'] = change
                item['second_visitors'] = second_compound_socials[key]
            except KeyError:
                item['change'] = 0 
                item['second_visitors'] = 0  
                  
        for item in top_device_results:
            dev_category = item['device_category']
            browser = item['browser']
            os = item['os']
            key = (dev_category, browser, os)
            try:#if devcat, browser and os all equal the same 
                change = item['visitors'] - second_compound_devices[key]
                item['change'] = change
                item['second_visitors'] = second_compound_devices[key]
            except KeyError:
                item['change'] = 0
                item['second_visitors'] = 0   
        """
        #total number visitors use social networks
        for social in unsorted_socials:
            visitors = social['metrics']['visitors']
            total_social_visitors += visitors           
                                                    
        report_html = render_template(self.template, {
            'start_date': self.period.get_start(),
            'end_date': self.second_period.get_end(),
            'traffic_list' : top_traffic_results,
            'devices_list' : top_device_results,  
            'social_list' : top_social_results,
            'totals': {'pageviews': total_pageviews, 'visitors': total_visitors, 'socials' : total_social_visitors, 
                        'second_visitors': second_total_visitors}       
        })
        return report_html


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
    report = report_class(config['recipients'], config['subject'], 
        config['sites'], period, **kwargs)
    return report


if __name__ == '__main__':
    all_sites = config.TABLES.keys()
    today = date.today() - timedelta(days=2)
    day_before = date.today() - timedelta(days=3)
    yesterday_stats_range = StatsRange("Yesterday", today, today)
    day_before_stats_range = StatsRange("Day Before", day_before, day_before)
    #network_breakdown = NetworkArticleBreakdown(['foo@example.net'], 'Network Article Breakdown', all_sites, 
        #yesterday_stats_range, day_before_stats_range, "Daily Summary", article_limit=25)
    network_breakdown = TrafficSourceBreakdown(['foo@example.net'], 'Network Article Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range)
    generated_html = network_breakdown.generate_report()
    #print generated_html.encode("utf-8")
