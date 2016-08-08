from Statsdash.report import YoutubeReport, AnalyticsCoreReport, AnalyticsSocialReport, AnalyticsSocialExport, AnalyticsYearSocialReport
import argparse
#import report_schedule

from datetime import date, timedelta
#from Statdateutils import subtract_one_month

import Statsdash.Youtube.config as yt_config
import Statsdash.GA.config as ga_config
import Statsdash.utilities as utils
import Statsdash.report_schedule as config

from premailer import transform


parser = argparse.ArgumentParser()
parser.add_argument("reporttype", help="the type of report you wish to generate")
parser.add_argument("-s", "--sitename", help="name of site", default ="all_sites")
parser.add_argument("-d", "--destination", help="destination for return file", default =".")
parser.add_argument("-n", "--filename", help="name of file", default =0)
args = parser.parse_args()
report_type = args.reporttype
user_file_name = args.filename
if(user_file_name == 0):
	file_name = "%s_preview.html" % report_type
else:
	file_name = "%s.html" % user_file_name
	#file_name = user_file_name
	
if args.sitename == "all_sites":
    sites = ga_config.TABLES.keys()
else:
    sites = [args.sitename]
	
file_src = args.destination + "/" + file_name

monthly_period = utils.StatsRange("period", date(2016, 07, 01), date(2016, 07, 31))
daily_period = utils.StatsRange("period", date(2016, 07, 05), date(2016, 07, 05))

test_period = utils.StatsRange("future", date(2016, 8, 01), date(2016, 8, 30))

if report_type == "YoutubeReport":
    sites =yt_config.CHANNELS.keys()
    yt = YoutubeReport(sites, test_period, [''], "MONTHLY", "Gamer Network Video Report statsdash for")
    check = yt.check_data_availability()
    print check
    html = yt.generate_html()
    #yt.send_email(html)
elif report_type == "AnalyticsCoreReport":
    ac = AnalyticsCoreReport(sites, daily_period, config.all_recipients, "WOW_DAILY", "Report for")
    #ac = AnalyticsCoreReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Report for")
    #ac = AnalyticsCoreReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Report for")
    html = ac.generate_html()
    ac.send_email(html)
elif report_type == "AnalyticsSocialReport":
    sc = AnalyticsSocialReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Social Report for")
    #sc = AnalyticsSocialReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Social Report for")
    html = sc.generate_html()
    sc.send_email(html)
elif report_type == "AnalyticsSocialExport":
    sc = AnalyticsSocialExport(sites, monthly_period, config.all_recipients, "MONTHLY", "Social Export for")
    html = sc.generate_html()   
    sc.send_email(html) 
elif report_type == "AnalyticsYearSocialReport":
    report = AnalyticsYearSocialReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Top Social Networks for")
    html = report.generate_html()
    report.send_email(html)
    
    

else:
    raise Exception("Unknown report type")

with open(file_src, 'w') as file:
	file.write(html.encode("utf-8"))	
	#file.write(html)

