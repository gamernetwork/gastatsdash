
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

*class* AnalyticsData(sites, period, frequency)
    | Creates a list of periods to gather data for based on the period and the frequency.
    | Using StatsRange objects it will get the previous period and yearly period to calculate percentage change against


Google Analytics Data Aggregator
-------------------------------

Data Tables
++++++++++

summary_table()
    | Find the pageviews, users, sessions, pageviews per session and average session duration
    | for each date period and each site specified
    | use utility functions to aggregate, add percentages and format
    | return the total sum metrics of all the specified sites as a dictionary

site_summary_table()
    | Find the pageviews, users, sessions, pageviews per session and average session duration
    | for each date period and each site specified
    | use utility functions to aggregate, add percentages and format
    | return the total sum metrics for each site as a list of dictionaries 

article_table()
    | Find the pageviews for the current and previous date period and for each site specified 
    | use utility functions to aggregate, add percentages and format
    | return the total sum metrics for top 20 articles for all sites sorted by descending pageviews

country_table()
    | Find the pageviews and users for each date period and each site specified
    | use the utility functions to aggregate, add percentages and format the data
    | return total sum of metrics for each country for all sites as a list of dictionaries
    | List of countries specify which countries to list, and those not in the list are included instead together in a "Rest of World" key

traffic_source_table()
    | see :ref:`my-source-list`
    | returns this, limited to 10 sources

referring_sites_table(num_articles)
    | see :ref:`my-source-list`
    | gets specified number of articles for each source in the source list
    | using referall_articles() function 

social_network_table(num_articles)
    | For each date period and for each site in specified site list calculate...
    | the pageviews, users and sessions for social networks
    | aggregate all this data so totals for each social network over all sites specified
    | add percentage change
    | using referall_articles() get top articles for each social network
    | return as list of dictionaries, one dictionary for each social network

referral_articles(filter, limit)
    | for current period and previous period and for each site specified calculate..
    | the pageviews for articles filtered by specified filter
    | aggregate data and add percentage change
    | return list of dictionaries 

device_table()
    | for each date period and for each site in specified calculate...
    | the users for each device category
    | aggregate data for each device category over all sites specified
    | add percentage change
    | return list of dictionaries 

device_chart(data)
    | return chart data for number of users on devices

social_chart()
    | return chart data for pageviews, users and sessions of socail networks


Helper Functions
++++++++++++++++

check_available_data()
    | for each site check if data is available
    | return dictionary with boolean of true/false and list of sites with no data available

_remove_ga_names(rows)
    | remove the "ga:" in front of the google analytics metrics and dimension keys

_remove_query_string(path)
    | remove the query string from the end of article page paths so similar articles can be aggregated properly
    | return the new article path

_get_title(path, title)
    | check if path includes the "amp" string
    | if it does, add "AMP" to the end of the article title to show it is an amp version

.. _my-source-list:

_get_source_list()
    | for each data period and for each site calculate...
    | the pageviews and users for traffic source and medium
    | aggregate the data for sources across all sites
    | add percentage change
    | return list of dictionaries, each dictionary being a source


Youtube Analytics Data Aggregator
--------------------------------

- country table
- channel summary table
- channel stats table
- video table
- traffic source table

helpers:

- check data availability

see :ref:`my-source-list`

Utilities
--------

Main Functions
++++++++++++++

Used mainly by aggregate_data.py in service folders to aggregate and format the data. 

Main format is set as a list of dictionaries, where each dictionary holds the data for one dimension.

For instance, the data for a social network table would be a list of dictionaries, where each dictionary is the data for one social network. You can then sort and the set the length of the list as needed. 

format_data_rows(*results*)
    | Google analytics returns data in a `set format <https://developers.google.com/analytics/devguides/reporting/core/v3/reference#data_response>`_
    | The function converts each row to a dictionary with the correct key value pairs, {metric:value, metric:value}
    | It returns a list of these dictionaries

aggregate_data(*table*, *aggregate_keys*, *match_key=None*)
    | If *match_key* exists (a dimension field that the data needs to be separated by)
    | uses *list_search* to create a new list of dictionaries with total accumulated metrics for each individual dimension 
    | Else returns a dictionary of total accumulated metrics

add_change(*this_period*, *previous_period*, *change_keys*, *label*, *match_key=None*)
    | Adds specified percentage change to *this_period* data
    | For each metric in *change_keys*, will add the previous figure, the difference and the percentage difference
    | If a dimension is specified in *match_key* then must use *list_search* as list of dictionaries structure inputted and returned, otherwise simple dictionary

list_search(*to_search*, *key*, *value*)
    | Searches through the list of dictionaries *to_search* and returns the dictionary that matches the key, value pair given

sort_data(*unsorted_list*, *metric*, *limit=1000*, *reverse=True*)
    | Sorts a list of dictionaries by the metric given

convert_to_floats(*row*, *metrics*)
    | For list of dictionaries, *row*
    | converts all the metrics specified into floats
    | returns *rows*

change_key_names(*rows*, *changes*)
    | For list of dictionaries, *rows*
    | changes key names specified in *changes*
    | where changes = {new_key: original_key, new_key: original_key}
    | returns *rows* with new key names

percentage(*change*, *total*)
    | returns the percentage of change over total

sig_fig(*sf*, *num*)
    | returns *num* with specified number of significant figures

rate_per_1000(*metric*, *comparative*)
    | returns the rate of the metric per 1000 comparative

convert_values_list(*id_dict*)
    | converts values of the dictionary given into lists 
    | Used to generalise the site ID values, so if only one ID makes into a list with one element, otherwise leaves as a list of multiple elements

chart(*title*, *x_labels*, *data*, *x_title*, *y_title*)
    | Uses pygal library to create a line chart 
    | `Documentation <http://pygal.org/en/stable/index.html>`_

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
     


