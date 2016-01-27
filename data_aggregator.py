import config
import re
from datetime import date, timedelta, datetime
from analytics import get_analytics, StatsRange
from collections import OrderedDict, defaultdict

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plot
import matplotlib.dates as plotdates
from matplotlib.font_manager import FontProperties

import StringIO
import cStringIO
import urllib, base64

analytics = get_analytics()

class DataAggregator():

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

    #NETWORK BREAKDOWN        
    def _get_change(self, first_period_totals, second_period_totals):
        """
        """
        change = {}
        for key in first_period_totals:
            value = float(first_period_totals[key]) - float(second_period_totals[key])
            change[key] = value
        return change           
        
    def get_country_metrics(self, sites, period):
        countries = ["Czec", "Germa", "Denma", "Spai", "Franc", "Italy", 
            "Portug", "Swede", "Polan", "Brazi", "Belgiu", "Netherl", 
            "United Ki", "Irela", "United St", "Canad", "Austral", "New Ze"]
        site_data = []
        num_sites = len(sites)
        
        start = period.start_date - timedelta(days=365)
        end = period.end_date - timedelta(days=365)
        last_year_period = StatsRange("This Period Last Year", start, end)              
        
        for count, site in enumerate(sites):
            site_ga_id = config.TABLES[site]
            print "getting country data for %s.. %d / %d" % (site, count+1, num_sites)
            
            country_data = analytics.get_country_breakdown_for_period(site_ga_id, period, countries)
            prev_country_data = analytics.get_country_breakdown_for_period(site_ga_id, last_year_period, countries)
            data = {
                'name' : site,
                'country_metrics' : country_data,
                'prev_metrics' : prev_country_data,
            }
            site_data.append(data)
            

        country_data = {}
        for data in site_data:
            for country, metrics in data['country_metrics'].items():
                try:
                    prev_pageviews = data['prev_metrics'][country]['pageviews']
                    prev_visitors = data['prev_metrics'][country]['visitors']     
                except KeyError:
                    prev_pageviews = 0
                    prev_visitors = 0
                    
                try:
                    pageviews = metrics['pageviews']
                    visitors = metrics['visitors']     
                except KeyError:
                    pageviews = 0
                    visitors = 0 
                    metrics = {'pageviews':0, 'visitors':0, 'country':country}                   
                    
                try:
                    country_data[country]['metrics']['pageviews'] += pageviews
                    country_data[country]['metrics']['visitors'] += visitors
                    country_data[country]['yoy_metrics']['pageviews'] += prev_pageviews
                    country_data[country]['yoy_metrics']['visitors'] += prev_visitors                  
                    
                except KeyError:
                    country_data[country] = {
                        'dimensions': {
                            'name': country,
                        },
                        'metrics': {
                            'pageviews': pageviews,
                            'visitors': visitors,
                        },
                        'yoy_metrics': {
                            'pageviews': prev_pageviews,
                            'visitors': prev_visitors,                         
                        }
                    }
        country_metrics = country_data.values()
        country_metrics = sorted(country_metrics, 
            key=lambda k: k['metrics']['visitors'], reverse=True)
        cumulative_pageviews = 0
        cumulative_visitors = 0
        for country_stats in country_metrics:
            cumulative_pageviews += country_stats['metrics']['pageviews']
            cumulative_visitors += country_stats['metrics']['visitors']
            country_stats['cum'] = {
                'pageviews': cumulative_pageviews,
                'visitors': cumulative_visitors,
            }
            country_stats['yoy_metrics']['pageviews_change'] = country_stats['metrics']['pageviews'] - country_stats['yoy_metrics']['pageviews']
            country_stats['yoy_metrics']['visitors_change'] = country_stats['metrics']['visitors'] - country_stats['yoy_metrics']['visitors']

        return country_metrics

    #NETWORK ARTICLE BREAKDOWN        
    """def get_article_breakdown(self, sites, period, second_period, article_limit):
        all_network_data = []
        num_sites = len(sites)
        
        for count, site in enumerate(sites):        
            site_ga_id = config.TABLES[site]
            print "getting article breakdown for %s.. %d / %d" % (site, count+1, num_sites)
            data = analytics.get_article_breakdown_two_periods(site_ga_id, period, second_period, min_pageviews=250)
            all_network_data.extend(data.values())

            
        sorted_data = sorted(all_network_data, key=lambda article: article['pageviews'], reverse=True)
        top_network_data = list(sorted_data)[:article_limit]
        formatted = []
        for article in top_network_data:
            formatted.append((article['path'], article))      
        return formatted"""

    def remove_query_string(self, path):
        exp = '^([^\?]+)\?.*'
        regex = re.compile(exp) 
        m = regex.search(path)
        if m:
            new_path = regex.split(path)[1]            
            return new_path       
        else:
            return path      
        
    def get_top_articles(self, sites, period, second_period, num_articles):
        top_articles = []
        second_top_articles = []
        num_sites = len(sites)
        
        
        #LOOP TO GET ARTICLES 
        for n, site in enumerate(sites):
            site_ga_id = config.TABLES[site]
            print 'articles for %s.. %d / %d ' % (site, n+1, num_sites)      
            #TOP TEN ARTICLES 
            articles_data = analytics.get_article_breakdown(site_ga_id, period)
            #print 'articles', articles_data
            separated_data = []
            for item in articles_data:
                path = articles_data[item]['path']  
                new_path = self.remove_query_string(path)
                articles_data[item]['path'] = new_path       
                separated_data.append(articles_data[item])

            second_articles_data = analytics.get_article_breakdown(site_ga_id, second_period)
            second_separated_data = []
            for item in second_articles_data:
                path = second_articles_data[item]['path']  
                new_path = self.remove_query_string(path)
                second_articles_data[item]['path'] = new_path 
                second_separated_data.append(second_articles_data[item])
            top_articles += separated_data[:num_articles]
            
            second_top_articles += second_separated_data[:num_articles]   
            
        un_sorted = self.aggregate_data(top_articles, ['title', 'host', 'path'], ['pageviews'])
        sorted = self.sort_data(un_sorted, 'pageviews', num_articles)   
        second_aggregate = self.aggregate_data(second_top_articles, ['title', 'host', 'path'], ['pageviews']) 
        complete_articles = self.add_change(sorted, second_aggregate, ['pageviews'])    

        return complete_articles        

   
    def get_traffic_device_social_data(self, sites, period, second_period):
        results_traffic = []
        results_device = []
        results_social = []
        second_results_traffic = []
        second_results_device = []
        second_results_social = []
        last_yr_results_social = []
        num_sites = len(sites)
        results = {}
        
        #devices should have yoy change
        start = period.start_date - timedelta(days=365)
        end = period.end_date - timedelta(days=365)
        last_year_period = StatsRange("This Period Last Year", start, end)          
        
        #LOOP TO GET TRAFFIC/DEVICE/SOCIAL DATA
        for count, site in enumerate(sites):
            site_ga_id = config.TABLES[site]
            print 'Calculation for %s ... %d / %d' % (site, count+1, num_sites)
            results_traffic += analytics.get_site_traffic_for_period(site_ga_id, period)
            second_results_traffic += analytics.get_site_traffic_for_period(site_ga_id, second_period)
            print '-- traffic'
            results_device += analytics.get_site_devices_for_period(site_ga_id, period)
            second_results_device += analytics.get_site_devices_for_period(site_ga_id, last_year_period)
            print '-- devices'
            results_social += analytics.get_site_socials_for_period(site_ga_id, period)
            second_results_social += analytics.get_site_socials_for_period(site_ga_id, second_period)
            last_yr_results_social += analytics.get_site_socials_for_period(site_ga_id, last_year_period)
            print '-- social networks'

        #AGGREGATE AND SORT ALL DATA 
        first_traffic = self.aggregate_data(results_traffic, ['source'], ['visitors', 'pageviews'])
        first_devices = self.aggregate_data(results_device, ['deviceCategory'], ['visitors'])
        first_socials = self.aggregate_data(results_social, ['socialNetwork'],['visitors', 'pageviews'])
        
        second_traffic = self.aggregate_data(second_results_traffic, ['source'], ['visitors', 'pageviews'])
        second_devices = self.aggregate_data(second_results_device, ['deviceCategory'], ['visitors'])
        second_socials = self.aggregate_data(second_results_social, ['socialNetwork'],['visitors', 'pageviews'])     
        last_year_socials = self.aggregate_data(last_yr_results_social, ['socialNetwork'],['visitors', 'pageviews'])            
        
        for item in first_socials:
            for data in last_year_socials:
                if item['dimensions']['socialNetwork'] == data['dimensions']['socialNetwork']:
                    yoy_change = self._get_change(item['metrics'], data['metrics'])
                    item['yoy_change'] = yoy_change
        
        results['traffic'] = {}
        results['devices'] = {}
        results['social'] = {}
        
        results['traffic']['first_period'] = first_traffic
        results['traffic']['second_period'] = second_traffic
        results['devices']['first_period'] = first_devices
        results['devices']['second_period'] = second_devices       
        results['social']['first_period'] = first_socials
        results['social']['second_period'] = second_socials
        results['social']['last_year_period'] = last_year_socials
        
                
        return results       

    #SITE TOTALS FOR NETWORK BREAKDOWN AND TRAFFIC SOURCE BREAKDOWN
    def get_site_totals(self, sites, period, second_period, yoy_change=False):
        aggregate_pageviews = 0
        aggregate_visitors = 0
        site_data = []
        num_sites = len(sites)
        totals={'first_period':{'visitors':0, 'pageviews':0, 'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}, 'second_period':{'visitors':0, 'pageviews':0, 
            'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}}
            
        if yoy_change == True:
            start = period.start_date - timedelta(days=365)
            end = period.end_date - timedelta(days=365)
            last_year_period = StatsRange("This Period Last Year", start, end)  
            totals['last_yr_data'] = {'visitors':0, 'pageviews':0, 'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}          

        for count, site in enumerate(sites):
            print "calculating for %s..." % site
            site_ga_id = config.TABLES[site]
            try:
                first_period_totals = analytics.get_site_totals_for_period(site_ga_id, period)[0]
            except IndexError:
                first_period_totals = {'visitors': 0, 'pageviews': 0, 'avg_time': '0', 'pv_per_session': '0', 'sessions':0}
                
            try:
                second_period_totals = analytics.get_site_totals_for_period(site_ga_id, second_period)[0]
            except IndexError:
                second_period_totals = {'visitors': 0, 'pageviews': 0, 'avg_time': '0', 'pv_per_session': '0', 'sessions':0}
                
            if yoy_change== True:
                try:
                    last_year_totals = analytics.get_site_totals_for_period(site_ga_id, last_year_period)[0]
                except IndexError:
                    last_year_totals = {'visitors': 0, 'pageviews': 0, 'avg_time': '0', 'pv_per_session': '0', 'sessions':0}
                    
            for key in totals['first_period'].keys():
                totals['first_period'][key] += float(first_period_totals[key])
            for key in totals['second_period'].keys():
                totals['second_period'][key] += float(second_period_totals[key])
            if yoy_change == True:
                for key in totals['last_yr_data'].keys():
                    totals['last_yr_data'][key] += float(last_year_totals[key])                            
                    
            change_totals = self._get_change(first_period_totals, second_period_totals)
            #country_data = analytics.get_country_breakdown_for_period(site_ga_id, self.period, countries)
            data = {
                'name': site,
                'totals': first_period_totals,
                'previous_totals': second_period_totals,
                'change': change_totals,
                #'country_metrics': country_data,
            }
            if yoy_change== True:
                data['yoy_totals'] = last_year_totals
                data['yoy_change'] = self._get_change(first_period_totals, last_year_totals)
                
            site_data.append(data)
            
            print ' %d / %d sites complete ' % (count+1, num_sites)  
        
        totals['first_period']['pv_per_session'] = totals['first_period']['pv_per_session']/float(num_sites)
        totals['first_period']['avg_time'] = (totals['first_period']['avg_time']/float(num_sites))/60.0
        
        totals['second_period']['pv_per_session'] = totals['second_period']['pv_per_session']/float(num_sites)
        totals['second_period']['avg_time'] = (totals['second_period']['avg_time']/float(num_sites))/60.0

        totals['change'] = self._get_change(totals['first_period'], totals['second_period'])   
                
        if yoy_change == True:
            totals['last_yr_data']['pv_per_session'] = totals['last_yr_data']['pv_per_session']/float(num_sites)
            totals['last_yr_data']['avg_time'] = (totals['last_yr_data']['avg_time']/float(num_sites))/60.0  
            totals['yoy_change'] = self._get_change(totals['first_period'], totals['last_yr_data'])
                
        site_data = sorted(site_data, key=lambda k: k['totals']['visitors'],
            reverse=True)
        
            
        results = {}
        results['totals'] = totals
        results['network_data'] = site_data
        return results                         

        
    def get_site_referral_articles(self, sites, period, second_period, top_sites, black_list, num_articles, num_referrals):
        site_referrals = OrderedDict()   
        second_site_referrals = OrderedDict()  
        num_sites = len(sites)      
            
        #LOOP TO GET ARTICLES 
        for n, site in enumerate(sites):
            site_ga_id = config.TABLES[site]
            print 'articles for %s.. %d / %d ' % (site, n+1, num_sites) 
            #TOP SITE REFERRAL ARTICLES
            count = 0
            for item in top_sites:
                source_medium = item['dimensions']['source']
                source = source_medium.split(' / ')[0]
                black_ex = '|'
                black_string = black_ex.join(black_list)
                regex = re.compile(black_string)
                match = regex.search(source)
                if match: 
                    continue;
                    #do nothing, move onto next, do not include in site referrals
                elif count == num_referrals:
                    break;
                else:  
                    data = analytics.get_article_breakdown(site_ga_id, period, extra_filters='ga:source==%s' % source)
                    second_data = analytics.get_article_breakdown(site_ga_id, second_period, extra_filters='ga:source==%s' % source)
                    data = list(data.items())[:6]
                    second_data = list(second_data.items())[:6]
                    separated_data = []
                    for article in data:
                        path = article[1]['path']  
                        new_path = self.remove_query_string(path)
                        article[1]['path'] = new_path    
                        separated_data.append(article[1])
                    try:
                        site_referrals[source] +=  separated_data
                    except KeyError:
                        site_referrals[source] = separated_data 
                        
                    second_separated_data = []
                    for article in second_data:
                        path = article[1]['path']  
                        new_path = self.remove_query_string(path)
                        article[1]['path'] = new_path                       
                        second_separated_data.append(article[1])
                    try:
                        second_site_referrals[source] +=  second_separated_data
                    except KeyError:
                        second_site_referrals[source] = second_separated_data 
                    print 'from %s.. %d / %d ' % (source, count+1, num_referrals) 
                    count += 1  
                    
        #AGGREGATE AND SORT ARTICLES            
        for source in site_referrals:
            un_sorted = self.aggregate_data(site_referrals[source], ['title', 'host', 'path'], ['pageviews'])
            sorted = self.sort_data(un_sorted, 'pageviews', num_articles)   
            second_aggregate = self.aggregate_data(second_site_referrals[source], ['title', 'host', 'path'], ['pageviews']) 
            complete = self.add_change(sorted, second_aggregate, ['pageviews'])          
            site_referrals[source] = complete 
            
        return site_referrals
        
        
    def get_social_referral_articles(self, sites, period, second_period, social_networks, num_articles): 
        social_articles = OrderedDict()
        second_social_articles = OrderedDict()    
        num_sites = len(sites)    
        num_socials = len(social_networks)
           
        #LOOP TO GET ARTICLES 
        for n, site in enumerate(sites):      
            site_ga_id = config.TABLES[site]
            print 'articles for %s.. %d / %d ' % (site, n+1, num_sites) 
      
             #TOP SOCIAL ARTICLES                                            
            for m, item in enumerate(social_networks):
                social_network = item['dimensions']['socialNetwork'] 
                data = analytics.get_article_breakdown(site_ga_id, period, extra_filters='ga:socialNetwork==%s' % social_network)
                second_data = analytics.get_article_breakdown(site_ga_id, second_period, extra_filters='ga:socialNetwork==%s' % social_network)
                data = list(data.items())[:6]
                second_data = list(second_data.items())[:6]
                separated_data = []
                for article in data:
                    path = article[1]['path']  
                    new_path = self.remove_query_string(path)
                    article[1]['path'] = new_path                   
                    separated_data.append(article[1])
                try:
                    social_articles[social_network] +=  separated_data
                except KeyError:
                    social_articles[social_network] = separated_data                
                second_separated_data = []
                for article in second_data:
                    path = article[1]['path']  
                    new_path = self.remove_query_string(path)
                    article[1]['path'] = new_path                   
                    second_separated_data.append(article[1])
                try:
                    second_social_articles[social_network] +=  second_separated_data
                except KeyError:
                    second_social_articles[social_network] = second_separated_data   
                    
                print 'from %s.. %d / %d ' % (social_network, m+1, num_socials)   
                    
                    
        #AGGREGATE AND SORT ARTICLES              
        for social in social_articles:
            un_sorted = self.aggregate_data(social_articles[social], ['title', 'host', 'path'], ['pageviews'])
            sorted = self.sort_data(un_sorted, 'pageviews', num_articles)
            second_aggregate = self.aggregate_data(second_social_articles[social], ['title', 'host', 'path'], ['pageviews'])
            complete = self.add_change(sorted, second_aggregate, ['pageviews'])
            social_articles[social] = complete                
            
        return social_articles   

    def get_monthly_device_data(self, sites, period_list):
        devices ={}  
        total_dict = {}           
        for count, date in enumerate(period_list):
            month = date.start_date.strftime('%b')
            print "for %s.." % month
            value = []
            visitors =0
            totals_list = []
            for count_site, site in enumerate(sites):
                print "for %s.." % site
                key = '%s' % month
                site_ga_id = config.TABLES[site]
                value += analytics.get_site_devices_for_period(site_ga_id, date)
                devices[key] = value
                try:
                    totals_list = analytics.get_site_totals_for_period(site_ga_id, date)[0]
                except IndexError:
                    totals_list = {'visitors':0, 'pageviews':0, 'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}
                visitors += totals_list['visitors']
                total_dict[key] = visitors
        
        devices_list = []
        for month in devices:
            results = devices[month]
            unsorted_devices = self.aggregate_data(results, ['deviceCategory'], ['visitors'])
            sorted_devices = self.sort_data(unsorted_devices, 'visitors', 26)
            devices_list.append(sorted_devices)
            
        results = {}
        results['devices'] = devices
        results['totals'] = total_dict
        #print devices
        return results



    def plot_line_graph(self, results, periods):
        """
        line graph of percentages over a list of periods, saved to destination of file
        """
        #list of dates
        dates = []
        months = []
        #list of data
        desktop_results = []
        mobile_results = []
        tablet_results = []

        for date in periods:
            dates.append(date.get_start())  
            months.append(date.start_date.strftime('%b'))
            

        device_results = results['devices']
        total_results = results['totals']
        for month in months: 
            print month
            desktop_total = 0
            mobile_total = 0
            tablet_total = 0  
            for device in device_results[month]:
                if device['deviceCategory'] == 'desktop':
                    desktop_total += device['visitors']
                elif device['deviceCategory'] == 'mobile':
                    mobile_total += device['visitors']
                elif device['deviceCategory'] == 'tablet':
                    tablet_total += device['visitors']
            
            try:                     
                desktop_percent = (desktop_total / float(total_results[month])) * 100
            except ZeroDivisionError:
                desktop_percent = 0
            desktop_results.append(desktop_percent)
            
            try: 
                mobile_percent = (mobile_total / float(total_results[month])) * 100
            except ZeroDivisionError:
                mobile_percent = 0
            mobile_results.append(mobile_percent)
            
            try:
                tablet_percent = (tablet_total / float(total_results[month])) * 100
            except ZeroDivisionError:
                tablet_percent = 0
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
        
        plot.xlabel('Dates', fontsize=8)
        plot.ylabel('Percentage of Visitors', fontsize=8)
        
        fontP = FontProperties()
        fontP.set_size('small')
        axis.legend((line_1, line_2, line_3), ('desktop', 'mobile', 'tablet'), prop=fontP) 
        
        axis.fmt_xdata = plotdates.DateFormatter("%b '%y")
        
        plot.xticks(rotation='vertical', fontsize=8)
        plot.yticks(fontsize=8)
        
        #figure.autofmt_xdate()
        image_path = '/var/www/dev/faye/statsdash_reports/device1.png' 
        #plot.savefig(image_path, bbox_inches='tight')
        #box = axis.get_position() 
        #axis.set_position([box.x0, box.y0, box.width * 0.3, box.height * 0.3])
              
        imgdata = StringIO.StringIO()
        plot.savefig(imgdata, format = 'png', bbox_inches='tight')
        imgdata.seek(0)

        name = 'device_graph'
        
        return {'name' : name, 'string' : imgdata.buf}           
                      
                    