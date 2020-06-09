import os

from mock import Mock
import unittest
from unittest.mock import patch

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMock

from Statsdash.tests.data import mock_responses
from Statsdash.analytics import GoogleAnalytics, YouTubeAnalytics


class TestGoogleAnalytics(unittest.TestCase):

    def setUp(self):
        analytics_discovery = os.path.join(os.path.dirname(__file__), 'data/analytics-discovery.json')

        http = HttpMock(analytics_discovery, {'status': '200'})
        api_key = 'test_api_key'
        service = build(
            'analytics',
            'v3',
            http=http,
            developerKey=api_key,
        ).data().ga()
        self.analytics = GoogleAnalytics(service)
        self._id = 'ga:123456789'
        self.stats_date = '2020-03-12'

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_data_ready(self, mock_query_result):
        """
        Data is available if there are 24 rows available.
        """
        mock_query_result.return_value = mock_responses.response_ready
        self.assertTrue(
            self.analytics.data_available('ga:123456789', '2020-03-12')
        )

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_data_not_yet_avaliable(self, mock_logger, mock_query_result):
        """
        Data is not available when there are fewer than 24 rows available.
        Message added to logger.
        """
        mock_query_result.return_value = mock_responses.response_not_ready
        self.assertFalse(
            self.analytics.data_available(self._id, self.stats_date)
        )
        mock_logger.info.assert_called_with(
            f'ID {self._id} data_available check on '
            f'{self.stats_date} returned rows: '
            f'{mock_responses.response_not_ready["rows"]}'
        )

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_data_no_rows(self, mock_logger, mock_query_result):
        """
        Data is not available when there are no rows. Message added to logger.
        """
        mock_query_result.return_value = mock_responses.response_no_rows
        self.assertFalse(
            self.analytics.data_available(self._id, self.stats_date)
        )
        mock_logger.info.assert_called_with(
            f'ID {self._id} returned no rows for data_available '
            f'check on {self.stats_date}'
        )

    @patch('Statsdash.analytics.logger')
    def test_execute_query_http_error(self, mock_logger):
        """
        If a HttpError occurs during the `query.execute()` method, a warning
        message is added to the logger.
        """
        query = Mock()
        response = Mock(status=500)
        e = HttpError(response, b'content')
        query.execute.side_effect = e
        self.analytics._execute_query(query)
        mock_logger.warning.assert_called_with(
            f'HTTP error {e.resp.status} occurred:\n{e.content}'
        )

    @patch('Statsdash.analytics.logger')
    def test_execute_query_other_error(self, mock_logger):
        """
        If any other error occurs during the `query.execute()` method, a
        different warning message is added to the logger.
        """
        query = Mock()
        e = TypeError('Something went wrong.')
        query.execute.side_effect = e
        self.analytics._execute_query(query)
        mock_logger.warning.assert_called_with(
            f'Unknown error from Google Analytics\nType: {str(type(e))} '
            f'{str(e)}'
        )

    def test_execute_no_exception(self):
        """
        If no exceptions occur during execution, the output of
        `query.execute()` is returned.
        """
        output = 'Return value'
        query = Mock()
        query.execute.return_value = output
        self.assertEqual(self.analytics._execute_query(query), output)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_fetch_multiple(self, mock_query_result):
        """

        """
        mock_query_result.return_value = mock_responses.response_ready
        all_reports = self.analytics._fetch_multiple(
            ['1', '2'], self.stats_date, self.stats_date, 'ga:pageviews')
        self.assertEqual(len(all_reports), 2)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_fetch_multiple_log(self, mock_logger, mock_query_result):
        """
        Fetch multiple adds a message to the log when a report has no rows.
        """
        mock_query_result.return_value = mock_responses.response_no_rows
        all_reports = self.analytics._fetch_multiple(
            [self._id], self.stats_date, self.stats_date, ['ga:pageviews'])
        self.assertEqual(len(all_reports), 0)
        mock_logger.debug.assert_called_with(
            f'No data for {self._id} on {self.stats_date} - {self.stats_date}.'
            '\nmetrics: ga:pageviews\ndimensions: None.\nfilters: None.'
        )

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_one_metric(self, mock_query_result):
        """
        Returns a single dict inside a list with the aggregated pageviews.
        """
        mock_query_result.return_value = mock_responses.response_ready
        aggregated_data = self.analytics.get_data(
            [self._id], self.stats_date, self.stats_date, ['ga:pageviews'])
        self.assertEqual(aggregated_data, [{'ga:pageviews': 126070.0}])

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_two_metrics(self, mock_query_result):
        """
        Returns a single dict inside a list with the aggregated pageviews and
        dateHour.
        """
        mock_query_result.return_value = mock_responses.response_ready
        metrics = ['ga:pageviews', 'ga:dateHour']
        aggregated_data = self.analytics.get_data(
            [self._id], self.stats_date, self.stats_date, metrics)
        self.assertEqual(
            aggregated_data,
            [{'ga:dateHour': 48480749076.0, 'ga:pageviews': 126070.0}]
        )

    # TODO test match key.

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_no_data(self, mock_query_result):
        """
        Returns `None` if no rows in response.
        """
        mock_query_result.return_value = mock_responses.response_no_rows
        aggregated_data = self.analytics.get_data(
            [self._id], self.stats_date, self.stats_date, 'ga:pageviews')
        self.assertEqual(aggregated_data, [])


