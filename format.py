#!/usr/bin/python

import sys
import json
import pynliner

from django.template import Template, Context
import django.conf
django.conf.settings.configure()

data = json.loads( sys.stdin.read() )
#{ "period" : sys.argv[1], "start_date" : start_date, "end_date": end_date, "sites": sites }
# calc country totals

from collections import defaultdict

countries = defaultdict(int)
total = 0
for site in data[ "sites" ]:
	for country in site[ "countries" ]:
		countries[ country[ "name" ] ] += country[ "metrics" ][ "pageviews" ]
	total += site[ "totals" ][ "pageviews" ]

countries = ( { "name": key, "pageviews": val } for key, val in countries.items() )

t = Template( open( "dash.html" ).read() )
c = Context( {
	"sites": data[ "sites" ],
	"countries": countries,
	"period": data[ "period" ],
	"start_date": data[ "start_date" ],
	"end_date": data[ "end_date" ],
	"total_pageviews": total,
} )
html = t.render(c)

print pynliner.fromString(html)
