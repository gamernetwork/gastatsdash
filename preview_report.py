import reporting
import argparse

from datetime import date, timedelta
from dateutils import subtract_one_month
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
week_before = date.today() - timedelta(days = 9)
last_week = week_before  - timedelta(days = 7)
yesterday_stats_range = StatsRange("Yesterday", today, today)
day_before_stats_range = StatsRange("Day Before", day_before, day_before)
week_before_stats_range = StatsRange("Week Before", week_before, week_before)
this_week_stats_range = StatsRange("This Week", week_before, today)
last_week_stats_range = StatsRange("Week Before", last_week, week_before)

first_dec = date(2015, 12, 01)
last_dec = date(2015, 12, 31)
first_nov = date(2015, 11, 01)
last_nov = date(2015, 11, 30)

dec_stats_range = StatsRange("December", first_dec, last_dec)
nov_stats_range = StatsRange("November", first_nov, last_nov)

print today

previous_months = 3
end_date = today
month_stats_range = []
for i in range(0, previous_months):
    start_date = subtract_one_month(end_date)
    month_stats_range.append(StatsRange("month_%d" % i, start_date, end_date))
    end_date = start_date

black_list = ['google', '(direct)', 'eurogamer', 'facebook', 'Twitter', 'bing', '^t.co', 'reddit.com', 'yahoo', 'feedburner', 'newsletter']
   
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
    network_breakdown = reporting.TrafficSourceBreakdown(['foo@example.net'], 'Gamer Network daily statsdash for', all_sites, 
        yesterday_stats_range, week_before_stats_range, 'daily', black_list)
else:
	print "unknown report type"	

print "Generating Report..."
generated_html = network_breakdown.generate_report()['html'] 
    
with open(file_src, 'w') as file:
	file.write(generated_html.encode("utf-8"))	
