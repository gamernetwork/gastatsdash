
Analytics Services
==================

Overview
--------

This tool is made to be used so that reports can be made using multiple different services. This is to help enable comparison across different platforms. So far Google Analytics and Youtube Analytics have been integrated, but other services such as Facebook or Twitter could be added.

Each service has a separate folder with similar files inside. Main files:

Analytics.py
  
  - connection to the service's API
  - querying functions to get the data

Aggregate_data.py

  - creates a class that the reports can call
  - set the date period, frequency, sites
  - returns the data in a fixed format using functions defined in the shared ``utilities.py``

Config.py

  - mainly sets the variables for service connection
  - holds a dictionary of site names and IDs
  - see :ref:`config <config_settings>`


Google Analytics
---------------

The analytics file is setup with exponential backoff for errors. It has just one main query function, into which can be passed the specific metrics, dimensions and dates that are needed.

Data Check
To check if data is available we query to get pageviews for every hour for the period's end date. If the results returned does not include 24 hours, then the data is not ready yet.


Youtube Analytics
-----------------

You must have a content owner ID as this is how the analytics queries are set up. 

Using this tool works best for content owners with multiple channels.

Data Check
To check if data is available we query for views on the period end date. If no results are returned then the data is not ready yet.


Adding a new service
--------------------

To add a new service, you would need to set up the main files following the instructions from the API to create the connection and make the queries.
In the aggregate_data file you would need to create the right functions using helper functions in the utilities to file to make sure the data is returned in similar format that the report and templates could use.
You will also have to create new templates and a new report to utilise your new service.





