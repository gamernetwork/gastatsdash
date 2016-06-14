import reporting
import argparse
import csv

from datetime import date, timedelta
from dateutils import subtract_one_month, add_one_month
import config
from analytics import get_analytics, StatsRange

analytics = get_analytics()

#get totals =  page views, visitors etc 
#get top articles 
#aggregate all things
# print out
today = date.today() - timedelta(days=2)
start_date = date(2015, 01, 01)
end_date = today
year_range = StatsRange("Yearly", start_date, end_date)


sites = config.TABLES
num_sites = len(sites.keys())


top_articles =[]
totals = {}

for count, site in enumerate(sites):
    site_ga_id = sites[site]
    print "Calculating for %s..." % site
    results = analytics.get_article_breakdown(site_ga_id, year_range)
    total = analytics.get_site_totals_for_period(site_ga_id, year_range)[0]

    separated_data = []
    for item in results:
        separated_data.append(results[item])    
    
    totals[site] = total
    
    top_articles += separated_data[:11]
    print "%d/%d sites complete" % (count+1, num_sites)

total_stats = {}

for site in totals.keys():
    numbers = totals[site] 
    for key in numbers.keys():
        try:
            total_stats[key] += float(numbers[key])
        except KeyError:
            total_stats[key] = float(numbers[key])
            
            
total_stats['pv_per_session'] = total_stats['pv_per_session']/float(num_sites)
total_stats['avg_time'] = (total_stats['avg_time']/float(num_sites))/60.0


print "TOTALS : ", total_stats

tables = ['title', 'host', 'path']
metrics = ['pageviews']
#use and pass out dictionary instead less nesting forloops
organised_results = []
for item in top_articles:
    site = {}
    total_dimensions = {}
    for table_type in tables:
        total_dimensions[table_type] = item[table_type]  
    site['dimensions'] = total_dimensions
    total_metrics = {}
    for metric in metrics:
        total_metrics[metric] = item[metric]                                         
    site['metrics'] = total_metrics
    organised_results.append(site)


aggregated_results = [] 
length = len(aggregated_results)
for item in organised_results:
    #item = {'dimensions' :{'source/medium':'google'}, 'metrics':{'visitors':20, 'pageviews':15}}
    if length > 0:
        for count, record in enumerate(aggregated_results):
            if item['dimensions'] == record['dimensions']:
                for metric in metrics:            
                    record['metrics'][metric] += item['metrics'][metric]
                break
            else:
                #has it gone throgh all the records??
                if count == length-1:
                    new_record = {}
                    new_record['dimensions'] = item['dimensions']
                    new_record['metrics'] = item['metrics']
                    aggregated_results.append(new_record)
                    break
                else:
                    continue
    else:
        record = {}
        record['dimensions'] = item['dimensions']
        record['metrics'] = item['metrics']
        aggregated_results.append(record)
        
    length = len(aggregated_results) 
    
    
def sortDev(item):
    return item['metrics']['pageviews']                
            
sorted_list = sorted(aggregated_results, key = sortDev, reverse = True)
top_results = sorted_list[:25]      

hosts = {}
for item in top_results:
    host = item['dimensions']['host']
    host = host[4:]
    try:
        hosts[host] += [item['dimensions']['path']]
    except KeyError:
        hosts[host] = [item['dimensions']['path']]  

#not working! 
#list of months
previous_months = 12
end_date = today
month_stats_range = []
for i in range(0, previous_months):
    start_date = subtract_one_month(end_date)
    month_stats_range.append(StatsRange("month_%d" % i, start_date, end_date))
    end_date = start_date

end_results = {}

        
for host in hosts:
  print "HOST", host
  
  site_ga_id = sites[host]
  #for eahc month, for each article, get pageviws
  for month in month_stats_range:
      print month.get_start()
      end_results[host] = {}
      for article in hosts[host]:
          print article
          #article_split = article.split(',')
          #print article_split
          #title= '\,'.join(article_split) #now itds \\, how to make it just one \
          #print title
          try:
              pageviews = analytics.get_article_pageviews_for_period(site_ga_id, month, extra_filters = 'ga:pagePath==%s' % article)[0]['pageviews']
          except IndexError:
              pageviews = 0
          print pageviews
          try: 
              end_results[host][article] += [pageviews]
          except KeyError:
              end_results[host][article] = [pageviews]
    

  
  


"""  
with open('/var/www/dev/faye/statsdash_reports/yearly_results.csv', 'wb') as file:
    writer = csv.writer(file)
    writer.writerow(['Site', 'Page Title', 'Total Pageviews'])
    for item in top_results:
        title = item['dimensions']['title']
        title = ''.join(i for i in title if ord(i)<128)
        host_name = item['dimensions']['host'][4:]
        path = item['dimensions']['path']
        pv = end_results[host_name][path]
        print "PV", pv
        writer.writerow([item['dimensions']['host'], title, item['metrics']['pageviews'], ])
        writer.writerow(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'])
        writer.writerow([pv[11], pv[10], pv[9], pv[8], pv[7], pv[6], pv[5], pv[4], pv[3], pv[2], pv[1], pv[0]])
        
    writer.writerow([])
    writer.writerow(['Total Network Stats'])
    writer.writerow(['Page Views', 'Visitors', 'Sessions', 'Page Views per Session', 'Average Session Time'])
    writer.writerow([total_stats['pageviews'], total_stats['visitors'], total_stats['sessions'], total_stats['pv_per_session'], total_stats['avg_time']]) 
"""