"""Test parser functions"""
import io
import logging
from unittest import TestCase
from networkconfigparser.parser import num_leading_spaces, parse_autodetect, parse_from_file
from networkconfigparser.documentline import DocumentLine

logging.basicConfig(level=logging.INFO)

class TestParseSpacedConfig(TestCase):
    """Test parser functions"""

    def test_num_leading_spaces(self):
        """Test detection of leading spaces"""
        interface = 'interface'
        for i in range(10):
            line = ' ' * i + interface
            assert num_leading_spaces(line) == i

    def test_plain_line(self):
        """Test parsing a single line fed to a DocumentLine object"""
        line = 'router bgp 65535\n'
        dl = DocumentLine(1, line.rstrip())
        doc_lines = parse_autodetect([line])
        assert doc_lines == [dl]

    def test_banner(self):
        """Test banner parsing, an exceptional section with its own rules"""
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
        assert lo.gen == 1
        assert lo.children == p[1:17]
        assert lo.all_descendants == p[1:17]

    def test_section_multilevel(self):
        """Test parsing a multi-level section, ensure parent / child relationships are working"""
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
        """Test route-policy and prefix-set parsing, an exceptional section with its own rules"""
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
        """A route-policy with no end-policy statement will generate a warning, test for that"""
        log_output = io.StringIO()
        stream_handler = logging.StreamHandler(log_output)
        logging.getLogger().addHandler(stream_handler)
        logging.warning('The next WARNING is normal, testing route policy with no trailing end- '
                        'statement. Please ignore')
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
        assert ('no end-set or end-policy encountered at line 9 within section route-policy '
                'FOOBR-IN' in log_output.getvalue())
        assert p[0].children == p[1:8]
        assert p[0].all_descendants == p[1:8]
        assert p[0].family() == p[0:8]
        assert p[8].children == p[9:14]
        assert p[8].all_descendants == p[9:14]
        log_output.close()

    def test_parse_from_file(self):
        """Test parsing from a file"""
        p = parse_from_file('example-junos.txt')
        assert 'groups' in p[0].line
