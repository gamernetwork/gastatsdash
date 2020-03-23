response_not_ready = {
    'columnHeaders': [{'columnType': 'DIMENSION',
                       'dataType': 'STRING',
                       'name': 'ga:dateHour'},
                      {'columnType': 'METRIC',
                       'dataType': 'INTEGER',
                       'name': 'ga:pageviews'}],
    'containsSampledData': False,
    'id': 'fakelink',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'profileInfo': {'accountId': 'fakeid',
                    'internalWebPropertyId': 'fakeid',
                    'profileId': 'fakeid',
                    'profileName': 'Without multipages www.fakesite.com/',
                    'tableId': 'fakeid',
                    'webPropertyId': 'fakeid'},
    'query': {'dimensions': 'ga:dateHour',
              'end-date': '2020-03-12',
              'ids': 'fakeid',
              'max-results': 1000,
              'metrics': ['ga:pageviews'],
              'start-date': '2020-03-12',
              'start-index': 1},
    'rows': [['2020031200', '7260'],
             ['2020031201', '6502'],
             ['2020031202', '6141'],
             ['2020031203', '5416'],
             ['2020031204', '5276'],
             ['2020031205', '4679'],
             ['2020031206', '5220'],
             ['2020031207', '2056']],
    'selfLink': 'fakelink',
    'totalResults': 8,
    'totalsForAllResults': {'ga:pageviews': '42550'}
}


response_ready = {
    'columnHeaders': [{'columnType': 'DIMENSION',
                       'dataType': 'STRING',
                       'name': 'ga:dateHour'},
                      {'columnType': 'METRIC',
                       'dataType': 'INTEGER',
                       'name': 'ga:pageviews'}],
    'containsSampledData': False,
    'id': 'fakeid',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'profileInfo': {'accountId': 'fakeid',
                    'internalWebPropertyId': 'fakeid',
                    'profileId': 'fakeid',
                    'profileName': 'Without multipages www.fakesite.com/',
                    'tableId': 'ga:fakeid',
                    'webPropertyId': 'fakeid'},
    'query': {'dimensions': 'ga:dateHour',
              'end-date': '2020-03-12',
              'ids': 'fakeid',
              'max-results': 1000,
              'metrics': ['ga:pageviews'],
              'start-date': '2020-03-12',
              'start-index': 1},
    'rows': [['2020031200', '7260'],
             ['2020031201', '6502'],
             ['2020031202', '6141'],
             ['2020031203', '5416'],
             ['2020031204', '5276'],
             ['2020031205', '4679'],
             ['2020031206', '5220'],
             ['2020031207', '5220'],
             ['2020031208', '5220'],
             ['2020031209', '5220'],
             ['2020031210', '5220'],
             ['2020031211', '5220'],
             ['2020031212', '5220'],
             ['2020031213', '5220'],
             ['2020031214', '5220'],
             ['2020031215', '5220'],
             ['2020031216', '5220'],
             ['2020031217', '5220'],
             ['2020031218', '5220'],
             ['2020031219', '5220'],
             ['2020031220', '5220'],
             ['2020031221', '5220'],
             ['2020031222', '5220'],
             ['2020031223', '2056']],
    'selfLink': 'fakelink',
    'totalResults': 24,
    'totalsForAllResults': {'ga:pageviews': '42550'}
}

response_no_rows = {
    'columnHeaders': [{'columnType': 'DIMENSION',
                       'dataType': 'STRING',
                       'name': 'ga:dateHour'},
                      {'columnType': 'METRIC',
                       'dataType': 'INTEGER',
                       'name': 'ga:pageviews'}],
    'containsSampledData': False,
    'id': 'fakelink',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'profileInfo': {'accountId': 'fakeid',
                    'internalWebPropertyId': 'fakeid',
                    'profileId': 'fakeid',
                    'profileName': 'Without multipages www.fakesite.com/',
                    'tableId': 'fakeid',
                    'webPropertyId': 'fakeid'},
    'query': {'dimensions': 'ga:dateHour',
              'end-date': '2020-03-12',
              'ids': 'fakeid',
              'max-results': 1000,
              'metrics': ['ga:pageviews'],
              'start-date': '2020-03-12',
              'start-index': 1},
    'rows': [],
    'selfLink': 'fakelink',
    'totalResults': 0,
    'totalsForAllResults': {'ga:pageviews': '0'}
}

