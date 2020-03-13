from datetime import datetime, date, timedelta
from mock import patch, Mock
from pprint import pprint
import unittest
from unittest.mock import Mock, patch

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMock

from utilities import find_last_weekday, find_next_weekday, StatsRange
from scheduler import RunLogger
from Statsdash.analytics import GoogleAnalytics
from Statsdash import mock_repsonses, utils


class TestUtils(unittest.TestCase):

    def test_format_data_rows(self):
        data = {
            'columnHeaders': [{'name': 'ga:pageviews'}, {'name': 'ga:dateHour'}],
            'rows': [['a', 'b'], ['c', 'd']],
        }
        result = utils.format_data_rows(data)
        self.assertEqual(result[0]['ga:pageviews'], 'a')
        self.assertEqual(result[0]['ga:dateHour'], 'b')
        self.assertEqual(result[1]['ga:pageviews'], 'c')
        self.assertEqual(result[1]['ga:dateHour'], 'd')

    def test_convert_to_floats(self):
        data = {'metric_a': 3, 'metric_b': 0}
        metrics = ['metric_a', 'metric_b', 'metric_c']
        result = utils.convert_to_floats(data, metrics)
        self.assertEqual(result['metric_a'], 3.0)
        self.assertEqual(result['metric_b'], 0.0)
        self.assertEqual(result['metric_c'], 0.0)


