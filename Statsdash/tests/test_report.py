from datetime import date
import unittest
from unittest.mock import patch

from Statsdash import utils
from Statsdash.tests.data import mock_responses
from Statsdash.report import AnalyticsCoreReport, YouTubeReport
from Statsdash.stats_range import StatsRange

DAILY = utils.Frequency.DAILY
WEEKLY = utils.Frequency.WEEKLY
MONTHLY = utils.Frequency.MONTHLY
YEARLY = utils.Frequency.YEARLY


class TestReport(unittest.TestCase):

    @patch('Statsdash.report.AnalyticsCoreReport.get_resource')
    def setUp(self, mock_get_resource):
        mock_get_resource.return_value = {}
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_tables = {
            'fake.site1.com': [{'id': 'ga:12345678'}],
            'fake.site2.com': [{'id': 'ga:87654321'}],
        }
        self.report = AnalyticsCoreReport(self.site_tables, self.period, DAILY, '')

    def test_frequency_label_dod(self):
        self.assertEqual(self.report.frequency_label, 'DoD')

    def test_frequency_label_wow(self):
        self.report.frequency = WEEKLY
        self.assertEqual(self.report.frequency_label, 'WoW')

    def test_frequency_label_mom(self):
        self.report.frequency = MONTHLY
        self.assertEqual(self.report.frequency_label, 'MoM')

    def test_frequency_label_yoy(self):
        self.report.frequency = YEARLY
        self.assertEqual(self.report.frequency_label, 'YoY')


class TestAnalyticsCoreReport(unittest.TestCase):

    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_tables = {
            'fake.site1.com': [{'id': 'ga:12345678'}],
            'fake.site2.com': [{'id': 'ga:87654321'}],
        }

    @patch('Statsdash.report.AnalyticsCoreReport.get_resource')
    @patch('Statsdash.report.logger')
    def test_debug_message(self, mock_logger, mock_get_resource):
        mock_get_resource.return_value = {}
        AnalyticsCoreReport(self.site_tables, self.period, MONTHLY, '')
        mock_logger.debug.assert_called_with('Running analytics core report.')

    @patch('Statsdash.report.AnalyticsCoreReport.get_resource')
    @patch('Statsdash.report.AnalyticsCoreReport._get_tables')
    def test_get_html_monthly(self, mock_get_tables_monthly, mock_get_resource):
        mock_get_resource.return_value = {}
        self.report = AnalyticsCoreReport(self.site_tables, self.period, MONTHLY, '')
        mock_get_tables_monthly.return_value = mock_responses.mock_get_tables_monthly
        # print(self.report.generate_html())

    @patch('Statsdash.report.AnalyticsCoreReport.get_resource')
    @patch('Statsdash.report.AnalyticsCoreReport._get_tables')
    def test_get_html_daily(self, mock_get_tables_daily, mock_get_resource):
        mock_get_resource.return_value = {}
        self.report = AnalyticsCoreReport(self.site_tables, self.period, DAILY, 'SUBJECT')
        mock_get_tables_daily.return_value = mock_responses.mock_get_tables_daily
        # print(self.report.generate_html())


class TestYouTubeReport(unittest.TestCase):

    def setUp(self):
        self.period = StatsRange(
            'Month to date Aggregate',
            date(2020, 3, 12),
            date(2020, 3, 13)
        )
        self.site_tables = {
            'channel_1': ['12345678'],
            'channel_2': ['87654321'],
        }

    @patch('Statsdash.report.YouTubeReport.get_resource')
    @patch('Statsdash.report.logger')
    def test_debug_message(self, mock_logger, mock_get_resource):
        mock_get_resource.return_value = {}
        YouTubeReport(self.site_tables, self.period, MONTHLY, '')
        mock_logger.debug.assert_called_with('Running youtube report.')

    @patch('Statsdash.report.YouTubeReport.get_resource')
    @patch('Statsdash.report.YouTubeReport._get_tables')
    def test_get_html(self, mock_get_tables_monthly, mock_get_resource):
        mock_get_resource.return_value = {}
        self.report = YouTubeReport(self.site_tables, self.period, MONTHLY, 'SUBJECT')
        mock_get_tables_monthly.return_value = mock_responses.mock_get_tables_youtube
        # print(self.report.generate_html())
