Reports
=======

Overview
--------
The main function of the program is to aggregate and display the data in helpful html reports.
For each new report type there is a specific report class that inherits from the base Report class. 

Report Class
------------

The report class defines what each report contains. 
The parent class defines some base functions that all reports use:

get_subject() 
	creates the subject of the email, which is also the title of the report using the frequency and period variables.

get_freq_label()
	Creates a string to be used in templates for appearances. I.e. is the comparison WoW or MoM

check_data_availability()
	calls through to analytics. Returns true if data is available, false if not. If override is set to true, then it returns the name of the sites that have no data and must be overridden. 

send_email()
	simple function to send the html email.

Each child report class must define a **generate_html()** function. Within this they call to the aggregate_data class and retrieve the data tables needed. Should then pass the table data to the template.

Report Types
-----------

Each report type needs the following arguments to be intialised

=================	===============================================================
Channels/Sites		A list of channel or site names equal to name in the config
Period			StatsRange object defining the date range of the report
Recipients		List of emails for the report to go to
Frequency 		Value of either "WOW_DAILY", "WEEKLY" or "MONTHLY"
Subject			Email subject line and heading of report
=================	===============================================================


Youtube Report
++++++++++++++

This report uses the Youtube data service.

.. image:: video_report.png

Templates
--------
`Jinja 2 <http://jinja.pocoo.org/docs/dev/#>`_


Add a new report
---------------

- new class



Run a report
------------

- preview report
- scheduler


 




