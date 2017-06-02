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

with open(config.KEY_FILE) as f:
    private_key = f.read()

credentials = SignedJwtAssertionCredentials(config.CLIENT_EMAIL, private_key,
    'https://www.googleapis.com/auth/analytics.readonly')

http_auth = credentials.authorize(Http())

ga_service = build('analytics', 'v3', http=http_auth)
ga = ga_service.data().ga()

COUNTRIES_REGEX = "Czec|Germa|Denma|Spai|Franc|Italy|Portug|Swede|Polan|Brazi|Belgiu|Netherl|United Ki|Irela|United St|Canad|Austral|New Ze"

# so I think it's an inclusive date range
# same as the web interface
if sys.argv[1] == "month":
    end_date = date.today() - timedelta(days=1)
    start_date = dateutils.subtract_one_month( date.today() )
if sys.argv[1].startswith('201'):
    start_date = date(int(sys.argv[1]), 1, 1)
    end_date = start_date + timedelta(days=365)
else:
    d = int(sys.argv[1])
    end_date = date.today() - timedelta(days=1)
    start_date = date.today() - timedelta(days=d)

start_date = start_date.isoformat()
end_date = end_date.isoformat()

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

def get_country_breakdown( gaid, start_date, end_date ):

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

def get_totals( gaid, start_date, end_date ):
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
        totals[ label.replace( u"ga:", u"" ) ] = int( metric );

    return totals

if __name__ == "__main__":
    for table, props in sorted( config.TABLES.items() ):

        sys.stderr.write( table + "\n" )
        # get totals
        for prop in props:
            totals = get_totals( prop['id'], start_date, end_date )

            # country breakdown
            #countries = get_country_breakdown( gaid, start_date, end_date )

            sites.append( {
                "name": table + ' ' + prop['id'],
                #"countries": countries,
                "totals": totals,
            } )

    print json.dumps({
        "period" : sys.argv[1],
        "start_date" : unicode( start_date ),
        "end_date": unicode( end_date ),
        "sites": sites
    })
    sys.exit(0)

