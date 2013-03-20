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

# GA table ids for each site
TABLES = {'eurogamer.net':'ga:24487962',
          'eurogamer.de' :'ga:20485214',
          'eurogamer.fr' :'ga:24488326',
          'eurogamer.es' :'ga:24488378',
          'eurogamer.it' :'ga:24488410',
          'eurogamer.se' :'ga:31986560',
          'eurogamer.nl' :'ga:24488436',
          'eurogamer.pt' :'ga:24488474',
          'eurogamer.cz' :'ga:24488523',
          'eurogamer.be' :'ga:24488541',
          'eurogamer.dk' :'ga:24488560',
          'eurogamer.pl' :'ga:64991349',
          'eurogamer.br' :'ga:64988449',
          'modojo.com' :'ga:43806',
          'vg247.com' :'ga:6872882',
          'vg247.ru' :'ga:59715320',
          'nintendolife.com' :'ga:961919',
          'purexbox.com' :'ga:38375276',
          'pushsquare.com' :'ga:14459794',
          'outsidexbox.com' :'ga:61719556',
          'rockpapershotgun.com' :'ga:5031782',
          'video-game-wallpapers.com' :'ga:68749538',
          'gamesindustry.biz' :'ga:11504681'}

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
for table, gaid in sorted( TABLES.items()[:2] ):

	# get totals

	data_query = gdata.analytics.client.DataFeedQuery({
		'ids' : gaid,
		'start-date' : start_date,
		'end-date' : end_date,
		'metrics' : 'ga:visitors,ga:pageviews'
	})

	feed = gac.GetDataFeed(data_query)

	totals = {}

	for metric in feed.aggregates.metric:
		if metric.type == "integer":
			totals[ metric.name.replace( "ga:", "" ) ] = int( metric.value );

	# country breakdown

	data_query = gdata.analytics.client.DataFeedQuery({
		'ids' : gaid,
		'start-date' : start_date,
		'end-date' : end_date,
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

	sites.append( {
		"name": table,
		"countries": countries,
		"totals": totals
	} )

#print total_hits, total_pages

print json.dumps( sites )
sys.exit(0)

t = Template( open( "dash.html" ).read() )
c = Context( {
	"sites": sites
} )
html = t.render(c)

print html
sys.exit(0)

