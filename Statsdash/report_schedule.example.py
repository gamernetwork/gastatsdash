from Statsdash import config
from Statsdash.report import AnalyticsCoreReport


all_recipients = ['all@gamer-network.net']


all_sites = config.GOOGLE['TABLES'].keys()
network_sites = config.ALL_NETWORK_SITES
all_channels = config.YOUTUBE['CHANNELS'].keys()

reports = [
    {
        'report': AnalyticsCoreReport,
        'recipients': all_recipients,
        'subject': 'Gamer Network monthly statsdash for',
        'sites': network_sites,
        'frequency': 'MONTHLY',
        'frequency_options': {'day': 1},
        'identifier': 'network-monthly-report'
    },
    {
        'report': AnalyticsCoreReport,
        'recipients': all_recipients,
        'subject': 'Gamer Network daily statsdash for',
        'sites': network_sites,
        'frequency': 'WOW_DAILY',
        'identifier': 'network-daily-report'
    },
]

for key in config.EMAILS.keys():
    if key == 'gamer-network.net':
        continue
    elif key not in network_sites:
        continue
    else:
        site_report = [
            {
                'report': AnalyticsCoreReport,
                'recipients': [config.EMAILS[key]],
                'subject': '%s daily statsdash for' % key.capitalize(),
                'sites': [key],
                'frequency': 'WOW_DAILY',
                'identifier': '%s-daily-report' % config.CUSTOM_NAMES[key]
            },
            {
                'report': AnalyticsCoreReport,
                'recipients': [config.EMAILS[key]],
                'subject': '%s monthly statsdash for' % key.capitalize(),
                'sites': [key],
                'frequency': 'MONTHLY',
                'frequency_options': {'day': 1},
                'identifier': '%s-monthly-report' % config.CUSTOM_NAMES[key]
            }
        ]
        reports.extend(site_report)
