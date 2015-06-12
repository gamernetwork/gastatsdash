import unittest

from datetime import datetime

from analytics import StatsRange

class TestStatsRange(unittest.TestCase):
    
    def test_date_formatting(self):
        start = datetime(2015,06,12)
        end = datetime(2015,06,13)
        stats_range = StatsRange("Now", start, end)
        self.assertEqual(stats_range.get_start(), "2015-06-12T00:00:00")
        #self.assertEqual(stats_range.get_end(), "2015-06-13T00:00:00")
        self.assertEqual(stats_range.get_end(), "2015-06-13T00:10:00")

if __name__ == '__main__':
    unittest.main()
