Reports
=======

Overview
--------
The main function of the program is to aggregate and display the data in helpful html reports.
For each new report type there is a specific report class that inherits from the base Report class. 

Reports
-------

*class* Report(sites, period, recipients, frequency, subject)
    | **sites** - A list of site names to run the report on
    | **period** - A StatsRange object that defines the period that report should run over
    | **recipients** - A list of emails the report will send to
    | **frequency** - Can be "MONTHLY", "WEEKLY" or "WOW_DAILY". Specifies how often it runs and previous period comparison, e.g. month on month comparison for monthly reports.
    | **subject** - Subject line of the email and heading of the report

    get_subject()
        | Adds date period onto the end of the argument subject. 
        | E.g. for daily it will append Mon 12 Sep 2016.

    get_freq_label()
        | Returns the string to be used for previous period comparisons. 
        | E.g. for monthly returns MoM 

    check_data_availability()
        | Calls through to analytics to check data availability for that period for the requested sites. 
        | Returns True if data is available, false if not.
        | If override is set to True, then it returns the name of the sites that must be overridden.

    send_email()
        | Function to send a html email, inlines all the styles.

    generate_html()
        | Function that gathers the data and renders the template

*class* YoutubeReport(Report)
    Init function sets up the template file and link to youtube analytics data class.    

    generate_html()
        | Gather data tables from youtube analytics data class:
        |    - Summary table
	|    - Statistics table
        |    - Country table
	|    - Top Video table
	|    - Traffic Source table
        | Render data tables to the specified html template

*class* AnalyticsCoreReport(Report)
    Init function sets up the template file and link to google analytics data class.

    get_site()
        | Returns either the name of the site to be used in the template
	| If the report iterates over all sites, then use a all inclusive name set in config, e.g. Network

    generate_html()
        | Gather data tables from google analytics data class:
	|    - Summary table
	|    - Site summary table
	|    - Country table
	|    - Top Article table
	|    - Traffic Source table
	|    - Referral table
	|    - Device table
	|    - Social Network table
	|    -  If it's not monthly:
	|        - "Month to date" summary table
	|    - If it is monthly:
	|        - Device graph over the last year
	|    - If it's not all sites:
	|        - All sites summary table
	|        - If not monthly:
	|            - "Month to date" network summary table
	| Render data to html template


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
============	=========	============	==========================================================

Example configuration might be::

	python preview_report.py AnalyticsCoreReport -s site.net -d file/to/path -n my_report_test

The frequency and periods are manually set up within the file. To alter these you'll have to alter the file.There are preset monthly, weekly and daily StatsRange objects setup but you may need to just change the date or frequency of the report.

		
Schedule
+++++++

Set up a report in ``report_schedule.py`` and run the scheduler.
For more info see Report Schedule Settings and Using the Scheduler.
 




