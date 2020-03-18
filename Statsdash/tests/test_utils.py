import unittest
from Statsdash.utils import utils


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

    def test_get_change(self):
        data_a = {'apples': 10, 'bananas': 8, 'pears': 7}
        data_b = {'apples': 5, 'bananas': 8, 'pears': 6}
        result = utils.get_change(data_a, data_b, ['apples', 'bananas'])
        expected_result = {
            'figure_apples': 5, 'change_apples': 5, 'percentage_apples': 100.0,
            'figure_bananas': 8, 'change_bananas': 0, 'percentage_bananas': 0.0
        }
        self.assertEqual(result, expected_result)
