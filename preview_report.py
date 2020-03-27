import argparse
from datetime import date, timedelta
import html

from Statsdash import config, utils
from Statsdash.report import AnalyticsCoreReport, AnalyticsSocialReport, \
    AnalyticsSocialExport, AnalyticsYearSocialReport, YouTubeReport
import Statsdash.report_schedule as report_conf
from Statsdash.stats_range import StatsRange


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
    sites = config.GOOGLE['TABLES'].keys()
elif args.sitename == "all_network_sites":
    sites = config.GOOGLE.ALL_NETWORK_SITES
else:
    sites = [args.sitename]

file_src = args.destination + "/" + file_name


date_2_days_ago = date.today() - timedelta(days=2)

monthly_period = StatsRange("period", date(2018, 5, 1), date(2018, 5, 31))
daily_period = StatsRange("period", date_2_days_ago, date_2_days_ago)
weekly_period = StatsRange("period", date(2018, 2, 12), date(2018, 2, 18))


test_period = StatsRange("future", date(2016, 8, 1), date(2016, 8, 30))

# if report_type == "YoutubeReport":
#     sites =yt_config.CHANNELS.keys()
#     #yt = YoutubeReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Video Report for")
#     yt = YoutubeReport(sites, monthly_period, report_conf.recipients, "WEEKLY", "Video Report for")
#     html = yt.generate_html()
#     #yt.send_email(html)
# elif report_type == "AnalyticsCoreReport":
#     #ac = AnalyticsCoreReport(['jelly.deals'], daily_period, config.all_recipients, "WOW_DAILY", "Report for")
#     ac = AnalyticsCoreReport(['usgamer.net'], daily_period, report_conf['recipients'], "WOW_DAILY", "Report for")
#     html = ac.generate_html()
#     #ac.send_email(html)
# elif report_type == "AnalyticsSocialReport":
#     sc = AnalyticsSocialReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Social Report for")
#     #sc = AnalyticsSocialReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Social Report for")
#     html = sc.generate_html()
#     sc.send_email(html)
# elif report_type == "AnalyticsSocialExport":
#     sc = AnalyticsSocialExport(sites, monthly_period, config.all_recipients, "MONTHLY", "Social Export for")
#     html = sc.generate_html()
#     sc.send_email(html)
# elif report_type == "AnalyticsYearSocialReport":
#     report = AnalyticsYearSocialReport(sites, monthly_period, config.all_recipients, "MONTHLY", "Top Social Networks for")
#     html = report.generate_html()
#     #report.send_email(html)
    
    

# else:
#     raise Exception("Unknown report type")

with open(file_src, 'w') as file:
    pass
    # file.write(html.encode("utf-8"))
    #file.write(html)