get_data_for_period_mock_1 = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:dateHour'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:users'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:sessions'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviewsPerSession'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:avgSessionDuration'
        },
    ],
    'rows': [
        ['2020031200', '7260', '350', '400', '2', '15'],
        ['2020031201', '5060', '360', '800', '4', '15'],
    ]
}

get_data_for_period_mock_2 = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:dateHour'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:users'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:sessions'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviewsPerSession'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:avgSessionDuration'
        },
    ],
    'rows': [
        ['2020031200', '3890', '125', '250', '10', '5'],
        ['2020031201', '5060', '360', '800', '4', '15'],
    ]
}

article_query_response_1 = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:pageTitle'
        },
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:pagePath'},
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:hostname'},
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'}
    ],
    'containsSampledData': False,
    'id': 'fakeid',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'nextLink': 'fakelink',
    'query': {
        'dimensions': 'ga:pageTitle,ga:pagePath,ga:hostname',
        'end-date': '2020-03-18',
        'filters': 'ga:pagePathLevel1!=/;ga:pagePath!~/page/*;ga:pagePath!~^/\\?.*',
        'ids': 'fakeif',
        'max-results': 1000,
        'metrics': ['ga:pageviews'],
        'sort': ['-ga:pageviews'],
        'start-date': '2020-03-18',
        'start-index': 1
    },
    'rows': [
        [
            'Article 1',
            '/link/to/article-1/',
            'www.fake.site1.com',
            '15200'
        ],
        [
            'Article 2',
            '/link/to/article-2/',
            'www.fake.site1.com',
            '16800'
        ],
    ]
}

article_query_response_2 = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:pageTitle'
        },
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:pagePath'},
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:hostname'},
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'}
    ],
    'containsSampledData': False,
    'id': 'fakeid',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'nextLink': 'fakelink',
    'query': {
        'dimensions': 'ga:pageTitle,ga:pagePath,ga:hostname',
        'end-date': '2020-03-18',
        'filters': 'ga:pagePathLevel1!=/;ga:pagePath!~/page/*;ga:pagePath!~^/\\?.*',
        'ids': 'fakeif',
        'max-results': 1000,
        'metrics': ['ga:pageviews'],
        'sort': ['-ga:pageviews'],
        'start-date': '2020-03-18',
        'start-index': 1
    },
    'rows': [
        [
            'Article 3',
            '/link/to/article-3/',
            'www.fake.site2.com',
            '16800'
        ],
        [
            'Article 4',
            '/link/to/article-4/',
            'www.fake.site2.com',
            '45300'
        ],
    ]
}

mock_join_periods_data = [
    [
        {
            'avg_session_time': 30.0,
            'pageviews': 12320.0,
            'pv_per_session': 6.0,
            'sessions': 1200.0,
            'site': 'fake.site1.com',
            'users': 710.0
        },
        {
            'avg_session_time': 20.0,
            'pageviews': 8950.0,
            'pv_per_session': 14.0,
            'sessions': 1050.0,
            'site': 'fake.site2.com',
            'users': 485.0
        }
    ],
    [
        {
            'avg_session_time': 30.0,
            'pageviews': 12320.0,
            'pv_per_session': 6.0,
            'sessions': 1200.0,
            'site': 'fake.site1.com',
            'users': 710.0
        },
        {
            'avg_session_time': 20.0,
            'pageviews': 8950.0,
            'pv_per_session': 14.0,
            'sessions': 1050.0,
            'site': 'fake.site2.com',
            'users': 485.0
        }
    ],
    [
        {
            'avg_session_time': 30.0,
            'pageviews': 12320.0,
            'pv_per_session': 6.0,
            'sessions': 1200.0,
            'site': 'fake.site1.com',
            'users': 710.0
        },
        {
            'avg_session_time': 20.0,
            'pageviews': 8950.0,
            'pv_per_session': 14.0,
            'sessions': 1050.0,
            'site': 'fake.site2.com',
            'users': 485.0
        }
    ],
]

