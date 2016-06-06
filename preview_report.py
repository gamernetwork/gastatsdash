import reporting
import argparse
import report_schedule
from slimmer import html_slimmer

from datetime import date, timedelta
from dateutils import subtract_one_month
import GA.config as config
from analytics import get_analytics, StatsRange

import logging, logging.config, logging.handlers

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
week_before = date.today() - timedelta(days = 9)
last_week = week_before  - timedelta(days = 7)
yesterday_stats_range = StatsRange("Yesterday", today, today)
day_before_stats_range = StatsRange("Day Before", day_before, day_before)
week_before_stats_range = StatsRange("Week Before", week_before, week_before)
this_week_stats_range = StatsRange("This Week", week_before, today)
last_week_stats_range = StatsRange("Week Before", last_week, week_before)

first_feb = date(2016, 02, 01)
last_feb = date(2016, 02, 29)
first_jan = date(2016, 01, 01)
last_jan = date(2016, 01, 30)

feb_stats_range = StatsRange("FEb", first_feb, last_feb)
jan_stats_range = StatsRange("Jan", first_jan, last_jan)

sat = date(2016, 03, 12)
sun = date(2016, 03, 13)
sat_range = StatsRange("sat", sat, sat)
sun_range = StatsRange("sun", sun, sun)


previous_months = 3
end_date = today
month_stats_range = []
for i in range(0, previous_months):
    start_date = subtract_one_month(end_date)
    month_stats_range.append(StatsRange("month_%d" % i, start_date, end_date))
    end_date = start_date

black_list = report_schedule.black_list

#logging.config.dictConfig(config.LOGGING)
#ogger = logging.getLogger('report')
   
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
    network_breakdown = reporting.TrafficSourceBreakdown(['foo@example.net'], 'Eurogamer.net daily statsdash for', ['eurogamer.net'], 
        sun_range, sat_range, 'daily', black_list)
        
elif report_type == "SocialReport":
    network_breakdown = reporting.SocialReport(['foo@example.net'], 'Gamer Network monthly social report for', all_sites, 
        feb_stats_range, jan_stats_range, 'monthly')
        
else:
	print "unknown report type"	

if network_breakdown.data_available(override=True):
  generated_html = network_breakdown.generate_report()['html'] 
  generated_html = html_slimmer(generated_html)
    
with open(file_src, 'w') as file:
	file.write(generated_html.encode("utf-8"))	
