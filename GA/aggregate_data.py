import config
import re
from datetime import date, timedelta, datetime
from analytics import Analytics
import utilities as utils

site_ids = config.TABLES
analytics = Analytics()

class AnalyticsData(object):
    
    def __init__(self, sites, period, frequency):
        self.sites = sites
        self.period = period
        self.frequency = frequency
        self.previous = utils.StatsRange.get_previous_period(self.period, self.frequency)
    
	def check_available_data(self):
		run_report = {"result":True}
		for channel in self.channels:
			id = channel_ids[channel]
			data_available = analytics.data_available(id, self.end.strftime("%Y-%m-%d"))
			if not data_available:
				run_report['result'] = False
				run_report['channel'] = channel			
		return run_report    
		

    def _remove_query_string(self, path):
        """
        Removes any queries attached to the end of a page path, so aggregation can be accurate
        """
        exp = '^([^\?]+)\?.*'
        regex = re.compile(exp) 
        m = regex.search(path)
        if m:
            new_path = regex.split(path)[1]            
            return new_path       
        else:
            return path    
            
 
    def article_table(self):
        """
        Return top articles as a list of dictionaries
        Each dictionary has the pageviews, page title, page path and host name
        """
        data = {}
        for count, date in enumerate([self.period, self.previous]):
            articles = []
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews", dimensions="ga:pageTitle,ga:pagePath,ga:hostname", 
                                                filters= config.ARTICLE_FILTER, sort="-ga:pageviews")
                rows = utils.format_data_rows(results)
                for row in rows:
                    path = row['ga:pagePath']
                    new_path = self._remove_query_string(path)
                    row['ga:pagePath'] = new_path
                    row['ga:pageviews'] = float(row['ga:pageviews'])
                
                articles.extend(rows)
            aggregated = utils.aggregate_data(articles, "ga:pagePath", ["ga:pageviews"])
            sorted = utils.sort_data(aggregated, "ga:pageviews", limit=20)
            data[count] = sorted
            #group

        added_change = utils.add_change(data[0], data[1], "ga:pagePath", ["ga:pageviews"])

        return added_change
        
        
        
    def country_table(self):
        countries = ["Czec", "Germa", "Denma", "Spai", "Franc", "Italy", 
            "Portug", "Swede", "Polan", "Brazi", "Belgiu", "Netherl", 
            "United Ki", "Irela", "United St", "Canad", "Austral", "New Ze"]
            
        countries_regex = '|'.join(countries)
        filters = 'ga:country=~%s' % countries_regex
        row_filters = 'ga:country!~%s' % countries_regex
        self.previous = utils.StatsRange.get_previous_period(self.period, "WOW_DAILY")#how to do this
        data = {}
        for count, date in enumerate([self.period, self.previous]):
            breakdown = []
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews,ga:visitors", dimensions="ga:country", filters=filters, sort="-ga:pageviews")
                world_results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews,ga:visitors", filters=row_filters, sort="-ga:pageviews")
                rows = utils.format_data_rows(results)
                world_rows = utils.format_data_rows(world_results)
                world_rows[0]['ga:country'] = "ROW"
                
                breakdown.extend(world_rows)
                breakdown.extend(rows)
                for row in breakdown:
                    row['ga:pageviews'] = float(row['ga:pageviews'])
                    row['ga:visitors'] = float(row['ga:visitors'])
                    
            aggregated = utils.aggregate_data(breakdown, "ga:country", ["ga:pageviews", "ga:visitors"])
            sorted = utils.sort_data(aggregated, "ga:visitors")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "ga:country", ["ga:pageviews", "ga:visitors"])
        
        return added_change
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
        
        
        
        
        
        