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
                    'profileId': '130215556',
                    'profileName': 'Without multipages www.fakesite.com/',
                    'tableId': 'ga:130215556',
                    'webPropertyId': 'UA-2667859-1'},
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
},
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
