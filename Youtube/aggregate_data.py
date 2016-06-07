#!/usr/bin/python

from renderer import render_template
from analytics import Analytics
import webbrowser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import pygal
from datetime import datetime, timedelta
import StringIO
from fractions import gcd
import config

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
	
	def __init__(self, channels, start, end):
		"""
		Set up data collection parameters
		Find time span using dates given
		"""
		self.channels = channels
		self.start = start
		self.end = end

		self._find_time_span()	#just pass in the frequency variable 	
		
	def check_available_data(self):
		run_report = {"result":True}
		for channel in self.channels:
			id = channel_ids[channel]
			data_available = analytics.data_available(id, self.end.strftime("%Y-%m-%d"))
			if not data_available:
				run_report['result'] = False
				run_report['channel'] = channel			
		return run_report
			
			
	def _find_time_span(self):
		"""
		Finds if the time span is weekly or monthly
		Sets the time span equal to the relative dimension in analytics
		Finds the previous date used for analytics
		Weekly = start should be the sunday (last day) of the previous week
				 end should be the sunday of the week getting data for
		Monthly = both need to be 1st of months
				  start should be 1st of previous month
				  end should be 1st of month getting data for
		"""
		diff = self.end - self.start 
		if diff.days == 6:
			self.time_span = "7DayTotals" #weekly
			self.previous = self.start - timedelta(days=1)
		elif diff.days > 26:
			self.time_span = "month" #monthly
			last_month = self.start - timedelta(days=1)
			self.previous = datetime(last_month.year, last_month.month, 01)
			
							
	def _format_data_rows(self, results):
		"""
		Returns results from analytics as a list of dictionaries with correct key/value pairs of data 
		"""
		rows = []
		for row in results.get("rows", []):
			data = {}
			for count, column in enumerate(results.get("columnHeaders", [])):
				data[column['name']] = row[count]
			rows.append(data)
		return rows

	def _format_period_data(self, rows, start, end):
		"""
		Return current and previous data as separate dictionaries
		"""
		if self.time_span == "7DayTotals":
			current = end.strftime("%Y-%m-%d")
			previous = start.strftime("%Y-%m-%d")
		elif self.time_span == "month":
			current = end.strftime("%Y-%m")		
			previous = start.strftime("%Y-%m")
			
		for row in rows:
			if row[self.time_span] == current:
				current_data = row
			elif row[self.time_span] == previous:
				previous_data = row
				
		data = {}
		data['prev_data'] = previous_data
		data['current_data'] = current_data
		return data
		
	def _date_last_year(self, date):
		if self.time_span == "7DayTotals":
			return date - timedelta(days=364)
		elif self.time_span == "month":
			return datetime(date.year-1, date.month, date.day)
		
	def subscribers(self, id):
		"""
		Returns dictionary containing data for Subscriber Change
		"""
		subscriber_count = analytics.get_stats(id)['subscriberCount'] # number of CURRENT subscribers 

		results = analytics.run_analytics_report(start_date=self.previous.strftime("%Y-%m-%d"), end_date=self.start.strftime("%Y-%m-%d"), metrics="subscribersGained,subscribersLost", 
													dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	

		#format data into previous and current dictionaries 
		data = self._format_data_rows(results)
		data = self._format_period_data(data, self.previous, self.start)

		prev_data = data['prev_data']
		current_data = data['current_data']

		yr_start= self._date_last_year(self.previous)
		yr_end = self._date_last_year(self.start)
		year_results = analytics.run_analytics_report(start_date=yr_start.strftime("%Y-%m-%d"), end_date=yr_end.strftime("%Y-%m-%d"), metrics="subscribersGained,subscribersLost", 
													dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	

		#format data into previous and current dictionaries 
		data = self._format_data_rows(year_results)
		data = self._format_period_data(data, yr_start, yr_end)

		year_data = data['current_data']
	
		current_subs_change = current_data['subscribersGained'] - current_data['subscribersLost']
		prev_subs_change = prev_data['subscribersGained'] - prev_data['subscribersLost']
		year_subs_change = year_data['subscribersGained'] - year_data['subscribersLost']

		#find total last month and change
		subs_prev = float(subscriber_count) - current_subs_change
		total_percentage = percentage(current_subs_change, subs_prev)

		difference = current_subs_change - prev_subs_change
		percent = percentage(difference, prev_subs_change)
	
		yr_difference = current_subs_change - year_subs_change
		yoy_percent = percentage(yr_difference, year_subs_change)
		
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
		"""
		Returns dictionary containing data for Estimated Minutes Watched 
		"""
		results = analytics.run_analytics_report(start_date=self.previous.strftime("%Y-%m-%d"), end_date=self.start.strftime("%Y-%m-%d"), metrics="estimatedMinutesWatched", 
													dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	

		#format data into previous and current dictionaries 
		data = self._format_data_rows(results)
		data = self._format_period_data(data, self.previous, self.start)

		prev_data = data['prev_data']
		current_data = data['current_data']

		yr_start= self._date_last_year(self.previous)
		yr_end = self._date_last_year(self.start)
		year_results = analytics.run_analytics_report(start_date=yr_start.strftime("%Y-%m-%d"), end_date=yr_end.strftime("%Y-%m-%d"), metrics="estimatedMinutesWatched", 
													dimensions=self.time_span, filters="channel==%s" % id, max_results="100")

		#format data into previous and current dictionaries 
		data = self._format_data_rows(year_results)
		data = self._format_period_data(data, yr_start, yr_end)

		year_data = data['current_data']
	
		current = current_data['estimatedMinutesWatched']
		last = prev_data['estimatedMinutesWatched']
		year = year_data['estimatedMinutesWatched']

	
		difference = current-last
		percent = percentage(difference, last)
		
		yr_difference = current-year
		yoy_percent = percentage(yr_difference, year)
		
		watch_time = {}
		watch_time['current'] = int(current)
		watch_time['last_month'] = int(last)
		watch_time['change_fig'] = int(difference)
		watch_time['change_percentage'] = percent
		watch_time['yoy_percentage'] = yoy_percent
	
		return watch_time
		
	def get_summary_table(self):
		"""
		Returns a list of dictionaries, one dictionary (or row) per channel:
		[{
			channel: channel_name,
			watch_time:	{
							current: n,			#sorted by this number
							last_month: n,
							change_fig: n,
							change_percentage: n(%),
							yoy_percentage: n(%),
			}
			subscribers: {
							current: n,	
							last_month: n,
							change_fig: n,
							change_percentage: n(%),
							yoy_percentage: n(%),
			}
		}]
		"""
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
		
	def data_by_country(self, start, end):
		"""
		Returns metrics for channels aggregated by country 
		"""
		current_data = []
		for channel in self.channels:
			id = channel_ids[channel]
			results = analytics.run_analytics_report(start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"), metrics="views,estimatedMinutesWatched,subscribersGained,subscribersLost", dimensions="country", 
															filters="channel==%s" % id, max_results=None, sort="-estimatedMinutesWatched")		
												
			rows = self._format_data_rows(results)
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
		"""
		Returns metrics ordered by watch time for countries
		"""
		#get previous month dates
		prev_end = self.start - timedelta(days=1)
		if self.time_span == "month":
			prev_start = datetime(prev_end.year, prev_end.month, 1)
		elif self.time_span == "7DayTotals":
			prev_start = prev_end - timedelta(days=6)
		
		yr_end = self._date_last_year(self.end)
		yr_start = self._date_last_year(self.start)

		countries = self.data_by_country(self.start, self.end)
		prev_countries = self.data_by_country(prev_start, prev_end)
		yr_countries = self.data_by_country(yr_start, yr_end)
	
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
			row['emw_percentage'] =  percentage(row['emw_change'], prev['estimatedMinutesWatched'])
			
			row['views_change'] = row['views'] - prev['views']
			row['views_percentage'] =  percentage(row['views_change'], prev['views'])

			row['subscribers'] = row['subscribersGained'] - row['subscribersLost']
			prev['subscribers'] = prev['subscribersGained'] - prev['subscribersLost']
			row['sub_change'] = row['subscribers'] - prev['subscribers']
		
			row['sub_percentage'] = percentage(row['sub_change'], prev['subscribers'])
			
			
			row['emw_yoy_change'] = row['estimatedMinutesWatched'] - year['estimatedMinutesWatched']
			row['emw_yoy_percentage'] =  percentage(row['emw_yoy_change'], year['estimatedMinutesWatched'])

			row['views_yoy_change'] = row['views'] - year['views']
			row['views_yoy_percentage'] =  percentage(row['views_change'], year['views'])

			year['subscribers'] = year['subscribersGained'] - year['subscribersLost']
			row['yoy_sub_change'] = row['subscribers'] - year['subscribers']
		
			row['yoy_sub_percentage'] = percentage(row['yoy_sub_change'], year['subscribers'])			
		
		return table			

	def get_stats_table(self):
		"""
		Returns a list of dictionaries, one dictionary (or row) per channel:
		[{
			channel: channel_name,
			stats : {
						prev_data : {
										views: n,
										likes: n,
										dislikes: n,
										comments: n,
										shares: n,
										subscribersGained: n,
						},
						current_data : {
										views: n,	#sorted by this number
										likes: n,
										dislikes: n,
										comments: n,
										shares: n,
										subscribersGained: n,
						},
						year_data : {
										views: n,
										likes: n,
										dislikes: n,
										comments: n,
										shares: n,
										subscribersGained: n,
						},
						ld_ratio : {
										l_ratio: n,
										d_ratio: n,
										prev: n, (%)
										current: n, (%) 
										year: n, (%)
										percentage: n, (%)
										yoy_percentage: n (%)
						},
						likes: {
												prev: n, (rate)
												current: n, (rate)
												year: n, (rate)
												change: n, (rate)
												percentage: n, (%)	
												yoy_change: n, (rate)
												yoy_percentage: n, (%)							
						},
						subscribersGained: {
												prev: n, (rate)
												current: n, (rate)
												year: n, (rate)
												change: n, (rate)
												percentage: n, (%)	
												yoy_change: n, (rate)
												yoy_percentage: n, (%)							
						},
						comments: {
												prev: n, (rate)
												current: n, (rate)
												year: n, (rate)
												change: n, (rate)
												percentage: n, (%)	
												yoy_change: n, (rate)
												yoy_percentage: n, (%)							
						},
						shares: {
												prev: n, (rate)
												current: n, (rate)
												year: n, (rate)
												change: n, (rate)
												percentage: n, (%)	
												yoy_change: n, (rate)
												yoy_percentage: n, (%)							
						}
			}
		},...]
		"""
		table=[]
		for channel in self.channels:
			row = {}
			id = channel_ids[channel]
			row['channel'] = channel	
			results = analytics.run_analytics_report(start_date=self.previous.strftime("%Y-%m-%d"), end_date=self.start.strftime("%Y-%m-%d"), metrics="views,likes,dislikes,comments,shares,subscribersGained", 
														dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
																	
			#format data into previous and current dictionaries 
			data = self._format_data_rows(results)
			data = self._format_period_data(data, self.previous, self.start)

			prev_data = data['prev_data']
			current_data = data['current_data']

			yr_start= self._date_last_year(self.previous)
			yr_end = self._date_last_year(self.start)
			year_results = analytics.run_analytics_report(start_date=yr_start.strftime("%Y-%m-%d"), end_date=yr_end.strftime("%Y-%m-%d"), metrics="views,likes,dislikes,comments,shares,subscribersGained", 
														dimensions=self.time_span, filters="channel==%s" % id, max_results="100")	
																	
			#format data into previous and current dictionaries 
			data = self._format_data_rows(year_results)
			data = self._format_period_data(data, yr_start, yr_end)

			year_data = data['current_data']
			
			#like/dislike ratio mom change
			ld_ratio = {}

			#multiple = gcd(current_data['likes'], current_data['dislikes']) #highest common divisor
			multiple = current_data['dislikes'] #use dislikes so create a n:1 like:dislike ratio
			try:
				ld_ratio['l_ratio'] = sig_fig(2, current_data['likes'] / multiple)
			except ZeroDivisionError:
				ld_ratio['l_ratio'] = 0
				
			try:
				ld_ratio['d_ratio'] = sig_fig(2, current_data['dislikes'] / multiple)
			except ZeroDivisionError:
				ld_ratio['d_Ratio'] = 0
				
			#work out the percentages and find the change
			ld_ratio['prev'] = percentage(prev_data['likes'], prev_data['dislikes'])
			ld_ratio['current'] = percentage(current_data['likes'], current_data['dislikes'])
			ld_ratio['year'] = percentage(year_data['likes'], year_data['dislikes'])

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
				prev_rate = rate_per_1000(prev_data[metric], prev_data['views'])
				data['prev'] = sig_fig(2, prev_rate)
				curr_rate = rate_per_1000(current_data[metric], current_data['views'])
				data['current'] = sig_fig(2, curr_rate)
				year_rate = rate_per_1000(year_data[metric], year_data['views'])
				data['year'] = sig_fig(2, year_rate)
				
				data['change'] = data['current'] - data['prev']
				change = percentage(data['change'], data['prev'])
				data['percentage'] = change
				
				data['yoy_change'] = data['current'] - data['year']
				change = percentage(data['yoy_change'], data['year'])
				data['yoy_percentage'] = change			
				
				total[metric] = data
			
			row['stats']= total
			table.append(row)
		
		#sort by views
		table = sorted(table, key=lambda k: k['stats']['current_data']['views'], reverse=True)
		return table

	def get_top_videos_table(self):
		table=[]
		for channel in self.channels:
			id = channel_ids[channel]
			results = analytics.run_analytics_report(start_date=self.start.strftime("%Y-%m-%d"), end_date=self.end.strftime("%Y-%m-%d"), metrics="estimatedMinutesWatched,views", dimensions="video", 
													filters="channel==%s" % id, max_results="20", sort="-estimatedMinutesWatched")		
								
			data = self._format_data_rows(results)							
			for video in data:
				video_name = analytics.get_video(video['video'])
				video['title'] = video_name['items'][0]['snippet']['title'] 
				video['channel'] = channel				
				table.append(video)
				
		table = sorted(table, key=lambda k: k['estimatedMinutesWatched'], reverse=True)
		return table[:10]	
	
	def data_by_traffic_source(self, start, end):
		"""
		Returns data for specified traffic source types for each channel
		Removes the sources "advertising", "no link embedded" and "promoted" as currently giving 0% traffic
		"""
		table=[]
		source_types= ['ANNOTATION', 'EXT_URL', 'NO_LINK_OTHER', 'NOTIFICATION', 'PLAYLIST', 'RELATED_VIDEO', 'SUBSCRIBER', 'YT_CHANNEL', 'YT_OTHER_PAGE', 'YT_PLAYLIST_PAGE', 'YT_SEARCH']
		for channel in self.channels:
			id = channel_ids[channel]
			row = {}
			row['channel'] = channel	
			results = analytics.run_analytics_report(start_date=start.strftime("%Y-%m-%d"), end_date=end.strftime("%Y-%m-%d"), metrics="estimatedMinutesWatched", 
														dimensions="insightTrafficSourceType", filters="channel==%s" % id, sort="-estimatedMinutesWatched")			
			data = self._format_data_rows(results)	
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
				for type in missing:
					checked_data.append({'insightTrafficSourceType':type, 'estimatedMinutesWatched':0.0})
			
			row['data'] = checked_data
			table.append(row)
			
		return table	

	def get_traffic_source_table(self):
		"""
		Returns data for traffic sources
		List of channels sorted by total watch time (from traffic sources), data for sources and sources also sorted by total watch time
		"""
		"""
		#for if need to gather previous data for mom/yoy change 
		prev_end = self.start - timedelta(days=1)
		if self.time_span == "month":
			prev_start = datetime(prev_end.year, prev_end.month, 1)
		elif self.time_span == "7DayTotals":
			prev_start = prev_end - timedelta(days=6)
		
		yr_end = self._date_last_year(self.end)
		yr_start = self._date_last_year(self.start)"""		
			
		table = self.data_by_traffic_source(self.start, self.end)
		
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
				source['breakdown'] = percentage(source['estimatedMinutesWatched'], row['channel_watch_time'])
		
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
			