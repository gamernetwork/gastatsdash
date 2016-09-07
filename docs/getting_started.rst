Getting Started
==============

A quick way to set up Statsdash.

Install
-------

Pop it in a virtualenv for safety.

```shell
virtualenv env
env/bin/pip install -r requirements.txt
```

Copy ```report_schedule.py-example``` to ```report_schedule.py``` and change the reports config to be appropriate to you.

Copy ```config.py-example``` to ```config.py``` for Statsdash/config.py and change values to those appropriate to you. 

Do the same for each API config.py - ```Statsdash/GA/config.py``` and/or ```Statsdash/Youtube/config.py``` and change values to those appropriate to you. 

Get your tables IDs from the Google Analytics backends - look for the view IDs.

Get your channel IDs as a content owner from here: https://www.youtube.com/analytics or from a channels individual settings page here: https://www.youtube.com/account_advanced.

To get your content owner ID see below.

Generating service account
--------------------------

  - Register for Google Developers Console: https://console.developers.google.com/
  - Create a project
  - Go to APIs & Auth -> Credentials
  - Click 'Create a new client ID'
    - Choose 'Service account'
  - You will be prompted to save a .p12 file - this is the private key file referenced in GA/config.py
  - Copy the service account email address and pop into GA/config.py

Generating OAuth Client ID
--------------------------

  - Register for Google Developers Console: https://console.developers.google.com/
  - Create a project
  - Go to APIs & Auth
  - Enable Youtube Analytics API, Youtube Data API v3, Youtube Reporting API, Youtube Content ID API
  - Go to Credentials -> Create Credentials
    - Choose "OAuth Client ID"
    - Choose "Other"
  - Save the client ID and client Secret numbers
  - The Client ID will appear under the Credentials tab, on the right click to "download JSON"
  - Copy this file into the "Youtube folder" and fill in the path in the Youtube/config.py


Get your content owner ID
--------------------------

  - You must run the ```get_content_owner()``` function in ```Statsdash/Youtube/analytics.py```, to do this:
  - Generate the OAuth client ID first (see above)
  - Add this code at the very top of analytics.py:
```  
  import sys
    sys.path.append("/path/to/gastatsdash")
```
  - Add this code at the bottom of the analytics.py:
```  
  if __name__=="__main__":
      analytics = Analytics()
      print analytics.get_content_owner()["items"][0]["id"]
```
  - You can then run ``` python analytics.py --noauth_local_webserver ```
  - Follow the instructions. Copy the link into your browser, click "allow" and copy and paste the code back into the shell. 
  - Your content owner id will be printed out, put it into the Youtube/config.py 
  - Remember to remove these bits of code after! 

  

Usage
-----

Reports are run using a lightweight scheduler - scheduler.py.

If you are using the Youtube API you must first set up the OAuth connection by running:

```
python scheduler.py --noauth_local_webserver
```
Then copy the link into your browser, click "allow" and copy and paste the key given into the shell. 

This should now have set up your scheduler with an oauth connection and created a file "scheduler.py-oauth2.json".

You will have to do this for every file you want to run the Youtube API from. 

You can now run the scheduler as normal:


```
python scheduler.py
```

This will iterate through the reports in your report config ```report_schedule.py```,
check whether a report is due to run now and whether the data for the report is
available in Google Analytics.

If the data is available for the dependent sites, the scheduler will trigger
the report to run and email its recipients.

It is advised that an hourly cron runs scheduler.py so that stats reports are
available soon after the data becomes available on Google Analytics.

