from datetime import date
import unittest

from Statsdash.stats_range import StatsRange


class TestStatsRange(unittest.TestCase):

    def setUp(self):
        start = date(2020, 3, 19)
        end = date(2020, 3, 20)
        self.test_range = StatsRange('Test Range', start, end)

    def test_start(self):
        self.assertEqual(self.test_range.get_start(), '2020-03-19')

    def test_get_end(self):
        self.assertEqual(self.test_range.get_end(), '2020-03-20')

    def test_days_in_range(self):
        self.assertEqual(self.test_range.days_in_range(), 2)

    def test_days_in_range_one_day_range(self):
        self.test_range.start_date = date(2020, 3, 20)
        self.assertEqual(self.test_range.days_in_range(), 1)

    def test_get_period_daily(self):
        d = date(2020, 3, 19)
        date_range = StatsRange.get_period(d, StatsRange.Frequency.DAILY)
        self.assertEqual(date_range.start_date, d)
        self.assertEqual(date_range.end_date, d)

    def test_get_period_wow_daily(self):
        d = date(2020, 3, 19)
        date_range = StatsRange.get_period(d, StatsRange.Frequency.WOW_DAILY)
        self.assertEqual(date_range.start_date, d)
        self.assertEqual(date_range.end_date, d)

    def test_get_period_weekly(self):
        d = date(2020, 3, 19)
        expected_start = date(2020, 3, 12)
        expected_end = date(2020, 3, 18)
        date_range = StatsRange.get_period(d, StatsRange.Frequency.WEEKLY)
        self.assertEqual(date_range.start_date, expected_start)
        self.assertEqual(date_range.end_date, expected_end)

    def test_get_period_monthly(self):
        d = date(2020, 3, 19)
        expected_start = date(2020, 2, 19)
        expected_end = date(2020, 3, 18)
        date_range = StatsRange.get_period(d, StatsRange.Frequency.MONTHLY)
        self.assertEqual(date_range.start_date, expected_start)
        self.assertEqual(date_range.end_date, expected_end)

    def test_get_previous_period_daily(self):
        expected_start = date(2020, 3, 18)
        expected_end = date(2020, 3, 18)
        result = StatsRange.get_previous_period(
            self.test_range,
            StatsRange.Frequency.DAILY
        )
        self.assertEqual(result.start_date, expected_start)
        self.assertEqual(result.end_date, expected_end)

    def test_get_previous_period_wow_daily(self):
        expected_start = date(2020, 3, 12)
        expected_end = date(2020, 3, 12)
        result = StatsRange.get_previous_period(
            self.test_range,
            StatsRange.Frequency.WOW_DAILY
        )
        self.assertEqual(result.start_date, expected_start)
        self.assertEqual(result.end_date, expected_end)

    def test_get_previous_period_weekly(self):
        expected_start = date(2020, 3, 6)
        expected_end = date(2020, 3, 12)
        result = StatsRange.get_previous_period(
            self.test_range,
            StatsRange.Frequency.WEEKLY
        )
        self.assertEqual(result.start_date, expected_start)
        self.assertEqual(result.end_date, expected_end)

    def test_get_previous_period_monthly(self):
        expected_start = date(2020, 2, 19)
        expected_end = date(2020, 3, 18)
        result = StatsRange.get_previous_period(
            self.test_range,
            StatsRange.Frequency.MONTHLY
        )
        self.assertEqual(result.start_date, expected_start)
        self.assertEqual(result.end_date, expected_end)

    def test_get_previous_period_yearly(self):
        expected_start = date(2019, 3, 19)
        expected_end = date(2019, 3, 19)
        result = StatsRange.get_previous_period(
            self.test_range,
            StatsRange.Frequency.YEARLY
        )
        self.assertEqual(result.start_date, expected_start)
        self.assertEqual(result.start_date, expected_end)

    def test_get_previous_period_invalid(self):
        with self.assertRaises(ValueError):
            StatsRange.get_previous_period(
                self.test_range,
                'Invalid string'
            )


