
Analytics Services
==================

Overview
---------

Reports can be made using multiple different services. This is to help enable comparison across different platforms. So far Google Analytics and Youtube Analytics have been integrated, but other services such as Facebook or Twitter could be added.

Each service has a separate folder with similar files inside. Main files:

**Analytics.py**
  - connection to the service's API
  - querying functions to retrieve the data

**Aggregate_data.py**
  - initialises the date period and sites to get the data from analytics for
  - class that defines separate functions to get different tables of data
  - returns the data in a set format using functions defined in the shared ``utilities.py``

**Config.py**
  - mainly sets the variables for service connection
  - holds a dictionary of site names and IDs
  - see :ref:`config settings <config_settings>`

Google Analytics
-----------------

We have set up access to the Google Analytics Core Reporting API using a service account. You will need to do this as well, following :ref:`these steps <service_account>` or for more info go `here <https://developers.google.com/analytics/devguides/reporting/core/v3/quickstart/service-py>`_.

*class* Analytics()
    Sets up the service credentials and connection to google analytics API

    execute_query(*query*)
        | Executes the report query. If there is an error uses `exponential backoff <https://developers.google.com/analytics/devguides/reporting/core/v3/coreErrors>`_ to retry up to 5 times.

.. _ga-data-available:

    data_available(*site_id*, *stats_date*)
        | Queries the number of pageviews for each hour on the date specified.
        | If the results returned does not include all 24 hours, then the data is not available yet.
        | Returns True or False

    run_report(*site_id*, *start*, *end*, *query args*)
        | Creates a query using the data provided
        | Runs through query through the function *execute_query*

    rollup_ids(*properties*, *start*, *end*, *metrics*, *report args*)
        | Wrapper for run report
        | If a property has been defined with multiple IDs in the config, this queries the data for each ID and aggregates it together to return one list of results

Youtube Analytics
------------------

We have set up access to the Youtube Analytics and Reporting API using OAuth 2.0. You will need to do this as well, following :ref:`these steps <oauth_account>` or for more info go to the `youtube implementation <https://developers.google.com/youtube/reporting/guides/authorization>`_ or the `google python API client implementation <https://developers.google.com/api-client-library/python/guide/aaa_oauth>`_.


You must have a content owner ID as this is how the analytics queries are set up. 

Using this tool works best for content owners with multiple channels.

*class* Analytics()
    Sets up the service credentials using OAuth and connection to youtube analytics API

    execute_query(*query*)
        | Tries to execute the query, otherwise returns an error

.. _youtube-data-available:

    data_available(*id*, *date*)
        | Queries views for the specified date
        | If no results are returned, then the data is not available yet
        | Returns True or False

    get_content_owner()
        | Gets your content owner data response
        | Returns a dictionary containing the info, including your content owner ID

    get_channel_id()
        | Gets the list of channels owned by the content owner ID
        | Returns a dictionary response containing the info

    get_stats(*id*)
        | Gets the current, real time statistics of the channel defined by *id*
        | Returns a dictionary response

    rollup_stats(*ids*)
        | Wrapper for get stats
        | If a channel has been defined with multiple IDs, this queries and rolls up the data from the *get_stats* function to return as one result

    run_analytics_report(*start_date*, *end_date*, *metrics*, *dimensions*, *filters*, *extra args*)
        | Creates a query using the data provided and the content owner ID
        | Runs the query through the *execute_query* function

    rollup_ids(*ids*, *start*, *end*, *query args*)
        | Wrapper for run analytics report
        | If a channel has multiple IDs, this queries and rolls up the data from the *run_analytics_report* function to return the data as one result

    get_video(*id*)
        | Given the *id* of a video gets the data for that video
        | Returns a dictionary of info, including the name, channel etc

Adding a new service
--------------------

To extend Statsdash you could add more analytics services such as Facebook or Twitter to get more comparison. 

To add a new service, you would need to set up the main files following the instructions from the API to create the connection and make the queries.

In the aggregate_data file you would need to create the right functions using helper functions in the utilities to file to make sure the data is returned in similar format that the report and templates could use.
You will also have to create new templates and a new report to utilise your new service.





