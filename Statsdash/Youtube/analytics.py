#!/usr/bin/python

from datetime import datetime, timedelta
import httplib2
import os
import sys
import json
import config
import Statsdash.utilities as utils
from Statsdash.config import LOGGING

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from oauth2client.service_account import ServiceAccountCredentials
import logging, logging.config, logging.handlers

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

CLIENT_SECRETS_FILE = config.CLIENT_SECRETS_FILE

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/yt-analytics.readonly", "https://www.googleapis.com/auth/youtubepartner"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_ANALYTICS_API_SERVICE_NAME = "youtubeAnalytics"
YOUTUBE_ANALYTICS_API_VERSION = "v1"
YOUTUBE_PARTNER_API_SERVICE_NAME = "youtubePartner"
YOUTUBE_PARTNER_API_VERSION = "v1"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))


class Analytics(object):
    """
    Class to retrieve data from the Youtube APIs.
    """
    youtube = None
    youtube_analytics = None
    youtube_partner = None
    
    def __init__(self):
    	"""
    	initialise credentials and build api object to query
    	"""
    	flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,scope=" ".join(YOUTUBE_SCOPES),redirect_uri='http://localhost:8080')
    	storage = Storage("%s-oauth2.json" % sys.argv[0])
    	credentials = storage.get()
    
    	#credentials = None
    
    	if credentials is None or credentials.invalid:
    		credentials = run_flow(flow, storage)
    
    	http = credentials.authorize(httplib2.Http())
    
    	self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    		http=http)
    	self.youtube_analytics = build(YOUTUBE_ANALYTICS_API_SERVICE_NAME,
    		YOUTUBE_ANALYTICS_API_VERSION, http=http)
    	self.youtube_partner = build(YOUTUBE_PARTNER_API_SERVICE_NAME,
    		YOUTUBE_PARTNER_API_VERSION, http=http)
    
    
    def execute_query(self, query):
    	"""
    	Try to execute the api query
    	"""
    	try:
    		results = query.execute()
    		return results
    	except HttpError, e:
    		logger.warning("HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    
    def data_available(self, id, date):
    	analytics_query_response = self.youtube_analytics.reports().query(
    		ids="contentOwner==%s" % config.CONTENT_OWNER_ID,
    		metrics="views",
    		dimensions=None,
    		start_date=date,
    		end_date=date,
    		filters="channel==%s" % id,
    		max_results=None,
    		sort=None,
    		)
    
    	results = self.execute_query(analytics_query_response)		
    	try:
    		results['rows']
    		return True
    	except KeyError:
    		return False
        
    def get_content_owner(self):
    	"""
    	returns info on the content owner 
    	returns a dictionary, use ["items"][0]["id"] to get the content owner id 
    	"""
    	contentOwnersService = self.youtube_partner.contentOwners()	
    	request = contentOwnersService.list(fetchMine=True)
    	content_owner_doc = request
    	
    	return self.execute_query(content_owner_doc)
    
    
    def get_channel_id(self):
    	"""
    	returns channel list owned by the content owner
    	"""
    	channels_list_response = self.youtube.channels().list(
    		managedByMe=True,
    		#mine=True,
    		onBehalfOfContentOwner=config.CONTENT_OWNER_ID,
    		part="snippet,contentDetails, contentOwnerDetails"
    		)
    	
    	return self.execute_query(channels_list_response)
    
    def get_stats(self, id):
    	subs = self.youtube.channels().list(
    		part = "statistics",
    		id=id,
    	)

    	return self.execute_query(subs)['items']
    	
    def rollup_stats(self, ids):
        id_combo = ",".join(ids)
        num_ids = len(ids)
        results = self.get_stats(id_combo)
        stats = {}
        for row in results:
            row["statistics"] = utils.convert_to_floats(row["statistics"], row["statistics"].keys())
            for key in row['statistics']:       
                try:
                    stats[key] += row["statistics"][key]
                except:
                    stats[key] = row["statistics"][key]
        return stats
        

  
    def run_analytics_report(self, start_date, end_date, metrics, dimensions, filters, max_results=None, sort=None):
        """
        run a query on youtube analytics
        returns response with data in response['rows']
        rows :list contains all rows of the result table. Each item in the list is an array that contains comma-delimited data corresponding to a single row of data, 
        		ordered by order specified in query
        """
        
        analytics_query_response = self.youtube_analytics.reports().query(
        	ids="contentOwner==%s" % config.CONTENT_OWNER_ID,
        	metrics=metrics,
        	dimensions=dimensions,
        	start_date=start_date,
        	end_date=end_date,
        	filters=filters,
        	max_results=max_results,
        	sort=sort,
        	)
        
        return self.execute_query(analytics_query_response)

    def rollup_ids(self, ids, start, end, metrics, dimensions=None, filters=None, sort=None, max_results=None, aggregate_key=None):
        main_row = []
        for id in ids:
            if filters:
                filter = filters + ";channel==%s" % id
            else: 
                filter = "channel==%s" % id
            results = self.run_analytics_report(start, end, metrics=metrics, dimensions=dimensions, filters=filter, max_results=max_results, sort=sort)
            rows = utils.format_data_rows(results)
            if rows:
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                main_row.extend(rows)
            else:
                #print "No data for id " + id + " " + " on " + start + " - " + end
                logger.debug("No data for " + id + " " + " on " + start + " - " + end)                
        main_row = utils.aggregate_data(main_row, metrics.split(","), aggregate_key)
        return main_row       
        

    def get_video(self, id):
        """
        returns info on video with specified id
        """
        video_results = self.youtube.videos().list(
        	id=id,
        	part="snippet"
        )
        
        return self.execute_query(video_results)
		