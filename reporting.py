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

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date, timedelta, datetime
from collections import OrderedDict, defaultdict

import config
from analytics import get_analytics, StatsRange
from renderer import render_template
from dateutils import subtract_one_month

from django import template 
from django.template.defaultfilters import stringfilter

from data_aggregator import DataAggregator

register = template.Library()

@register.filter(is_safe=True)
@stringfilter
def get_report_change(value):
  	if value == 'daily':
  		  return 'WoW'
  	elif value == 'weekly':
  		  return 'Weekly'
  	elif value == 'monthly':
  		  return 'Monthly'   
          		  

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

    def format_top_data(self, top_data):
        formatted = []
        for article in top_data:
            formatted.append((article['path'], article))
        return formatted

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
         
        network_data = get_data.get_site_totals(self.sites, self.period, self.second_period, True)   
        
        country_metrics = get_data.get_country_metrics(self.sites, self.period, self.second_period)

        report_html = render_template(self.template, {
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'period': self.report_span,
            'totals': network_data['totals'],
            'sites': network_data['site_data'],
            'countries': country_metrics
        })
        results = {
            'html' : report_html,
            'images' : []
        }
        return results


class TrafficSourceBreakdown(Report):
    template='traffic_source.html'
    
    #init
    def __init__(self, recipients, subject, sites, period, second_period, report_span, period_list, destination_path, black_list):
        super(TrafficSourceBreakdown, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
        self.period_list = period_list
        self.report_span = report_span
        self.destination_path = destination_path
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
        for site in config.TABLES.keys():
            site_ga_id = config.TABLES[site]
            site_data_available = analytics.data_available_for_site(site_ga_id, 
                self.period.get_end())
            if site_data_available == False:
                return False
        return True
          
           
    def draw_graph(self, results, total, result_type, dest_path):
        """
        draw pie chart of percentages and save to same destination as file 
        """
        labels = []
        percents = []
        for item in results:
            label = item['dimensions'].values() # use join and split 
            labels.append(label)
            percent = (item['metrics']['visitors'] / float(total)) * 100
            percents.append(percent)
            
        new_labels = []
        for li in labels:
            new = ";".join(li)
            new_labels.append(new)
        
        filtered_labels = []
        filtered_percents = []
        for count, percent in enumerate(percents):
            if percent > 1.0:
                filtered_labels.append(new_labels[count])
                filtered_percents.append(percent)
            else:
                continue        
    
        legend_labels=[]    
        for count, text in enumerate(filtered_labels):
            label = "%s, %d.1%%" %(text,filtered_percents[count])
            legend_labels.append(label)  
                        
        colors =['red', 'orangered','gold', 'limegreen', 'blue', 'indigo', 'violet']
        plot.close('all')
        figure, axis = plot.subplots(1,1)
        figure.set_size_inches(6,4)
        patches, text = plot.pie(filtered_percents, colors=colors,shadow=False)
        plot.legend(patches, legend_labels, loc = 'best', prop={'size':12})
        plot.axis('equal')
        image_path = '%s/%s.png' % (dest_path, result_type)
        plot.savefig(image_path)
        #box = axis.get_position()
        #axis.set_position([box.x0, box.y0, box.width * 0.3, box.height * 0.3])
        
        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png', bbox_inches='tight')
        imgdata.seek(0)
        
        name = 'social_graph'
        
        return {'name' : name, 'string' : imgdata.buf}
               

    def plot_scatter_graph(self, results, period, dest_path):
        """
        scatter graph of peak points for all sites, saved to destination of file
        """
        

        sites = ['eurogamer.de', 'eurogamer.es', 'eurogamer.it', 'eurogamer.nl', 'eurogamer.pt', 'eurogamer.cz', 'eurogamer.se', 'eurogamer.dk', 'eurogamer.pl', 'brasilgamer.com.br']
        #sites = []
        dt_list = []
        #sessions = []
        dt_dict = {}
        sessions = {}
        date = period.get_start()
        values = date.split('-')
        ym = values[0] + '/' + values[1]
        peak_results = {}
        print 'YM : ', ym
        for site in results:
            if site not in sites:
                print 'Site: ', results[site], 'is in the list'
                day = results[site]['day']
                hour = results[site]['hour']
                minute = results[site]['minute']
                session = int(results[site]['sessions'])
                time = hour + ':' + minute 
                date = ym +'/' + day
                dati = date + ' ' + time
                dt_list.append(str(dati))
                #sessions.append(session)
                dt_dict[site] = str(dati)
                sessions[site] = session
                peak_results[site] = results[site]
            else:
                continue
            
   
        #print 'DT : ', dt
        #time_value = [datetime.strptime(t, '%Y/%m/%d %H:%M') for t in dt]  
        time_value = {}  
        timings = []
        for site in dt_dict:
            timing = datetime.strptime(dt_dict[site], '%Y/%m/%d %H:%M')
            time_value[site] = timing
            timings.append(timing)
           
       
        plot.close('all')
        figure, axis = plot.subplots(1,1)
        
        figure.set_size_inches(6,4)

        min = timings[0]
        max = timings[0]
        for d in timings:
            if d < min:
                min = d
            elif d > max:
                max = d
                
        site_names = config.CUSTOM_NAMES
        site_symbols = config.CUSTOM_SYMBOLS

        #looks like the only way to get annotations to work will be to work out surrounding text box and then move it to somwhere with no overlaps
        #or just amke rotations random?
        annotations = []
        for count, site in enumerate(peak_results):
            label = site_names[site] + '  ' + peak_results[site]['sessions'] + ' on ' + peak_results[site]['day'] + ' at ' + peak_results[site]['hour'] + ':' + peak_results[site]['minute']  
            colour = [random.random(), random.random(), random.random()] 
            axis.scatter(time_value[site], sessions[site], c=colour, label=label, edgecolors='none')
            #symbols axis.scatter(time_value[count], sessions[count], marker=site_symbols[site], label=label)      
            annotations.append(axis.text(time_value[site], sessions[site], site_names[site], ha='left', rotation_mode='anchor', rotation=45, fontsize=8))
            #random angle random.randint(0,45)
            #trasnlucent coloured bbox bbox=dict(boxstyle='round,pad=0.2', fc=colour, alpha=0.3),
            
        plot.xlim(min, max)
        axis.set_ylim(bottom=0)
        
        if self.report_span == 'daily':
            axis.xaxis.set_major_locator(plotdates.HourLocator())
            axis.xaxis.set_minor_locator(plotdates.MinuteLocator())
        elif self.report_span == 'weekly' or 'monthly':
            axis.xaxis.set_major_locator(plotdates.DayLocator())
            axis.xaxis.set_minor_locator(plotdates.HourLocator())       
        axis.xaxis.set_major_formatter(plotdates.DateFormatter('%a %H:%M'))

        axis.spines['top'].set_visible(False)
        axis.spines['bottom'].set_visible(False)
        axis.spines['right'].set_visible(False)
        axis.spines['left'].set_visible(False)
        
        axis.get_xaxis().tick_bottom()
        axis.get_yaxis().tick_left()
                    
        plot.tick_params(axis='both', which='both', bottom='on', top='off', labelbottom='on', left='on', right='off', labelleft='on')
        plot.xticks(rotation='vertical', fontsize=8)
        plot.yticks(fontsize=8)
        
        plot.xlabel('Date/Time', fontsize=8)
        plot.ylabel('Concurrent Peak Number Visitors', fontsize=8)
        
        #box = axis.get_position()

        #axis.set_position([box.x0, box.y0, box.width * 0.6, box.height * 0.6])

        fontP = FontProperties()
        fontP.set_size('small')
        lgd = plot.legend(loc='center left', bbox_to_anchor=(1,0.5), prop=fontP)
        
        image_path = '%s/peak1.png' % dest_path
        plot.savefig(image_path, bbox_extra_artists=(lgd,), bbox_inches='tight')

        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png', bbox_extra_artists=(lgd,), bbox_inches='tight')
        imgdata.seek(0)
        name = 'peak_graph'
        
        return {'name' : name, 'string' : imgdata.buf}
    

    def plot_line_graph(self, results, periods, total, dest_path):
        """
        line graph of percentages over a list of periods, saved to destination of file
        """
        #list of dates
        dates = []
        #list of data
        desktop_results = []
        mobile_results = []
        tablet_results = []

        for date in periods:
            dates.append(date.get_start())  

        for month in results: 
            desktop_total = 0
            mobile_total = 0
            tablet_total = 0  
            for device in results[month]:
                if device['deviceCategory'] == 'desktop':
                    desktop_total += device['visitors']
                elif device['deviceCategory'] == 'mobile':
                    mobile_total += device['visitors']
                elif device['deviceCategory'] == 'tablet':
                    tablet_total += device['visitors']
                                
            desktop_percent = (desktop_total / float(total[month])) * 100
            desktop_results.append(desktop_percent)
            mobile_percent = (mobile_total / float(total[month])) * 100
            mobile_results.append(mobile_percent)
            tablet_percent = (tablet_total / float(total[month])) * 100
            tablet_results.append(tablet_percent)
                                                   
        x = [datetime.strptime(d,'%Y-%m-%d').date() for d in dates] #list of datetime objects
        new_dates = plotdates.date2num(x) #converts dates tofloating poit numbers      

        plot.close('all')
        figure, axis = plot.subplots(1,1,figsize=(12,9))
        
        figure.set_size_inches(6,4)
        
        last_num = len(new_dates)
        x_min = new_dates[last_num-1]
        x_max = new_dates[0]

        axis.spines['top'].set_visible(False)
        axis.spines['bottom'].set_visible(False)
        axis.spines['right'].set_visible(False)
        axis.spines['left'].set_visible(False)
        
        axis.get_xaxis().tick_bottom()
        axis.get_yaxis().tick_left()
        
        plot.xlim(x_min, x_max)
        plot.ylim(0,100)
        
        for y in range(0,100,10):
            plot.plot(new_dates, [y] * len(new_dates), '--', lw=0.5, color='black', alpha=0.3)
            
        plot.tick_params(axis='both', which='both', bottom='off', top='off', labelbottom='on', left='off', right='off', labelleft='on')
                        
        #axis.xaxis.set_minor_locator(plotdates.DayLocator())
        axis.xaxis.set_major_locator(plotdates.MonthLocator())
        axis.xaxis.set_major_formatter(plotdates.DateFormatter("%b '%y"))
        
        line_1, = axis.plot_date(new_dates, desktop_results, '-', linewidth=2.0, solid_joinstyle='bevel', marker='|', markeredgewidth=1.0)
        line_2, = axis.plot_date(new_dates, mobile_results, '-', linewidth=2.0, solid_joinstyle='bevel', marker='|', markeredgewidth=1.0)
        line_3, = axis.plot_date(new_dates, tablet_results, '-', linewidth=2.0, solid_joinstyle='bevel', marker='|', markeredgewidth=1.0)
        
        plot.xlabel('Dates')
        plot.ylabel('Percentage of Visitors')
        axis.legend((line_1, line_2, line_3), ('desktop', 'mobile', 'tablet')) 
        
        axis.fmt_xdata = plotdates.DateFormatter("%b '%y")
        #figure.autofmt_xdate()
        image_path = '%s/device1.png' % dest_path
        plot.savefig(image_path)
        #box = axis.get_position() 
        #axis.set_position([box.x0, box.y0, box.width * 0.3, box.height * 0.3])
              
        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png', bbox_inches='tight')
        imgdata.seek(0)

        name = 'month_graph'
        
        return {'name' : name, 'string' : imgdata.buf}
        
                     
    def generate_report(self):
        """
        main function 
        gather data from analytics, call functions to aggregate/sort data and draw charts 
        template to html
        """

        image_strings = []              
               
        total_num_sites = len(config.TABLES)            
        num_sites = len(self.sites)
        site_names=[]
            
        #getting stat ranges for monthly accum
        today = self.period.end_date
        first = datetime(today.year, today.month, 1).date()
        month_range = StatsRange("Monthly Aggregate", first, today)
        prev_yr_first = first - timedelta(days=365)
        prev_yr_today = today - timedelta(days=365)
        last_yr_range = StatsRange("Last Year Monthly Aggregate", prev_yr_first, prev_yr_today)     
        
        
        #get data for totals of the site and network if not network report
        period_totals = get_data.get_overview_totals(self.sites, self.period, self.second_period, True) 
        monthly_totals = get_data.get_overview_totals(self.sites, month_range, last_yr_range, False) 
        
        if num_sites < total_num_sites:
            network_period_totals = get_data.get_overview_totals('all_sites', self.period, self.second_period, True) 
            network_monthly_totals = get_data.get_overview_totals('all_sites', month_range, last_yr_range, False) 
          
        #get data for traffic/devices/socials 
        results = get_data.get_traffic_device_social_data(self.sites, self.period, self.second_period)
        socials = results['social']['first_period']
        traffic = results['traffic']['first_period']
        devices = results['devices']['first_period']
        
        second_socials = results['social']['second_period']
        second_traffic = results['traffic']['second_period']
        second_devices = results['devices']['second_period']
                
        sorted_traffic = get_data.sort_data(traffic, 'visitors', 11)
        sorted_devices = get_data.sort_data(devices, 'visitors', 5)
        sorted_socials = get_data.sort_data(socials, 'visitors', 6)              
          
        top_traffic_results = get_data.add_change(sorted_traffic, second_traffic, ['visitors', 'pageviews'])
        top_device_results = get_data.add_change(sorted_devices, second_devices, ['visitors'])
        top_social_results = get_data.add_change(sorted_socials, second_socials, ['visitors'])        
        
                
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
            
        social_articles = get_data.get_social_referral_articles(self.sites, self.period, self.second_period, top_social_results, num_articles)
        site_referrals = get_data.get_site_referral_articles(self.sites, self.period, self.second_period, top_sites, self.black_list, num_articles, num_referrals)
        top_articles = get_data.get_top_articles(self.sites, self.period, self.second_period, num_articles)
        
        #MONTHLY DEVICES
        """"
        devices ={}  
        total_dict = {}           
        for count, date in enumerate(self.period_list):
            value = []
            visitors =0
            totals_list = []
            for count_site, site in enumerate(self.sites):
                key = 'month_%d' % count 
                site_ga_id = config.TABLES[site]
                value += analytics.get_site_devices_for_period(site_ga_id, date)
                devices[key] = value
                totals_list = analytics.get_site_totals_for_period(site_ga_id, date)[0]
                visitors += totals_list['visitors']
                total_dict[key] = visitors
            print '-- devices (month)' 
        
        devices_list = []
        for month in devices:
            results = devices[month]
            unsorted_devices = self.aggregate_data(results, ['deviceCategory'], ['visitors'])
            sorted_devices = self.sort_data(unsorted_devices, 'visitors', 26)
            devices_list.append(sorted_devices)
        
        """
        #DRAW GRAPHS    
        #self.draw_graph(top_traffic_results, totals['first_period']['visitors'], 'traffic1', self.destination_path)
        if self.report_span == 'weekly' or 'monthly':
            social= self.draw_graph(top_social_results, period_totals['first_period']['social_visitors'], 'social1', self.destination_path)
            social_img = social['name']
            image_strings.append(social)
        else:
            social_img = 0       
        #device = self.plot_line_graph(devices, self.period_list, total_dict, self.destination_path)
        #device_img = device['name']
        #image_strings.append(device)
        
        @register.filter(is_safe=True)
        @stringfilter
        def get_report_change(value):
          	if value == 'daily':
          		  return 'WoW'
          	elif value == 'weekly':
          		  return 'Weekly'
          	elif value == 'monthly':
          		  return 'Monthly'    
       
          
        #RENDER TEMPLATE                                         
        report_html = render_template(self.template, {
            'start_date': self.period.start_date.strftime("%d/%m/%y"),
            'end_date': self.period.end_date.strftime("%d/%m/%y"),
            'report_span': self.report_span,
            'subject': self.get_subject(),
            #'img_url': config.ASSETS_URL,
            'img_name' : {'social' : social_img},
            'traffic_list' : top_traffic_results,
            'devices_list' : top_device_results, 
            'social_list' : top_social_results,
            'social_articles': social_articles,
            'site_referrals': site_referrals,
            'top_articles' : top_articles,
            'num_sites': num_sites,
            'total_num_sites': total_num_sites,
            #'peak': peak,
            'period_totals': period_totals, 
            'monthly_totals': monthly_totals, 
            'network_period_totals': network_period_totals,
            'network_monthly_totals': network_monthly_totals        
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
            kwargs['second_period'] = StatsRange.get_previous_period(period, 'WEEKLY')            
            
            
    month_list =[]
    end_date = period.start_date
    if kwargs.get('period_list'):
        for month in range(0, kwargs['period_list']):
            #get previous months
            start_date = subtract_one_month(end_date)
            month_list.append(StatsRange("month_%d" % month, start_date, end_date))
            end_date = start_date       
        kwargs['period_list'] = month_list   
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
