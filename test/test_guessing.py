# -*- coding: utf-8 -*-
import unittest
import StringIO

from . import horror_fobj
from nose.plugins.attrib import attr
from nose.tools import assert_equal
from messytables import (CSVTableSet, type_guess, headers_guess,
                         offset_processor, DateType, StringType,
                         DecimalType, IntegerType, TimeType,
                         DateUtilType, BoolType, RegExType, JsonType,
                         EWKB, EWKT)


class TypeGuessTest(unittest.TestCase):
    @attr("slow")
    def test_type_guess(self):
        csv_file = StringIO.StringIO('''
            1,   2012/2/12, 2,   02 October 2011,  yes,     11
            2,   2012/2/12, 2,   02 October 2011,  true,    9 am
            2.4, 2012/2/12, 1,   1 May 2011,       no,      23:00.123
            foo, bar,       1000, ,                false,   12:00
            4.3, ,          42,  24 October 2012,  ,        7.12
             ,   2012/2/12, 21,  24 December 2013, true,    11PM ''')
        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(rows.sample)

        assert_equal(guessed_types, [
            DecimalType(), DateType('%Y/%m/%d'), IntegerType(),
            DateType('%d %B %Y'), BoolType(), TimeType()])

    def test_regex_type(self):
        csv_file = StringIO.StringIO('''
        aaa,    bbb,    ccc
        ,   ,
        aa,     bb,     cc
        a,      b,      c
        ''')

        class Type1(RegExType):
            regex = '^a+$'

        class Type2(RegExType):
            regex = '^b+$'

        rows = CSVTableSet(csv_file).tables[0]
        guessed_types =\
            type_guess(rows.sample, types=[Type1(), Type2(), StringType()])

        assert_equal(guessed_types, [
            Type1(), Type2(), StringType()
        ])

    def test_json_type(self):
        csv_file = StringIO.StringIO('''
        "{""a"":""b"", ""c"":""d""}",       "[1, 2, 3]",                12a
        "[""a"", [1, 2, {""a"":""b""}]]",   "{""a"": 1, ""b"":[1, 2]}", abc
        ,,                                                              "abc"
        ''')

        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(rows.sample)

        assert_equal(guessed_types, [JsonType(), JsonType(), StringType()])

    def test_wkt_type(self):
        csv_file = StringIO.StringIO('''
        "0102000020e6100000020000000000000000002640000000000000474000000000000024400000000000804640",
        "0102000020787f0000020000000000000000002640000000000000474000000000000024400000000000804640", "SRID=4326;LINESTRING(11 46,10 45)"
        "0101000020e610000000000000000026400000000000004740", "SRID=4326;LINESTRING(11 46,10 45)"
        , "SRID=4326;POINT(11 46)"
        ''')

        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(rows.sample, strict=True)

        assert_equal(guessed_types, [EWKB(), EWKT()])

    def test_type_guess_strict(self):
        import locale
        locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')
        csv_file = StringIO.StringIO('''
            1,   2012/2/12, 2,      2,02 October 2011,"100.234354"
            2,   2012/2/12, 1.1,    0,1 May 2011,"100,000,000.12"
            foo, bar,       1500,   0,,"NaN"
            4,   2012/2/12, 42,"-2,000",24 October 2012,"42"
            ,,,,,''')
        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(rows.sample, strict=True)
        assert_equal(guessed_types, [
            StringType(), StringType(),
            DecimalType(), IntegerType(), DateType('%d %B %Y'),
            DecimalType()])

    def test_type_guess_forced(self):
        csv_file = StringIO.StringIO('''
            1,  aaa,    true
            2,  bbb,    false
            3,  ccc,
            4,  ,       yes
            5,  ddd,    no
        ''')
        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(
            rows.sample,
            forced_types=[None, None, StringType()]
        )
        assert_equal(guessed_types, [IntegerType(), StringType(), StringType()])

    def test_strict_guessing_handles_padding(self):
        csv_file = StringIO.StringIO('''
            1,   , 2
            2,   , 1.1
            foo, , 1500''')
        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(rows.sample, strict=True)
        assert_equal(len(guessed_types), 3)
        assert_equal(guessed_types,
                     [StringType(), StringType(), DecimalType()])

    def test_non_strict_guessing_handles_padding(self):
        csv_file = StringIO.StringIO('''
            1,   , 2.1
            2,   , 1.1
            foo, , 1500''')
        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(rows.sample, strict=False)
        assert_equal(len(guessed_types), 3)
        assert_equal(guessed_types,
                     [IntegerType(), StringType(), DecimalType()])

    def test_guessing_uses_first_in_case_of_tie(self):
        csv_file = StringIO.StringIO('''
            2
            1.1
            1500''')
        rows = CSVTableSet(csv_file).tables[0]
        guessed_types = type_guess(
            rows.sample, types=[DecimalType, IntegerType], strict=False)
        assert_equal(guessed_types, [DecimalType()])

        guessed_types = type_guess(
            rows.sample, types=[IntegerType, DecimalType], strict=False)
        assert_equal(guessed_types, [IntegerType()])

    @attr("slow")
    def test_strict_type_guessing_with_large_file(self):
        fh = horror_fobj('211.csv')
        rows = CSVTableSet(fh).tables[0]
        offset, headers = headers_guess(rows.sample)
        rows.register_processor(offset_processor(offset + 1))
        types = [StringType, IntegerType, DecimalType, DateUtilType]
        guessed_types = type_guess(rows.sample, types, True)
        assert_equal(len(guessed_types), 96)
        assert_equal(guessed_types, [
            IntegerType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            IntegerType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), IntegerType(), StringType(), DecimalType(),
            DecimalType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            IntegerType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            IntegerType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), DateUtilType(),
            DateUtilType(), DateUtilType(), DateUtilType(), StringType(),
            StringType(), StringType()])

    def test_file_with_few_strings_among_integers(self):
        fh = horror_fobj('mixedGLB.csv')
        rows = CSVTableSet(fh).tables[0]
        offset, headers = headers_guess(rows.sample)
        rows.register_processor(offset_processor(offset + 1))
        types = [StringType, IntegerType, DecimalType, DateUtilType]
        guessed_types = type_guess(rows.sample, types, True)
        assert_equal(len(guessed_types), 19)
        print guessed_types
        assert_equal(guessed_types, [
            IntegerType(), IntegerType(),
            IntegerType(), IntegerType(), IntegerType(), IntegerType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), StringType(), StringType(),
            StringType(), StringType(), IntegerType(), StringType(),
            StringType()])
