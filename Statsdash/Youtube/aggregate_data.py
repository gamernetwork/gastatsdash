#!/usr/bin/python
import sys
sys.path.append('/home/faye/src/gastatsdash/')


from analytics import Analytics
import pygal
from datetime import datetime, timedelta, date
from fractions import gcd
import config

import Statsdash.utilities as utils

analytics = Analytics()
channel_ids = config.CHANNELS

class YoutubeData(object):
    """
    Set the parameters for the data tables
    channels: list of channel names to be included in the data
    start: start date for the period of time over which to get the data
    end: end date for the period of time over which to get the data
    if weekly, must be monday - sunday dates 
    if monthly, must 1st - 31st (last date in month)
    """
	
    def __init__(self, channels, period, frequency):
        """
        Set up data collection parameters
        Find time span using dates given
        """
        self.channels = channels
        self.period = period
        self.frequency = frequency
        self.previous = utils.StatsRange.get_previous_period(self.period, self.frequency)
        self.yearly = utils.StatsRange.get_previous_period(self.period, "YEARLY")
        self.date_list = [self.period, self.previous, self.yearly]
        
        """"
        if self.frequency == "DAILY":
            self.time_span = "day"
        elif self.frequency == "WEEKLY":
            self.time_span = "7DayTotals"
        elif self.frequency == "MONTHLY":
            self.time_span == "month"
        """
		
    def check_available_data(self):
        run_report = {"result":True, "channel":[]}
        for channel in self.channels:
        	id = channel_ids[channel]
        	data_available = analytics.data_available(id, self.end.strftime("%Y-%m-%d"))
        	if not data_available:
        		run_report['result'] = False
        		run_report['channel'] += channel			
        return run_report

		
    def country_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            table = []
            metrics = "views,estimatedMinutesWatched,subscribersGained,subscribersLost"
            for channel in self.channels:
                id = channel_ids[channel]
                results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics=metrics, dimensions="country", 
                												filters="channel==%s" % id, max_results=None, sort="-estimatedMinutesWatched")		
                									
                rows = utils.format_data_rows(results)
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                    row["subscriberChange"] = row["subscribersGained"] - row["subscribersLost"]
                table.extend(rows)
            	    			
            aggregated = utils.aggregate_data(table, "country", (metrics + ",subscriberChange").split(","))
            sorted = utils.sort_data(aggregated, "estimatedMinutesWatched", limit=20)
            data[count] = sorted
        
        added_change = utils.add_change(data[0], data[1], "country", ["views","estimatedMinutesWatched","subscriberChange"], "previous")
        added_change = utils.add_change(added_change, data[2], "country", ["views","estimatedMinutesWatched","subscriberChange"], "yearly")
        
        return added_change


    def channel_summary_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            table = []
            metrics="subscribersGained,subscribersLost,estimatedMinutesWatched"
            for channel_num, channel in enumerate(self.channels):
                id = channel_ids[channel]

                if count == 0:
                    subscriber_count = analytics.get_stats(id)['subscriberCount'] #only gets the current subscriber count
                elif count == 1:
                    #last period date, work out last periods subscriber count from current periods sub change 
                    this_channel = utils.list_search(data[0], "channel", channel)
                    subscriber_count = this_channel["subscriberCount"] - this_channel["subscriberChange"]
                else:
                    #don't need to work out yearly sub change 
                    subscriber_count = 0.0
                    
                results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics=metrics, dimensions=None, filters="channel==%s" % id)	
                  
                rows = utils.format_data_rows(results)
                for row in rows:
                    row = utils.convert_to_floats(row, metrics.split(","))
                    row["channel"] = channel
                    row["subscriberChange"] = row["subscribersGained"] - row["subscribersLost"]
                    row["subscriberCount"] = float(subscriber_count)
                    
                table.extend(rows)
                
            aggregated = utils.aggregate_data(table, "channel", ["subscriberChange", "subscriberCount", "estimatedMinutesWatched"])
            sorted = utils.sort_data(aggregated, "estimatedMinutesWatched")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "channel", ["subscriberChange", "subscriberCount", "estimatedMinutesWatched"], "previous")
        added_change = utils.add_change(added_change, data[2], "channel", ["subscriberChange", "estimatedMinutesWatched"], "yearly")
        
        return added_change
 
    
    def channel_stats_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            table = []
            #just subscribersGained to get number of subscribers per 1000 views 
            metrics="views,likes,dislikes,comments,shares,subscribersGained"
            for channel_num, channel in enumerate(self.channels):
                id = channel_ids[channel]
                results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics=metrics, dimensions=None, filters="channel==%s" % id)	
                rows = utils.format_data_rows(results)
                for row in rows:
                    row = utils.convert_to_floats(row, metrics.split(","))
                    row["channel"] = channel
                    row["likeRate"] = utils.rate_per_1000(row["likes"], row['views'])
                    row["commentRate"] = utils.rate_per_1000(row["comments"], row['views'])
                    row["sharesRate"] = utils.rate_per_1000(row["shares"], row['views'])
                    row["subsRate"] = utils.rate_per_1000(row["subscribersGained"], row['views']) 
                    try:
                        row["likeRatio"] = utils.sig_fig(2, row["likes"] / row["dislikes"])
                    except ZeroDivisionError:
                        row["likeRatio"] = 0
                    try:
                        row["dislikeRatio"] = utils.sig_fig(2, row["dislikes"] / row["dislikes"])
                    except ZeroDivisionError:
                        row["dislikeRatio"] = 0                        
                
                table.extend(rows)
                           
            #aggregated = utils.aggregate_data(table, "channel", )
            sorted = utils.sort_data(table, "views")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], "channel", ["views", "likeRate", "commentRate", "sharesRate", "subsRate", "likeRatio", "dislikeRatio"], "previous")
        added_change = utils.add_change(added_change, data[2], "channel", ["views", "likeRate", "commentRate", "sharesRate", "subsRate", "likeRatio", "dislikeRatio"], "yearly") 
        
        return added_change               

    def video_table(self):
        data = {}
        for count, date in enumerate([self.period]):
            table = []        
            for channel_num, channel in enumerate(self.channels):
                id = channel_ids[channel]
                results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics="estimatedMinutesWatched,views", dimensions="video", 
        											filters="channel==%s" % id, max_results="20", sort="-estimatedMinutesWatched")
                rows = utils.format_data_rows(results)
                for row in rows:
                    row = utils.convert_to_floats(row, ["estimatedMinutesWatched", "views"])
                    video_name = analytics.get_video(row['video'])
                    row['title'] = video_name['items'][0]['snippet']['title'] 
                    row['channel'] = channel	

                table.extend(rows)
            		
            aggregated = utils.aggregate_data(table, "video", ["estimatedMinutesWatched", "views"])
            sorted = utils.sort_data(aggregated, "estimatedMinutesWatched", limit=10)
            data[count] = sorted
            #group

        
        #added_change = utils.add_change(data[0], data[1], "video", ["estimatedMinutesWatched", "views"], "DAILY")     
        
        return data[0]       			
        

    #TODO the traffic source breakdown epic    
    def traffic_source_table(self):
        data = {}
        source_types= ['ANNOTATION', 'EXT_URL', 'NO_LINK_OTHER', 'NOTIFICATION', 'PLAYLIST', 'RELATED_VIDEO', 'SUBSCRIBER', 'YT_CHANNEL', 'YT_OTHER_PAGE', 'YT_PLAYLIST_PAGE', 'YT_SEARCH']
        traffic_source = []
        for source in source_types:
            row = {"insightTrafficSourceType":source, "source_total":0.0}
            traffic_source.append(row)
        
        for count, date in enumerate(self.date_list):
            table = []
            for channel in self.channels:
                id = channel_ids[channel]
                results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics="estimatedMinutesWatched",
                                                            dimensions="insightTrafficSourceType", filters="channel==%s" % id, sort="-estimatedMinutesWatched")	
                rows = utils.format_data_rows(results)
                channel_total = 0.0
                for row in rows:
                    row = utils.convert_to_floats(row, ["estimatedMinutesWatched"])
                    row["channel"] = channel
                    channel_total += row["estimatedMinutesWatched"]                    
                    
                new_rows = []
                for source_type in traffic_source:
                    try:
                        result = utils.list_search(rows, "insightTrafficSourceType", source_type["insightTrafficSourceType"])
                        result["channel_total"] = channel_total
                        new_rows.append(result)
                        source_type["source_total"] += result["estimatedMinutesWatched"]
                    except KeyError:
                        new_rows.append({"insightTrafficSourceType":source_type["insightTrafficSourceType"], "channel":channel, "channel_total":channel_total, "estimatedMinutesWatched":0.0})

                 
                #table is list of lists, list for each channel
                table.append(new_rows)
            
            #table = utils.sort_data(table, "channel_total")  
            
            new_table = []
            for channel in table:
                for row in channel:
                    #order each channel section by the total minutes watched for each source 
                    #calculate channels percentage breakdown by source
                    breakdown = utils.percentage(row["estimatedMinutesWatched"], row["channel_total"])
                    row["source_percentage"] = breakdown
                    result = utils.list_search(traffic_source, "insightTrafficSourceType", row["insightTrafficSourceType"])
                    row["source_total"] = result["source_total"]
                sort_row = utils.sort_data(channel, "source_total")  
                new_table.append(sort_row)
            
            #sort the new table of dictionaries by total channel watch time 
            #sorted = utils.sort_data(new_table, "channel_total")   

            sorted_list = sorted(new_table, key = lambda k: k[0]["channel_total"], reverse = True)
            data[count] = sorted_list       
            
            
        return data[0]            

            
            	        
	
