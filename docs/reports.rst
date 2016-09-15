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

Analytics Core Report
+++++++++++++++++++++

A main core report that gives an overview of a site.

Analytics Social Report
+++++++++++++++++++++++

A report that focuses on the current social referral traffic

Analytics Year Social Report
++++++++++++++++++++++++++++

A report that focuses on social referrals over the last 3 years

Analytics Social Export
++++++++++++++++++++++

Sends out an email with a csv attachment containing data about the social referrals over the last year 



Templates
--------
`Jinja 2 <http://jinja.pocoo.org/docs/dev/#>`_


Add a new report
---------------

- new class



Run a report
------------

Preview 
++++++

You can preview an individual report using the ``preview_report.py`` file.

To preview a report you can run the file from the command line with these paramaters: 

============	=========	===========	==========================================================
argument	Optional  	Default		Definition
============	=========	===========	==========================================================
reporttype	Required 	No default	The name of the report class, e.g. AnalyticsCoreReport
--sitename	Optional 	All sites	Name of the site, as it is in the config
--destination	Optional	"."		Path to where to save the report out
--filename	Optional	report_preview	Name of the file to save 

Example configuration might be::

	python preview_report.py AnalyticsCoreReport -s site.net -d file/to/path -n my_report_test

The frequency and periods are manually set up within the file. To alter these you'll have to alter the file.There are preset monthly, weekly and daily StatsRange objects setup but you may need to just change the date or frequency of the report.

		
Schedule
+++++++

Set up a report in ``report_schedule.py`` and run the scheduler.
For more info see Report Schedule Settings and Using the Scheduler.
 




