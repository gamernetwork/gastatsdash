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

analytics = get_analytics()

image_strings = {}

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

        global image_strings
        
        for image in image_strings:
            image_string = image_strings[image]
            img_part = MIMEImage(image_string, 'png')
            img_part.add_header('Content-ID', '<%s>' % image)
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
    def __init__(self, recipients, subject, sites, period, second_period, report_span, period_list, destination_path, black_list):
        super(TrafficSourceBreakdown, self).__init__(recipients, subject, sites, period)
        self.second_period = second_period
        self.period_list = period_list
        self.report_span = report_span
        self.destination_path = destination_path
        self.black_list = black_list
    
    def aggregate_data(self, results, tables, metrics):
        """
        Add up all the data from the different sites
        in : list of dictionaries for results, two lists containing strings of keys for dimensions and metrics
        out: aggregated list of dictionaries 
        """
        #use and pass out dictionary instead less nesting forloops
        organised_results = []
        for item in results:
            site = {}
            total_dimensions = {}
            for table_type in tables:
                total_dimensions[table_type] = item[table_type]  
            site['dimensions'] = total_dimensions
            total_metrics = {}
            for metric in metrics:
                total_metrics[metric] = item[metric]                                         
            site['metrics'] = total_metrics
            organised_results.append(site)

        
        aggregated_results = [] 
        length = len(aggregated_results)
        for item in organised_results:
            #item = {'dimensions' :{'source/medium':'google'}, 'metrics':{'visitors':20, 'pageviews':15}}
            if length > 0:
                for count, record in enumerate(aggregated_results):
                    if item['dimensions'] == record['dimensions']:
                        for metric in metrics:            
                            record['metrics'][metric] += item['metrics'][metric]
                        break
                    else:
                        #has it gone throgh all the records??
                        if count == length-1:
                            new_record = {}
                            new_record['dimensions'] = item['dimensions']
                            new_record['metrics'] = item['metrics']
                            aggregated_results.append(new_record)
                            break
                        else:
                            continue
            else:
                record = {}
                record['dimensions'] = item['dimensions']
                record['metrics'] = item['metrics']
                aggregated_results.append(record)
                
            length = len(aggregated_results) 
            
        return aggregated_results                   
     
    def sort_data(self, unsorted_list, metric, limit = 26):
        """
        sorts the data of a list containing separated 'dimension' and 'metric' dictionaries
        in: the list, 'metric' : the metric label to sort by, limit: the amount of results to return
        out: the top results highest to lowest 
        """
        def sortDev(item):
            return item['metrics'][metric]                
                    
        sorted_list = sorted(unsorted_list, key = sortDev, reverse = True)
        top_results = sorted_list[:limit]      
        return top_results  
        
    def add_change(self, top_results, second_period, metrics):
        """
        calculate change in metrics, add this to metrics dictionary
        """
        #what if pass in a dictionary? 
        #make this more generic for pageviews etc as well
        for item in top_results:
            for metric in metrics:
                key = 'second_%s' % metric
                item['metrics']['change_%s' % metric] = 0            
                item['metrics'][key] = 0
                for it in second_period:
                    if item['dimensions'] == it['dimensions']:
                        change = item['metrics'][metric] - it['metrics'][metric]
                        item['metrics']['change_%s' % metric] = change            
                        item['metrics'][key] = it['metrics'][metric]
        return top_results    
           
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
        patches, text = plot.pie(filtered_percents, colors=colors,shadow=False)
        plot.legend(patches, legend_labels, loc = 'best', prop={'size':12})
        plot.axis('equal')
        #image_path = '%s/%s.png' % (dest_path, result_type)
        #plot.savefig(image_path)
        
        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png')
        imgdata.seek(0)
        
        global image_strings
        name = 'social_graph'
        image_strings[name] = imgdata.buf
        
        return name

        
        
        
        

    def plot_scatter_graph(self, results, period, dest_path):
        """
        scatter graph of peak points for all sites, saved to destination of file
        """

        dt = []
        sessions = []
        date = period.get_start()
        values = date.split('-')
        ym = values[0] + '/' + values[1]
        print 'YM : ', ym
        for site in results:
            day = results[site]['day']
            hour = results[site]['hour']
            minute = results[site]['minute']
            session = int(results[site]['sessions'])
            time = hour + ':' + minute 
            date = ym +'/' + day
            dati = date + ' ' + time
            dt.append(str(dati))
            sessions.append(session)
            
   
        print 'DT : ', dt
        time_value = [datetime.strptime(t, '%Y/%m/%d %H:%M') for t in dt]       
        print 'TIMES : ', time_value
        print 'SESSIONS :', sessions
       
        plot.close('all')
        figure, axis = plot.subplots(1,1)
        min = time_value[0]
        max = time_value[0]
        for d in time_value:
            if d < min:
                min = d
            elif d > max:
                max = d

        for count, site in enumerate(results):
            label = site + '  ' + results[site]['sessions'] + ' on ' + results[site]['day'] + ' at ' + results[site]['hour'] + ':' + results[site]['minute']        
            axis.scatter(time_value[count], sessions[count], c=[random.random(), random.random(), random.random()], label=label, edgecolors='none')
            
            
        plot.xlim(min, max)
        axis.set_ylim(bottom=0)
        
        if self.report_span == 'daily':
            axis.xaxis.set_major_locator(plotdates.HourLocator())
            axis.xaxis.set_minor_locator(plotdates.MinuteLocator())
        elif self.report_span == 'weekly':
            axis.xaxis.set_major_locator(plotdates.DayLocator())
            axis.xaxis.set_minor_locator(plotdates.HourLocator())       
        axis.xaxis.set_major_formatter(plotdates.DateFormatter('%d %H:%M'))

        axis.spines['top'].set_visible(False)
        axis.spines['bottom'].set_visible(False)
        axis.spines['right'].set_visible(False)
        axis.spines['left'].set_visible(False)
        
        axis.get_xaxis().tick_bottom()
        axis.get_yaxis().tick_left()
                    
        plot.tick_params(axis='both', which='both', bottom='on', top='off', labelbottom='on', left='on', right='off', labelleft='on')
        plot.xticks(rotation='vertical')
        
        plot.xlabel('Date/Time')
        plot.ylabel('Cumulative Peak Number Visitors')
        
        box = axis.get_position()

        axis.set_position([box.x0, box.y0, box.width * 0.6, box.height * 0.6])

        fontP = FontProperties()
        fontP.set_size('small')
        lgd = plot.legend(loc='center left', bbox_to_anchor=(1,0.5), prop=fontP)
        
        #image_path = '%s/peak1.png' % dest_path
        #plot.savefig(image_path, bbox_extra_artists=(lgd,), bbox_inches='tight')

        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png', bbox_extra_artists=(lgd,), bbox_inches='tight')
        imgdata.seek(0)
        global image_strings
        name = 'peak_graph'
        image_strings[name] = imgdata.buf
        
        return name

        
        
        

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
        axis.xaxis.set_major_formatter(plotdates.DateFormatter('%Y-%m'))
        
        line_1, = axis.plot_date(new_dates, desktop_results, '-', linewidth=2.0, solid_joinstyle='bevel', marker='|', markeredgewidth=1.0)
        line_2, = axis.plot_date(new_dates, mobile_results, '-', linewidth=2.0, solid_joinstyle='bevel', marker='|', markeredgewidth=1.0)
        line_3, = axis.plot_date(new_dates, tablet_results, '-', linewidth=2.0, solid_joinstyle='bevel', marker='|', markeredgewidth=1.0)
        
        plot.xlabel('Dates')
        plot.ylabel('Percentage of Visitors')
        axis.legend((line_1, line_2, line_3), ('desktop', 'mobile', 'tablet')) 
        
        axis.fmt_xdata = plotdates.DateFormatter('%Y-%m')
        #figure.autofmt_xdate()
        #image_path = '%s/device1.png' % dest_path
        #plot.savefig(image_path)
               
        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png')
        imgdata.seek(0)
        
        global image_strings
        name = 'month_graph'
        image_strings[name] = imgdata.buf
        
        return name
                     
    def generate_report(self):
        """
        main function 
        gather data from analytics, call functions to aggregate/sort data and draw charts 
        template to html
        """
        results_traffic = []
        results_device = []
        results_browser = []
        results_social = []
        second_results_traffic = []
        second_results_device = []
        second_results_browser = []
        second_results_social = []
        third_results_device = []

        totals={'first_period':{'visitors':0, 'pageviews':0, 'pv_per_session':0.0, 'avg_time':0.0}, 'second_period':{'visitors':0, 'pageviews':0, 
                    'pv_per_session':0.0, 'avg_time':0.0}}
                    
        num_sites = len(self.sites)
        site_names=[]
        
        if num_sites > 1:
            peak = {}
        
        #MAIN LOOP TO GET DATA 
        for count, site in enumerate(self.sites):
            site_ga_id = config.TABLES[site]
            print 'Calculation for %s ...' % site
            results_traffic += analytics.get_site_traffic_for_period(site_ga_id, self.period)
            second_results_traffic += analytics.get_site_traffic_for_period(site_ga_id, self.second_period)
            print '-- traffic'
            results_device += analytics.get_site_devices_for_period(site_ga_id, self.period)
            second_results_device += analytics.get_site_devices_for_period(site_ga_id, self.second_period)
            print '-- devices (day)'
            #results_browser += analytics.get_site_browsers_for_period(site_ga_id, self.period)
            #second_results_browser += analytics.get_site_browsers_for_period(site_ga_id, self.second_period)
            #print '-- broswer'
            results_social += analytics.get_site_socials_for_period(site_ga_id, self.period)
            second_results_social += analytics.get_site_socials_for_period(site_ga_id, self.second_period)
            print '-- social networks'
            
            first_totals = analytics.get_site_totals_for_period(site_ga_id, self.period)[0]
            second_totals = analytics.get_site_totals_for_period(site_ga_id, self.second_period)[0]
            
            for key in totals['first_period'].keys():
                totals['first_period'][key] += float(first_totals[key])
            for key in totals['second_period'].keys():
                totals['second_period'][key] += float(second_totals[key])
            print '-- totals'
            if num_sites == 1:
                peak = analytics.get_site_peak_for_period(site_ga_id, self.period)[0]
            else:
                peak[site] = analytics.get_site_peak_for_period(site_ga_id, self.period)[0]
                
            if num_sites < 24:
                site_names.append(site)
               
            print ' %d / %d sites complete ' % (count+1, num_sites)
            #if count ==4: break    
        print peak       
        #AGGREGATE AND SORT ALL DATA 
        unsorted_traffic = self.aggregate_data(results_traffic, ['source'], ['visitors', 'pageviews'])
        unsorted_devices = self.aggregate_data(results_device, ['deviceCategory'], ['visitors'])
        #unsorted_browsers = self.aggregate_data(results_browser, ['browser'], ['visitors'])
        unsorted_socials = self.aggregate_data(results_social, ['socialNetwork'],['visitors', 'pageviews'])
        
        second_traffic = self.aggregate_data(second_results_traffic, ['source'], ['visitors', 'pageviews'])
        second_devices = self.aggregate_data(second_results_device, ['deviceCategory'], ['visitors'])
        #second_browsers = self.aggregate_data(second_results_browser, ['browser'], ['visitors'])
        second_socials = self.aggregate_data(second_results_social, ['socialNetwork'],['visitors', 'pageviews'])                
        
        sorted_traffic = self.sort_data(unsorted_traffic, 'visitors', 11)
        sorted_devices = self.sort_data(unsorted_devices, 'visitors', 5)
        #sorted_browsers = self.sort_data(unsorted_browsers, 'visitors', 11)
        sorted_socials = self.sort_data(unsorted_socials, 'visitors', 6)
        
        top_traffic_results = self.add_change(sorted_traffic, second_traffic, ['visitors', 'pageviews'])
        top_device_results = self.add_change(sorted_devices, second_devices, ['visitors'])
        #top_browser_results = self.add_change(sorted_browsers, second_browsers)
        top_social_results = self.add_change(sorted_socials, second_socials, ['visitors'])
        
        #OVERVIEW
        if num_sites > 1 :
            totals['first_period']['pv_per_session'] = totals['first_period']['pv_per_session']/float(num_sites)
            totals['first_period']['avg_time'] = (totals['first_period']['avg_time']/float(num_sites))/60.0
            
            totals['second_period']['pv_per_session'] = totals['second_period']['pv_per_session']/float(num_sites)
            totals['second_period']['avg_time'] = (totals['second_period']['avg_time']/float(num_sites))/60.0
            
            peak_img = self.plot_scatter_graph(peak, self.period, self.destination_path)   
        else:
            totals['first_period']['avg_time'] = totals['first_period']['avg_time']/60.0
            totals['second_period']['avg_time'] = totals['second_period']['avg_time']/60.0
            peak_img = 0
        
        totals['change'] = {}
        for key in totals['first_period']:
            change = totals['first_period'][key] - totals['second_period'][key]
            totals['change'][key] = change
        
        #total number visitors use social networks
        totals['first_period']['social_visitors'] = 0
        for social in unsorted_socials:
            visitors = social['metrics']['visitors']
            totals['first_period']['social_visitors'] += visitors   

        
        #ARTICLES 
        top_sites = self.sort_data(unsorted_traffic, 'visitors', 25)
        site_referrals = OrderedDict()   
        social_articles = OrderedDict()
        second_site_referrals = OrderedDict()
        second_social_articles = OrderedDict()
        top_articles = []
        second_top_articles = []
        num_articles = 0
        num_referrals = 0
        if self.report_span == 'daily':
            num_articles = 1
            num_referrals = 3
        elif self.report_span == 'weekly':
            num_articles = 5
            num_referrals = 5
        #LOOP TO GET ARTICLES 
        for site in self.sites:
            site_ga_id = config.TABLES[site]
            print 'site : ', site 
            #TOP SITE REFERRAL ARTICLES
            count = 0
            for item in top_sites:
                source_medium = item['dimensions']['source']
                source = source_medium.split(' / ')[0]
                print 'SOURCE SITE : ', source 
                #black_list = ['google', '(direct)', 'eurogamer', 'facebook', 'Twitter', 'bing', '^t.co', 'reddit.com', 'yahoo']
                black_ex = '|'
                black_string = black_ex.join(self.black_list)
                regex = re.compile(black_string)
                m = regex.search(source)
                if m: 
                    continue;
                    #do nothing, move onto next, do not include in site referrals
                elif count == num_referrals:
                    break;
                else:  
                    data = analytics.get_article_breakdown(site_ga_id, self.period, extra_filters='ga:source==%s' % source)
                    second_data = analytics.get_article_breakdown(site_ga_id, self.second_period, extra_filters='ga:source==%s' % source)
                    data = list(data.items())[:6]
                    second_data = list(second_data.items())[:6]
                    separated_data = []
                    for article in data:
                        separated_data.append(article[1])
                    try:
                        site_referrals[source] +=  separated_data
                    except KeyError:
                        site_referrals[source] = separated_data 
                    second_separated_data = []
                    for article in second_data:
                        second_separated_data.append(article[1])
                    try:
                        second_site_referrals[source] +=  second_separated_data
                    except KeyError:
                        second_site_referrals[source] = second_separated_data 
                    print 'add data'
                    count += 1     
            #TOP SOCIAL ARTICLES                                            
            for item in top_social_results:
                social_network = item['dimensions']['socialNetwork'] 
                print 'SOCIAL NETWORK : ', social_network
                data = analytics.get_article_breakdown(site_ga_id, self.period, extra_filters='ga:socialNetwork==%s' % social_network)
                second_data = analytics.get_article_breakdown(site_ga_id, self.second_period, extra_filters='ga:socialNetwork==%s' % social_network)
                data = list(data.items())[:6]
                second_data = list(second_data.items())[:6]
                separated_data = []
                for article in data:
                    separated_data.append(article[1])
                try:
                    social_articles[social_network] +=  separated_data
                except KeyError:
                    social_articles[social_network] = separated_data                
                second_separated_data = []
                for article in second_data:
                    second_separated_data.append(article[1])
                try:
                    second_social_articles[social_network] +=  second_separated_data
                except KeyError:
                    second_social_articles[social_network] = second_separated_data 
            #TOP TEN ARTICLES 
            articles_data = analytics.get_article_breakdown(site_ga_id, self.period)
            separated_data = []
            for item in articles_data:
                separated_data.append(articles_data[item])
            second_articles_data = analytics.get_article_breakdown(site_ga_id, self.second_period)
            second_separated_data = []
            for item in second_articles_data:
                second_separated_data.append(second_articles_data[item])
            top_articles += separated_data[:11]
            second_top_articles = second_separated_data[:11]                      
        #AGGREGATE AND SORT ALL ARTICLES            
        for source in site_referrals:
            un_sorted = self.aggregate_data(site_referrals[source], ['title', 'host'], ['pageviews'])
            sorted = self.sort_data(un_sorted, 'pageviews', num_articles)   
            second_aggregate = self.aggregate_data(second_site_referrals[source], ['title', 'host'], ['pageviews']) 
            complete = self.add_change(sorted, second_aggregate, ['pageviews'])          
            site_referrals[source] = complete 
            
        for social in social_articles:
            un_sorted = self.aggregate_data(social_articles[social], ['title', 'host'], ['pageviews'])
            sorted = self.sort_data(un_sorted, 'pageviews', num_articles)
            second_aggregate = self.aggregate_data(second_social_articles[social], ['title', 'host'], ['pageviews'])
            complete = self.add_change(sorted, second_aggregate, ['pageviews'])
            social_articles[social] = complete            

        un_sorted = self.aggregate_data(top_articles, ['title', 'host'], ['pageviews'])
        sorted = self.sort_data(un_sorted, 'pageviews', 10)   
        second_aggregate = self.aggregate_data(second_top_articles, ['title', 'host'], ['pageviews']) 
        complete_articles = self.add_change(sorted, second_aggregate, ['pageviews'])
        
        #MONTHLY DEVICES
        
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
        
    
        #DRAW GRAPHS    
        #self.draw_graph(top_traffic_results, totals['first_period']['visitors'], 'traffic1', self.destination_path)
        if self.report_span == 'weekly':
            social_img = self.draw_graph(top_social_results, totals['first_period']['social_visitors'], 'social1', self.destination_path)   
        else:
            social_img = 0       
        device_img = self.plot_line_graph(devices, self.period_list, total_dict, self.destination_path)
                  
          
        #RENDER TEMPLATE                                         
        report_html = render_template(self.template, {
            'start_date': self.period.get_start(),
            'end_date': self.period.get_end(),
            'report_span': self.report_span,
            #'img_url': config.ASSETS_URL,
            'img_name' : {'social' : social_img, 'device': device_img, 'peak':peak_img},
            'traffic_list' : top_traffic_results,
            'devices_list' : top_device_results, 
            'social_list' : top_social_results,
            'social_articles': social_articles,
            'site_referrals': site_referrals,
            'top_articles' : complete_articles,
            'num_sites': num_sites,
            'peak': peak,
            'site_names': site_names,
            'totals': totals      
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