summary_get_table_data = [
    {
        'avg_session_time': 0.5,
        'pageviews': 24640.0,
        'pv_per_session': 6.0,
        'sessions': 2400.0,
        'users': 1420.0
    }
]

site_summary_get_table_data = [
    {
        'avg_session_time': 30.0,
        'pageviews': 12320.0,
        'pv_per_session': 6.0,
        'sessions': 1200.0,
        'site': 'fake.site2.com',
        'users': 710.0
    },
    {
        'avg_session_time': 20.0,
        'pageviews': 8950.0,
        'pv_per_session': 14.0,
        'sessions': 1050.0,
        'site': 'fake.site1.com',
        'users': 485.0
    }
]

country_report = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:country'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:users'
        }
    ],
    'containsSampledData': False,
    'id': 'fakeid',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'profileInfo': {
        'accountId': 'fakeid',
        'internalWebPropertyId': 'fakeid',
        'profileId': 'fakeid',
        'profileName': 'fakename',
        'tableId': 'fakeid',
        'webPropertyId': 'fakeid'
    },
    'query': {
        'dimensions': 'ga:country',
        'end-date': '2020-03-18',
        'filters': 'ga:country=~Czec|Germa|Denma|Spai|Franc|Italy|Portug|Swede|Polan|Brazi|Belgiu|Netherl|United '
                   'Ki|Irela|United St|Canad|Austral|New Ze',
        'ids': 'fakeid',
        'max-results': 1000,
        'metrics': ['ga:pageviews', 'ga:users'],
        'sort': ['-ga:pageviews'],
        'start-date': '2020-03-18',
        'start-index': 1
    },
    'rows': [
        ['United States', '95483', '50559'],
        ['United Kingdom', '34436', '13710'],
        ['Canada', '15040', '7678'],
        ['Germany', '11979', '5665'],
        ['Australia', '8730', '4390'],
        ['France', '7230', '3593'],
        ['Netherlands', '6037', '2838'],
        ['Sweden', '5252', '2580'],
        ['Italy', '4266', '2027'],
        ['Brazil', '4225', '2040'],
        ['Poland', '4209', '2019'],
        ['Spain', '3373', '1660'],
        ['Denmark', '2920', '1456'],
        ['Belgium', '2481', '1217'],
        ['Czechia', '2010', '960'],
        ['Ireland', '1801', '822'],
        ['Portugal', '1753', '792'],
        ['New Zealand', '1605', '761']
    ],
    'selfLink': 'fakelink',
    'totalResults': 18,
    'totalsForAllResults': {'ga:pageviews': '212830', 'ga:users': '104767'}
}
rest_of_world_country_report = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:country'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:users'
        }
    ],
    'containsSampledData': False,
    'id': 'fakeid',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'profileInfo': {
        'accountId': 'fakeid',
        'internalWebPropertyId': 'fakeid',
        'profileId': 'fakeid',
        'profileName': 'fakename',
        'tableId': 'fakeid',
        'webPropertyId': 'fakeid'
    },
    'query': {
        'dimensions': 'ga:country',
        'end-date': '2020-03-18',
        'filters': 'ga:country!~Czec|Germa|Denma|Spai|Franc|Italy|Portug|Swede|Polan|Brazi|Belgiu|Netherl|United '
                   'Ki|Irela|United St|Canad|Austral|New Ze',
        'ids': 'fakeid',
        'max-results': 1000,
        'metrics': ['ga:pageviews', 'ga:users'],
        'sort': ['-ga:pageviews'],
        'start-date': '2020-03-18',
        'start-index': 1
    },
    'rows': [
        ['Some other country', '95483', '50559'],
        ['Another country', '2030', '6830'],
    ],
    'selfLink': 'fakelink',
    'totalResults': 18,
    'totalsForAllResults': {'ga:pageviews': '95483', 'ga:users': '50559'}
}

