Settings
=======

Report Schedule
--------------

``Statsdash/report_schedule.py``

This is where you list all the reports you want the scheduler to run.

In the ``report_scheduler.py-example`` you should be able to see an example configuration.

All the reports must be contained in a list named **reports**.

Each report config is a dictionary with the necessary key, value pairs to create that report, each one must have:

+--------------------+-------------------------------------------------------------------------+
|	Key	     |			Value 						       |
+====================+=========================================================================+
|	Report 	     |	Name of the report class you wish to use. 			       |
|		     |		(This needs to be imported into the file)		       |
+--------------------+-------------------------------------------------------------------------+
|	Recipients   |	 List of emails who will recieve this report.			       |
+--------------------+-------------------------------------------------------------------------+
|	Subject	     |	 The subject line of the report					       |
|		     |      | The date period for the report is appended to the subject,       |
|                    |      | so it might be best to end the subject line with " for ".        |
|                    |      | e.g. "Site.net daily report for"                                 |
+--------------------+-------------------------------------------------------------------------+
|	Sites	     |	 List of site names 						       |
|		     |      Must be the same string as in the individual analytics config      |
+--------------------+-------------------------------------------------------------------------+
|	Frequency    |	 Options are "WOW_DAILY" "WEEKLY" or "MONTHLY"			       |
+--------------------+----------------------+-------------------------+------------------------+
|  Frequency Options |   Set when to run a report for Weekly or Monthly frequecy values        |
|                    |    value should be a dictionary containing either:                      |
|		     +----------------------------------+--------------------------------------+
|		     |	 Weekly 		        |   Monthly		               |
|		     +----------------------------------+--------------------------------------+
|                    |  | Key = "weekday"              	|  | Key = "day'	               |
|		     |  | Value = name of the weekday   |  | Value = Number of day in month    |
|                    |  |   e.g. "Monday"               |  |   e.g. 1                          |
+--------------------+----------------------------------+--------------------------------------+
|     Identifier     |	 indiviudal report identifier					       |
|		     |		 used in the schedule database to store run dates.	       |
+--------------------+-------------------------------------------------------------------------+




Main Config
----------

``Statsdash/config.py``

In the main config should only be the settings you need for the report or schedule class. 

You can see an example at ``Statsdash/config.py-example``

For example, define in here:
  - Logging info and configuration
  - Mail settings and personal emails
  - Schedule database location


Google Analytics Config 
----------------------

``Statsdash/GA/config.py``

You should put all the relevant Google Analytics settings in here.

 - client email 
 - path to key file
 - dictionary of site names and IDs
 - black list of page paths to remove from article tables
 - black list of sources to remove from traffic source tables

See an example at ``Statsdash/GA/config.py-example``

You should have a dictionary called **TABLES** that contains your *site names* as *keys*.  

The *value* of each site name key should be a list of dictionaries, each dictionary containing a key value pair with key "id" and value profile id. This is to allow multiple ids to be rolled up into the same site. e.g. when theres main site traffic and AMP traffic. Also an additional optional "wait_for_data" key that can be added to each id dictionary, value is default True but can be defined to False if there's no need to wait for date to become available for that id. 

Additionally in the GA config values specific to GA are defined. For example, the path to your private analytics keyfile.
There is also a code snippet to remove pathnames from article tables, e.g. to remove static pages such as "/index" and "/forum".
Also a list of sources to remove from the source referral table. 

Youtube Analytics Config
-----------------------

``Statsdash/Youtube/config.py``

You should put all the relevant Youtube Analytics settings in here.

 - path to client secrets file
 - content owner id
 - dictionary of channel names and IDs

See an example at ``Statsdash/Youtube/config.py-example``





