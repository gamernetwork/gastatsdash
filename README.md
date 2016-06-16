Statsdash
=========

A simple email reporting tool for all your Google Analytics properties.  Not especially useful if you only have one account.

Uses Google Analytics API v3.

Install
-------

Pop it in a virtualenv for safety.

```shell
virtualenv env
env/bin/pip install -r requirements.txt
```

Copy ```config.py-example``` to ```config.py``` and change values to those appropriate to you. Get your tables IDs from
the Google Analytics backends - look for the view IDs.

Copy ```report_schedule.py-example``` to ```report_schedule.py``` and change the reports config to be appropriate to you.

See next section for generating a service account and private key.

Generating service account
--------------------------

  - Register for Google Developers Console: https://console.developers.google.com/
  - Create a project
  - Go to APIs & Auth -> Credentials
  - Click 'Create a new client ID'
    - Choose 'Service account'
  - You will be prompted to save a .p12 file - this is the private key file referenced in config.py
  - Copy the service account email address and pop into config.py
  - U r ready to rok (just remember not to check all this private stuff into git ok?)

Usage
-----

Reports are run using a lightweight scheduler - scheduler.py.

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
