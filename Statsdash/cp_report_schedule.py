from Statsdash.report import AnalyticsCoreReport, YouTubeReport

recipients = ['me@example.net', 'bob@example.net']

# EXAMPLE reports configuration - adjust this for your sites


reports = [
    {
        'report': AnalyticsCoreReport,
        'recipients': recipients,
        'subject': 'RPS Daily Report',  # subject as string
        'sites': ['rockpapershotgun.com'],
        'frequency': 'DAILY',
        'identifier': 'network-daily-report',
    },
    # {
    #     'report': YouTubeReport,
    #     'recipients': recipients,
    #     'subject': 'DiceBreaker Daily Report',  # subject as string
    #     'sites': ['dicebreaker'],
    #     'frequency': 'MONTHLY',
    #     'frequency_options': {'day': 1},
    #     'identifier': 'network-youtube-report',
    # }
]
