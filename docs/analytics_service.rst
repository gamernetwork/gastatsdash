
Analytics Services
==================

Overview
--------

This tool is made to be used so that reports can be made using multiple different services. This is to help enable comparison across different platforms. So far Google Analytics and Youtube Analytics have been integrated, but other services such as Facebook or Twitter could be added.

Each service has a separate folder with similar files inside. Main files:

**Analytics.py**
  
  - connection to the service's API
  - querying functions to get the data

**Aggregate_data.py**

  - creates a class that the reports can call
  - set the date period, frequency, sites
  - returns the data in a fixed format using functions defined in the shared ``utilities.py``

**Config.py**

  - mainly sets the variables for service connection
  - holds a dictionary of site names and IDs
  - see :ref:`config <config_settings>`


Google Analytics
---------------

We have set up access to the Google Analytics Core Reporting API using a service account. You will need to do this as well, following :ref:`these steps <service_account>` or for more info go `here <https://developers.google.com/analytics/devguides/reporting/core/v3/quickstart/service-py>`_.

The analytics class has a function to run a query, implement exponential backoff when there is an error and to rollup the data from same-site IDs.

It also has a function that checks the data's availability which queries to get pageviews for every hour for the period's end date. If the results returned does not include all 24 hours, then the data is not ready yet.

Youtube Analytics
-----------------

We have set up access to the Youtube Analytics and Reporting API using OAuth 2.0. You will need to do this as well, following :ref:`these steps <oauth_account>` or for more info go to the `youtube implementation <https://developers.google.com/youtube/reporting/guides/authorization>`_ or the `google python API client implementation <https://developers.google.com/api-client-library/python/guide/aaa_oauth>`_.


You must have a content owner ID as this is how the analytics queries are set up. 

Using this tool works best for content owners with multiple channels.

The analytics class has one main function to run a query, rollup the date from same-channel IDs and get specific values like your content owner ID, video names or realtime channel statistics.

It also has a function that checks the data availability which queries to get views on the period end date. If no results are returned then the data is not ready yet.


Adding a new service
--------------------

To add a new service, you would need to set up the main files following the instructions from the API to create the connection and make the queries.
In the aggregate_data file you would need to create the right functions using helper functions in the utilities to file to make sure the data is returned in similar format that the report and templates could use.
You will also have to create new templates and a new report to utilise your new service.





