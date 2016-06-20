import json
from datetime import timedelta

#from oauth2client.client import SignedJwtAssertionCredentials
from httplib2 import Http
from googleapiclient import errors
from apiclient.discovery import build

from oauth2client.service_account import ServiceAccountCredentials

import config
import Statsdash.utilities as utils

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
                    print 'Error, request has failed 5 times'
                    #logger.warning("Error, request has failed 5 times")
                    raise
                if error['error'].get('code') == 500:
                    print '500 Error #%d, trying again ...' % i
                    #logger.warning("500 Error, #%d, trying again...", i)
                else:
                    raise
            except Exception, e:
                print 'We got an unknown error from GA'
                #print 'Type:'
                #print type(e)
                #print e
                #logger.warning("Unknown error from GA")
                #logger.warning("Type: ", type(e), e)
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
            print "no data"
            #logger.info("site_id %s returned no rows for data_available check on %s" % (site_id, stats_date))
            return False
        if not data_available:
            print "no data"
            #logger.info("site_id %s data_available check on %s returned rows: %s" % (site_id, stats_date, results['rows']))
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
            for row in rows:
                row =  utils.convert_to_floats(row, metrics.split(","))
            main_row.extend(rows)
        main_row = utils.aggregate_data(main_row, metrics.split(","), aggregate_key)
        return main_row       
        
        
        
        
        
        
        
        