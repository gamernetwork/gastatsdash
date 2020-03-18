from pprint import pprint
from datetime import date
import unittest
from unittest.mock import patch

from Statsdash.aggregate_data import ArticleData, SiteSummaryData, SummaryData
from Statsdash import mock_responses
from Statsdash.stats_range import StatsRange


class TestSummaryData(unittest.TestCase):

    @patch('Statsdash.GA.config.TABLES')
    def setUp(self, mock_tables):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_tables = {
            'fake.site1.com': [{'id': 'ga:12345678'}],
            'fake.site2.com': [{'id': 'ga:87654321'}],
        }
        self.summary_data = SummaryData(self.site_tables, self.period, 'MONTHLY')
        self.expected_keys = [
            'pageviews',
            'users',
            'sessions',
            'pv_per_session',
            'avg_session_time',
            'previous_figure_pageviews',
            'previous_change_pageviews',
            'previous_percentage_pageviews',
            'previous_figure_users',
            'previous_change_users',
            'previous_percentage_users',
            'previous_figure_sessions',
            'previous_change_sessions',
            'previous_percentage_sessions',
            'previous_figure_pv_per_session',
            'previous_change_pv_per_session',
            'previous_percentage_pv_per_session',
            'previous_figure_avg_session_time',
            'previous_change_avg_session_time',
            'previous_percentage_avg_session_time',
            'yearly_figure_pageviews',
            'yearly_change_pageviews',
            'yearly_percentage_pageviews',
            'yearly_figure_users',
            'yearly_change_users',
            'yearly_percentage_users',
            'yearly_figure_sessions',
            'yearly_change_sessions',
            'yearly_percentage_sessions',
            'yearly_figure_pv_per_session',
            'yearly_change_pv_per_session',
            'yearly_percentage_pv_per_session',
            'yearly_figure_avg_session_time',
            'yearly_change_avg_session_time',
            'yearly_percentage_avg_session_time'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        """
        Gets the values for each site and adds them together.
        Also get the averages for values where appropriate.
        """
        mock_query_result.return_value = mock_responses.get_data_for_period_mock_1
        result = self.summary_data._get_data_for_period(self.period)
        self.assertEqual(result['pageviews'], 24640)
        self.assertEqual(result['users'], 1420)
        self.assertEqual(result['sessions'], 2400)
        self.assertEqual(result['pv_per_session'], 6)
        self.assertEqual(result['avg_session_time'], .5)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.aggregate_data.logger')
    def test_get_data_for_period_logger(self, mock_logger, mock_query_result):
        mock_query_result.return_value = {}
        self.summary_data._get_data_for_period(self.period)
        mock_logger.debug.assert_called_with(
            'No data for site fake.site2.com on 2020-03-12 - 2020-03-13'
        )
        self.assertEqual(mock_logger.debug.call_count, 2)

    def test_join_tables(self):
        data_1 = {'pageviews': 24640.0, 'users': 1420.0, 'sessions': 2400.0,
                  'pv_per_session': 6.0, 'avg_session_time': 0.5}
        data_2 = {'pageviews': 24400.0, 'users': 1200.0, 'sessions': 600.0,
                  'pv_per_session': 12.0, 'avg_session_time': 0.8}
        data_3 = {'pageviews': 15000.0, 'users': 800.0, 'sessions': 1200.0,
                  'pv_per_session': 8.0, 'avg_session_time': 0.2}
        all_periods = [data_1, data_2, data_3]

        result = self.summary_data._join_periods(all_periods)
        self.assertTrue(all([k in result.keys() for k in self.expected_keys]))

    @patch('Statsdash.aggregate_data.SummaryData._get_data_for_period')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = {
            'pageviews': 24640.0, 'users': 1420.0, 'sessions': 2400.0,
            'pv_per_session': 6.0, 'avg_session_time': 0.5
        }
        result = self.summary_data.get_table()
        self.assertTrue(all([k in result.keys() for k in self.expected_keys]))


class TestSiteSummaryData(unittest.TestCase):

    @patch('Statsdash.GA.config.TABLES')
    def setUp(self, mock_tables):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_tables = {
            'fake.site1.com': [{'id': 'ga:12345678'}],
            'fake.site2.com': [{'id': 'ga:87654321'}],
        }
        self.site_summary_data = SiteSummaryData(self.site_tables, self.period, 'MONTHLY')
        self.expected_keys = [
            'pageviews',
            'users',
            'sessions',
            'pv_per_session',
            'avg_session_time',
            'previous_figure_pageviews',
            'previous_change_pageviews',
            'previous_percentage_pageviews',
            'previous_figure_users',
            'previous_change_users',
            'previous_percentage_users',
            'previous_figure_sessions',
            'previous_change_sessions',
            'previous_percentage_sessions',
            'previous_figure_pv_per_session',
            'previous_change_pv_per_session',
            'previous_percentage_pv_per_session',
            'previous_figure_avg_session_time',
            'previous_change_avg_session_time',
            'previous_percentage_avg_session_time',
            'yearly_figure_pageviews',
            'yearly_change_pageviews',
            'yearly_percentage_pageviews',
            'yearly_figure_users',
            'yearly_change_users',
            'yearly_percentage_users',
            'yearly_figure_sessions',
            'yearly_change_sessions',
            'yearly_percentage_sessions',
            'yearly_figure_pv_per_session',
            'yearly_change_pv_per_session',
            'yearly_percentage_pv_per_session',
            'yearly_figure_avg_session_time',
            'yearly_change_avg_session_time',
            'yearly_percentage_avg_session_time'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        """
        Gets the values for each site and adds them together.
        Also get the averages for values where appropriate.
        """
        # Return different values for first and second calls.
        mock_query_result.side_effect = [
            mock_responses.get_data_for_period_mock_1,
            mock_responses.get_data_for_period_mock_2,
        ]
        result = self.site_summary_data._get_data_for_period(self.period)
        self.assertTrue(len(result), 2)  # one data set for each site.
        self.assertEqual(result[0]['site'], 'fake.site1.com')
        self.assertEqual(result[1]['site'], 'fake.site2.com')

        self.assertEqual(result[0]['pageviews'], 12320)
        self.assertEqual(result[0]['users'], 710)
        self.assertEqual(result[0]['sessions'], 1200)
        self.assertEqual(result[0]['pv_per_session'], 6)
        self.assertEqual(result[0]['avg_session_time'], 30)

        self.assertEqual(result[1]['pageviews'], 8950)
        self.assertEqual(result[1]['users'], 485)
        self.assertEqual(result[1]['sessions'], 1050)
        self.assertEqual(result[1]['pv_per_session'], 14)
        self.assertEqual(result[1]['avg_session_time'], 20)

        # Reverse order of values and result will be reversed becuase sorted by
        # users.
        mock_query_result.side_effect = [
            mock_responses.get_data_for_period_mock_2,
            mock_responses.get_data_for_period_mock_1,
        ]
        result = self.site_summary_data._get_data_for_period(self.period)
        self.assertTrue(len(result), 2)  # one data set for each site.
        self.assertEqual(result[0]['site'], 'fake.site2.com')
        self.assertEqual(result[1]['site'], 'fake.site1.com')

    #
    # @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    # @patch('Statsdash.aggregate_data.logger')
    # def test_get_data_for_period_logger(self, mock_logger, mock_query_result):
    #     mock_query_result.return_value = {}
    #     self.summary_data._get_data_for_period(self.period)
    #     mock_logger.debug.assert_called_with(
    #         'No data for site fake.site2.com on 2020-03-12 - 2020-03-13'
    #     )
    #     self.assertEqual(mock_logger.debug.call_count, 2)
    #
    # def test_join_tables(self):
    #     data_1 = {'pageviews': 24640.0, 'users': 1420.0, 'sessions': 2400.0,
    #               'pv_per_session': 6.0, 'avg_session_time': 0.5}
    #     data_2 = {'pageviews': 24400.0, 'users': 1200.0, 'sessions': 600.0,
    #               'pv_per_session': 12.0, 'avg_session_time': 0.8}
    #     data_3 = {'pageviews': 15000.0, 'users': 800.0, 'sessions': 1200.0,
    #               'pv_per_session': 8.0, 'avg_session_time': 0.2}
    #     all_periods = [data_1, data_2, data_3]
    #
    #     result = self.summary_data._join_periods(all_periods)
    #     self.assertTrue(all([k in result.keys() for k in self.expected_keys]))
    #
    # @patch('Statsdash.aggregate_data.SiteSummaryData._get_data_for_period')
    # def test_get_table(self, mock_query_result):
    #     mock_query_result.return_value = {
    #         'pageviews': 24640.0, 'users': 1420.0, 'sessions': 2400.0,
    #         'pv_per_session': 6.0, 'avg_session_time': 0.5
    #     }
    #     result = self.site_summary_data.get_table()
    #     print(result)
    #     self.assertTrue(all([k in result.keys() for k in self.expected_keys]))


class TestArticleData(unittest.TestCase):

    @patch('Statsdash.GA.config.TABLES')
    def setUp(self, mock_tables):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_tables = {
            'fake.site1.com': [{'id': 'ga:12345678'}],
            'fake.site2.com': [{'id': 'ga:87654321'}],
        }
        self.site_summary_data = ArticleData(self.site_tables, self.period, 'MONTHLY')
        self.expected_keys = [
            'pageviews',
            'users',
            'sessions',
            'pv_per_session',
            'avg_session_time',
            'previous_figure_pageviews',
            'previous_change_pageviews',
            'previous_percentage_pageviews',
            'previous_figure_users',
            'previous_change_users',
            'previous_percentage_users',
            'previous_figure_sessions',
            'previous_change_sessions',
            'previous_percentage_sessions',
            'previous_figure_pv_per_session',
            'previous_change_pv_per_session',
            'previous_percentage_pv_per_session',
            'previous_figure_avg_session_time',
            'previous_change_avg_session_time',
            'previous_percentage_avg_session_time',
            'yearly_figure_pageviews',
            'yearly_change_pageviews',
            'yearly_percentage_pageviews',
            'yearly_figure_users',
            'yearly_change_users',
            'yearly_percentage_users',
            'yearly_figure_sessions',
            'yearly_change_sessions',
            'yearly_percentage_sessions',
            'yearly_figure_pv_per_session',
            'yearly_change_pv_per_session',
            'yearly_percentage_pv_per_session',
            'yearly_figure_avg_session_time',
            'yearly_change_avg_session_time',
            'yearly_percentage_avg_session_time'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        """
        Gets the values for each site and adds them together.
        Also get the averages for values where appropriate.
        """
        # Return different values for first and second calls.
        mock_query_result.side_effect = [
            mock_responses.get_data_for_period_mock_1,
            mock_responses.get_data_for_period_mock_2,
        ]
        # TODO get a sample response for this.
        result = self.site_summary_data._get_data_for_period(self.period)
        # self.assertTrue(len(result), 2)  # one data set for each site.
        # self.assertEqual(result[0]['site'], 'fake.site1.com')
        # self.assertEqual(result[1]['site'], 'fake.site2.com')
        #
        # self.assertEqual(result[0]['pageviews'], 12320)
        # self.assertEqual(result[0]['users'], 710)
        # self.assertEqual(result[0]['sessions'], 1200)
        # self.assertEqual(result[0]['pv_per_session'], 6)
        # self.assertEqual(result[0]['avg_session_time'], 30)
        #
        # self.assertEqual(result[1]['pageviews'], 8950)
        # self.assertEqual(result[1]['users'], 485)
        # self.assertEqual(result[1]['sessions'], 1050)
        # self.assertEqual(result[1]['pv_per_session'], 14)
        # self.assertEqual(result[1]['avg_session_time'], 20)

    def test_sample(self):

        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 18),
            date(2020, 3, 18)
        )
        self.site_tables = {
            'rockpapershotgun.com': [{'id': 'ga:130215556'}],
        }
        self.site_summary_data = ArticleData(self.site_tables, self.period, 'DAILY')
        result = self.site_summary_data._get_data_for_period(self.period)
        pprint(result)

