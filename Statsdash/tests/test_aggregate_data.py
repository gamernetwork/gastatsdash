from pprint import pprint
from datetime import date
import unittest
from unittest.mock import patch

from Statsdash.aggregate_data import google, youtube
from Statsdash.tests.data import mock_responses
from Statsdash.stats_range import StatsRange

google_tables = {
    'fake.site1.com': [{'id': 'ga:12345678'}],
    'fake.site2.com': [{'id': 'ga:87654321'}],
}
google_sites = list(google_tables.keys())

youtube_tables = {
    'channel_1': '12345678',
    'channel_2': '87654321',
}
youtube_sites = list(youtube_tables.keys())

expected_keys = [
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


class TestGoogleSummaryData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.summary_data = google.SummaryData({}, google_sites, self.period, 'MONTHLY')

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        """
        Gets the values for each site and adds them together.
        Also get the averages for values where appropriate.
        """
        mock_query_result.return_value = mock_responses.get_data_for_period_mock_1
        result = self.summary_data._get_data_for_period(self.period)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['pageviews'], 24640)
        self.assertEqual(result[0]['users'], 1420)
        self.assertEqual(result[0]['sessions'], 2400)
        self.assertEqual(result[0]['pv_per_session'], 6)
        self.assertEqual(result[0]['avg_session_time'], .5)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_get_data_for_period_logger(self, mock_logger, mock_query_result):
        mock_query_result.return_value = {}
        self.summary_data._get_data_for_period(self.period)
        mock_logger.debug.assert_called_with((
            "No data for {'id': 'ga:87654321'} on 2020-03-12 - 2020-03-13.\n"
            "metrics: ga:pageviews,ga:users,ga:sessions,"
            "ga:pageviewsPerSession,ga:avgSessionDuration\ndimensions: None."
            "\nfilters: None.")
        )
        self.assertEqual(mock_logger.debug.call_count, 2)

    def test_join_tables(self):
        data_1 = [{'pageviews': 24640.0, 'users': 1420.0, 'sessions': 2400.0,
                  'pv_per_session': 6.0, 'avg_session_time': 0.5}]
        data_2 = [{'pageviews': 24400.0, 'users': 1200.0, 'sessions': 600.0,
                  'pv_per_session': 12.0, 'avg_session_time': 0.8}]
        data_3 = [{'pageviews': 15000.0, 'users': 800.0, 'sessions': 1200.0,
                  'pv_per_session': 8.0, 'avg_session_time': 0.2}]
        all_periods = [data_1, data_2, data_3]

        result = self.summary_data._join_periods(all_periods)[0]
        self.assertTrue(all([k in result.keys() for k in expected_keys]))

    @patch('Statsdash.aggregate_data.google.SummaryData._get_data_for_period')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.summary_get_table_data
        result = self.summary_data.get_table()[0]
        self.assertTrue(all([k in result.keys() for k in expected_keys]))
        self.assertEqual(result, mock_responses.summary_expected_data)


class TestGoogleSiteSummaryData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_summary_data = google.SiteSummaryData({}, google_sites, self.period, 'MONTHLY')


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

        # Reverse order of values and result will be reversed because sorted by
        # users.
        mock_query_result.side_effect = [
            mock_responses.get_data_for_period_mock_2,
            mock_responses.get_data_for_period_mock_1,
        ]
        result = self.site_summary_data._get_data_for_period(self.period)
        self.assertTrue(len(result), 2)  # one data set for each site.
        self.assertEqual(result[0]['site'], 'fake.site2.com')
        self.assertEqual(result[1]['site'], 'fake.site1.com')

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    @patch('Statsdash.analytics.logger')
    def test_get_data_for_period_logger(self, mock_logger, mock_query_result):
        mock_query_result.return_value = {}
        self.site_summary_data._get_data_for_period(self.period)
        mock_logger.debug.assert_called_with((
            "No data for {'id': 'ga:87654321'} on 2020-03-12 - 2020-03-13."
            "\nmetrics: ga:pageviews,ga:users,ga:sessions,ga:pageviewsPerSession,"
            "ga:avgSessionDuration\ndimensions: None.\nfilters: None."
        ))
        self.assertEqual(mock_logger.debug.call_count, 2)

    def test_join_periods(self):
        data = mock_responses.mock_join_periods_data
        result = self.site_summary_data._join_periods(data)
        for site_data in result:
            self.assertTrue(all([k in site_data.keys() for k in expected_keys]))
            self.assertTrue('site' in site_data.keys())

    @patch('Statsdash.aggregate_data.google.SiteSummaryData._get_data_for_period')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.site_summary_get_table_data
        result = self.site_summary_data.get_table()
        for site_data in result:
            self.assertTrue(all([k in site_data.keys() for k in expected_keys]))


