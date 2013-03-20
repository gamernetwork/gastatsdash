Statsdash
=========

A basic summary of all your Google Analytics properties, broken down by some territories.  Not especially useful if you only have one account.

Output in nice HTML form, with a filter to make it email safe in case you want to email it to your managers :)

Uses legacy Google Analytics API cos the new version (3) requires all sorts of OAuth nonsense and who's got time for that amirite?  Just remember not to leave your API credentials lying around, or checked in to github!

Install
-------

Pop it in a virtualenv for safety.

```shell
virtualenv env
env/bin/pip install gdata          # analytics API v2
env/bin/pip install django         # for templates (sorry, I know this is excessive)
env/bin/pip install pynliner       # css -> inline styles conversion
env/bin/pip install cssutils       # ditto
env/bin/pip install BeautifulSoup  # ditto
```

Copy ```example-credentials.py``` to ```credentials.py``` and change values to those appropriate to you.

Usage
-----

Need to tell python to assume stdout is UTF-8 or it'll moan when it tries to convert some country names.

```shell
PYTHONIOENCODING=utf-8 env/bin/python stats_dash.py <period> \
	| PYTHONIOENCODING=utf-8 env/bin/python format.py > <output-file>
```

<period>:
	n-days to run  | 'month' (calendar month - back to same date last month)

To pipe the output to an email, just send the right headers.

```shell
PYTHONIOENCODING=utf-8 env/bin/python stats_dash.py <period> \
	| PYTHONIOENCODING=utf-8 env/bin/python format.py > <output-file> \
	| mail -a "Content-Type: text/html; charset=utf-8" -s "statsdash" <email-address>
```

If you don't have a working local sendmail, then you're on your own (python has excellent SMTP libraries!)
