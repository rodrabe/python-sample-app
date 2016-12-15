import unittest

from jumpgate.common.utils import lookup


class TestLookup(unittest.TestCase):
    def test_lookup(self):
        self.assertIsNone(lookup({}, 'key'))

        self.assertEqual(lookup({'key': 'value'}, 'key'), 'value')
        self.assertEqual(
            lookup({'key': {'key': 'value'}}, 'key', 'key'), 'value')
