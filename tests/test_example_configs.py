"""Test documentation examples in ipynb"""
import ipaddress as ipa
import logging
import re
from unittest import TestCase
from networkconfigparser.parser import parse_from_str
from networkconfigparser.search_helpers import find_lines, parent_child_cb

logging.basicConfig(level=logging.INFO)

class TestDocExamples(TestCase):
    """Test documentation examples in ipynb"""

    @classmethod
    def setUpClass(cls):
        """Parse the example config that we'll use in the rest of the testing"""
        config = """interface TenGigE0/1/0/1
 description Backbone Circuit to North Pudsey from Metric Networks
 cdp
 mtu 2060
 ipv4 address 192.0.2.101 255.255.255.252
 load-interval 30
!
interface Loopback10
 description Router ID
 ipv4 address 192.0.2.1 255.255.255.255
!
router isis IGP
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
router static
 0.0.0.0/0 192.0.2.102
 203.0.113.100/30 192.0.2.102
"""
        cls.doc_lines = parse_from_str(config)

    def test_notebook_family(self):
        """Test familial relationships"""
        te0101 = find_lines(self.doc_lines, r'TenGigE0/1/0/1')
        line_nums = [1, 26, 34, 42, 54]
        assert [o.line_num for o in te0101] == line_nums
        te0101_anc = find_lines(self.doc_lines, r'TenGigE0/1/0/1',
                                include_ancestors=True)
        line_nums = [1, 12, 26, 33, 34, 39, 42, 45, 54]
        assert [o.line_num for o in te0101_anc] == line_nums
        te0101_ch = find_lines(self.doc_lines, r'TenGigE0/1/0/1', include_children=True)
        line_nums = [1, 2, 3, 4, 5, 6, 26, 27, 28, 29, 34, 42, 54]
        assert [o.line_num for o in te0101_ch] == line_nums
        te0101_desc = find_lines(self.doc_lines, r'TenGigE0/1/0/1',
                                 include_all_descendants=True)
        line_nums = [1, 2, 3, 4, 5, 6, 26, 27, 28, 29, 30, 31, 34, 42, 54]
        assert [o.line_num for o in te0101_desc] == line_nums

    def test_notebook_regex_opts(self):
        """Test regex options"""
        ign = find_lines(self.doc_lines, r'INTERFACE', regex_flags=re.IGNORECASE)
        line_nums = [1, 8, 20, 26, 34, 36, 40, 42, 52, 54]
        assert [o.line_num for o in ign] == line_nums

    def test_notebook_iter_search(self):
        """Test parent / child searching with search_spec as an iterable"""
        lsearch = find_lines(self.doc_lines, ['interface', 'metric'],
                             regex_flags=re.IGNORECASE, include_ancestors=True)
        line_nums = [1, 2, 12, 26, 29, 30]
        assert [o.line_num for o in lsearch] == line_nums
        norecurse = find_lines(self.doc_lines,
                               ['interface', 'metric'],
                               regex_flags=re.IGNORECASE,
                               include_ancestors=True,
                               recurse_search=False)
        line_nums = [1, 2]
        assert [o.line_num for o in norecurse] == line_nums
        norec_3term = find_lines(self.doc_lines,
                                 ['interface', 'address-family', 'metric'],
                                 regex_flags=re.IGNORECASE,
                                 include_ancestors=True,
                                 recurse_search=False)
        line_nums = [12, 26, 29, 30]
        assert [o.line_num for o in norec_3term] == line_nums

    def test_notebook_cb_search(self):
        """Test searching with callbacks"""
        intf_search_result = find_lines(self.doc_lines,
                                        ['interface', '192.0.2.1'],
                                        regex_flags=re.IGNORECASE,
                                        include_ancestors=True)
        line_nums = [1, 5, 8, 10]
        assert [o.line_num for o in intf_search_result] == line_nums
        assert (intf_search_result[1].ip_addrs, intf_search_result[3].ip_addrs) == \
               ({ipa.ip_address('192.0.2.101')}, {ipa.ip_address('192.0.2.1')})
        assert (intf_search_result[1].ip_nets, intf_search_result[3].ip_nets) == \
               ({ipa.ip_network('192.0.2.100/30')}, {ipa.ip_network('192.0.2.1/32')})
        assert not intf_search_result[1].has_ip(ipa.ip_address('192.0.2.1'))
        assert intf_search_result[3].has_ip(ipa.ip_address('192.0.2.1'))
        ip_addr_match = find_lines(self.doc_lines,
                                   ['interface',
                                               lambda x: x.has_ip(ipa.ip_address('192.0.2.1'))],
                                   regex_flags=re.IGNORECASE,
                                   include_ancestors=True)
        line_nums = [8, 10]
        assert [o.line_num for o in ip_addr_match] == line_nums
        ip_net_match = find_lines(self.doc_lines,
                                  lambda x: any(True for i in x.ip_nets if i.prefixlen == 30),
                                  include_ancestors=True)
        line_nums = [1, 5, 56, 58]
        assert [o.line_num for o in ip_net_match] == line_nums
        ip_in_slash_30 = find_lines(self.doc_lines,
                                    lambda x: any(i in ipa.ip_network('192.0.2.100/30') for i in
                                                  x.ip_addrs),
                                    include_ancestors=True)
        line_nums = [1, 5, 56, 57, 58]
        assert [o.line_num for o in ip_in_slash_30] == line_nums
        fpo = find_lines(self.doc_lines,
                         lambda x: x.re_search('interface') and
                                   any(c.re_search(r'metric \d+') for c in x.all_descendants),
                         include_ancestors=True)
        line_nums = [12, 26]
        assert [o.line_num for o in fpo] == line_nums
        fpo_pc = find_lines(self.doc_lines,
                            parent_child_cb('interface',
                                            r'metric \d+'),
                            include_ancestors=True)
        assert [o.line_num for o in fpo_pc] == line_nums

    def test_extract_ips(self):
        """Test extracting and working with IP objects"""
        ip_addrs = {
            ipa.ip_address('0.0.0.0'),
            ipa.ip_address('192.0.2.1'),
            ipa.ip_address('192.0.2.101'),
            ipa.ip_address('192.0.2.102'),
            ipa.ip_address('203.0.113.100'),
        }
        ip_nets = {
            ipa.ip_network('0.0.0.0/0'),
            ipa.ip_network('192.0.2.1/32'),
            ipa.ip_network('192.0.2.100/30'),
            ipa.ip_network('203.0.113.100/30'),
        }
        assert ip_addrs == {j for i in self.doc_lines for j in i.ip_addrs if not i.is_comment}
        assert ip_nets == {j for i in self.doc_lines for j in i.ip_nets if not i.is_comment}

    def test_convert(self):
        """Test use of convert_ options"""
        mstr_result = ['interface TenGigE0/1/0/1',
                       'interface Loopback10',
                       self.doc_lines[11],
                       ' interface Loopback10',
                       ' interface TenGigE0/1/0/1',
                       self.doc_lines[32],
                       ' interface TenGigE0/1/0/1',
                       ' interface TenGigE0/0/0/0',
                       self.doc_lines[38],
                       ' interface TenGigE0/0/0/0',
                       ' interface TenGigE0/1/0/1',
                       self.doc_lines[44],
                       ' interface TenGigE0/0/0/0',
                       ' interface TenGigE0/1/0/1']
        match_str = find_lines(self.doc_lines,
                               'interface',
                               convert_match=str,
                               include_ancestors=True)
        assert match_str == mstr_result
        all_str_result = ['interface TenGigE0/1/0/1',
                          'interface Loopback10',
                          'router isis IGP',
                          ' interface Loopback10',
                          ' interface TenGigE0/1/0/1',
                          'rsvp',
                          ' interface TenGigE0/1/0/1',
                          ' interface TenGigE0/0/0/0',
                          'mpls traffic-eng',
                          ' interface TenGigE0/0/0/0',
                          ' interface TenGigE0/1/0/1',
                          'mpls ldp',
                          ' interface TenGigE0/0/0/0',
                          ' interface TenGigE0/1/0/1']
        all_str = find_lines(self.doc_lines,
                             'interface',
                             convert_match=str,
                             convert_family=str,
                             include_ancestors=True)
        assert all_str == all_str_result
        str_dictcomp = [str(i) for i in find_lines(self.doc_lines,
                                                   'interface',
                                                   include_ancestors=True)]
        assert str_dictcomp == all_str_result

    def extract_ips_by_section(self):
        """Test extracting IPs by section"""
        out_result = ['interface TenGigE0/1/0/1',
         {' ipv4 address 192.0.2.101 255.255.255.252': {ipa.ip_network('192.0.2.100/30'),
                                                        ipa.ip_address('192.0.2.101')}},
         'interface Loopback10',
         {' ipv4 address 192.0.2.1 255.255.255.255': {ipa.ip_address('192.0.2.1'),
                                                      ipa.ip_network('192.0.2.1/32')}},
         'mpls ldp',
         {' router-id 192.0.2.1': {ipa.ip_address('192.0.2.1')}},
         'router static',
         {' 0.0.0.0/0 192.0.2.102': {ipa.ip_address('0.0.0.0'),
                                     ipa.ip_network('0.0.0.0/0'),
                                     ipa.ip_address('192.0.2.102')}},
         {' 203.0.113.100/30 192.0.2.102': {ipa.ip_address('192.0.2.102'),
                                            ipa.ip_address('203.0.113.100'),
                                            ipa.ip_network('203.0.113.100/30')}}]
        def gather_ips(o):
            return {str(o): o.ip_addrs | o.ip_nets}
        def has_ip_addr_or_net(o) -> bool:
            return len(o.ip_addrs) > 0 or len(o.ip_nets) > 0
        out = find_lines(self.doc_lines,
                         has_ip_addr_or_net,
                         convert_match=gather_ips,
                         convert_family=str,
                         include_ancestors=True)
        assert out == out_result
        out_result = [['interface TenGigE0/1/0/1',
                      {' ipv4 address 192.0.2.101 255.255.255.252':
                           {ipa.ip_network('192.0.2.100/30'),
                            ipa.ip_address('192.0.2.101')}}],
                      ['interface Loopback10',
                      {' ipv4 address 192.0.2.1 255.255.255.255':
                           {ipa.ip_address('192.0.2.1'),
                            ipa.ip_network('192.0.2.1/32')}}],
                      ['mpls ldp',
                      {' router-id 192.0.2.1': {ipa.ip_address('192.0.2.1')}}],
                      ['router static',
                      {' 0.0.0.0/0 192.0.2.102':
                           {ipa.ip_address('0.0.0.0'),
                            ipa.ip_network('0.0.0.0/0'),
                            ipa.ip_address('192.0.2.102')}},
                      {' 203.0.113.100/30 192.0.2.102':
                           {ipa.ip_address('192.0.2.102'),
                            ipa.ip_address('203.0.113.100'),
                            ipa.ip_network('203.0.113.100/30')}}]]
        out = find_lines(self.doc_lines,
                         has_ip_addr_or_net,
                         convert_match=gather_ips,
                         convert_family=str,
                         include_ancestors=True,
                         flatten_family=False)
        assert out == out_result
