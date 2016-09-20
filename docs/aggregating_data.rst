
Aggregating Data
=================

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
    | Initialises class from which to call analytics and get the data tables
    | Init function creates a list of periods to gather data for based on the period and the frequency.
    | Using StatsRange objects it will get the previous period and yearly period to calculate percentage change with

Data Table Functions
    | These functions query analytics with specific metrics, dimensions and filters needed to get the data
    | They call the data for each date period (current, previous and yearly) and for each site specified when the class was initialised
    | Then using utility functions they aggregate, format and add percentage changes to the data structure
    | Return the data as a list of dictionaries, each dictionary will be an inidividual dimension type, e.g. for the dimension social networks, you might have a dictionary for Facebook, Twitter, reddit etc

Helper Functions
    | These are specific functionss to be used by the service to help format the data into a more readable and sharable way for the reports and templates to use

Google Analytics Data Aggregator
---------------------------------

Data Tables
++++++++++++

summary_table()
    | Metrics: pageviews, users, sessions, pageviews per session, average session duration
    | Dimensions: None. 
    | This will return a single dictionary with the metrics accumulated for all the sites

site_summary_table()
    | Metrics: pageviews, users, sessions, pageviews per session, average session duration
    | Dimensions: None.
    | Adds "site" key which is a string of the site name to each dictionary
    | Returns list of dictionaries where each dictionary is data for a separate site

article_table()
    | Metrics: pageviews
    | Dimensions: page path, page title, host name
    | Does not return data or percentage change for yearly as articles change so quickly
    | Returns a list of dictionaries, each dictionary being a single article. The length will be 20 and sorted by descending pageviews 

country_table()
    | Metrics: pageviews, users
    | Dimensions: country 
    | List of countries specify what countries will be individuall listed in the table, the rest will be included in a "Rest of World" all inclusive dictionary
    | Return a list of dictionaries sorted by descending pageviews, length will be the length of list of countries plus 1

traffic_source_table()
    | see :ref:`get_source_list()  <get-source-list>`
    | return with length limited to 10

referring_sites_table(*num_articles*)
    | see :ref:`get_source_list() <get-source-list>`
    | gets specified number of articles for each source in the source list
    | using :ref:`referral_articles() <referral-articles>` function 

social_network_table(*num_articles*)
    | Metrics: pageviews, users, sessions
    | Dimensions: social network
    | Filter: Don't include data where social network is not set
    | Sort by descending users
    | Using :ref:`referral_articles() <referral-articles>` get *num_articles* for each network

.. _referral-articles:

referral_articles(*filter*, *limit*)
    | Metrics: pageviews
    | Dimensions: page path, page title, host name
    | Filter: set from *filter* could be empty or specify a social network or source for example
    | Does not return data or percentage change for yearly as articles change so quickly
    | Return a list of dictionaries, sorted by descending pageviews, length = *limit*

device_table()
    | Metrics: users
    | Dimensions: device category (desktop, mobile or tablet)
    | Sorted by descending users

device_chart(*data*)
    | return chart data for number of users on devices

social_chart()
    | return chart data for pageviews, users and sessions of socail networks


Helper Functions
++++++++++++++++

check_available_data()
    | for each site check if data is available
    | return dictionary with boolean of true/false and list of sites with no data available

_remove_ga_names(*rows*)
    | remove the "ga:" in front of the google analytics metrics and dimension keys

_remove_query_string(*path*)
    | remove the query string from the end of article page paths so similar articles can be aggregated properly
    | return the new article path

_get_title(*path*, *title*)
    | check if path includes the "amp" string
    | if it does, add "AMP" to the end of the article title to show it is an amp version

.. _get-source-list:

_get_source_list()
    | Metrics: pageviews, users
    | Dimensions: source / medium
    | Sort by descending users


Youtube Analytics Data Aggregator
----------------------------------

Data Tables
+++++++++++

country_table()
    | Metrics: views, estimated minutes watched, subscribers gained, subscribers lost
    | Dimensions: country
    | Add "subscriberChange" key, by subs gained - subs lost
    | Returns top 20 countries sorted by descending estimated minutes watched

channel_summary_table()
    | Metrics: subscribers gained, subscribers lost, estimated minutes watched
    | Dimensions: None
    | Adds "channel" key which is a string of the channel name to each dictionary
    | Adds "subscriberCount" using the current total number of subscribers
    | Adds "subscriberChange" key by subs gained - subs lost
    | Each dictionary is the data for a separate channel

channel_stats_table()
    | Metrics: views, likes, dislikes, comments, shares, subscribers gained
    | Dimensions: None
    | Adds "channel" key which is a string of the channel name to each dictionary
    | Adds a rate per 1000 views key value pair for likes, shares, comments and subscribers
    | Adds a like to dislike ratio key value pair

video_table()
    | Metrics: views, estimated minutes watched
    | Dimensions: video
    | Adds "channel" key which is a string of the channel name to each dictionary
    | Adds "title" key for the title of the video
    | Returns top 10 videos sorted by descending estimated minutes watched

traffic_source_table()
    | Metrics: estimated minutes watched
    | Dimensions: traffic source type
    | Returns a list of lists of dictionaries 
    | Each list describes one channel, and contains a dictionary for each traffic source
    | For traffic sources, the total of all channels for each one is calculated and it is ordered by descending estimated minutes watched, this order defines how the sources are ordered within each list
    | The total estimated minutes watched for each channel is calculated and this defines the order of the lists, descending estimated minutes watched
    | For each channel list, the percentage for each traffic source for that channel is calculated, added under the key "source_percentage" 

Helper Functions
++++++++++++++++

check_available_data()
    | queries analytics to see if data is available for each site
    | returns a dictionary with a value of True/False and a list of sites where data is not available

Utilities
---------

Main Functions
+++++++++++++++

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
++++++++++

Used mainly in reports to create a date range for the report to run
To create a StatsRange object, input a name as a string and two python datetime objects (start and end of the period).
Example::

    from datetime import date
    monthly_period = utils.StatsRange("July", date(2016, 07, 01), date(2016, 07, 31))

*class* StatsRange(name, start_date, end_date)
    Object that defines a date period from start_date to end_date, used to show the report period.

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
     


