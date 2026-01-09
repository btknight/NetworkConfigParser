from parser import *
from pprint import pprint
import logging
import re
from unittest import TestCase

logging.basicConfig(level=logging.DEBUG)

class TestSearch(TestCase):
    def test_str_methods(self):
        dl_list = parse_from_file('frapr5.core.inteliquent.com')
        intf_list = [j for i in dl_list for j in i.family() if i.startswith('interface')]
        gc_list = [i.ancestors[0] for i in intf_list if i.gen > 1 and 'Google Cloud' in i]
        assert len(gc_list) == 3
        bgp_list = [j for i in dl_list for j in i.family() if i.startswith('router bgp')]
        mg_list = [j for i in bgp_list for j in i.family() if ' vrf MAILGUN' in i]
        assert len(mg_list) == 48
        rp_list = [i for i in dl_list if i.startswith('route-policy ') or re.match(r'^\w+-set ', str(i))]
        assert len(rp_list) == 51

    def test_chites(self):
        dl_list = parse_from_file('chites01.core.inteliquent.com')
        sg_list = [i for i in dl_list if i.gen == 1]
        #pprint(sg_list)

    def test_atlbr1(self):
        dl_list = parse_from_file('atlbr1.core.inteliquent.com')
        #pprint(dl_list)

    def test_atlmr1(self):
        dl_list = parse_from_file('atlmr1.core.inteliquent.com')
        #pprint(dl_list)

    def test_atlnpt1(self):
        dl_list = parse_from_file('atlnpt1.core.inteliquent.com')
        #pprint([i for i in dl_list if not i.startswith('set ') and i.depth < 4])

    def test_router_kn(self):
        dl_list = parse_from_file('router.knight-networks.com')
        #pprint(dl_list)
