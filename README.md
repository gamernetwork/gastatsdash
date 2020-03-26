Want to work for Gamer Network? [We are
hiring!](http://www.gamesindustry.biz/jobs/gamer-network)

# Statsdash

A simple email reporting tool for all your Google Analytics properties and
Youtube channels.  Not especially useful if you only have one account.

Uses Google Analytics API v3 and various Youtube APIs.

Designed to run periodically and to send reports when data is ready; GA and YT
do not have live stats and data can take 48 hours to appear.

## Install

Clone and pop it in a virtualenv for safety.

```shell
virtualenv env
env/bin/pip install -r requirements.txt
```

### Configure

Copy `report_schedule.py-example` to `report_schedule.py` and change the
reports config to be appropriate to you.

Copy `config.py-example` to `config.py` for Statsdash/config.py and change
values to those appropriate to you. 

Do the same for each API config.py - `Statsdash/GA/config.py` and/or
`Statsdash/Youtube/config.py` and change values to those appropriate to you. 

Get your GA site view IDs from the Google Analytics backends - it can be a
little hard to find the view ID so follow these steps:

1. Navigate to the 'Admin' tab.
1. Select your account, property and view.
1. Select 'View Settings' in the rightmost column - voilà.

Get your Youtube channel IDs as a content owner from here:
https://www.youtube.com/analytics or from a channels individual settings page
here: https://www.youtube.com/advanced_settings

To get your content owner ID see below.

### Generating service account

* Register for Google Developers Console:
  https://console.developers.google.com/
* Create a project
* Go to APIs & Auth -> Credentials
* Click 'Create a new client ID'
* Choose 'Service account'
* You will be prompted to save a .p12 file * this is the private key file
  referenced in GA/config.py
* Copy the service account email address and pop into GA/config.py

### Generating OAuth Client ID for Youtube access

* Register for Google Developers Console:
  https://console.developers.google.com/
* Create a project
* Go to APIs & Auth
* Enable Youtube Analytics API, Youtube Data API v3, Youtube Reporting API,
  Youtube Content ID API
* Go to Credentials -> Create Credentials
* Choose "OAuth Client ID"
* Choose "Other"
* Save the client ID and client Secret numbers
* The Client ID will appear under the Credentials tab, on the right click to
  "download JSON"
* Copy this file into the "Youtube folder" and fill in the path in the
  Youtube/config.py

### Auth as yourself for Youtube APIs

```
python create_credentials.py --noauth_local_webserver
```

Then copy the link into your browser, click "allow" and copy and paste the key
given into the shell. 

This should now have set up your scheduler with an oauth connection and created
a file "scheduler.py-oauth2.json".

### Get your content owner ID

** TODO FIX THIS NONSENSE ** 

You must run the `get_content_owner()` function in
`Statsdash/Youtube/analytics.py`, to do this:

* Generate the OAuth client ID first (see above)
* Add this code at the very top of analytics.py:
    ```  
    import sys
    sys.path.append("/path/to/gastatsdash")
    ```
* Add this code at the bottom of the analytics.py:
    ```  
    if __name__=="__main__":
        analytics = Analytics()
        print analytics.get_content_owner()["items"][0]["id"]
    ```
* You can then run ` python analytics.py --noauth_local_webserver `
* Follow the instructions. Copy the link into your browser, click "allow" and
  copy and paste the code back into the shell. 
* Your content owner id will be printed out, put it into the Youtube/config.py 
* Remember to remove these bits of code after! 

## Usage

```
python scheduler.py
```

This will iterate through the reports in your report config
`report_schedule.py`, check whether a report is due to run now and whether the
data for the report is available.

If the data is available for the dependent sites, the scheduler will trigger
the report to run and email its recipients.

It is advised that an hourly cron runs scheduler.py so that stats reports are
available soon after the data becomes available.
