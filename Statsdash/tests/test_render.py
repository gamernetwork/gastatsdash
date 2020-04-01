import unittest

from Statsdash.render import int_comma


class TestRender(unittest.TestCase):

    def test_int_comma(self):
        integer = 1000.56
        result = int_comma(integer)
        self.assertEqual(result, '1,000.56')

    def test_int_comma_zero(self):
        integer = 0
        result = int_comma(integer)
        self.assertEqual(result, '0')

    def test_int_comma_negative(self):
        integer = -2500
        result = int_comma(integer)
        self.assertEqual(result, '-2,500')

    def test_int_comma_large(self):
        integer = 1250250
        result = int_comma(integer)
        self.assertEqual(result, '1,250,250')
