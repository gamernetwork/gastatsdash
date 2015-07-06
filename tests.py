import unittest

from datetime import datetime, date, timedelta

from analytics import StatsRange
from dateutils import find_last_weekday

class TestStatsRange(unittest.TestCase):
    
    def test_date_formatting(self):
        start = datetime(2015,06,12)
        end = datetime(2015,06,13)
        stats_range = StatsRange("Now", start, end)
        self.assertEqual(stats_range.get_start(), "2015-06-12T00:00:00")
        #self.assertEqual(stats_range.get_end(), "2015-06-13T00:00:00")
        self.assertEqual(stats_range.get_end(), "2015-06-13T00:10:00")

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



if __name__ == '__main__':
    unittest.main()