class TestGoogleArticleData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.article_data = google.ArticleData({}, google_sites, self.period, 'MONTHLY')


    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_article_get_data_for_period_one_site(self, mock_query_result):

        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 18),
            date(2020, 3, 18)
        )
        mock_query_result.side_effect = [
            mock_responses.article_query_response_1,
            {}  # no data for second site
        ]
        expected_data = [
            {
                'host': 'www.fake.site1.com',
                'pageviews': 15200.0,
                'path': '/link/to/article-1/',
                'site_path': 'fake.site1.com/link/to/article-1/',
                'title': 'Article 1'
            },
            {
                'host': 'www.fake.site1.com',
                'pageviews': 16800.0,
                'path': '/link/to/article-2/',
                'site_path': 'fake.site1.com/link/to/article-2/',
                'title': 'Article 2'
            },
        ]
        result = self.article_data._get_data_for_period(self.period)
        self.assertEqual(result, expected_data)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_article_get_data_for_period_two_sites(self, mock_query_result):

        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 18),
            date(2020, 3, 18)
        )
        mock_query_result.side_effect = [
            mock_responses.article_query_response_1,
            mock_responses.article_query_response_2,
        ]
        expected_data = [
            {
                'host': 'www.fake.site1.com',
                'pageviews': 15200.0,
                'path': '/link/to/article-1/',
                'site_path': 'fake.site1.com/link/to/article-1/',
                'title': 'Article 1'
            },
            {
                'host': 'www.fake.site1.com',
                'pageviews': 16800.0,
                'path': '/link/to/article-2/',
                'site_path': 'fake.site1.com/link/to/article-2/',
                'title': 'Article 2'
            },
            {
                'host': 'www.fake.site2.com',
                'pageviews': 16800.0,
                'path': '/link/to/article-3/',
                'site_path': 'fake.site2.com/link/to/article-3/',
                'title': 'Article 3'
            },
            {
                'host': 'www.fake.site2.com',
                'pageviews': 45300.0,
                'path': '/link/to/article-4/',
                'site_path': 'fake.site2.com/link/to/article-4/',
                'title': 'Article 4'
            },
        ]
        result = self.article_data._get_data_for_period(self.period)
        self.assertEqual(result, expected_data)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_article_get_table(self, mock_query_result):

        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 18),
            date(2020, 3, 18)
        )
        mock_query_result.return_value = mock_responses.article_query_response_1
        result = self.article_data.get_table()
        self.assertEqual(len(result), 4)
        self.assertEqual(result, mock_responses.article_table_expected_data)


