from datetime import date
import unittest
from unittest.mock import patch

from Statsdash import mock_responses
from Statsdash.report import AnalyticsCoreReport
from Statsdash.stats_range import StatsRange


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

    @patch('Statsdash.report.AnalyticsCoreReport._get_tables')
    def test_get_html_monthly(self, mock_get_tables_monthly):
        """
        """
        # TODO remove literal
        self.report = AnalyticsCoreReport(self.site_tables, self.period, 'MONTHLY', 'SUBJECT')
        mock_get_tables_monthly.return_value = mock_responses.mock_get_tables_monthly
        # TODO actual testing
        print(self.report.generate_html())

    @patch('Statsdash.report.AnalyticsCoreReport._get_tables')
    def test_get_html_daily(self, mock_get_tables_daily):
        """
        """
        # TODO remove literal
        self.report = AnalyticsCoreReport(self.site_tables, self.period, 'DAILY', 'SUBJECT')
        mock_get_tables_daily.return_value = mock_responses.mock_get_tables_daily
        print(self.report.generate_html())
