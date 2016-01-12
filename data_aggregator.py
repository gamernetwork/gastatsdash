import config
import re
from datetime import date, timedelta, datetime
from analytics import get_analytics, StatsRange
from collections import OrderedDict, defaultdict


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
        
    def get_country_metrics(self, sites, period, second_period):
        #aaaah
        countries = ["Czec", "Germa", "Denma", "Spai", "Franc", "Italy", 
            "Portug", "Swede", "Polan", "Brazi", "Belgiu", "Netherl", 
            "United Ki", "Irela", "United St", "Canad", "Austral", "New Ze"]
        site_data = []
        for site in sites:
            site_ga_id = config.TABLES[site]
            
            country_data = analytics.get_country_breakdown_for_period(site_ga_id, period, countries)
            data = {
                'name' : site,
                'country_metrics' : country_data,
            }
            site_data.append(data)

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
            
        return country_metrics
   
    def get_traffic_device_social_data(self, sites, period, second_period):
        results_traffic = []
        results_device = []
        results_social = []
        second_results_traffic = []
        second_results_device = []
        second_results_social = []
        
        results = {}
        
        #LOOP TO GET TRAFFIC/DEVICE/SOCIAL DATA
        for count, site in enumerate(sites):
            site_ga_id = config.TABLES[site]
            print 'Calculation for %s ...' % site
            results_traffic += analytics.get_site_traffic_for_period(site_ga_id, period)
            second_results_traffic += analytics.get_site_traffic_for_period(site_ga_id, second_period)
            print '-- traffic'
            results_device += analytics.get_site_devices_for_period(site_ga_id, period)
            second_results_device += analytics.get_site_devices_for_period(site_ga_id, second_period)
            print '-- devices (day)'
            results_social += analytics.get_site_socials_for_period(site_ga_id, period)
            second_results_social += analytics.get_site_socials_for_period(site_ga_id, second_period)
            print '-- social networks'

        #AGGREGATE AND SORT ALL DATA 
        first_traffic = self.aggregate_data(results_traffic, ['source'], ['visitors', 'pageviews'])
        first_devices = self.aggregate_data(results_device, ['deviceCategory'], ['visitors'])
        first_socials = self.aggregate_data(results_social, ['socialNetwork'],['visitors', 'pageviews'])
        
        second_traffic = self.aggregate_data(second_results_traffic, ['source'], ['visitors', 'pageviews'])
        second_devices = self.aggregate_data(second_results_device, ['deviceCategory'], ['visitors'])
        second_socials = self.aggregate_data(second_results_social, ['socialNetwork'],['visitors', 'pageviews'])                
        
        results['traffic'] = {}
        results['devices'] = {}
        results['social'] = {}
        
        results['traffic']['first_period'] = first_traffic
        results['traffic']['second_period'] = second_traffic
        results['devices']['first_period'] = first_devices
        results['devices']['second_period'] = second_devices       
        results['social']['first_period'] = first_socials
        results['social']['second_period'] = second_socials
        
                
        return results       

    def get_site_totals(self, sites, period, second_period, yoy_change=False):
        aggregate_pageviews = 0
        aggregate_visitors = 0
        site_data = []

        for site in sites:
            site_ga_id = config.TABLES[site]
            first_period_totals = analytics.get_site_totals_for_period(site_ga_id, period)[0]
            second_period_totals = analytics.get_site_totals_for_period(site_ga_id, second_period)[0]
            if yoy_change== True:
                start = period.start_date - timedelta(days=365)
                end = period.end_date - timedelta(days=365)
                last_year_period = StatsRange("This Period Last Year", start, end)
                try:
                    last_year_totals = analytics.get_site_totals_for_period(site_ga_id, last_year_period)[0]
                except IndexError:
                    last_year_totals = {'visitors': 0, 'pageviews': 0, 'avg_time': '0', 'pv_per_session': '0', 'sessions':0}
                    
                    
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
            aggregate_pageviews += first_period_totals['pageviews']
            aggregate_visitors += first_period_totals['visitors']
            
        site_data = sorted(site_data, key=lambda k: k['totals']['pageviews'],
            reverse=True)
        
        network_data = {}
        network_data['site_data'] = site_data
        network_data['totals'] = {'pageviews': aggregate_pageviews, 'visitors': aggregate_visitors}
            
        return network_data                          
                 
    def get_overview_totals(self, sites, period, second_period, yoy_change = False):
        #def get_overview_totals(self, sites, period, second_period, last_yr_period, month_range, last_yr_month):
        #input sites and period
        #return totals dictionary
        print 'get overview totals'
        if sites == 'all_sites':
            print 'for all sites'
            sites = config.TABLES.keys()
            num_sites = len(sites)
        else:
            print 'for ', sites
            num_sites = len(sites)


        totals={'first_period':{'visitors':0, 'pageviews':0, 'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}, 'second_period':{'visitors':0, 'pageviews':0, 
                    'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}}
        
        if yoy_change == True:
            totals['last_yr_data'] = {'visitors':0, 'pageviews':0, 'pv_per_session':0.0, 'avg_time':0.0, 'sessions':0}
            start = period.get_unformatted_start() - timedelta(days=365)
            end = period.get_unformatted_end() - timedelta(days=365) 
            last_yr_period = StatsRange("Last Year Period", start, end)
                    
            
        for count, site in enumerate(sites):
            print 'Calculation for %s ...' % site
            site_ga_id = config.TABLES[site]
            #causes index error if the other network sites dont have data available yet!
            first_totals = analytics.get_site_totals_for_period(site_ga_id, period)[0]
            second_totals = analytics.get_site_totals_for_period(site_ga_id, second_period)[0]
            if yoy_change == True:
                try:
                    last_yr_totals = analytics.get_site_totals_for_period(site_ga_id, last_yr_period)[0]
                except IndexError:
                    last_yr_totals = {'visitors': 0, 'pageviews': 0, 'avg_time': '0', 'pv_per_session': '0', 'sessions':0}
            
            for key in totals['first_period'].keys():
                totals['first_period'][key] += float(first_totals[key])
            for key in totals['second_period'].keys():
                totals['second_period'][key] += float(second_totals[key])
            if yoy_change == True:
                for key in totals['last_yr_data'].keys():
                    totals['last_yr_data'][key] += float(last_yr_totals[key])                                  
                                             
            print ' %d / %d sites complete ' % (count+1, num_sites)        
            
        totals['first_period']['pv_per_session'] = totals['first_period']['pv_per_session']/float(num_sites)
        totals['first_period']['avg_time'] = (totals['first_period']['avg_time']/float(num_sites))/60.0
        
        totals['second_period']['pv_per_session'] = totals['second_period']['pv_per_session']/float(num_sites)
        totals['second_period']['avg_time'] = (totals['second_period']['avg_time']/float(num_sites))/60.0
        
        if yoy_change == True:
            totals['last_yr_data']['pv_per_session'] = totals['last_yr_data']['pv_per_session']/float(num_sites)
            totals['last_yr_data']['avg_time'] = (totals['last_yr_data']['avg_time']/float(num_sites))/60.0        


        totals['change'] = {}
        for key in totals['first_period']:
            change = totals['first_period'][key] - totals['second_period'][key]
            totals['change'][key] = change
        
        if yoy_change == True:    
            totals['yoy_change'] = {}
            for key in totals['first_period']:
                change = totals['first_period'][key] - totals['last_yr_data'][key]
                totals['yoy_change'][key] = change 
                           
                       
        return totals
        
        
        
    def get_site_referral_articles(self, sites, period, second_period, top_sites, black_list, num_articles, num_referrals):
        site_referrals = OrderedDict()   
        second_site_referrals = OrderedDict()        
            
        #LOOP TO GET ARTICLES 
        for site in sites:
            site_ga_id = config.TABLES[site]
            print 'site : ', site 
            #TOP SITE REFERRAL ARTICLES
            count = 0
            for item in top_sites:
                source_medium = item['dimensions']['source']
                source = source_medium.split(' / ')[0]
                black_ex = '|'
                black_string = black_ex.join(black_list)
                regex = re.compile(black_string)
                m = regex.search(source)
                if m: 
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
                    print 'source : ', source
                    count += 1     
                    
        #AGGREGATE AND SORT ARTICLES            
        for source in site_referrals:
            un_sorted = self.aggregate_data(site_referrals[source], ['title', 'host'], ['pageviews'])
            sorted = self.sort_data(un_sorted, 'pageviews', num_articles)   
            second_aggregate = self.aggregate_data(second_site_referrals[source], ['title', 'host'], ['pageviews']) 
            complete = self.add_change(sorted, second_aggregate, ['pageviews'])          
            site_referrals[source] = complete 
            
        return site_referrals
        
        
    def get_social_referral_articles(self, sites, period, second_period, social_networks, num_articles): 
        social_articles = OrderedDict()
        second_social_articles = OrderedDict()        
           
        #LOOP TO GET ARTICLES 
        for site in sites:      
            site_ga_id = config.TABLES[site]
            print 'site : ', site 
      
             #TOP SOCIAL ARTICLES                                            
            for item in social_networks:
                social_network = item['dimensions']['socialNetwork'] 
                print 'social network : ', social_network
                data = analytics.get_article_breakdown(site_ga_id, period, extra_filters='ga:socialNetwork==%s' % social_network)
                second_data = analytics.get_article_breakdown(site_ga_id, second_period, extra_filters='ga:socialNetwork==%s' % social_network)
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
         
        #AGGREGATE AND SORT ARTICLES              
        for social in social_articles:
            un_sorted = self.aggregate_data(social_articles[social], ['title', 'host'], ['pageviews'])
            sorted = self.sort_data(un_sorted, 'pageviews', num_articles)
            second_aggregate = self.aggregate_data(second_social_articles[social], ['title', 'host'], ['pageviews'])
            complete = self.add_change(sorted, second_aggregate, ['pageviews'])
            social_articles[social] = complete                
            
        return social_articles   
           
                      
    def get_top_articles(self, sites, period, second_period, num_articles):
        top_articles = []
        second_top_articles = []
        #LOOP TO GET ARTICLES 
        for site in sites:
            site_ga_id = config.TABLES[site]
            print 'site : ', site         
            #TOP TEN ARTICLES 
            articles_data = analytics.get_article_breakdown(site_ga_id, period)
            separated_data = []
            for item in articles_data:
                separated_data.append(articles_data[item])
            second_articles_data = analytics.get_article_breakdown(site_ga_id, second_period)
            second_separated_data = []
            for item in second_articles_data:
                second_separated_data.append(second_articles_data[item])
            top_articles += separated_data[:11]
            second_top_articles = second_separated_data[:11]   
            
        un_sorted = self.aggregate_data(top_articles, ['title', 'host'], ['pageviews'])
        sorted = self.sort_data(un_sorted, 'pageviews', 10)   
        second_aggregate = self.aggregate_data(second_top_articles, ['title', 'host'], ['pageviews']) 
        complete_articles = self.add_change(sorted, second_aggregate, ['pageviews'])    
        
        return complete_articles        
                    