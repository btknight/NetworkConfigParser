import unittest

from parser import *
from search_helpers import *
from pprint import pprint
from unittest import TestCase

class TestSearchHelpers(unittest.TestCase):
    def test_find_line(self):
        doc_lines = parse_from_file('example-junos.txt')
        et_0_0_0 = find_lines(doc_lines, lambda o: 'et-0/0/0' in o, suppress_common_ancestors=True, include_ancestors=True, include_all_descendants=True)
        #pprint(et_0_0_0)