countries_expected_data_row = [
    {'country': 'ROW', 'pageviews': 195026.0, 'users': 114778.0},
    {'country': 'United States', 'pageviews': 190966.0, 'users': 101118.0},
    {'country': 'United Kingdom', 'pageviews': 68872.0, 'users': 27420.0},
    {'country': 'Canada', 'pageviews': 30080.0, 'users': 15356.0},
    {'country': 'Germany', 'pageviews': 23958.0, 'users': 11330.0},
    {'country': 'Australia', 'pageviews': 17460.0, 'users': 8780.0},
    {'country': 'France', 'pageviews': 14460.0, 'users': 7186.0},
    {'country': 'Netherlands', 'pageviews': 12074.0, 'users': 5676.0},
    {'country': 'Sweden', 'pageviews': 10504.0, 'users': 5160.0},
    {'country': 'Brazil', 'pageviews': 8450.0, 'users': 4080.0},
    {'country': 'Italy', 'pageviews': 8532.0, 'users': 4054.0},
    {'country': 'Poland', 'pageviews': 8418.0, 'users': 4038.0},
    {'country': 'Spain', 'pageviews': 6746.0, 'users': 3320.0},
    {'country': 'Denmark', 'pageviews': 5840.0, 'users': 2912.0},
    {'country': 'Belgium', 'pageviews': 4962.0, 'users': 2434.0},
    {'country': 'Czechia', 'pageviews': 4020.0, 'users': 1920.0},
    {'country': 'Ireland', 'pageviews': 3602.0, 'users': 1644.0},
    {'country': 'Portugal', 'pageviews': 3506.0, 'users': 1584.0},
    {'country': 'New Zealand', 'pageviews': 3210.0, 'users': 1522.0},
]

countries_expected_data_no_row = [
    {'country': 'United States', 'pageviews': 190966.0, 'users': 101118.0},
    {'country': 'United Kingdom', 'pageviews': 68872.0, 'users': 27420.0},
    {'country': 'Canada', 'pageviews': 30080.0, 'users': 15356.0},
    {'country': 'Germany', 'pageviews': 23958.0, 'users': 11330.0},
    {'country': 'Australia', 'pageviews': 17460.0, 'users': 8780.0},
    {'country': 'France', 'pageviews': 14460.0, 'users': 7186.0},
    {'country': 'Netherlands', 'pageviews': 12074.0, 'users': 5676.0},
    {'country': 'Sweden', 'pageviews': 10504.0, 'users': 5160.0},
    {'country': 'Brazil', 'pageviews': 8450.0, 'users': 4080.0},
    {'country': 'Italy', 'pageviews': 8532.0, 'users': 4054.0},
    {'country': 'Poland', 'pageviews': 8418.0, 'users': 4038.0},
    {'country': 'Spain', 'pageviews': 6746.0, 'users': 3320.0},
    {'country': 'Denmark', 'pageviews': 5840.0, 'users': 2912.0},
    {'country': 'Belgium', 'pageviews': 4962.0, 'users': 2434.0},
    {'country': 'Czechia', 'pageviews': 4020.0, 'users': 1920.0},
    {'country': 'Ireland', 'pageviews': 3602.0, 'users': 1644.0},
    {'country': 'Portugal', 'pageviews': 3506.0, 'users': 1584.0},
    {'country': 'New Zealand', 'pageviews': 3210.0, 'users': 1522.0},
    {'country': 'ROW', 'pageviews': 0.0, 'users': 0.0},
]

