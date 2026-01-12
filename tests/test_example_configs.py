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
        #router_isis_intf_lines = find_lines(doc_lines, ('router isis ', 'interface '))
        router_isis_intf_lines = find_lines(doc_lines, ('router isis ', 'address-family ipv4 '), include_ancestors=True)


    # TODO more cleanup and better testing
    def test_example_ios_xr(self):
        dl_list = parse_from_file('example-cisco-xr.txt')

    def test_example_ios_xe(self):
        dl_list = parse_from_file('example-cisco-xe.txt')

    def test_example_ios(self):
        dl_list = parse_from_file('example-cisco-ios.txt')

    def test_example_junos(self):
        dl_list = parse_from_file('example-junos.txt')

