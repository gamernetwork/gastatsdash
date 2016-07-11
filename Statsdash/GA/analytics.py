import json
from datetime import timedelta
import random
import time
from Statsdash.config import LOGGING

#from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
from googleapiclient import errors
from apiclient.discovery import build

from oauth2client.service_account import ServiceAccountCredentials

import config
import Statsdash.utilities as utils
import logging, logging.config, logging.handlers

logging.config.dictConfig(LOGGING)
logger = logging.getLogger('report')

with open(config.KEY_FILE) as f:
    PRIVATE_KEY = f.read()

class Analytics(object):
    
    def __init__(self):
        #credentials = SignedJwtAssertionCredentials(config.CLIENT_EMAIL, PRIVATE_KEY,
            #'https://www.googleapis.com/auth/analytics.readonly')
        credentials = ServiceAccountCredentials.from_p12_keyfile(config.CLIENT_EMAIL, config.KEY_FILE, scopes='https://www.googleapis.com/auth/analytics.readonly')
        http_auth = credentials.authorize(Http())
        ga_service = build('analytics', 'v3', http=http_auth)
        self.ga = ga_service.data().ga()   
             
    def execute_query(self, query):
        for i in range(1,6):
            try:
                return query.execute()	
            except errors.HttpError, e:
                error = json.loads(e.content)
                if i == 5:
                    logger.warning("Error, request has failed 5 times")
                    raise
                if error['error'].get('code') == 500:
                    logger.warning("500 Error, #%d, trying again...", i)
                    time.sleep((2 ** i) + random.random())
                if error['error'].get('code') == 503:
                    logger.warning("503 Error, #%d, trying again...", i)
                    time.sleep((2 ** i) + random.random())
                else:
                    raise
            except Exception, e:
                logger.warning("Unknown error from GA")
                logger.warning("Type: " + type(e) + "  " + e)
        return None

        
    def data_available(self, site_id, stats_date):
        # TODO: Persist these results in a cache so we don't smash our rate limit
        query = self.ga.get(
            ids=site_id,
            start_date=stats_date,
            end_date=stats_date,
            metrics="ga:pageviews",
            dimensions="ga:dateHour",
            include_empty_rows=True,
        )
        results = query.execute()
        try:
            data_available = len(results['rows']) == 24
        except KeyError:
            #print "no data"
            logger.info("site_id %s returned no rows for data_available check on %s" % (site_id, stats_date))
            return False
        if not data_available:
            #print "no data"
            logger.info("site_id %s data_available check on %s returned rows: %s" % (site_id, stats_date, results['rows']))
        return data_available
        
    def run_report(self, site_id, start, end, metrics=None, dimensions=None, filters=None, sort=None, max_results=None):
        query = self.ga.get(
            ids=site_id,
            start_date=start,
            end_date=end,
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            sort=sort,
            max_results=max_results,
            include_empty_rows=True,     
        )
        
        return self.execute_query(query)
 
 
    def rollup_ids(self, ids, start, end, metrics, dimensions=None, filters=None, sort=None, max_results=None, aggregate_key=None):
        main_row = []
        for id in ids:
            results = self.run_report(id, start, end, metrics=metrics, dimensions=dimensions, filters=filters, sort=sort, max_results=max_results)
            rows = utils.format_data_rows(results)
            if rows:     
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                main_row.extend(rows)
            else:
                #no data
                #print "No data for id " + id + " " + " on " + start + " - " + end
                logger.debug("No data for " + id + " " + " on " + start + " - " + end)
                logger.debug("for metrics: " + metrics + " dimensions: " + str(dimensions) + " filters: " + str(filters))
        main_row = utils.aggregate_data(main_row, metrics.split(","), aggregate_key)
        return main_row       
        
        
        
        
        
        
        
        