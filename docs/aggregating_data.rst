
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


