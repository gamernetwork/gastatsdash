#!/usr/bin/python

"""
Dashboard script for sales guys

Useful
------
metrics:
https://developers.google.com/analytics/devguides/reporting/core/dimsmets
"""

#import re
import sys
import json

#from operator import itemgetter
from datetime import date, timedelta

import gdata.analytics.client

import dateutils

# module containing tuples of account credentials (username, password), not under version control
import credentials

APP  = 'EG-DashBoard'

COUNTRIES_REGEX = "Czec|Germa|Denma|Spai|Franc|Italy|Portug|Swede|Polan|Brazi|Belgiu|Netherl|United Ki|Irela|United St|Canad|Austral|New Ze"

#credentials.TABLES

# so I think it's an inclusive date range
# same as the web interface
if sys.argv[1] == "month":
    end_date = date.today() - timedelta(days=1)
    start_date = dateutils.subtract_one_month( date.today() )
else:
    d = int(sys.argv[1])
    end_date = date.today() - timedelta(days=1)
    start_date = date.today() - timedelta(days=d)

gac = gdata.analytics.client.AnalyticsClient(source=APP)

try:
    user, password = credentials.google
    gac.ClientLogin(user, password, source=APP)
except gdata.client.BadAuthentication:
    print 'Invalid User Credentials'
    sys.exit(1)
except gdata.client.Error:
    print 'Login Error'
    sys.exit(1)

total_hits = 0
total_pages = 0
sites = []

def get_country_breakdown( gaid, start_date, end_date ):

    data_query = gdata.analytics.client.DataFeedQuery({
        'ids' : gaid,
        'start-date' : start_date,
        'end-date' : end_date,
        'sort' : '-ga:pageviews',
        'metrics' : 'ga:visitors,ga:pageviews',
        'dimensions' : 'ga:country',
        'filters': 'ga:country=~' + COUNTRIES_REGEX
    })

    feed = gac.GetDataFeed(data_query)
    countries = []

    for entry in feed.entry:
        cm = {}
        for metric in entry.metric:
            if metric.type == "integer":
                cm[ metric.name.replace( "ga:", "" ) ] = int( metric.value );

        countries.append( {
            "name": entry.dimension[0].value,
            "metrics": cm
        } )

    # get ROW data

    data_query = gdata.analytics.client.DataFeedQuery({
        'ids' : gaid,
        'start-date' : start_date,
        'end-date' : end_date,
        'sort' : '-ga:pageviews',
        'metrics' : 'ga:visitors,ga:pageviews',
        'filters': 'ga:country!~' + COUNTRIES_REGEX
    })

    feed = gac.GetDataFeed(data_query)

    data = {}
    for metric in feed.aggregates.metric:
        if metric.type == "integer":
            data[ metric.name.replace( "ga:", "" ) ] = int( metric.value );

    countries.append( {
        "name": "ROW",
        "metrics": data
    } )

    return countries

def get_totals( gaid, start_date, end_date ):

    data_query = gdata.analytics.client.DataFeedQuery({
        'ids' : gaid,
        'start-date' : start_date,
        'end-date' : end_date,
        'sort' : '-ga:pageviews',
        'metrics' : 'ga:visitors,ga:pageviews'
    })

    feed = gac.GetDataFeed(data_query)

    totals = {}

    for metric in feed.aggregates.metric:
        if metric.type == "integer":
            totals[ metric.name.replace( "ga:", "" ) ] = int( metric.value );

    return totals



if __name__ == "__main__":

    # rollup

    sys.stderr.write( "rollup\n" )
    rollup_totals = get_totals( credentials.ROLLUP, start_date, end_date )
    rollup_countries = get_country_breakdown( credentials.ROLLUP, start_date, end_date )

    for table, gaid in sorted( credentials.TABLES.items() ):

        sys.stderr.write( table + "\n" )
        # get totals
        totals = get_totals( gaid, start_date, end_date )

        # country breakdown
        countries = get_country_breakdown( gaid, start_date, end_date )

        sites.append( {
            "name": table,
            "countries": countries,
            "totals": totals,
        } )

    rollup = {
        "countries": rollup_countries,
        "totals": rollup_totals,
    }

    #print total_hits, total_pages

    print json.dumps( { "period" : sys.argv[1], "start_date" : unicode( start_date ), "end_date": unicode( end_date ), "sites": sites, "rollup": rollup } )
    sys.exit(0)

