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
