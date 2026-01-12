from parser import *
from search_helpers import *
from pprint import pprint
import logging
import re
from unittest import TestCase

logging.basicConfig(level=logging.INFO)

class TestSearch(TestCase):
    def test_notebook(self):
        config = """interface TenGigE0/1/0/1
 description Backbone Circuit to North Pudsey
 cdp
 mtu 2060
 ipv4 address 192.0.2.101 255.255.255.252
 load-interval 30
!
interface Loopback10
 description Router ID
 ipv4 address 192.0.2.1 255.255.255.255
!
router isis coreIGP
 net 49.0000.1920.0000.2001.00
 log adjacency changes
 address-family ipv4 unicast
  metric-style wide
  mpls traffic-eng level-1-2
  mpls traffic-eng router-id Loopback10
 !
 interface Loopback10
  passive
  circuit-type level-2-only
  address-family ipv4 unicast
  !
 !
 interface TenGigE0/1/0/1
  circuit-type level-2-only
  point-to-point
  address-family ipv4 unicast
   metric 1000
   mpls ldp sync
!
rsvp
 interface TenGigE0/1/0/1
 !
 interface TenGigE0/0/0/0
 !
!
mpls traffic-eng
 interface TenGigE0/0/0/0
 !
 interface TenGigE0/1/0/1
 !
!
mpls ldp
 !
 igp sync delay on-session-up 10
 router-id 192.0.2.1
 !
 session protection
 !
 interface TenGigE0/0/0/0
 !
 interface TenGigE0/1/0/1
 !
"""
        doc_lines = parse_from_str(config)
        #intf_lines = find_lines(doc_lines, lambda o: 'TenGigE0/1/0/1' in o, include_ancestors=True)
        intf_lines = find_lines(doc_lines, 'TenGigE0/1/0/1', include_ancestors=True)
        pprint(intf_lines)
        #router_isis_intf_lines = find_lines(doc_lines, ('router isis ', 'interface '))
        router_isis_intf_lines = find_lines(doc_lines, ('router isis ', 'address-family ipv4 '), include_ancestors=True)
        pprint(router_isis_intf_lines)


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
