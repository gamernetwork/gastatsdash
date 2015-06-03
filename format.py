#!/usr/bin/python

import sys
import argparse
import json
import pynliner
import os

from django.template import Template, Context
import django.template.loader
import django.template
import django.conf

import django

cwd=os.path.dirname(os.path.realpath(__file__))
django.conf.settings.configure( TEMPLATE_DIRS=(os.path.join(cwd, "templates"),), INSTALLED_APPS=['django.contrib.humanize'] )

django.setup()

parser = argparse.ArgumentParser(description='Format GAStatsDash data (json input) into nice tables and stuff.')
parser.add_argument('--template', dest='template', type=str, help='Which template to use (default: templates/dash.html)', default='dash.html')
parser.add_argument('--email-safe', dest='email', action='store_true', help='Inline all styles so output can be piped into an email.')
parser.add_argument('infile', type=argparse.FileType('r'), help='JSON input file (or - for stdin)')
args = parser.parse_args()

data = json.loads( args.infile.read() )
# { "period" : sys.argv[1], "start_date" : start_date, "end_date": end_date, "sites": sites }
# calc country totals

from collections import defaultdict

countries = defaultdict( lambda:defaultdict(int) )
totals = defaultdict(int)

sites = list( data["sites"] )
sites.sort( key=lambda k: k['totals']['pageviews'], reverse=True )
cum = { "pageviews":0, "visitors": 0 }

for site in sites:
    # set up cumulative values for site view
    cum[ "pageviews" ] += site[ "totals" ][ "pageviews" ]
    cum[ "visitors" ] += site[ "totals" ][ "visitors" ]
    site[ "cum" ] = cum.copy()
    site[ "countries" ].sort( key=lambda k: k['metrics']['pageviews'], reverse=True )
    # set 
    for country in site[ "countries" ]:
        # create global (aggregate) country stats (not rollup)
        countries[ country[ "name" ] ][ "pageviews" ] += country[ "metrics" ][ "pageviews" ]
        countries[ country[ "name" ] ][ "visitors" ] += country[ "metrics" ][ "visitors" ]

    # create global (aggregate) totals (not rollup)
    totals["pageviews"] += site[ "totals" ][ "pageviews" ]
    totals["visitors"] += site[ "totals" ][ "visitors" ]

#rollup_countries = list(( { "name": key, "metrics": val } for key, val in rollup[ "countries" ].items() ))
countries = list(( { "name": key, "metrics": val } for key, val in countries.items() ))
countries.sort( key=lambda k: k['metrics']['pageviews'], reverse=True )
cum = { "pageviews":0, "visitors": 0 }
r_cum = { "pageviews":0, "visitors": 0 }
for c in countries:
    cum[ "pageviews" ] += c[ "metrics" ][ "pageviews" ]
    cum[ "visitors" ] += c[ "metrics" ][ "visitors" ]
    c[ "cum" ] = cum.copy()

register = django.template.Library()
@register.filter
def as_percentage_of(part, whole):
    try:
        return "%0.1f%%" % (float(part) / whole * 100)
    except (ValueError, ZeroDivisionError):
        return ""

@register.filter
def pages_per_visitor(part, whole):
    try:
        return "%0.1f" % (float(part) / whole)
    except (ValueError, ZeroDivisionError):
        return "%%Err%%"

django.template.builtins.append(register)

t = django.template.loader.get_template( args.template )
c = Context( {
    "sites": sites,
    "countries": countries,
    "period": data[ "period" ],
    "start_date": data[ "start_date" ],
    "end_date": data[ "end_date" ],
    "totals": totals,
    "do_rollup": False,
} )
html = t.render(c)

if args.email:
    print pynliner.fromString(html)
else:
    print html
