import config
import re
from datetime import date, timedelta, datetime
from analytics import Analytics

import Statsdash.utilities as utils

site_ids = config.TABLES
analytics = Analytics()

class AnalyticsData(object):
    
    def __init__(self, sites, period, frequency):
        self.sites = sites
        self.period = period
        self.frequency = frequency
        self.previous = utils.StatsRange.get_previous_period(self.period, self.frequency)
        self.yearly = utils.StatsRange.get_previous_period(self.period, "YEARLY")
        self.date_list = [self.period, self.previous, self.yearly]
    
	def check_available_data(self):
		run_report = {"result":True, "site":[]}
		for site in self.sites:
			id = channel_ids[channel]
			data_available = analytics.data_available(id, self.period.get_end())
			if not data_available:
				run_report["result"] = False
				run_report["site"].append(site)		
		return run_report    
		
		
    def _remove_ga_names(self, rows):
        for row in rows:
            for key in row.keys():
                new = key.split("ga:")[1]
                row[new] = row.pop(key)
        return rows
        
        
    def _rollup_rows(self, ids, metrics, dimensions=None, filters=None, sort=None, max_results=None):
        #is this the best way to aggregate site data 
        pass
        main_row = []
        for id in ids:
            results = analytics.run_report(id, date.get_start(), date.get_end(), metrics=metrics, dimensions=dimensions, sort=sort, max_results=max_results)
            rows = utils.format_data_rows(results)
            for row in rows:
                for metric in metrics.split(","):
                    row[metric] = float(row[metric])
            rows = self._remove_ga_names(rows)
            main_row.append(rows)
            
        main_row = utils.aggregate_data
            

    def summary_table(self):	
        data = {}
        for count, date in enumerate(self.date_list):
            totals = []
            metrics="ga:pageviews,ga:users,ga:sessions,ga:pageviewsPerSession,ga:avgSessionDuration"
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics=metrics)
                rows = utils.format_data_rows(results)
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))

                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"pv_per_session":"pageviewsPerSession", "avg_session_time":"avgSessionDuration"})
                
                totals.extend(rows)
            #new aggregate data where just matches the metric and add it 
            aggregate = {"pageviews":0, "users":0, "sessions":0, "pv_per_session":0, "avg_session_time":0}
            for row in totals:
                for key in aggregate.keys():
                    aggregate[key] += row[key]
            
            data[count] = aggregate      
        
        for period in data:
            data[period]["pv_per_session"] = data[period]["pv_per_session"]/len(self.sites)
            data[period]["avg_session_time"] = (data[period]["avg_session_time"]/len(self.sites))/60.0
            
        #add change 
        for key in ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"]:
            this_period = data[0]
            prev_period = data[1]
            year_period = data[2]
            this_period["%s_figure_%s" % ("previous", key)] = prev_period[key]
            this_period["%s_change_%s" % ("previous", key)] = this_period[key] - prev_period[key]
            this_period["%s_percentage_%s" % ("previous", key)] = utils.percentage(this_period["%s_change_%s" % ("previous", key)], prev_period[key])
            this_period["%s_change_%s" % ("yearly", key)] = this_period[key] - year_period[key]
            this_period["%s_percentage_%s" % ("yearly", key)] = utils.percentage(this_period["%s_change_%s" % ("yearly", key)], year_period[key])  
            
        return this_period          
                
                              
    def site_summary_table(self):
        #should this be combined with overall summary table?
        data = {}
        for count, date in enumerate(self.date_list):
            totals = []
            metrics="ga:pageviews,ga:users,ga:sessions,ga:pageviewsPerSession,ga:avgSessionDuration"
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics=metrics)
                rows = utils.format_data_rows(results)
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                    row["ga:site"] = site 

                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"pv_per_session":"pageviewsPerSession", "avg_session_time":"avgSessionDuration"})
                                    
                totals.extend(rows)
                
            aggregated = utils.aggregate_data(totals, "site", ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"])
            sorted = utils.sort_data(aggregated, "users")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "site", ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], "previous")
        added_change = utils.add_change(added_change, data[2], "site", ["pageviews", "users", "sessions", "pv_per_session", "avg_session_time"], "yearly")
        
        return added_change
                           


    def _remove_query_string(self, path):
        """
        Removes any queries attached to the end of a page path, so aggregation can be accurate
        """
        exp = "^([^\?]+)\?.*"
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
        self.previous = utils.StatsRange.get_previous_period(self.period, "WOW_DAILY")#how to do this
        data = {}
        for count, date in enumerate(self.date_list):
            articles = []
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews", dimensions="ga:pageTitle,ga:pagePath,ga:hostname", 
                                                filters= config.ARTICLE_FILTER, sort="-ga:pageviews")
                rows = utils.format_data_rows(results)
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"title":"pageTitle", "path":"pagePath", "host":"hostname"})
                for row in rows:
                    path = row["path"]
                    new_path = self._remove_query_string(path)
                    row["path"] = new_path
                    row["pageviews"] = float(row["pageviews"])
                
                articles.extend(rows)
            aggregated = utils.aggregate_data(articles, "path", ["pageviews"])
            sorted = utils.sort_data(aggregated, "pageviews", limit=20)
            data[count] = sorted
            #group

        added_change = utils.add_change(data[0], data[1], "pagePath", ["pageviews"], "DAILY")

        return added_change
        
        
        
    def country_table(self):
        countries = ["Czec", "Germa", "Denma", "Spai", "Franc", "Italy", 
            "Portug", "Swede", "Polan", "Brazi", "Belgiu", "Netherl", 
            "United Ki", "Irela", "United St", "Canad", "Austral", "New Ze"]
            
        countries_regex = "|".join(countries)
        filters = "ga:country=~%s" % countries_regex
        row_filters = "ga:country!~%s" % countries_regex
        data = {}
        for count, date in enumerate(self.date_list):
            breakdown = []
            metrics = "ga:pageviews,ga:users"
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions="ga:country", filters=filters, sort="-ga:pageviews")
                world_results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews,ga:users", filters=row_filters, sort="-ga:pageviews")
                rows = utils.format_data_rows(results)
                world_rows = utils.format_data_rows(world_results)
                try:
                    world_rows[0]["ga:country"] = "ROW"
                except IndexError:
                    world_rows = [{"ga:country":"ROW", "ga:pageviews":0, "ga:users":0}]
                    
                rows.extend(world_rows)
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                    
                rows = self._remove_ga_names(rows)   
                breakdown.extend(rows)
                    
            aggregated = utils.aggregate_data(breakdown, "country", ["pageviews", "users"])
            sorted = utils.sort_data(aggregated, "users")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "country", ["pageviews", "users"], "previous")
        added_change = utils.add_change(added_change, data[2], "country", ["pageviews", "users"], "yearly")
        
        return added_change
            
    def _get_source_list(self):
        data = {}
        for count, date in enumerate(self.date_list):
            traffic_sources = []
            metrics = "ga:pageviews,ga:users"
            for site in self.sites:       
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions="ga:sourceMedium", sort="-ga:users")
                rows = utils.format_data_rows(results)
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"source_medium":"sourceMedium"})
                for row in rows:
                    row =  utils.convert_to_floats(row, ["pageviews", "users"])
                    
                traffic_sources.extend(rows)
                
            aggregated = utils.aggregate_data(traffic_sources, "source_medium", ["pageviews", "users"])
            sorted = utils.sort_data(aggregated, "users")
            data[count] = sorted   
            
        added_change = utils.add_change(data[0], data[1], "source_medium", ["pageviews", "users"], "previous")
        added_change = utils.add_change(added_change, data[2], "source_medium", ["pageviews", "users"], "yearly")
        
        return added_change

        
    def traffic_source_table(self):
        table = self._get_source_list()
        table = table[:10]
        return table    
        
        
    def referring_sites_table(self):
        sources = self._get_source_list()
        count = 0
        referrals = []
        for row in sources:
            source = row["source_medium"].split(" / ")[0] 
            black_ex = '|'
            black_string = black_ex.join(config.SOURCE_BLACK_LIST)
            regex = re.compile(black_string)
            match = regex.search(source)
            if match: 
                continue;           
            else:
                if count == 5:
                    break
                else:
                    count += 1
                    filter = "ga:source==%s" % source
                    article = self.referral_articles(filter, 1)
                    row["source"] = source
                    row["articles"] = article   
                    referrals.append(row)    
        
        return referrals 
        
        
    def social_network_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            social = []
            metrics = "ga:pageviews,ga:users"
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics=metrics, dimensions="ga:socialNetwork", 
                                                filters = "ga:socialNetwork!=(not set)", sort="-ga:users")
                rows = utils.format_data_rows(results)
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"social_network":"socialNetwork"})
                for row in rows:
                    row =  utils.convert_to_floats(row, ["pageviews", "users"])
                    
                social.extend(rows)
            
            aggregated = utils.aggregate_data(social, "social_network", ["pageviews", "users"])
            sorted = utils.sort_data(aggregated, "users", limit=15)
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "social_network", ["pageviews", "users"], "previous")
        added_change = utils.add_change(added_change, data[2], "social_network", ["pageviews", "users"], "yearly")
        
        for row in added_change:
            filter = "ga:socialNetwork==%s" % row["social_network"]
            article = self.referral_articles(filter, 1)
            row["articles"] = article            
        
        return added_change
        
        
    def referral_articles(self, filter, limit):
        #pass in a social network and get the top articles?
        filters = config.ARTICLE_FILTER + ";" + filter
        self.previous = utils.StatsRange.get_previous_period(self.period, "DAILY")#how to do this
        data = {}
        for count, date in enumerate(self.date_list):
            articles = []
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:pageviews", dimensions="ga:pageTitle,ga:pagePath,ga:hostname", 
                                                filters= filters, sort="-ga:pageviews")
                rows = utils.format_data_rows(results)
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"title":"pageTitle", "path":"pagePath", "host":"hostname"})
                for row in rows:
                    path = row["path"]
                    new_path = self._remove_query_string(path)
                    row["path"] = new_path
                    row["pageviews"] = float(row["pageviews"])
                
                articles.extend(rows)
            aggregated = utils.aggregate_data(articles, "path", ["pageviews"])
            sorted = utils.sort_data(aggregated, "pageviews", limit=limit)
            data[count] = sorted
            #group

        added_change = utils.add_change(data[0], data[1], "pagePath", ["pageviews"], "DAILY")

        return added_change                
        
        
    def device_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            devices = []
            for site in self.sites:
                results = analytics.run_report(site_ids[site], date.get_start(), date.get_end(), metrics="ga:users", dimensions="ga:deviceCategory", sort="-ga:users")
                rows = utils.format_data_rows(results)
                rows = self._remove_ga_names(rows)
                rows = utils.change_key_names(rows, {"device_category":"deviceCategory"})
                for row in rows:
                    row["users"] = float(row["users"])
                    
                devices.extend(rows)
            
            aggregated = utils.aggregate_data(devices, "device_category", ["users"])
            sorted = utils.sort_data(aggregated, "users", limit=6)
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "device_category", ["users"], "previous")
        added_change = utils.add_change(added_change, data[2], "device_category", ["users"], "yearly")
        
        return added_change
                
                
                
                
                
                
                
        
        
        
        
        
        