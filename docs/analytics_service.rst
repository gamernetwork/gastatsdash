
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
  - see :ref:`config <settings>`
