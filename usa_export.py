import reporting
import argparse
import csv

from datetime import date, timedelta
from dateutils import subtract_one_month, add_one_month
import config
from analytics import get_analytics, StatsRange

#parser = argparse.ArgumentParser()
#parser.add_argument("-d", "--destination", help="destination for return file", default =".")
#args = parser.parse_args()
#report_type = args.reporttype


#sort out months
#Jan-13 to Nov-15
start_month = date(2015, 05, 01)
end_month = date(2016, 06, 01)
current = start_month
month_stats_range = []
months = []
while current != end_month:
    start_date = current
    end_date = add_one_month((current - timedelta(days=1)))
    print 'end date: ', end_date
    name =  start_date.strftime("%b-%Y")
    month_stats_range.append(StatsRange(name, start_date, end_date))
    months.append(name)
    current = add_one_month(start_date)
    
    
#get data for each site for each month
print len(months), months
analytics = get_analytics()
sites = ['eurogamer.net', 'vg247.com', 'rockpapershotgun.com','usgamer.net', 'moddb.com', 'indiedb.com']
config_sites = config.TABLES

stats = []
for m_count, month in enumerate(month_stats_range):
    data = {}
    for count, site in enumerate(sites):
        site_ga_id = config_sites[site]
        results = analytics._execute_stats_query(site_ga_id, month, "ga:users,ga:pageviews", sort=None, dimensions=None, filters="ga:country==United States,ga:country==Canada", max_results=None, sampling_level=None, include_empty_rows=None)
        num_users = results['rows'][0][0]
        num_pvs = results['rows'][0][1]
        data[site] = {'users':num_users, 'pageviews':num_pvs}
    data['month'] = months[m_count]
    print months[m_count], month.end_date
    
    stats.append(data)
    
    
print stats




with open('/var/www/dev/faye/statsdash_reports/results_pageviews.csv', 'wb') as file:
    writer = csv.writer(file)
    writer.writerow(['Month', 'Eurogamer.net', 'VG247', 'USGamer', 'RPS', 'ModDB', 'IndieDB'])
    for month in stats:
        writer.writerow([month['month'], month['eurogamer.net']['pageviews'], month['vg247.com']['pageviews'], month['usgamer.net']['pageviews'], month['rockpapershotgun.com']['pageviews'], month['moddb.com']['pageviews'], month['indiedb.com']['pageviews']])
        
with open('/var/www/dev/faye/statsdash_reports/results_users.csv', 'wb') as file:
    writer = csv.writer(file)
    writer.writerow(['Month', 'Eurogamer.net', 'VG247', 'USGamer', 'RPS', 'ModDB', 'IndieDB'])
    for month in stats:
        writer.writerow([month['month'], month['eurogamer.net']['users'], month['vg247.com']['users'], month['usgamer.net']['users'], month['rockpapershotgun.com']['users'], month['moddb.com']['users'], month['indiedb.com']['users']])
        
        