traffic_source_data = {
    'columnHeaders': [
        {
            'columnType': 'DIMENSION',
            'dataType': 'STRING',
            'name': 'ga:sourceMedium'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:pageviews'
        },
        {
            'columnType': 'METRIC',
            'dataType': 'INTEGER',
            'name': 'ga:users'
        }
    ],
    'containsSampledData': False,
    'id': 'fakeid',
    'itemsPerPage': 1000,
    'kind': 'analytics#gaData',
    'profileInfo': {
        'accountId': 'fakeid',
        'internalWebPropertyId': 'fakeid',
        'profileId': 'fakeid',
        'profileName': 'fakeid',
        'tableId': 'fakeid',
        'webPropertyId': 'fakeid'
    },
    'query': {
        'dimensions': 'ga:sourceMedium',
        'end-date': '2020-03-13',
        'ids': 'fakeid',
        'max-results': 1000,
        'metrics': ['ga:pageviews', 'ga:users'],
        'sort': ['-ga:users'],
        'start-date': '2020-03-12',
        'start-index': 1
    },
    'rows': [['google / organic', '236163', '110057'],
             ['(direct) / (none)', '104762', '42628'],
             ['feedburner / feed', '12147', '6539'],
             ['googleads.g.doubleclick.net / referral',
              '20613', '3451'],
             ['mormont / inline_image', '18361', '3148'],
             ['t.co / referral', '6414', '1911'],
             ['bing / organic', '3714', '1710']],

    'selfLink': 'fakeid',
    'totalResults': 781,
    'totalsForAllResults': {'ga:pageviews': '436729',
                            'ga:users': '182786'}
}

expected_traffic_source_data = [
    {'pageviews': 472326.0,
     'source_medium': 'google / organic',
     'users': 220114.0},
    {'pageviews': 209524.0,
     'source_medium': '(direct) / (none)',
     'users': 85256.0},
    {'pageviews': 24294.0, 'source_medium': 'feedburner / feed',
     'users': 13078.0},
    {'pageviews': 41226.0,
     'source_medium': 'googleads.g.doubleclick.net / referral',
     'users': 6902.0},
    {'pageviews': 36722.0,
     'source_medium': 'mormont / inline_image',
     'users': 6296.0},
    {'pageviews': 12828.0, 'source_medium': 't.co / referral',
     'users': 3822.0},
    {'pageviews': 7428.0, 'source_medium': 'bing / organic', 'users': 3420.0}
]

device_response = {'columnHeaders': [{'columnType': 'DIMENSION',
                    'dataType': 'STRING',
                    'name': 'ga:deviceCategory'},
                   {'columnType': 'METRIC',
                    'dataType': 'INTEGER',
                    'name': 'ga:users'}],
 'containsSampledData': False,
 'id': '',
 'itemsPerPage': 1000,
 'kind': 'analytics#gaData',
 'profileInfo': {'accountId': '',
                 'internalWebPropertyId': '',
                 'profileId': '',
                 'profileName': '',
                 'tableId': '',
                 'webPropertyId': ''},
 'query': {'dimensions': 'ga:deviceCategory',
           'end-date': '2020-03-13',
           'ids': '',
           'max-results': 1000,
           'metrics': ['ga:users'],
           'sort': ['-ga:users'],
           'start-date': '2020-03-12',
           'start-index': 1},
 'rows': [['desktop', '105338'], ['mobile', '69385'], ['tablet', '4745']],
 'selfLink': '',
 'totalResults': 3,
 'totalsForAllResults': {'ga:users': '179468'}}

device_data_expected_1 = [
    {'device_category': 'desktop', 'users': 105338.0},
    {'device_category': 'mobile', 'users': 69385.0},
    {'device_category': 'tablet', 'users': 4745.0}
]

