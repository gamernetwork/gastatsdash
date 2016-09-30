Settings
========

.. _report-schedule:

Report Schedule
---------------

``Statsdash/report_schedule.py``

This is where you list all the reports you want the scheduler to run.

In the ``report_scheduler.py-example`` you should be able to see an example configuration.

All the reports must be contained in a list named **reports**.

Each report config is a dictionary with the necessary key, value pairs to create that report, each one must have:

+--------------------+-------------------------------------------------------------------------+
|	Key	     |			Value 						       |
+====================+=========================================================================+
|	Report 	     | | Name of the report class you wish to use. 			       |
|		     | | (This needs to be imported into the file)		               |
+--------------------+-------------------------------------------------------------------------+
|	Recipients   | | List of emails who will recieve this report.			       |
+--------------------+-------------------------------------------------------------------------+
|	Subject	     | | The subject line of the report					       |
|		     | | The date period for the report is appended to the subject,            |
|                    | | so it might be best to end the subject line with "for ".              |
|                    | | e.g. "Site.net daily report for"                                      |
+--------------------+-------------------------------------------------------------------------+
|	Sites	     | | List of site names 						       |
|		     | | Must equal the name in the individual analytics config                |
+--------------------+-------------------------------------------------------------------------+
|	Frequency    | | Options are "WOW_DAILY", "WEEKLY", "MONTHLY"			       |
+--------------------+----------------------+-------------------------+------------------------+
|  Frequency Options | | Only set when a report's frequency is Weekly or Monthly               |
|                    | | Value should be a dictionary containing either:                       |
|		     +----------------------------------+--------------------------------------+
|		     |	 Weekly 		        |   Monthly		               |
|		     +----------------------------------+--------------------------------------+
|                    | | Key = "weekday"              	| | Key = "day'	                       |
|		     | | Value = Name of the weekday    | | Value = Number of day in month     |
|                    | |   e.g. "Monday"                | |   e.g. 1                           |
+--------------------+----------------------------------+--------------------------------------+
|     Identifier     | | Indiviudal report identifier					       |
|		     | | Used in the schedule database to store run dates.	               |
+--------------------+-------------------------------------------------------------------------+


Main Config
----------

``Statsdash/config.py``

In the main config should only be the settings you need for the report or schedule class. 

- Logging info and configuration

  - A basic python logger config
  - Get more info `here <https://docs.python.org/2/library/logging.html>`_
  - Uses a dictionary based config, `example <https://docs.python.org/2/howto/logging-cookbook.html#an-example-dictionary-based-configuration>`_

- Mail settings and personal emails

  - *SMTP_ADDRESS*: The server from which to send emails
  - *SEND_FROM*: The email from which to send the reports
  - *ERROR_REPORTER*: The email to send the error logs to
   
- Schedule database location

You can see an example at ``Statsdash/config.py-example``

.. _config_settings:

Google Analytics Config 
----------------------

``Statsdash/GA/config.py``

You should put all the relevant Google Analytics settings in here.

- Client email 
- Path to key file
- Dictionary of site names and IDs

  - must be called "TABLES"
  - use site names as keys
  - values should be a list of ID dictionaries 

    - allows you to roll up multipls IDs, helpful for sites with AMP. 
    - format: {"id":"ga:12345"}
    - each ID dict can optionally set "wait_for_data" to be False (default = True)
    - e.g. {"id":"ga:12345", "wait_for_data":False}

- Black list of page paths to remove from article tables
- Black list of sources to remove from traffic source tables
- Name for all your sites, labelled as "ALL_SITES_NAME"

See an example at ``Statsdash/GA/config.py-example``


Youtube Analytics Config
-----------------------

``Statsdash/Youtube/config.py``

You should put all the relevant Youtube Analytics settings in here.

- Path to client secrets file
- Content owner id
- Dictionary of channel names and IDs

  - must be called "CHANNELS"
  - use channel names as keys
  - channels IDs as values 

See an example at ``Statsdash/Youtube/config.py-example``




