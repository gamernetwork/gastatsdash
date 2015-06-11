#!/usr/bin/python

"""
Dashboard script for sales guys

Useful
------
metrics:
https://developers.google.com/analytics/devguides/reporting/core/dimsmets
"""

import sys
import json
from datetime import date, timedelta
from oauth2client.client import SignedJwtAssertionCredentials
import config

from httplib2 import Http
from apiclient.discovery import build
import dateutils

from analytics import StatsRange


with open(config.KEY_FILE) as f:
    private_key = f.read()

credentials = SignedJwtAssertionCredentials(config.CLIENT_EMAIL, private_key,
    'https://www.googleapis.com/auth/analytics.readonly')

http_auth = credentials.authorize(Http())

ga_service = build('analytics', 'v3', http=http_auth)
ga = ga_service.data().ga()

COUNTRIES_REGEX = "Czec|Germa|Denma|Spai|Franc|Italy|Portug|Swede|Polan|Brazi|Belgiu|Netherl|United Ki|Irela|United St|Canad|Austral|New Ze"

last_year_range = None
# so I think it's an inclusive date range
# same as the web interface
if sys.argv[1] == "month":
    end_date = date.today() - timedelta(days=1)
    start_date = dateutils.subtract_one_month(date.today())
    current_range = StatsRange("This Month", start_date, end_date)
    last_year_end_date = end_date - timedelta(days=365)
    last_year_start_date = start_date - timedelta(days=365)
    last_year_range = StatsRange("This Month Last Year", last_year_start_date, last_year_end_date)
    end_date = start_date - timedelta(days=1)
    start_date = dateutils.subtract_one_month(end_date)
    previous_range = StatsRange("Last Month", start_date, end_date)
else:
    d = int(sys.argv[1])
    end_date = date.today() - timedelta(days=1)
    start_date = date.today() - timedelta(days=d)
    current_range = StatsRange("This Period", start_date, end_date)
    end_date = start_date - timedelta(days=1)
    start_date = start_date - timedelta(days=d)
    previous_range = StatsRange("Last Period", start_date, end_date)

total_hits = 0
total_pages = 0
sites = []

def unpack(seq, n=2):
    """ unpacks a the first n elements from a list and returns a list seq[0]...seq[n-1] + seq[n:]
        to emulate python 3's extended iterable unpacking https://www.python.org/dev/peps/pep-3132/
    """
    for row in seq:
        yield [e for e in row[:n]] + [row[n:]]

def repack(feed):
    countries = []

    for country, metrics in unpack(feed['rows'], 1):
        cm = {}
        for label, value in zip(feed['query']['metrics'], metrics):
            cm[label.replace('ga:', '')] = int(value)

        countries.append( {
            "name": country,
            "metrics": cm
        } )

    return countries

def get_country_breakdown(gaid, start_date, end_date):

    feed = ga.get(
        ids = gaid,
        start_date = start_date,
        end_date = end_date,
        sort = '-ga:pageviews',
        metrics = 'ga:visitors,ga:pageviews',
        dimensions = 'ga:country',
        filters = 'ga:country=~' + COUNTRIES_REGEX
    ).execute()

    countries = repack(feed)

    # get ROW data

    feed = ga.get(
        ids = gaid,
        start_date = start_date,
        end_date = end_date,
        sort = '-ga:pageviews',
        metrics = 'ga:visitors,ga:pageviews',
        filters = 'ga:country!~' + COUNTRIES_REGEX
    ).execute()

    data = {}
    for label, value in feed['totalsForAllResults'].items():
        data[label.replace('ga:', '')] = int(value)

    countries.append( {
        "name": "ROW",
        "metrics": data
    } )

    return countries

def get_totals(gaid, start_date, end_date):
    data_query = ga.get(
        ids=gaid,
        start_date=start_date,
        end_date=end_date,
        sort='-ga:pageviews',
        metrics='ga:visitors,ga:pageviews'
    ).execute()
    feed = data_query['totalsForAllResults']

    totals = {}
    for label, metric in feed.items():
        totals[ label.replace( u"ga:", u"" ) ] = int(metric);

    return totals

def get_change(current_totals, previous_totals):
    change = {}
    current_visitors = current_totals.get('visitors', 0)
    previous_visitors = previous_totals.get('visitors', 0)
    change['visitors'] = current_visitors - previous_visitors
    current_pageviews = current_totals.get('pageviews', 0)
    previous_pageviews = previous_totals.get('pageviews', 0)
    change['pageviews'] = current_pageviews - previous_pageviews
    return change

if __name__ == "__main__":
    current_start = current_range.get_start()
    current_end = current_range.get_end()
    previous_start = previous_range.get_start()
    previous_end = previous_range.get_end()
    #print "current: %s - %s" % (current_start, current_end)
    #print "previous: %s - %s" % (previous_start, previous_end)

    for table, gaid in sorted( config.TABLES.items() ):

        sys.stderr.write( table + "\n" )
        # get totals
        current_totals = get_totals(gaid, current_start, 
            current_end)
        previous_totals = get_totals(gaid, previous_start, 
            previous_end)
        if last_year_range:
            yoy_totals  = get_totals(gaid, last_year_range.get_start(), 
                last_year_range.get_end())

        # country breakdown
        countries = get_country_breakdown(gaid, current_start, 
            current_end)

        change = get_change(current_totals, previous_totals)
        site_data = {
            "name": table,
            "countries": countries,
            "totals": current_totals,
            "previous_totals": previous_totals,
            "change": change,
        }
        if last_year_range:
            site_data['yoy_totals'] = yoy_totals
            site_data['yoy_change'] = get_change(current_totals, yoy_totals)

        sites.append(site_data)

        

    print json.dumps({
        "period" : sys.argv[1],
        "start_date" : unicode(current_start),
        "end_date": unicode(current_end),
        "sites": sites
    })
    sys.exit(0)

