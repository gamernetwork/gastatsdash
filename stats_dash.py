#!/usr/bin/python

"""
Dashboard script for sales guys

Useful
------
metrics:
https://developers.google.com/analytics/devguides/reporting/core/dimsmets
"""

import re
import sys

from operator import itemgetter
from datetime import date, timedelta

import gdata.analytics.client
import gdata.sample_util

# module containing tuples of account credentials (username, password), not under version control
import credentials

APP  = 'EG-UniquesAcrossNetwork'

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

def usage():
	print 'Retrieves the total uniques hits for network sites.'
	print
	print 'Usage:', sys.argv[0], '<days>'
	print '  <days>  - number of days to query'
	
try:
	days     = int(sys.argv[1])
except (IndexError, KeyError, ValueError):
	usage()
	sys.exit(2)

my_client = gdata.analytics.client.AnalyticsClient(source=APP)

try:
    user, password = credentials.google
    my_client.ClientLogin(user, password, source=APP)
except gdata.client.BadAuthentication:
    print 'Invalid User Credentials'
    sys.exit(1)
except gdata.client.Error:
    print 'Login Error'
    sys.exit(1)

total_hits = 0
total_pages = 0
for table, gaid in TABLES.items():

	data_query = gdata.analytics.client.DataFeedQuery({
		'ids' : gaid,
		'start-date' : date.today() - timedelta(days=days) - timedelta(days=365),
		'end-date' : date.today() - timedelta(days=1) -  timedelta(days=365),
		'metrics' : 'ga:visitors,ga:pageviews'
	})

	feed = my_client.GetDataFeed(data_query)

	for entry in feed.entry:
		hits = int(entry.metric[0].value)
		pages = int(entry.metric[1].value)
		
		print "%s: %i %i" % (table, hits, pages)
		total_hits += hits
		total_pages += pages

print total_hits, total_pages
		


