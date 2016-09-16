
Aggregating Data
===============

Each data service should have an aggregate_data.py. This includes a class which defines functions that create and return data tables in a set format. 

The main aim is for the report to be able to create an instance of the data class and call the data tables it needs.
Example:: 

    def generate_html(self):
        get_data = AnalyticsData(all_sites, this_period, this_frequency)
        first_table = get_data.get_summary_table()
        second_table = get_data.get_article_table()
        third_table = get_data.get_traffic_source_table()
        
        #send tables to template

The functions within the aggregate_data files should query the analytics class to get the data, then use shared functions from the utilities file to aggregate and format the data in a set form.

*class* AnalyticsData(sites period, frequency)
    | Creates a list of periods to gather data for based on the period and the frequency.
    | Using StatsRange objects it will get the previous period and yearly period to calculate percentage change against


Google Analytics Data Aggregator
-------------------------------

summary_table()
    | For each date period, and for each site in the site list calculate...
    | pageviews, users, sessions, pageviews per sessions and average session duration
    | aggregate all this data, so it's a total for all the sites specified
    | add percentage change against each past period (previous and yearly)
    | return data as a list of dictionaries.

site_summary_table()
    | For each date period and for each site specified calculate...
    | pageviews, users, sessions, pageviews per session and average session duration
    | add percentage change against each past period
    | return data as a list of dictionaries, each dictionary being one sites data

article_table()
    | For current period and the previous period and for each site specified calculate...
    | pageviews in descending order, return the page path, title and site name.
    | aggregate data so it's most viewed articles for all sites
    | add percentage change 
    | return top 20 articles as a list of dictionaries

country_table()
    | 

- summary table
- site summary table
- article table
- country table
- traffic source table
- referring sites table
- social network table
- referral articles
- device table
- device chart
- social chart

ga helper functions

- remove ga names
- check data availability
- remove query string
- get title
- get source list


Youtube Analytics Data Aggregator
--------------------------------

- country table
- channel summary table
- channel stats table
- video table
- traffic source table

helpers:

- check data availability


Utilities
--------

Main Functions
++++++++++++++

Used mainly by aggregate_data.py in service folders to aggregate and format data. 


Date Utils
++++++++++

Used mainly in scheduler to calculate next runs.

get_month_day_range(*date*)
    return start and end date of the month in date

add_one_month(*t*)
   returns datetime object that has had one month added to t

subtract_one_month(*t*)
    returns datetime object that has had one much subtracted from t

find_last_weekday(*start_date*, *weekday*)
    returns the date of the previous closest day of the week that matches the string weekday

find_next_weekday(*start_date*, *weekday*)
    returns the date of the next closest day of the week that matches the string weekday

StatsRange
+++++++++

Used mainly in reports to create a date range for the report to run
To create a StatsRange object, input a name as a string and two python datetime objects (start and end of the period).
Example::

    from datetime import date
    monthly_period = utils.StatsRange("July", date(2016, 07, 01), date(2016, 07, 31))

*class* StatsRange(name, start_date, end_date)
    
    get_start()
        return start date in isoformat

    get_end()
        return end date in isoformat

    days_in_range()
        return number of days in period

    get_period(*date*, *frequency*)
        return a StatsRange object based on the date and frequency given

    get_previuos_period(*current_period*, *frequency*)
        return a StatsRange object based on the current period and frequency

    get_one_day_period(*date*)
        return a StatsRange object for the date given

    get_one_week_period(*date*)
        return a StatsRange object of a week ending on the date given

    get_one_month_period(*date*)
        return a StatsRange object of a month ending on the date given 
     


