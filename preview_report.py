import reporting
import argparse

from datetime import date, timedelta

import config
from analytics import get_analytics, StatsRange

parser = argparse.ArgumentParser()
parser.add_argument("reporttype", help="the type of report you wish to generate")
parser.add_argument("-d", "--destination", help="destination for return file", default =".")
parser.add_argument("-n", "--filename", help="name of file", default =0)
args = parser.parse_args()
report_type = args.reporttype
user_file_name = args.filename
if(user_file_name == 0):
	file_name = "%s_preview.html" % report_type
else:
	file_name = "%s.html" % user_file_name
	
file_src = args.destination + "/" + file_name

all_sites = config.TABLES.keys()
today = date.today() - timedelta(days=2)
day_before = date.today() - timedelta(days=3)
yesterday_stats_range = StatsRange("Yesterday", today, today)
day_before_stats_range = StatsRange("Day Before", day_before, day_before)

first_jul = date(2015, 7, 1)
last_jul = date(2015, 7, 30)
first_aug = date(2015, 8, 1)
last_aug = date(2015, 8, 30)
first_sep = date(2015, 9, 1)
last_sep = date(2015, 9, 30)  
july_stats_range = StatsRange("July", first_jul, last_jul)  
august_stats_range = StatsRange("August", first_aug, last_aug)
sept_stats_range = StatsRange("Sept", first_sep, last_sep)
month_stats_range =[july_stats_range, august_stats_range, sept_stats_range]
    
if report_type == "NetworkArticleBreakdown":
    network_breakdown = reporting.NetworkArticleBreakdown(['foo@example.net'], 'Network Article Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range, "Daily Summary", article_limit=25)  
    
elif report_type == "NetworkBreakdown":
    network_breakdown = reporting.NetworkBreakdown(['foo@example.net'], 'Network Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range)
    
elif report_type == "ArticleBreakdown":
    network_breakdown = reporting.ArticleBreakdown(['foo@example.net'], 'Article Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range, "Daily Summary")
    
elif report_type == "TrafficSourceBreakdown":
    network_breakdown = reporting.TrafficSourceBreakdown(['foo@example.net'], 'Traffic Source Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range, month_stats_range, args.destination)
else:
	print "unknown report type"	

print "Generating Report..."
generated_html = network_breakdown.generate_report() 
    
with open(file_src, 'w') as file:
	file.write(generated_html.encode("utf-8"))	