class TestGoogleCountryData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.country_data = google.CountryData({}, google_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'country', 'pageviews', 'users', 'previous_figure_pageviews',
            'previous_change_pageviews', 'previous_percentage_pageviews',
            'previous_figure_users', 'previous_change_users',
            'previous_percentage_users', 'yearly_figure_pageviews',
            'yearly_change_pageviews', 'yearly_percentage_pageviews',
            'yearly_figure_users', 'yearly_change_users',
            'yearly_percentage_users'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_country_get_data_for_period(self, mock_query_result):

        def mock_run_report(*args, **kwargs):
            if kwargs['filters'].startswith('ga:country=~'):
                return mock_responses.country_report
            return mock_responses.rest_of_world_country_report

        mock_query_result.side_effect = mock_run_report
        expected_data = mock_responses.countries_expected_data_row
        result = self.country_data._get_data_for_period(self.period)
        self.assertEqual(expected_data, result)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_country_get_data_for_period_no_row(self, mock_query_result):
        def mock_run_report(*args, **kwargs):
            if kwargs['filters'].startswith('ga:country=~'):
                return mock_responses.country_report
            return None
        mock_query_result.side_effect = mock_run_report
        expected_data = mock_responses.countries_expected_data_no_row
        result = self.country_data._get_data_for_period(self.period)
        self.assertEqual(expected_data, result)

    def test_join_tables(self):
        all_periods = [mock_responses.countries_expected_data_row] * 3
        result = self.country_data._join_periods(all_periods)

        for data in result:
            self.assertTrue(all([k in data.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        def mock_run_report(*args, **kwargs):
            if kwargs['filters'].startswith('ga:country=~'):
                return mock_responses.country_report
            return mock_responses.rest_of_world_country_report
        mock_query_result.side_effect = mock_run_report
        result = self.country_data.get_table()[0]
        self.assertTrue(all([k in result.keys() for k in self.expected_keys]))


class TestGoogleTrafficSourceData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.traffic_source_data = google.TrafficSourceData({}, google_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'pageviews', 'source_medium', 'users', 'previous_figure_pageviews',
            'previous_change_pageviews', 'previous_percentage_pageviews',
            'previous_figure_users', 'previous_change_users',
            'previous_percentage_users', 'yearly_figure_pageviews',
            'yearly_change_pageviews', 'yearly_percentage_pageviews',
            'yearly_figure_users', 'yearly_change_users',
            'yearly_percentage_users'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_country_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.traffic_source_data
        expected_data = mock_responses.expected_traffic_source_data
        result = self.traffic_source_data._get_data_for_period(self.period)
        self.assertEqual(expected_data, result)

    def test_join_tables(self):
        all_periods = [mock_responses.expected_traffic_source_data] * 3
        result = self.traffic_source_data._join_periods(all_periods)
        for data in result:
            self.assertTrue(all([k in data.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.traffic_source_data
        result = self.traffic_source_data.get_table()
        self.assertEqual(result, mock_responses.traffic_expected_data)

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_table_limit_works(self, mock_query_result):
        mock_query_result.return_value = mock_responses.traffic_source_data
        result = self.traffic_source_data.get_table()
        self.assertEqual(len(result), 7)
        self.traffic_source_data.limit = 5
        result = self.traffic_source_data.get_table()
        self.assertEqual(len(result), 5)


class TestGoogleDeviceData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.social_data = google.DeviceData({}, google_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'device_category', 'users', 'previous_figure_users',
            'previous_change_users', 'previous_percentage_users',
            'yearly_figure_users', 'yearly_change_users',
            'yearly_percentage_users'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_device_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.device_response
        expected_data = mock_responses.device_data_expected_1
        result = self.social_data._get_data_for_period(self.period)

        self.assertEqual(expected_data, result)

    def test_join_tables(self):
        all_periods = [mock_responses.device_data_expected_1] * 3
        result = self.social_data._join_periods(all_periods)
        for data in result:
            self.assertTrue(all([k in data.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.device_response
        result = self.social_data.get_table()
        for data in result:
            self.assertTrue(all([k in data.keys() for k in self.expected_keys]))


class TestGoogleSocialData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.google.TABLES', google_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.social_data = google.SocialData({}, google_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'pageviews', 'sessions', 'social_network', 'users',
            'previous_figure_pageviews', 'previous_change_pageviews',
            'previous_percentage_pageviews', 'previous_figure_users',
            'previous_change_users', 'previous_percentage_users',
            'previous_figure_sessions', 'previous_change_sessions',
            'previous_percentage_sessions', 'yearly_figure_pageviews',
            'yearly_change_pageviews', 'yearly_percentage_pageviews',
            'yearly_figure_users', 'yearly_change_users',
            'yearly_percentage_users', 'yearly_figure_sessions',
            'yearly_change_sessions', 'yearly_percentage_sessions'
        ]

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_social_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.social_response
        expected_data = [
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
        result = self.social_data._get_data_for_period(self.period)
        self.assertEqual(expected_data, result)
        self.assertEqual(len(result), 15)

    def test_join_tables(self):
        all_periods = [mock_responses.social_data_expected_1] * 3
        result = self.social_data._join_periods(all_periods)
        for data in result:
            self.assertTrue(all([k in data.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.GoogleAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.social_response
        result = self.social_data.get_table()
        for data in result:
            self.assertTrue(all([k in data.keys() for k in self.expected_keys]))


class TestYouTubeChannelSummaryData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.youtube.TABLES', youtube_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.channel_summary_data = youtube.ChannelSummaryData({}, youtube_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'channel', 'estimated_minutes_watched', 'subscriber_change',
            'subscribers_gained', 'subscribers_lost',
            'previous_figure_estimated_minutes_watched',
            'previous_change_estimated_minutes_watched',
            'previous_percentage_estimated_minutes_watched',
            'previous_figure_subscribers_gained',
            'previous_change_subscribers_gained',
            'previous_percentage_subscribers_gained',
            'previous_figure_subscribers_lost',
            'previous_change_subscribers_lost',
            'previous_percentage_subscribers_lost',
            'yearly_figure_estimated_minutes_watched',
            'yearly_change_estimated_minutes_watched',
            'yearly_percentage_estimated_minutes_watched',
            'yearly_figure_subscribers_gained',
            'yearly_change_subscribers_gained',
            'yearly_percentage_subscribers_gained',
            'yearly_figure_subscribers_lost',
            'yearly_change_subscribers_lost',
            'yearly_percentage_subscribers_lost'
        ]

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_channel_summary_report_response
        expected_data = mock_responses.youtube_channel_summary_expected_data_for_period
        result = self.channel_summary_data._get_data_for_period(self.period)
        self.assertEqual(
            result[0]['subscriber_change'],
            result[0]['subscribers_gained'] - result[0]['subscribers_lost']
        )
        self.assertEqual(result, expected_data)

    def test_join_tables(self):
        all_periods = [mock_responses.youtube_channel_summary_expected_data_for_period] * 3
        result = self.channel_summary_data._join_periods(all_periods)
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_country_report_response
        result = self.channel_summary_data.get_table()
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))


class TestYouTubeChannelStatsData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.youtube.TABLES', youtube_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.channel_stats_data = youtube.ChannelStatsData({}, youtube_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'channel', 'comment_rate', 'comments', 'dislike_ratio',
            'dislikes', 'like_rate', 'like_ratio', 'likes', 'shares',
            'shares_rate', 'subs_rate', 'subscribers_gained', 'views',
            'previous_figure_views', 'previous_change_views',
            'previous_percentage_views', 'previous_figure_likes',
            'previous_change_likes', 'previous_percentage_likes',
            'previous_figure_dislikes', 'previous_change_dislikes',
            'previous_percentage_dislikes', 'previous_figure_comments',
            'previous_change_comments', 'previous_percentage_comments',
            'previous_figure_shares', 'previous_change_shares',
            'previous_percentage_shares',
            'previous_figure_subscribers_gained',
            'previous_change_subscribers_gained',
            'previous_percentage_subscribers_gained', 'yearly_figure_views',
            'yearly_change_views', 'yearly_percentage_views',
            'yearly_figure_likes', 'yearly_change_likes',
            'yearly_percentage_likes', 'yearly_figure_dislikes',
            'yearly_change_dislikes', 'yearly_percentage_dislikes',
            'yearly_figure_comments', 'yearly_change_comments',
            'yearly_percentage_comments', 'yearly_figure_shares',
            'yearly_change_shares', 'yearly_percentage_shares',
            'yearly_figure_subscribers_gained',
            'yearly_change_subscribers_gained',
            'yearly_percentage_subscribers_gained'
        ]

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_channel_stats_report_response
        expected_data = mock_responses.youtube_channel_stats_expected_data_for_period
        result = self.channel_stats_data._get_data_for_period(self.period)
        self.assertEqual(result, expected_data)

    def test_join_tables(self):
        all_periods = [
                          mock_responses.youtube_channel_stats_expected_data_for_period] * 3
        result = self.channel_stats_data._join_periods(all_periods)
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_channel_stats_report_response
        result = self.channel_stats_data.get_table()
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))


class TestYouTubeCountryData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.youtube.TABLES', youtube_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )

        self.country_data = youtube.CountryData({}, youtube_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'country', 'estimated_minutes_watched', 'subscriber_change',
            'subscribers_gained', 'subscribers_lost', 'views',
            'previous_figure_views', 'previous_change_views',
            'previous_percentage_views',
            'previous_figure_estimated_minutes_watched',
            'previous_change_estimated_minutes_watched',
            'previous_percentage_estimated_minutes_watched',
            'previous_figure_subscribers_gained',
            'previous_change_subscribers_gained',
            'previous_percentage_subscribers_gained',
            'previous_figure_subscribers_lost',
            'previous_change_subscribers_lost',
            'previous_percentage_subscribers_lost',
            'yearly_figure_views', 'yearly_change_views',
            'yearly_percentage_views', 'yearly_figure_estimated_minutes_watched',
            'yearly_change_estimated_minutes_watched',
            'yearly_percentage_estimated_minutes_watched',
            'yearly_figure_subscribers_gained',
            'yearly_change_subscribers_gained',
            'yearly_percentage_subscribers_gained',
            'yearly_figure_subscribers_lost', 'yearly_change_subscribers_lost',
            'yearly_percentage_subscribers_lost'
        ]

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_country_report_response
        expected_data = mock_responses.youtube_country_data_for_period_response
        result = self.country_data._get_data_for_period(self.period)
        self.assertEqual(len(result), 20)
        self.assertEqual(
            result[0]['subscriber_change'],
            result[0]['subscribers_gained'] - result[0]['subscribers_lost']
        )
        self.assertEqual(result, expected_data)

    def test_join_tables(self):
        all_periods = [mock_responses.youtube_country_data_for_period_response] * 3
        result = self.country_data._join_periods(all_periods)
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))

    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_table(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_country_report_response
        result = self.country_data.get_table()
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))


class TestYouTubeVideoData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.youtube.TABLES', youtube_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.video_data = youtube.VideoData({}, youtube_sites, self.period, 'MONTHLY')
        self.expected_keys = [
            'channel', 'estimated_minutes_watched', 'title', 'video', 'views',
            'previous_figure_views', 'previous_change_views',
            'previous_percentage_views',
            'previous_figure_estimated_minutes_watched',
            'previous_change_estimated_minutes_watched',
            'previous_percentage_estimated_minutes_watched',
            'yearly_figure_views', 'yearly_change_views',
            'yearly_percentage_views',
            'yearly_figure_estimated_minutes_watched',
            'yearly_change_estimated_minutes_watched',
            'yearly_percentage_estimated_minutes_watched'
        ]

    @patch('Statsdash.aggregate_data.youtube.VideoData._get_video_title')
    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result, mock_get_video_title):
        mock_query_result.return_value = mock_responses.youtube_video_data_report_response
        mock_get_video_title.return_value = 'Video Title'
        expected_data = mock_responses.youtube_video_expected_data_for_period
        result = self.video_data._get_data_for_period(self.period)
        self.assertEqual(len(result), 20)
        self.assertEqual(result, expected_data)

    def test_join_tables(self):
        all_periods = [
                          mock_responses.youtube_video_expected_data_for_period] * 3
        result = self.video_data._join_periods(all_periods)
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))

    @patch('Statsdash.aggregate_data.youtube.VideoData._get_video_title')
    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_table(self, mock_query_result, mock_get_video_title):
        mock_query_result.return_value = mock_responses.youtube_video_data_report_response
        mock_get_video_title.return_value = 'Video Title'
        result = self.video_data.get_table()
        for item in result:
            self.assertTrue(all([k in item.keys() for k in self.expected_keys]))


class TestYouTubeTrafficSourceData(unittest.TestCase):

    @patch('Statsdash.aggregate_data.youtube.TABLES', youtube_tables)
    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.traffic_source_data = youtube.TrafficSourceData({}, youtube_sites, self.period, 'MONTHLY')

    # TODO need to get to the bottom of what this table is meant to do.
    @patch('Statsdash.analytics.YouTubeAnalytics._run_report')
    def test_get_data_for_period(self, mock_query_result):
        mock_query_result.return_value = mock_responses.youtube_traffic_source_report_result
        expected_data = mock_responses.youtube_traffic_source_expected_data_for_period
        result = self.traffic_source_data._get_data_for_period(self.period)
        self.assertEqual(result, expected_data)
