from Statsdash.report import YoutubeReport, AnalyticsCoreReport, AnalyticsSocialReport, AnalyticsSocialExport
import argparse
#import report_schedule

from datetime import date, timedelta
#from Statdateutils import subtract_one_month

import Statsdash.Youtube.config as yt_config
import Statsdash.GA.config as ga_config
import Statsdash.utilities as utils

from premailer import transform


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
	#file_name = user_file_name
	
file_src = args.destination + "/" + file_name


monthly_period = utils.StatsRange("period", date(2016, 05, 01), date(2016, 05, 30))
daily_period = utils.StatsRange("period", date(2016, 06, 05), date(2016, 06, 05))


if report_type == "YoutubeReport":
    yt = YoutubeReport(yt_config.CHANNELS.keys(), monthly_period, ["faye.butler@gamer-network.net"], "MONTHLY", "Gamer Network Video Report for")
    html = yt.generate_html()
    yt.send_email(html)
elif report_type == "AnalyticsCoreReport":
    ac = AnalyticsCoreReport(ga_config.TABLES.keys(), daily_period, ["faye.butler@gamer-network.net"], "WOW_DAILY", "Gamer Network Report for")
    #ac = AnalyticsCoreReport(["eurogamer.net"], monthly_period, ["faye.butler@gamer-network.net"], "MONTHLY", "Eurogamer.net Report for")
    html = ac.generate_html()
    ac.send_email(html)
elif report_type == "AnalyticsSocialReport":
    #sc = AnalyticsSocialReport(ga_config.TABLES.keys(), monthly_period, ["faye.butler@gamer-network.net"], "MONTHLY", "Gamer Network Social Report for")
    sc = AnalyticsSocialReport(["eurogamer.net"], monthly_period, ["faye.butler@gamer-network.net"], "MONTHLY", "Eurogamer.net Social Report for")
    html = sc.generate_html()
    sc.send_email(html)
elif report_type == "AnalyticsSocialExport":
    sc = AnalyticsSocialExport(["eurogamer.net"], monthly_period, ["faye.butler@gamer-network.net"], "MONTHLY", "Eurogamer.net Social Export for")
    html = sc.generate_html()   
    sc.send_email(html) 
else:
    raise Exception("Unknown report type")

with open(file_src, 'w') as file:
	file.write(html.encode("utf-8"))	
	#file.write(html)

