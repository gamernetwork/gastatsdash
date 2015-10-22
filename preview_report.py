import reporting
import argparse

from datetime import date, timedelta

import config
from analytics import get_analytics, StatsRange

parser = argparse.ArgumentParser()
parser.add_argument("reporttype", help="the type of report you wish to generate")
parser.add_argument("-d", "--destination", help="destination for return file", default =".")
args = parser.parse_args()
report_type = args.reporttype
file_name = "%s_preview.html" % report_type
file_src = args.destination + "/" + file_name

all_sites = config.TABLES.keys()
today = date.today() - timedelta(days=2)
day_before = date.today() - timedelta(days=3)
yesterday_stats_range = StatsRange("Yesterday", today, today)
day_before_stats_range = StatsRange("Day Before", day_before, day_before)
    
if report_type == "NetworkArticleBreakdown":
    network_breakdown = reporting.NetworkArticleBreakdown(['foo@example.net'], 'Network Article Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range, "Daily Summary", article_limit=25)  
    
elif report_type == "NetworkBreakdown":
    network_breakdown = reporting.NetworkBreakdown(['foo@example.net'], 'Network Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range)
    
elif report_type == "ArticleBreakdown":
    network_breakdown = reporting.NetworkBreakdown(['foo@example.net'], 'Article Breakdown', all_sites, 
        yesterday_stats_range, day_before_stats_range, "Daily Summary")
    
else:
	print "unknown report type"	

generated_html = network_breakdown.generate_report() 
    
with open(file_src, 'w') as file:
	file.write(generated_html.encode("utf-8"))	
