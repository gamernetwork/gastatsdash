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

Here are the reports that are provided:

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
    Report uses graphs so in __init__ set self.imgdata = None

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

    send_email()
        | Overwrite basic send email function to include images


*class* AnalyticsSocialReport(Report)
    Initialise data class, template, image data 

    get_site()
        | Returns either the name of the site to be used in the template
        | If the report iterates over all sites, then use a all inclusive name set in config, e.g. Network

    generate_html()
        | Gathers data tables from google analytics data class:
        |    - Summary table
        |    - All sites summary table
        |    - Social network table
        |    - Social network graph
        | Render data to html template

     send_email()
        | Overwrite basic send email function to include images        


*class* AnalyticsYearSocialReport(Report)
    Initialise data class, template etc

    get_subject()
        | Overwrite basic subject function
        | Returns subject appended with date period from 3years ago to now

    get_site()
        | Returns either the name of the site to be used in the template
        | If the report iterates over all sites, then use a all inclusive name set in config, e.g. Network

    _get_social_data()
        | Gets social network data table for every month over the last 3 years

    _get_top_networks()
        | Get social network data table over the last year and find top social networks
        | Other than Facebook, Twitter and reddit

    generate_html()
        | Using the top social networks, find the data for each of these networks for each month over the last 3 years
        | using the data found in _get_social_data()
        | Render data to html template    


*class* AnalyticsSocialExport(Report)
    Initialise template, data class etc
 
    generate_html()
        | Get social network table for each month over the last year
        | Render data to a csv file

    send_email()
        | overwrites basic email function
        | sends email with a csv attachment


Templates
--------
`Jinja 2 <http://jinja.pocoo.org/docs/dev/#>`_

Templates use the `Jinja 2 <http://jinja.pocoo.org/docs/dev/#>`_ templating language. 

The layout is set up so that each table function in the aggregating data classes corresponds to a template file, within the relevant folder. 

For instance, within the templates folder there is GA folder, each google analytics data table has a separate template file. 

The file ``Templates/GA/base.html`` extends the main base, and it includes each table only if that table value exists. 

All template files should inherit from ``Templates/base.html``. In this file the styles are set, as is the subject and some confidentiality lines.

Add a new report
---------------

To set up a new report, you'll need to create a new class that inherits from "Report".

Basic example that returns just a google analytics summary table::

    class MyReport(Report):

        def __init__(self, sites, period, recipients, frequency, subject):
            super(MyReport, self).__init__(sites, period, recipients, frequency, subject)
            self.sites = sites
            self.period = period
            self.recipients = recipients
            self.frequency = frequency
            self.subject = subject
            self.warning_sites = []
            self.template = self.env.get_template("template.html")
            self.date = AnalyticsData(self.sites, self.period, self.frequency)

        def generate_html(self):
            summary = self.data.summary_talbe()
            html = self.template.render(
                subject = self.get_subject(),
                change = self.get_freq_label(),
                report_span = self.frequency,
                warning_sites = self.warning_sites,
                summary_table = summary
            )
            return html

Run a report
------------

Preview 
++++++

You can preview an individual report using the ``preview_report.py`` file.

To preview a report you can run the file from the command line with these paramaters: 

==============	=========   ================	==========================================================
argument	Optional    Default		Definition
==============	=========   ================	==========================================================
reporttype	Required    No default		The name of the report class, e.g. AnalyticsCoreReport
--sitename	Optional    All sites		Name of the site, as it is in the config
--destination	Optional    "."			Path to where to save the report out
--filename	Optional    report_preview	Name of the file to save 
==============	=========   ================	==========================================================

Example configuration might be::

	python preview_report.py AnalyticsCoreReport -s site.net -d file/to/path -n my_report_test

The frequency and periods are manually set up within the file. To alter these you'll have to alter the file.There are preset monthly, weekly and daily StatsRange objects setup but you may need to just change the date or frequency of the report.

		
Schedule
+++++++

Set up a report in ``report_schedule.py`` and run the scheduler.
For more info see Report Schedule Settings and Using the Scheduler.
 




