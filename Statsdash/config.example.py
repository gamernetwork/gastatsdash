import os


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_filter_list():
    # path names to remove from top articles
    black_list = ["/forum", "/login.php", "/cookies.php"]
    # remove homepage etc from lists also - used in getting the articles
    filter_list = 'ga:pagePathLevel1!=/;ga:pagePath!~/page/*;ga:pagePath!~^/\?.*'
    for i in black_list:
        filter = '^' + i + '.*'
        filter_list += ';ga:pagePath!~%s' % filter
    return filter_list


# set up logging config
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s->%(funcName)s %(message)s',
            'datefmt': '%d-%m-%Y %H-%M-%S'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'report_generation.log',
            'mode': 'w',
        }
    },
    'loggers': {
        'report': {
            'handlers': ['file'],
            'level': 'DEBUG',
        }
    }
}

GOOGLE = {
    'KEY_FILE': 'path/to/keyfile',  # update this
    'TABLES': {
        # 'site-name.com': [{'id': 'ga:12345678'}]
    },
    'ALL_SITES_NAME': 'Network',
    'ALL_NETWORK_SITES': False,
    'ARTICLE_FILTER': get_filter_list(),
    'SOURCE_BLACK_LIST': ['google', '(direct)']
}

YOUTUBE = {
    'KEY_FILE': 'path/to/keyfile',  # update this
    'CREDENTIALS_FILE': PROJECT_ROOT + '/credentials.json',
    'CHANNELS': {
        # 'channel-name': ['UC0abcdefgh12345678']
    },
    'CONTENT_OWNER_ID': '-some_id',
}
# Email recipient for specific sites.
EMAILS = {
    # 'site_name': 'email_address'
}

CUSTOM_NAMES = {
    # 'site_name': 'custom_name'
}

SMTP_ADDRESS = 'localhost:1025'
SEND_FROM = 'statsdash@your-hostname.net'
ERROR_REPORTER = ['logging@your-hostname.net']
SCHEDULE_DB_LOCATION = os.path.abspath('.')

