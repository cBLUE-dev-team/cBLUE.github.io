import unittest
import Las

class TestLas(unittest.TestCase):

    def test_get_flight_line_ids(self):
        result = Las.Las.get_flight_line_ids