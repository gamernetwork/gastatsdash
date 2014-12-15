Statsdash
=========

A basic summary of all your Google Analytics properties, broken down by some territories.  Not especially useful if you only have one account.

Output in nice HTML form, with a filter to make it email safe in case you want to email it to your managers :)

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

Need to tell python to assume stdout is UTF-8 or it'll moan when it tries to convert some country names.

```shell
PYTHONIOENCODING=utf-8 env/bin/python stats_dash.py <period> \
	| PYTHONIOENCODING=utf-8 env/bin/python format.py [--email] [--template=<template-file>] <output-file>
```

period
:   n-days to run  | 'month' (calendar month - back to same date last month)

--email
:   whether or not to inline the stylesheet for better email compatibility

--template
:   which file, relative to templates/, to use for formatting the output.  Templates are in Django format.

output-file
:   a file, or - for stdout


To pipe the output to an email, just send the right headers.

```shell
PYTHONIOENCODING=utf-8 env/bin/python stats_dash.py <period> \
	| PYTHONIOENCODING=utf-8 env/bin/python format.py - \
	| mail -a "Content-Type: text/html; charset=utf-8" -s "statsdash" <email-address>
```

If you don't have a working local sendmail, then you're on your own (python has excellent SMTP libraries!)