class TestGoogleAnalytics(unittest.TestCase):

    def setUp(self):
        analytics_discovery = \
            '/Users/john/src/gastatsdash/analytics-discovery.json'
        http = HttpMock(analytics_discovery, {'status': '200'})
        api_key = 'test_api_key'
        service = build(
            'analytics',
            'v3',
            http=http,
            developerKey=api_key,
        )
        self.analytics = GoogleAnalytics(service)
        self.view_id = 'ga:123456789'
        self.stats_date = '2020-03-12'

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_data_ready(self, mock_query_result):
        """
        Data is available if there are 24 rows available.
        """
        mock_query_result.return_value = mock_repsonses.response_ready
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
        mock_query_result.return_value = mock_repsonses.response_not_ready
        self.assertFalse(
            self.analytics.data_available(self.view_id, self.stats_date)
        )
        mock_logger.info.assert_called_with(
            f'view_id {self.view_id} data_available check on '
            f'{self.stats_date} returned rows: '
            f'{mock_repsonses.response_not_ready["rows"]}'
        )

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_data_no_rows(self, mock_logger, mock_query_result):
        """
        Data is not available when there are no rows. Message added to logger.
        """
        mock_query_result.return_value = mock_repsonses.response_no_rows
        self.assertFalse(
            self.analytics.data_available(self.view_id, self.stats_date)
        )
        mock_logger.info.assert_called_with(
            f'view_id {self.view_id} returned no rows for data_available '
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
            f'Unknown error from GA\nType: {str(type(e))} {str(e)}'
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
        mock_query_result.return_value = mock_repsonses.response_ready
        all_reports = self.analytics._fetch_multiple(
            ['1', '2'], self.stats_date, self.stats_date, 'ga:pageviews')
        self.assertEqual(len(all_reports), 2)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_fetch_multiple_log(self, mock_logger, mock_query_result):
        """
        Fetch multiple adds a message to the log when a report has no rows.
        """
        mock_query_result.return_value = mock_repsonses.response_no_rows
        all_reports = self.analytics._fetch_multiple(
            [self.view_id], self.stats_date, self.stats_date, 'ga:pageviews')
        self.assertEqual(len(all_reports), 0)
        mock_logger.debug.assert_called_with(
            f'No data for {self.view_id} on {self.stats_date} - {self.stats_date}.'
            '\nmetrics: ga:pageviews\ndimensions: None.\nfilters: None.'
        )

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_rollup_ids_one_metric(self, mock_query_result):
        """
        Returns a single dict with the aggregated pageviews.
        """
        mock_query_result.return_value = mock_repsonses.response_ready
        aggregated_data = self.analytics.rollup_ids(
            [self.view_id], self.stats_date, self.stats_date, 'ga:pageviews')
        self.assertEqual(aggregated_data, {'ga:pageviews': 126070.0})

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_rollup_ids_two_metrics(self, mock_query_result):
        """
        Returns a single dict with the aggregated pageviews and dateHour.
        """
        mock_query_result.return_value = mock_repsonses.response_ready
        metrics = 'ga:pageviews,ga:dateHour'
        aggregated_data = self.analytics.rollup_ids(
            [self.view_id], self.stats_date, self.stats_date, metrics)
        self.assertEqual(
            aggregated_data,
            # NOTE kinda weird to use dateHour like this but doesn't matter.
            {'ga:dateHour': 48480749076.0, 'ga:pageviews': 126070.0}
        )

    # TODO test match key.

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_rollup_ids_no_data(self, mock_query_result):
        """
        Returns an empty dict if no rows in response.
        """
        mock_query_result.return_value = mock_repsonses.response_no_rows
        aggregated_data = self.analytics.rollup_ids(
            [self.view_id], self.stats_date, self.stats_date, 'ga:pageviews')
        self.assertEqual(aggregated_data, {})


class TestStatsRange(unittest.TestCase):

    def test_date_formatting(self):
        start = datetime(2015, 6, 12)
        end = datetime(2015, 6, 13)
        stats_range = StatsRange("Now", start, end)
        self.assertEqual(stats_range.get_start(), "2015-06-12T00:00:00")
        self.assertEqual(stats_range.get_end(), "2015-06-13T00:00:00")


class TestDateUtils(unittest.TestCase):

    def test_last_weekday_currentWeekdayMatches(self):
        today = datetime(year=2015, month=7, day=2)
        day = "Thursday"
        result = find_last_weekday(today, day)
        self.assertEqual(result, datetime(year=2015, month=7, day=2))

    def test_last_weekday_currentWeekdayBelowDesired(self):
        today = datetime(year=2015, month=7, day=2)
        day = "Friday"
        result = find_last_weekday(today, day)
        self.assertEqual(result, datetime(year=2015, month=6, day=26))

    def test_last_weekday_currentWeekdayAboveDesired(self):
        today = datetime(year=2015, month=7, day=2)
        day = "Wednesday"
        result = find_last_weekday(today, day)
        self.assertEqual(result, datetime(year=2015, month=7, day=1))

    def test_next_weekday_currentWeekdayMatches(self):
        today = datetime(year=2015, month=7, day=2)
        day = "Thursday"
        result = find_next_weekday(today, day)
        self.assertEqual(result, datetime(year=2015, month=7, day=2))

    def test_next_weekday_currentWeekdayBelowDesired(self):
        today = datetime(year=2015, month=7, day=2)
        day = "Friday"
        result = find_next_weekday(today, day)
        self.assertEqual(result, datetime(year=2015, month=7, day=3))

    def test_next_weekday_currentWeekdayAboveDesired(self):
        today = datetime(year=2015, month=7, day=2)
        day = "Wednesday"
        result = find_next_weekday(today, day)
        self.assertEqual(result, datetime(year=2015, month=7, day=8))


class TestNextRun(unittest.TestCase):
    run_log = RunLogger()
    dates = [
        datetime(2016, 1, 31),
        datetime(2015, 1, 31),
        datetime(2015, 3, 1),
        datetime(2015, 3, 23),
        datetime(2016, 1, 1),
        datetime(2016, 2, 28),
        datetime(2016, 2, 29),
        datetime(2016, 12, 1)
    ]

    """test_returns = [
        (datetime(2016, 01, 31), datetime(2016, 03, 01)),
        (datetime(2015, 01, 31), datetime(2015, 03, 01)),
        (datetime(2016, 03, 31), datetime(2016, 04, 01)),
        (datetime(2016, 03, 30), datetime(2016, 04, 01))
    ]"""

    def setUp(self):
        pass

    """Test for MONTHLY reports"""

    def test_monthly_run_on_first_day(self):
        """Test routine to check monthly runs on the first"""
        for d in self.dates:
            last_run = d
            next_run = self.run_log.get_next_run(
                last_run,
                "MONTHLY",
                {"day": 1},
            )
            self.assertEqual(1, next_run.day)

    def test_last_run_last_day(self):
        """Test routine to check works when last run is last day in the month"""
        test_date = [datetime(2016, 3, 31, 00, 00, 00, 1)]
        test_next_run = datetime(2016, 5, 1, 00, 00, 00, 1)
        for d in test_date:
            last_run = d
            next_run = self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
            self.assertEqual(next_run, test_next_run)

    def test_leap_year(self):
        """Test routine to check dates over a leap year"""
        test_date = [datetime(2016, 1, 31)]
        test_next_run = datetime(2016, 3, 1)
        for d in test_date:
            last_run = d
            next_run = self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
            self.assertEqual(next_run, test_next_run)

    def test_not_leap_year(self):
        """Test routine to check dates over a non leap year"""
        test_date = [datetime(2015, 1, 31)]
        test_next_run = datetime(2015, 3, 1)
        for d in test_date:
            last_run = d
            next_run = self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
            self.assertEqual(next_run, test_next_run)

    def test_other_days(self):
        """Test routine to check monthly correct for different day"""
        # repace with range
        days = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
        test_date = datetime(2015, 1, 31)
        for day in days:
            last_run = test_date
            test_next_run = datetime(2015, 3, day)
            next_run = self.run_log.get_next_run(
                last_run,
                "MONTHLY",
                {"day": day}
            )
            self.assertEqual(next_run, test_next_run)

    def test_wrong_days(self):
        """Test routine to check monthly returns error for wrong days"""
        days = [29, 30, 31, 33, 32, 50, 100, 0, -10, -100]
        test_date = datetime(2015, 1, 31)
        for day in days:
            last_run = test_date
            self.assertRaises(
                ValueError,
                self.run_log.get_next_run,
                last_run,
                "MONTHLY",
                {"day": day}
            )

    def test_looping(self):
        """Test routine to check return dates in a sequence"""
        start_date = datetime(2015, 12, 31)
        end_date = datetime(2016, 3, 31)
        runs = []
        periods = [start_date]
        while start_date < end_date:
            next_run = self.run_log.get_next_run(
                start_date,
                "MONTHLY",
                {"day": 1}
            )
            runs.append(next_run)
            start_date = next_run - timedelta(days=1)
            periods.append(start_date)
        self.assertEqual(runs, [datetime(2016, 2, 1), datetime(2016, 3, 1), datetime(2016, 4, 1)])

    def test_override_late_send(self):
        """
        Test routine to check monthly returns override true when next run was
        over 2 days ago
        """
        last_run = datetime(2015, 11, 30)
        self.run_log.get_next_run(last_run, "MONTHLY", {"day": 1})
        self.assertTrue(self.run_log.override_data)

    def test_override_2_days_late(self):
        """
        Test routine to check daily returns override true when last run was
        over 2 days ago
        """
        today = date.today() - timedelta(days=1)
        now = datetime(today.year, today.month, today.day)
        last_run = datetime(2016, 2, 29)
        last_run = now - timedelta(days=2)
        self.run_log.get_next_run(last_run, "DAILY")
        self.assertTrue(self.run_log.override_data)


# class TestScheduler(unittest.TestCase):
#     # mock_run = mock.Mock(spec = RunLogger)
#     # mock_report = mock.Mock(spec = Report)

#     # @patch('scheduler.create_report')
#     # @patch('scheduler.reporting')
#     # @patch('scheduler.RunLogger')
#     def test_run_through(self):
#         """
#         Test routine to check the scheduler run through.
#         """
#         with nested(
#             patch('scheduler.create_report'),
#             patch('scheduler.RunLogger')
#         ) as (mock, run):
#             instance = mock.return_value
#             instance.data_available.return_value = True

#             runlog = run.return_value
#             runlog.override_data = False
#             runlog.get_last_run.return_value = datetime(2016, 3, 1)
#             runlog.get_next_run.return_value = datetime(2016, 4, 1)
#             runlog.record_run.return_value = None


if __name__ == '__main__':
    unittest.main()
