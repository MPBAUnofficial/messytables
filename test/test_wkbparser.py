# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_equal
from messytables.wkbparser import Geometry, parse_wkb, parse_wkt

TEST_VALUES = [
    {
        'wkt': 'SRID=4326;POINT(11 46)',
        'wkb': '0101000020e610000000000000000026400000000000004740',
        'res': Geometry('Point', 1, 4326, False, False)
    },
    {
        'wkt': 'SRID=32632;POINT(11 46)',
        'wkb': '0101000020787f000000000000000026400000000000004740',
        'res': Geometry('Point', 1, 32632, False, False)
    },
    {
        'wkt': 'POINT(11 46)',
        'wkb': '010100000000000000000026400000000000004740',
        'res': Geometry('Point', 1, -1, False, False)
    },
    {
        'wkt': 'SRID=4326;LINESTRING(11 46,10 45)',
        'wkb': '0102000020e6100000020000000000000000002640000000000000474000000000000024400000000000804640',
        'res': Geometry('LineString', 2, 4326, False, False)
    },
    {
        'wkt': 'SRID=32632;LINESTRING(11 46,10 45)',
        'wkb': '0102000020787f0000020000000000000000002640000000000000474000000000000024400000000000804640',
        'res': Geometry('LineString', 2, 32632, False, False)
    },
    {
        'wkt': 'LINESTRING(11 46,10 45)',
        'wkb': '0102000000020000000000000000002640000000000000474000000000000024400000000000804640',
        'res': Geometry('LineString', 2, -1, False, False)
    },
    {
        'wkt': 'SRID=4326;LINESTRING(11 46,10 45)',
        'wkb': '0102000020e6100000020000000000000000002640000000000000474000000000000024400000000000804640',
        'res': Geometry('LineString', 2, 4326, False, False)
    },
    # todo: add MOAR tests
]


class TestWKBParser(unittest.TestCase):
    def test_wkb_parser(self):
        for geom in TEST_VALUES:
            parsed_wkb = parse_wkb(geom['wkb'])
            assert_equal(parsed_wkb, geom['res'])

    def test_wkt_parser(self):
        for geom in TEST_VALUES:
            parsed_wkt = parse_wkt(geom['wkt'])
            assert_equal(parsed_wkt, geom['res'], msg='{0}'.format(geom['wkt']))
