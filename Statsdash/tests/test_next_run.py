from datetime import datetime, date, timedelta
import unittest

from Statsdash.utils import Frequency

from scheduler import RunLogger


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

    def test_looping(self):
        """
        Test routine to check return dates in a sequence
        """
        start_date = datetime(2015, 12, 31)
        end_date = datetime(2016, 3, 31)
        runs = []
        periods = [start_date]
        while start_date < end_date:
            next_run = self.run_log.get_next_run(
                start_date,
                Frequency.MONTHLY,
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
        last_run = now - timedelta(days=2)
        self.run_log.get_next_run(last_run, "DAILY")
        self.assertTrue(self.run_log.override_data)