class TestYouTubeAnalytics(unittest.TestCase):

    def setUp(self):
        analytics_discovery = os.path.join(os.path.dirname(__file__), 'data/youtube-analytics-discovery.json')

        http = HttpMock(analytics_discovery, {'status': '200'})
        api_key = 'test_api_key'
        service = build(
            'youtubeAnalytics',
            'v2',
            http=http,
            developerKey=api_key,
        ).reports()
        self.analytics = YouTubeAnalytics(service, 'CONTENT_OWNER')
        self._id = '123456789'
        self.stats_date = '2020-03-12'

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_data_ready(self, mock_query_result):
        """
        Data is available if there are any rows.
        """
        # TODO replace this with YouTube Analytics API response
        mock_query_result.return_value = mock_responses.response_ready
        self.assertTrue(
            self.analytics.data_available(self._id, '2020-03-12')
        )

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_data_no_rows(self, mock_logger, mock_query_result):
        """
        Data is not available when there are no rows. Message added to logger.
        """
        mock_query_result.return_value = mock_responses.response_no_rows
        self.assertFalse(
            self.analytics.data_available(self._id, self.stats_date)
        )
        mock_logger.info.assert_called_with(
            f'ID {self._id} returned no rows for data_available '
            f'check on {self.stats_date}'
        )

    @patch('Statsdash.analytics.logger')
    def test_execute_query_http_error(self, mock_logger):
        """
        If a HttpError occurs during the `query.execute()` method, a warning
        message is added to the logger.
        """
        query = Mock()
        response = Mock(status=500)
        e = HttpError(response, b'content')
        query.execute.side_effect = e
        self.analytics._execute_query(query)
        mock_logger.warning.assert_called_with(
            f'HTTP error {e.resp.status} occurred:\n{e.content}'
        )

    @patch('Statsdash.analytics.logger')
    def test_execute_query_other_error(self, mock_logger):
        """
        If any other error occurs during the `query.execute()` method, a
        different warning message is added to the logger.
        """
        query = Mock()
        e = TypeError('Something went wrong.')
        query.execute.side_effect = e
        self.analytics._execute_query(query)
        mock_logger.warning.assert_called_with(
            f'Unknown error from YouTube Analytics\nType: {str(type(e))} '
            f'{str(e)}'
        )

    def test_execute_no_exception(self):
        """
        If no exceptions occur during execution, the output of
        `query.execute()` is returned.
        """
        output = 'Return value'
        query = Mock()
        query.execute.return_value = output
        self.assertEqual(self.analytics._execute_query(query), output)

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_fetch_multiple(self, mock_query_result):
        """

        """
        mock_query_result.return_value = mock_responses.response_ready
        all_reports = self.analytics._fetch_multiple(
            ['1', '2'],
            self.stats_date,
            self.stats_date,
            YouTubeAnalytics.Metrics.views
        )
        self.assertEqual(len(all_reports), 2)

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_fetch_multiple_log(self, mock_logger, mock_query_result):
        """
        Fetch multiple adds a message to the log when a report has no rows.
        """
        mock_query_result.return_value = mock_responses.response_no_rows
        all_reports = self.analytics._fetch_multiple(
            [self._id],
            self.stats_date,
            self.stats_date,
            [YouTubeAnalytics.Metrics.views[0]]
        )
        self.assertEqual(len(all_reports), 0)
        mock_logger.debug.assert_called_with(
            f'No data for {self._id} on {self.stats_date} - {self.stats_date}.'
            f'\nmetrics: {YouTubeAnalytics.Metrics.views[0]}\ndimensions: '
            'None.\nfilters: None.'
        )

    def test_prepare_no_filters(self):
        _id = '123'
        filters = None
        result = self.analytics._prepare_filters(_id, filters)
        self.assertEqual(result, 'channel==123')

    def test_prepare_filters(self):
        _id = '123'
        filters = 'some-filter==x'
        result = self.analytics._prepare_filters(_id, filters)
        self.assertEqual(result, 'some-filter==x;channel==123')


    # TODO with real data
    # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # def test_get_data_one_metric(self, mock_query_result):
    #     """
    #     Returns a single dict with the aggregated pageviews.
    #     """
    #     mock_query_result.return_value = mock_responses.response_ready
    #     aggregated_data = self.analytics.get_data(
    #         [self._id], self.stats_date, self.stats_date, 'ga:pageviews')
    #     self.assertEqual(aggregated_data, {'ga:pageviews': 126070.0})
    #
    # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # def test_get_data_two_metrics(self, mock_query_result):
    #     """
    #     Returns a single dict with the aggregated pageviews and dateHour.
    #     """
    #     mock_query_result.return_value = mock_responses.response_ready
    #     metrics = 'ga:pageviews,ga:dateHour'
    #     aggregated_data = self.analytics.get_data(
    #         [self._id], self.stats_date, self.stats_date, metrics)
    #     self.assertEqual(
    #         aggregated_data,
    #         # NOTE kinda weird to use dateHour like this but doesn't matter.
    #         {'ga:dateHour': 48480749076.0, 'ga:pageviews': 126070.0}
    #     )
    #
    # # TODO test match key.
    #
    # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # def test_get_data_no_data(self, mock_query_result):
    #     """
    #     Returns an empty dict if no rows in response.
    #     """
    #     mock_query_result.return_value = mock_responses.response_no_rows
    #     aggregated_data = self.analytics.get_data(
    #         [self._id], self.stats_date, self.stats_date, 'ga:pageviews')
    #     self.assertEqual(aggregated_data, {})


