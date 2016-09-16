
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


Utilities
--------

Main Functions
++++++++++++++

Used mainly by aggregate_data.py in service folders to aggregate and format data. 


Date Utils
++++++++++

Used mainly in scheduler to calculate next runs.

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

    get_period(date, frequency)
        return a StatsRange object based on the date and frequency given

    get_previuos_period(current_period, frequency)
        return a StatsRange object based on the current period and frequency

    get_one_day_period(date)
        return a StatsRange object for the date given

    get_one_week_period(date)
        return a StatsRange object of a week ending on the date given

    get_one_month_period(date)
        return a StatsRange object of a month ending on the date given 
     