social_response = {'columnHeaders': [{'columnType': 'DIMENSION',
                    'dataType': 'STRING',
                    'name': 'ga:socialNetwork'},
                   {'columnType': 'METRIC',
                    'dataType': 'INTEGER',
                    'name': 'ga:pageviews'},
                   {'columnType': 'METRIC',
                    'dataType': 'INTEGER',
                    'name': 'ga:users'},
                   {'columnType': 'METRIC',
                    'dataType': 'INTEGER',
                    'name': 'ga:sessions'}],
 'containsSampledData': False,
 'id': '',
 'itemsPerPage': 1000,
 'kind': 'analytics#gaData',
 'profileInfo': {'accountId': '',
                 'internalWebPropertyId': '',
                 'profileId': '',
                 'profileName': '',
                 'tableId': '',
                 'webPropertyId': ''},
 'query': {'dimensions': 'ga:socialNetwork',
           'end-date': '2020-03-13',
           'filters': 'ga:socialNetwork!=(not set)',
           'ids': '',
           'max-results': 1000,
           'metrics': ['ga:pageviews', 'ga:users', 'ga:sessions'],
           'sort': ['-ga:users'],
           'start-date': '2020-03-12',
           'start-index': 1},
 'rows': [['Facebook', '5980', '3001', '4149'],
          ['Twitter', '6421', '1914', '3483'],
          ['reddit', '909', '287', '502'],
          ['YouTube', '168', '72', '84'],
          ['Hacker News', '155', '67', '88'],
          ['Quora', '77', '58', '69'],
          ['Pocket', '107', '32', '64'],
          ['Pinterest', '40', '23', '24'],
          ['Netvibes', '60', '19', '35'],
          ['Blogger', '34', '8', '23'],
          ['VKontakte', '7', '6', '7'],
          ['Naver', '7', '5', '5'],
          ['LiveJournal', '4', '4', '4'],
          ['WordPress', '12', '4', '5'],
          ['Instagram', '2', '2', '2'],
          ['LinkedIn', '3', '2', '2'],
          ['Yammer', '6', '2', '2'],
          ['Disqus', '1', '1', '1'],
          ['Instapaper', '4', '1', '1'],
          ['Plurk', '16', '1', '6'],
          ['TypePad', '1', '1', '1'],
          ['tinyURL', '1', '1', '1']],
 'selfLink': '',
 'totalResults': 22,
 'totalsForAllResults': {'ga:pageviews': '14015',
                         'ga:sessions': '8558',
                         'ga:users': '5511'}}

social_data_expected_1 = [
    {'pageviews': 11960.0,
     'sessions': 8298.0,
     'social_network': 'Facebook',
     'users': 6002.0},
    {'pageviews': 12842.0,
     'sessions': 6966.0,
     'social_network': 'Twitter',
     'users': 3828.0},
    {'pageviews': 1818.0,
     'sessions': 1004.0,
     'social_network': 'reddit',
     'users': 574.0},
    {'pageviews': 336.0,
     'sessions': 168.0,
     'social_network': 'YouTube',
     'users': 144.0},
    {'pageviews': 310.0,
     'sessions': 176.0,
     'social_network': 'Hacker News',
     'users': 134.0},
    {'pageviews': 154.0,
     'sessions': 138.0,
     'social_network': 'Quora',
     'users': 116.0},
    {'pageviews': 214.0,
     'sessions': 128.0,
     'social_network': 'Pocket',
     'users': 64.0},
    {'pageviews': 80.0,
     'sessions': 48.0,
     'social_network': 'Pinterest',
     'users': 46.0},
    {'pageviews': 120.0,
     'sessions': 70.0,
     'social_network': 'Netvibes',
     'users': 38.0},
    {'pageviews': 68.0,
     'sessions': 46.0,
     'social_network': 'Blogger',
     'users': 16.0},
    {'pageviews': 14.0,
     'sessions': 14.0,
     'social_network': 'VKontakte',
     'users': 12.0},
    {'pageviews': 14.0,
     'sessions': 10.0,
     'social_network': 'Naver',
     'users': 10.0},
    {'pageviews': 8.0,
     'sessions': 8.0,
     'social_network': 'LiveJournal',
     'users': 8.0},
    {'pageviews': 24.0,
     'sessions': 10.0,
     'social_network': 'WordPress',
     'users': 8.0},
    {'pageviews': 4.0,
     'sessions': 4.0,
     'social_network': 'Instagram',
     'users': 4.0},
]