# class TestYouTubeAPI(unittest.TestCase):
#
#     def setUp(self):
#         analytics_discovery = os.path.join(os.path.dirname(__file__), 'data/youtube-data-discovery.json')
#         http = HttpMock(analytics_discovery, {'status': '200'})
#         api_key = 'test_api_key'
#         YOUTUBE_API_SERVICE_NAME = 'youtube'
#         YOUTUBE_API_VERSION = 'v3'
#         service = build(
#             YOUTUBE_API_SERVICE_NAME,
#             YOUTUBE_API_VERSION,
#             http=http,
#             developerKey=api_key,
#         )
#         data_resource = service.videos()
#         result = data_resource.list(
#             id='87MNuBgeg34',
#             part='snippet'
#         )
#         result = result.execute()
#         pprint(result)
#         self.analytics = YouTubeChannels(data_resource)
#         self._id = '123456789'
#         self.stats_date = '2020-03-12'
#
#     def test_data_ready(self):
#         """
#         Data is available if there are any rows.
#         """

        # mock_query_result.return_value = mock_responses.response_ready
        # self.assertTrue(
        #     self.analytics.data_available(self._id, '2020-03-12')
        # )
    #
    # @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    # @patch('Statsdash.analytics.logger')
    # def test_data_no_rows(self, mock_logger, mock_query_result):
    #     """
    #     Data is not available when there are no rows. Message added to logger.
    #     """
    #     mock_query_result.return_value = mock_responses.response_no_rows
    #     self.assertFalse(
    #         self.analytics.data_available(self._id, self.stats_date)
    #     )
    #     mock_logger.info.assert_called_with(
    #         f'ID {self._id} returned no rows for data_available '
    #         f'check on {self.stats_date}'
    #     )

    # @patch('Statsdash.analytics.logger')
    # def test_execute_query_http_error(self, mock_logger):
    #     """
    #     If a HttpError occurs during the `query.execute()` method, a warning
    #     message is added to the logger.
    #     """
    #     query = Mock()
    #     response = Mock(status=500)
    #     e = HttpError(response, b'content')
    #     query.execute.side_effect = e
    #     self.analytics._execute_query(query)
    #     mock_logger.warning.assert_called_with(
    #         f'HTTP error {e.resp.status} occurred:\n{e.content}'
    #     )
    #
    # @patch('Statsdash.analytics.logger')
    # def test_execute_query_other_error(self, mock_logger):
    #     """
    #     If any other error occurs during the `query.execute()` method, a
    #     different warning message is added to the logger.
    #     """
    #     query = Mock()
    #     e = TypeError('Something went wrong.')
    #     query.execute.side_effect = e
    #     self.analytics._execute_query(query)
    #     mock_logger.warning.assert_called_with(
    #         f'Unknown error from YouTube Analytics\nType: {str(type(e))} '
    #         f'{str(e)}'
    #     )
    #
    # def test_execute_no_exception(self):
    #     """
    #     If no exceptions occur during execution, the output of
    #     `query.execute()` is returned.
    #     """
    #     output = 'Return value'
    #     query = Mock()
    #     query.execute.return_value = output
    #     self.assertEqual(self.analytics._execute_query(query), output)
    #
    # @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    # def test_fetch_multiple(self, mock_query_result):
    #     """
    #
    #     """
    #     mock_query_result.return_value = mock_responses.response_ready
    #     all_reports = self.analytics._fetch_multiple(
    #         ['1', '2'],
    #         self.stats_date,
    #         self.stats_date,
    #         YouTubeAnalytics.Metrics.views
    #     )
    #     self.assertEqual(len(all_reports), 2)
    #
    # @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    # @patch('Statsdash.analytics.logger')
    # def test_fetch_multiple_log(self, mock_logger, mock_query_result):
    #     """
    #     Fetch multiple adds a message to the log when a report has no rows.
    #     """
    #     mock_query_result.return_value = mock_responses.response_no_rows
    #     all_reports = self.analytics._fetch_multiple(
    #         [self._id],
    #         self.stats_date,
    #         self.stats_date,
    #         YouTubeAnalytics.Metrics.views
    #     )
    #     self.assertEqual(len(all_reports), 0)
    #     mock_logger.debug.assert_called_with(
    #         f'No data for {self._id} on {self.stats_date} - {self.stats_date}.'
    #         f'\nmetrics: {YouTubeAnalytics.Metrics.views}\ndimensions: '
    #         'None.\nfilters: None.'
    #     )
    #
    # # TODO with real data
    # # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # # def test_get_data_one_metric(self, mock_query_result):
    # #     """
    # #     Returns a single dict with the aggregated pageviews.
    # #     """
    # #     mock_query_result.return_value = mock_responses.response_ready
    # #     aggregated_data = self.analytics.get_data(
    # #         [self._id], self.stats_date, self.stats_date, 'ga:pageviews')
    # #     self.assertEqual(aggregated_data, {'ga:pageviews': 126070.0})
    # #
    # # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # # def test_get_data_two_metrics(self, mock_query_result):
    # #     """
    # #     Returns a single dict with the aggregated pageviews and dateHour.
    # #     """
    # #     mock_query_result.return_value = mock_responses.response_ready
    # #     metrics = 'ga:pageviews,ga:dateHour'
    # #     aggregated_data = self.analytics.get_data(
    # #         [self._id], self.stats_date, self.stats_date, metrics)
    # #     self.assertEqual(
    # #         aggregated_data,
    # #         # NOTE kinda weird to use dateHour like this but doesn't matter.
    # #         {'ga:dateHour': 48480749076.0, 'ga:pageviews': 126070.0}
    # #     )
    # #
    # # # TODO test match key.
    # #
    # # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # # def test_get_data_no_data(self, mock_query_result):
    # #     """
    # #     Returns an empty dict if no rows in response.
    # #     """
    # #     mock_query_result.return_value = mock_responses.response_no_rows
    # #     aggregated_data = self.analytics.get_data(
    # #         [self._id], self.stats_date, self.stats_date, 'ga:pageviews')
    # #     self.assertEqual(aggregated_data, {})

