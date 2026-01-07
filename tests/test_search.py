from readers import read_config_from_file
from parser import *
from pprint import pprint
import logging
from unittest import TestCase

logging.basicConfig(level=logging.INFO)

class TestSearch(TestCase):
    def test_search_startswith(self):
        dl_list = read_config_from_file('frapr5.core.inteliquent.com')
        intf_list = [j for i in dl_list for j in i.fam() if str(i).startswith('interface')]
        gc_list = [j for i in intf_list for j in i.fam(include_cousins_maxdepth = 1) if 'Google Cloud' in str(i)]
        pprint(gc_list)
        bgp_list = [j for i in dl_list for j in i.fam() if str(i).startswith('router bgp')]
        mg_list = [j for i in bgp_list for j in i.fam() if 'vrf MAILGUN' in str(i)]
        pprint(mg_list)
