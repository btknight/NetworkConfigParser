from readers import read_config_from_file
from parser import *
from pprint import pprint
import logging
from unittest import TestCase

logging.basicConfig(level=logging.INFO)

class ParseLinesTest(TestCase):
    def test_num_leading_spaces(self):
        line = 'interface'
        assert num_leading_spaces(line) == 0
        line = '  ' + line
        assert num_leading_spaces(line) == 2

    def test_parse(self):
        dns = read_config_from_file('frals1.core.inteliquent.com')
        #pprint(dns)