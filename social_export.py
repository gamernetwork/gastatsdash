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
start_month = date(2013, 01, 01)
end_month = date(2015, 12, 01)
current = start_month
month_stats_range = []
months = []
while current != end_month:
    start_date = current
    end_date = add_one_month(current)
    print 'end date: ', end_date
    month_stats_range.append(StatsRange("%s_%s" % (start_date.month, start_date.year), start_date, end_date))
    name =  "%s_%s" % (start_date.month, start_date.year)
    months.append(name)
    current = end_date
    
    
#get data for each site for each month

analytics = get_analytics()


sites = config.TABLES
num_months = len(month_stats_range)
num_sites = len(sites.keys())

stats = []
for m_count, month in enumerate(month_stats_range):
    data = []
    for count, site in enumerate(sites):
        site_ga_id = sites[site]
        results = analytics.get_social_export_for_period(site_ga_id, month)
        print "month: ", month.get_start(), "site: ", site, "results: ", results
        data.append({'site':site, 'data':results}) 
        print "%d/%d sites complete" % (count+1, num_sites)
        
    stats.append({month.get_start():data})
    print "%d/%d months complete" % (m_count+1, num_months)   
    


#aggregate

social_export = []

for data in stats:
    month = data.keys()[0]
    site_list = data.values()[0]
    monthly_data = {}
    monthly_data[month] = {}
    for site in site_list:
        print "SITE: ", site
        #test if have the data 
        try: 
            fb_pv = int(site['data'][0]['pageviews']) 
            fb_sns = int(site['data'][0]['sessions'])
            tw_pv = int(site['data'][1]['pageviews'])
            tw_sns = int(site['data'][1]['sessions']) 
        except IndexError:
            fb_pv = 0
            fb_sns = 0
            tw_pv = 0
            tw_sns = 0         
        #test if already have the key, if so aggregate
        try:
            monthly_data[month]['fb_sessions'] += fb_sns   
            monthly_data[month]['fb_pageviews'] += fb_pv 
            monthly_data[month]['tw_sessions'] += tw_sns   
            monthly_data[month]['tw_pageviews'] += tw_pv
        except KeyError:
            monthly_data[month]['fb_sessions'] = fb_sns   
            monthly_data[month]['fb_pageviews'] = fb_pv 
            monthly_data[month]['tw_sessions'] = tw_sns   
            monthly_data[month]['tw_pageviews'] = tw_pv  
            
    social_export.append(monthly_data)
    
print "social export: ", social_export
            



#return as csv file 


with open('/var/www/dev/faye/statsdash_reports/results.csv', 'wb') as file:
    writer = csv.writer(file)
    writer.writerow(['Month', 'Facebook-sessions', 'Facebook-pageviews', 'Twitter-sessions', 'Twitter-pageviews'])
    for item in social_export:
        month = item.keys()[0]
        results = item.values()[0]
        data = [results['fb_sessions'], results['fb_pageviews'], results['tw_sessions'], results['tw_pageviews']]
        writer.writerow([month, results['fb_sessions'], results['fb_pageviews'], results['tw_sessions'], results['tw_pageviews']])
    
     
    
   