Want to work for Gamer Network? [We are
hiring!](http://www.gamesindustry.biz/jobs/gamer-network)

# Statsdash

A simple email reporting tool for all your Google Analytics properties and
Youtube channels.

Uses Google Analytics API v3 and various Youtube APIs.

Designed to run periodically and to send reports when data is ready; GA and YT
do not have live stats and data can take 48 hours to appear.


## Getting Started


### Installing

Clone the repo and create a `virtualenv`. Activate the `virtualenv` and install requirements.

```shell
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

For development you should have `mailcatcher` installed. Install it inside the environment
or system wide. 

```shell script
brew install ruby
sudo gem install mailcatcher
```

### Configure

Copy the example configuration files.

```shell script
cp Statsdash/report_schedule.example.py report_schedule.py
cp Statsdash/config.example.py config.py
```

Update `Statsdash/report_schedule.py` for whatever reports you want to generate.

**Important**
* Inside `Statsdash/config.py` you will need to provide paths to two key files
for Google Analytics and YouTube Analytics authentication. This step is explained
[here](#getting-your-property-ids).

* You will also need to update `GOOGLE['TABLES']` and `YOUTUBE['CHANNELS']`
to reflect your properties. This step is explained [here](#generating-analytics-key-file).

* For YouTube Analytics you will need your content owner ID. This step is explained
[here](#getting-your-content-owner-id).

* Finally, you will need to auth yourself for YouTube Analytics API. This step is explained
[here](#generating-analytics-key-file).


Once you have completed these steps you can [run the project](#usage).


## Getting your property IDs

### Google Analytics

Get your GA site view IDs from the 
[Google Analytics backend](https://analytics.google.com/analytics/web)

It can be a little hard to find the view ID so follow these steps:

1. Navigate to the 'Admin' tab.
1. Select your account, property and view.
1. Select 'View Settings' in the rightmost column.

**Note:** the view ID will be a numeric ID with about nine characters. In
`Statsdash/config.py`, the id should have `ga:` prepended to it (see `config.example.py`).

### YouTube

To get your Youtube channel ID, navigate to the
[YouTube Analytics page](https://www.youtube.com/analytics). Your ID will appear in the
URL after `/channel/`. It should be a combination of letters and numbers.

**Note:** you may need to switch accounts to the appropriate account.

## Generating analytics key file

### Generating service account key file

1. Register for [Google Developers Console](https://console.developers.google.com/)
1. Create a project
1. Enable Google Analytics API
1. Go to Credentials and click `Create Credentials`
1. Choose 'Service account'
1. You will be prompted to save a `.json` file. This is the private key file
  referenced in `config.GOOGLE['KEY_FILE']`.
1. Update the `config.GOOGLE['KEY_FILE']` path to reflect the location of the key file
on your machine.

### Generating OAuth Client ID for Youtube access

1. Register for [Google Developers Console](https://console.developers.google.com/)
1. Create a project
1. Enable Youtube Analytics API, Youtube Data API v3, Youtube Reporting API,
Youtube Content ID API
1. Go to Credentials and click `Create Credentials`
1. Choose 'OAuth Client ID'
1. The Client ID will appear under the Credentials tab, on the right click to
  download the `.json` file.
1. Update the `config.YOUTUBE['KEY_FILE']` path to reflect the location of the key file
on your machine.
  
## Getting your content owner ID

TODO

## Auth as yourself for Youtube APIs

Run the `create_credentials` file.
```
python create_credentials.py
```

A web browser will launch where you can sign into your Google account. Once you have
signed in, a file called `credentials.json` will be saved in the project root directory.

## Running the tests

Make sure you are inside your virtual environment and have installed requirements.
```shell script
nosetests Statsdash/tests/
```

## Usage

**Note:** For development, run mailcatcher so that you can see the emails that are sent.
By default they will be available at `http://127.0.0.1:1080/`.
```shell script
mailcatcher
``` 

To run the scheduler:

```
python scheduler.py
```

This will iterate through the reports in your report config
`report_schedule.py`, check whether a report is due to run now and whether the
data for the report is available.

If the data is available for the dependent sites, the scheduler will trigger
the report to run and email its recipients.

It is advised that an hourly cron runs `scheduler.py` so that stats reports are
available soon after the data becomes available.