if __name__ == '__main__':
    from datetime import datetime, timedelta, date
    period = utils.StatsRange("period", date(2016, 04, 01), date(2016, 04, 30))

    youtube = YoutubeData(config.CHANNELS.keys(), period, "MONTHLY" )
    import pprint
    #pprint.pprint(youtube.channel_summary_table(), width=1)
    #pprint.pprint(youtube.country_table(), width=1)
    #pprint.pprint(youtube.channel_stats_table(), width=1)
    #pprint.pprint(youtube.video_table(), width=1)
    
    pprint.pprint(youtube.traffic_source_table(), width=1)
    

    """
    def data_by_traffic_source(self, start, end):

        table=[]
        source_types= ['ANNOTATION', 'EXT_URL', 'NO_LINK_OTHER', 'NOTIFICATION', 'PLAYLIST', 'RELATED_VIDEO', 'SUBSCRIBER', 'YT_CHANNEL', 'YT_OTHER_PAGE', 'YT_PLAYLIST_PAGE', 'YT_SEARCH']
        for channel in self.channels:
        	id = channel_ids[channel]
        	row = {}
        	row['channel'] = channel	
        	results = analytics.run_analytics_report(start_date=start, end_date=end, metrics="estimatedMinutesWatched", 
        												dimensions="insightTrafficSourceType", filters="channel==%s" % id, sort="-estimatedMinutesWatched")			
        	data = utils.format_data_rows(results)	
        	checked_data = []
        	data_check = []
        	#remove unwanted sources from the results
        	for source in source_types:
        		for d in data:
        			if d['insightTrafficSourceType'] == source:
        				new_d ={}
        				new_d['insightTrafficSourceType'] = source
        				new_d['estimatedMinutesWatched'] = d['estimatedMinutesWatched']
        				data_check.append(d['insightTrafficSourceType'])
        				checked_data.append(new_d)					
        
        	#if missing traffic source from list add in 
        	missing = list(set(source_types) - set(data_check))
        	if missing:
        		for traffic_source in missing:
        			checked_data.append({'insightTrafficSourceType':traffic_source, 'estimatedMinutesWatched':0.0})
        	
        	row['data'] = checked_data
        	table.append(row)
        	
        return table	

    def get_traffic_source_table(self):

        	
        table = self.data_by_traffic_source(self.period.get_start(), self.period.get_end())
        
        sources = {}
        for count, row in enumerate(table):
        	row['channel_watch_time'] = 0		
        	for source in row['data']:
        		row['channel_watch_time'] += source['estimatedMinutesWatched']
        		traffic_source = source['insightTrafficSourceType']
        		watch_time = source['estimatedMinutesWatched']
        		try:
        			sources[traffic_source] += watch_time
        		except KeyError:
        			sources[traffic_source] = watch_time
        				
        #work out each source as percentage of channel watch time
        for row in table:
        	#each channel
        	for source in row['data']:
        		source['breakdown'] = utils.percentage(source['estimatedMinutesWatched'], row['channel_watch_time'])
        
        #sources = sorted(sources, key=lambda k: k['watch_time'], reverse=True)
        table = sorted(table, key=lambda k: k['channel_watch_time'], reverse=True)
        #sort the rows within table by watch time in sources 		
        for row in table:
        	row['data'].sort(key=lambda x: sources[x['insightTrafficSourceType']], reverse = True)			
        	
        sources = sources.items()
        sources.sort(key=lambda x: x[1], reverse=True)
        
        sum = {}
        sum['channels'] = table
        sum['sources'] = sources
        return sum			

    def _format_period_data(self, rows, start, end):

        if self.time_span == "7DayTotals":
        	current = self.period.end_date.strftime("%Y-%m-%d")
        	previous = self.period.start_date.strftime("%Y-%m-%d")
        elif self.time_span == "month":
        	current = self.period.end_date.strftime("%Y-%m")		
        	previous = self.period.start_date.strftime("%Y-%m")
        	
        for row in rows:
        	if row[self.time_span] == current:
        		current_data = row
        	elif row[self.time_span] == previous:
        		previous_data = row
        		
        data = {}
        data['prev_data'] = previous_data
        data['current_data'] = current_data
        return data
		
"""		


    """"
    def get_stats_table(self):  
        table=[]
        for channel in self.channels:
        	row = {}
        	id = channel_ids[channel]
        	row['channel'] = channel	
        	results = analytics.run_analytics_report(start_date=self.previous.get_start(), end_date=self.period.get_start(), metrics="views,likes,dislikes,comments,shares,subscribersGained", 
        												dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
        															
        	#format data into previous and current dictionaries 
        	data = utils.format_data_rows(results)
        	data = self._format_period_data(data, self.previous, self.start)
        
        	prev_data = data['prev_data']
        	current_data = data['current_data']
        
        	year_results = analytics.run_analytics_report(start_date=self.yearly.get_start(), end_date=self.yearly.get_start(), metrics="views,likes,dislikes,comments,shares,subscribersGained", 
        												dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
        															
        	#format data into previous and current dictionaries 
        	data = utils.format_data_rows(year_results)
        	data = self._format_period_data(data, yr_start, yr_end)
        
        	year_data = data['current_data']
        	
        	#like/dislike ratio mom change
        	ld_ratio = {}
        
        	#multiple = gcd(current_data['likes'], current_data['dislikes']) #highest common divisor
        	multiple = current_data['dislikes'] #use dislikes so create a n:1 like:dislike ratio
        	try:
        		ld_ratio['l_ratio'] = utils.sig_fig(2, current_data['likes'] / multiple)
        	except ZeroDivisionError:
        		ld_ratio['l_ratio'] = 0
        		
        	try:
        		ld_ratio['d_ratio'] = utils.sig_fig(2, current_data['dislikes'] / multiple)
        	except ZeroDivisionError:
        		ld_ratio['d_Ratio'] = 0
        		
        	#work out the percentages and find the change
        	ld_ratio['prev'] = utils.percentage(prev_data['likes'], prev_data['dislikes'])
        	ld_ratio['current'] = utils.percentage(current_data['likes'], current_data['dislikes'])
        	ld_ratio['year'] = utils.percentage(year_data['likes'], year_data['dislikes'])
        
        	ld_ratio['percentage'] = ld_ratio['current'] - ld_ratio['prev']
        	ld_ratio['yoy_percentage'] = ld_ratio['current'] - ld_ratio['year']
        
        	metrics = ["subscribersGained", "comments", "shares", "likes"]
        	total = {}
        	total['ld_ratio'] = ld_ratio
        	total['prev_data'] = prev_data
        	total['current_data'] = current_data
        	total['year_data'] = year_data
        				
        	#find /1000 views and percentage change for each  metric
        	for metric in metrics:
        		data = {}
        		prev_rate = utils.rate_per_1000(prev_data[metric], prev_data['views'])
        		data['prev'] = utils.sig_fig(2, prev_rate)
        		curr_rate = utils.rate_per_1000(current_data[metric], current_data['views'])
        		data['current'] = utils.sig_fig(2, curr_rate)
        		year_rate = utils.rate_per_1000(year_data[metric], year_data['views'])
        		data['year'] = utils.sig_fig(2, year_rate)
        		
        		data['change'] = data['current'] - data['prev']
        		change = utils.percentage(data['change'], data['prev'])
        		data['percentage'] = change
        		
        		data['yoy_change'] = data['current'] - data['year']
        		change = utils.percentage(data['yoy_change'], data['year'])
        		data['yoy_percentage'] = change			
        		
        		total[metric] = data
        	
        	row['stats']= total
        	table.append(row)
        
        #sort by views
        table = sorted(table, key=lambda k: k['stats']['current_data']['views'], reverse=True)
        return table

"""


    """"
    def subscribers(self, id):

        subscriber_count = analytics.get_stats(id)['subscriberCount'] # number of CURRENT subscribers 
        
        results = analytics.run_analytics_report(start_date=self.previous.get_start(), end_date=self.start.get_start(), metrics="subscribersGained,subscribersLost", 
        											dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
        
        #format data into previous and current dictionaries 
        data = utils.format_data_rows(results)
        data = self._format_period_data(data, self.previous, self.start)
        
        prev_data = data['prev_data']
        current_data = data['current_data']
        
        
        year_results = analytics.run_analytics_report(start_date=self.yearly.get_start(), end_date=self.yearly.get_start(), metrics="subscribersGained,subscribersLost", 
        											dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
        
        #format data into previous and current dictionaries 
        data = utils.format_data_rows(year_results)
        data = self._format_period_data(data, yr_start, yr_end)
        
        year_data = data['current_data']
        
        current_subs_change = current_data['subscribersGained'] - current_data['subscribersLost']
        prev_subs_change = prev_data['subscribersGained'] - prev_data['subscribersLost']
        year_subs_change = year_data['subscribersGained'] - year_data['subscribersLost']
        
        #find total last month and change
        subs_prev = float(subscriber_count) - current_subs_change
        total_percentage = utils.percentage(current_subs_change, subs_prev)
        
        difference = current_subs_change - prev_subs_change
        percent = utils.percentage(difference, prev_subs_change)
        
        yr_difference = current_subs_change - year_subs_change
        yoy_percent = utils.percentage(yr_difference, year_subs_change)
        
        subscribers = {}
        subscribers['current'] = current_subs_change
        subscribers['last_month'] = prev_subs_change
        subscribers['change_fig'] = int(difference)
        subscribers['change_percentage'] = percent
        subscribers['yoy_percentage'] = yoy_percent
        subscribers['total'] = subscriber_count
        subscribers['total_prev'] = subs_prev
        subscribers['total_percentage'] = total_percentage
        
        return subscribers			

    def watch_time(self, id):

        results = analytics.run_analytics_report(start_date=self.previous.strftime("%Y-%m-%d"), end_date=self.start.strftime("%Y-%m-%d"), metrics="estimatedMinutesWatched", 
        											dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
        
        #format data into previous and current dictionaries 
        data = utils.format_data_rows(results)
        data = self._format_period_data(data, self.previous, self.start)
        
        prev_data = data['prev_data']
        current_data = data['current_data']
        
        year_results = analytics.run_analytics_report(start_date=self.yearly.get_start(), end_date=self.yearly.get_start(), metrics="estimatedMinutesWatched", 
        											dimensions=self.time_span, filters="channel==%s" % id, max_results="100")
        
        #format data into previous and current dictionaries 
        data = utils.format_data_rows(year_results)
        data = self._format_period_data(data, yr_start, yr_end)
        
        year_data = data['current_data']
        
        current = current_data['estimatedMinutesWatched']
        last = prev_data['estimatedMinutesWatched']
        year = year_data['estimatedMinutesWatched']
        
        
        difference = current-last
        percent = utils.percentage(difference, last)
        
        yr_difference = current-year
        yoy_percent = utils.percentage(yr_difference, year)
        
        watch_time = {}
        watch_time['current'] = int(current)
        watch_time['last_month'] = int(last)
        watch_time['change_fig'] = int(difference)
        watch_time['change_percentage'] = percent
        watch_time['yoy_percentage'] = yoy_percent
        
        return watch_time
		
    def get_summary_table(self):

        table =[]
        for channel in self.channels:
            row = {}
            id = channel_ids[channel]
            row['channel'] = channel	
            row['watch_time'] = self.watch_time(id)
            row['subscribers'] = self.subscribers(id)
            table.append(row)
        
        table = sorted(table, key=lambda k: k['watch_time']['current'], reverse=True)	
        return table
		
"""


        
    """"
    def data_by_country(self, start, end):
        
        current_data = []
        for channel in self.channels:
        	id = channel_ids[channel]
        	results = analytics.run_analytics_report(start_date=start, end_date=end, metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost", dimensions="country", 
        													filters="channel==%s" % id, max_results=None, sort="-estimatedMinutesWatched")		
        										
        	rows = utils.format_data_rows(results)
        	#list of dictionaries with data for each country
        	current_data.append(rows)
        
        countries = {}
        
        for data in current_data:
        	#data will be list of dictionaries with data for each country
        	for row in data:
        		#row is a dictionary
        		country = row['country']
        		subs_gained = row['subscribersGained']
        		subs_lost = row['subscribersLost']
        		watch_time = row['estimatedMinutesWatched']
        		views = row['views']			
        		try:
        			countries[country]['estimatedMinutesWatched'] += watch_time
        			countries[country]['views'] += views
        			countries[country]['subscribersGained'] += subs_gained
        			countries[country]['subscribersLost'] += subs_lost
        		except KeyError:
        			countries[country] = { 'estimatedMinutesWatched': watch_time, 'subscribersGained': subs_gained, 'subscribersLost': subs_lost, 'views': views }	
        			
        return countries 	
    			
    def get_geo_table(self):
        
        countries = self.data_by_country(self.period.get_start(), self.period.get_end())
        prev_countries = self.data_by_country(self.previous.get_start(), self.previous.get_end())
        yr_countries = self.data_by_country(self.yearly.get_start(), self.yearly.get_start())
        
        #put data into list so can sort and reduce to max number of countries 				
        country_list = []
        for country in countries:
        	data = {'country':country}
        	data.update(countries[country])		
        	country_list.append(data)
        
        table = sorted(country_list, key=lambda k: k['estimatedMinutesWatched'], reverse=True)
        table = table[:20]
        #add in previous data to create percentage MoM change
        for row in table:
        	country = row['country']
        	try:
        		prev = prev_countries[country]
        	except KeyError:
        		prev = { 'estimatedMinutesWatched': 0, 'subscribersGained': 0, 'subscribersLost': 0, 'views': 0 }	
        	try:
        		year = yr_countries[country]
        	except KeyError:
        		year = { 'estimatedMinutesWatched': 0, 'subscribersGained': 0, 'subscribersLost': 0, 'views': 0 }	
        
        	row['emw_change'] = row['estimatedMinutesWatched'] - prev['estimatedMinutesWatched']
        	row['emw_percentage'] =  utils.percentage(row['emw_change'], prev['estimatedMinutesWatched'])
        	
        	row['views_change'] = row['views'] - prev['views']
        	row['views_percentage'] =  utils.percentage(row['views_change'], prev['views'])
        
        	row['subscribers'] = row['subscribersGained'] - row['subscribersLost']
        	prev['subscribers'] = prev['subscribersGained'] - prev['subscribersLost']
        	row['sub_change'] = row['subscribers'] - prev['subscribers']
        
        	row['sub_percentage'] = utils.percentage(row['sub_change'], prev['subscribers'])
        	
        	
        	row['emw_yoy_change'] = row['estimatedMinutesWatched'] - year['estimatedMinutesWatched']
        	row['emw_yoy_percentage'] =  utils.percentage(row['emw_yoy_change'], year['estimatedMinutesWatched'])
        
        	row['views_yoy_change'] = row['views'] - year['views']
        	row['views_yoy_percentage'] =  utils.percentage(row['views_change'], year['views'])
        
        	year['subscribers'] = year['subscribersGained'] - year['subscribersLost']
        	row['yoy_sub_change'] = row['subscribers'] - year['subscribers']
        
        	row['yoy_sub_percentage'] = utils.percentage(row['yoy_sub_change'], year['subscribers'])			
        
        return table		
        """	    
    