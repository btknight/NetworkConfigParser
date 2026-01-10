from parser import *
from pprint import pprint
from collections import defaultdict
import io
import ipaddress as ipa
import logging
from unittest import TestCase

logging.basicConfig(level=logging.INFO)

class Test_ParseSpacedConfig(TestCase):
    # TODO add tests oriented around specific methods and functions, not general UAT
    def test_num_leading_spaces(self):
        line = 'interface'
        assert num_leading_spaces(line) == 0
        line = '  ' + line
        assert num_leading_spaces(line) == 2

    def test_plain_line(self):
        line = 'router bgp 65535\n'
        p = parse_autodetect([line])
        assert len(p) == 1
        lo = p[0]
        assert lo.line == line.rstrip()
        assert str(lo) == line.rstrip()
        assert lo.line_num == 1
        assert lo.gen == 1
        assert lo.ancestors == []
        assert lo.children == []
        assert lo.all_descendants == []
        assert lo.family() == [lo]
        assert lo == lo

    def test_banner(self):
        config = """banner login ^C
+----------------------------------------------------------------------------+
|                                big banner                                  |
|                                                                            |
|  This system is provided for authorized users ONLY.                        |
|  If you are not an authorized user, disconnect immediately.                |
|  By continuing to access this system, you acknowledge that:                |
|   - you have no right or expectation of privacy                            |
|   - all of your activity is monitored and recorded                         |
|   - all communications and data transiting, traveling to or from, or       |
|       stored on this system are monitored and recorded                     |
|   - records of your activity will be stored, retrieved, and reviewed for   |
|       any lawful purpose, including criminal prosecution                   |
|   - records of your activity will be shared with any entity authorized by  |
|       Big Corp, Inc.                                                       |
+----------------------------------------------------------------------------+
^C"""
        lines = [i + '\n' for i in config.split('\n')]
        p = parse_autodetect(lines)
        assert len(p) == 17
        lo = p[0]
        assert lo.line == lines[0].rstrip()
        assert lo.line_num == 1
        assert lo.gen == 1
        assert lo.ancestors == []
        assert lo.children == p[1:17]
        assert lo.all_descendants == p[1:17]
        assert lo.family() == p
        assert lo == lo

    def test_section_2level(self):
        config = """interface TenGigE0/1/0/2
 description An example interface
 ipv4 address 192.0.2.1 255.255.255.252
 ipv6 address 2001:db8:1337:93::1/64
 load-interval 30
 ipv4 access-group TenGigACL ingress
!"""
        lines = [i + '\n' for i in config.split('\n')]
        p = parse_autodetect(lines)
        assert len(p) == 7
        lo = p[0]
        assert lo.line == lines[0].rstrip()
        assert lo.line_num == 1
        assert lo.gen == 1
        assert lo.ancestors == []
        assert lo.children == p[1:6]
        assert lo.all_descendants == p[1:6]
        assert lo.family() == p[0:6]
        assert lo == lo
        assert p[2].has_ip(ipa.ip_network('192.0.2.0/30'))
        assert p[2].has_ip(ipa.ip_address('192.0.2.1'))
        assert p[2].has_ip(ipa.ip_interface('192.0.2.1/30'))
        assert not p[2].has_ip(ipa.ip_address('203.0.113.1'))
        assert not p[2].has_ip(ipa.ip_network('203.0.113.0/24'))
        assert not p[2].has_ip(ipa.ip_interface('203.0.113.224/24'))
        assert p[3].has_ip(ipa.ip_network('2001:db8:1337:93::/64'))
        assert p[3].has_ip(ipa.ip_address('2001:db8:1337:93::1'))
        assert p[3].has_ip(ipa.ip_interface('2001:db8:1337:93::1/64'))
        assert not p[3].has_ip(ipa.ip_network('2001:db8:1337:fb00::/56'))
        assert not p[3].has_ip(ipa.ip_address('2001:db8:1337:6942::2'))
        assert not p[3].has_ip(ipa.ip_interface('2001:db8:1338:93::1/64'))
        with self.assertRaises(ValueError):
            assert not p[2].has_ip('203.0.113.224/24')

    def test_section_multilevel(self):
        config = """l2vpn
 logging
  pseudowire
 bridge group BANANA
  bridge-domain SANDWICH
   interface GigabitEthernet0/0/0/16.50
   interface GigabitEthernet0/0/0/17.50
   interface GigabitEthernet0/1/0/14.50
   interface GigabitEthernet0/1/0/15.50
   routed interface BVI50
interface TenGigE0/1/0/2
 description An example interface
 ipv4 address 192.0.2.1 255.255.255.252
 load-interval 30
 ipv4 access-group TenGigACL ingress
!"""
        lines = [i + '\n' for i in config.split('\n')]
        p = parse_autodetect(lines)
        assert len(p) == 16
        assert len([i for i in p if i.gen == 1]) == 3
        assert p[0].children == [p[1], p[3]]
        assert p[0].all_descendants == p[1:10]
        assert p[10].children == p[11:15]
        assert p[10].all_descendants == p[11:15]
        assert str(p[15]) == '!'
        assert p[3].family() == [p[0]] + p[3:10]
        assert p[3].family(include_ancestors=False) == p[3:10]
        assert p[3].family(include_children=False) == [p[0], p[3]]
        assert p[3].family(include_all_descendants=False) == [p[0]] + p[3:5]
        assert p[4].ancestors[-2].family() == p[0:10]
        assert p[4].ancestors[-1].family() == [p[0]] + p[3:10]

    def test_route_policy(self):
        config = """route-policy FOOBR-IN
  if destination in FOOBR-PFX-SET then
    set med 0
    set local-preference 31337
    done
  else
    drop
  endif
end-policy
route-policy DEFAULT-ONLY
  if destination in DEFAULT-ROUTE then
    set local-preference 10
  else
    drop
  endif
end-policy"""
        lines = [i + '\n' for i in config.split('\n')]
        p = parse_autodetect(lines)
        assert len(p) == 16
        assert len([i for i in p if i.gen == 1]) == 2
        assert p[0].children == p[1:9]
        assert p[0].all_descendants == p[1:9]
        assert p[9].children == p[10:16]
        assert p[9].all_descendants == p[10:16]

    def test_route_policy_with_no_trailing_end(self):
        log_output = io.StringIO()
        stream_handler = logging.StreamHandler(log_output)
        logging.getLogger().addHandler(stream_handler)
        logging.warning('The next WARNING is normal, testing route policy with no trailing end- statement. Please ignore')
        config = """route-policy FOOBR-IN
  if destination in FOOBR-PFX-SET then
    set med 0
    set local-preference 31337
    done
  else
    drop
  endif
route-policy DEFAULT-ONLY
  if destination in DEFAULT-ROUTE then
    set local-preference 10
  else
    drop
  endif"""
        lines = [i + '\n' for i in config.split('\n')]
        try:
            p = parse_autodetect(lines)
        finally:
            logging.getLogger().removeHandler(stream_handler)
        assert len(p) == 14
        assert len([i for i in p if i.gen == 1]) == 2
        assert len([i for i in p if i.gen == 2]) == 12
        assert 'no end-set or end-policy encountered at line 9 within section route-policy FOOBR-IN' in log_output.getvalue()
        assert p[0].children == p[1:8]
        assert p[0].all_descendants == p[1:8]
        assert p[0].family() == p[0:8]
        assert p[8].children == p[9:14]
        assert p[8].all_descendants == p[9:14]
        log_output.close()

    def test_example_arista(self):
        p = parse_from_file('example-arista.txt')
        #print(f'test_example_arista: len(p) = {len(p)}')
        assert len(p) == 114
        gen_distribution = defaultdict(lambda: 0)
        for dl in p:
            gen_distribution[dl.gen] += 1
        measured_distribution = {1: 78, 2: 34, 3: 2}
        assert gen_distribution == measured_distribution

    def test_example_junos(self):
        p = parse_from_file('example-junos.txt')
        assert len(p) == 224
        gen_distribution = defaultdict(lambda: 0)
        for dl in p:
            gen_distribution[dl.gen] += 1
        measured_distribution = {1: 11, 2: 41, 3: 66, 4: 74, 5: 21, 6: 7, 7: 4}
        assert gen_distribution == measured_distribution
