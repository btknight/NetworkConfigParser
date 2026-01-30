"""Testing for DocumentLine object."""
import ipaddress as ipa
import re
import unittest
from networkconfigparser.documentline import DocumentLine

class TestDocumentLine(unittest.TestCase):
    """Testing for DocumentLine object."""
    def test_ipv6_parsing(self):
        """Test IPv6 address / network parsing and conversion to ipaddress objects"""
        #
        # Two IPs should be found in this line, one parsed as IPv6Network, one as IPv6Address
        ip_route = 'ipv6 route 2001:db8:690:f00b::/64 Tunnel6 2001:db8:690::1'
        dl = DocumentLine(1, ip_route)
        ips = list(dl._gen_ip_addrs_nets())
        assert len(ips) == 2
        a, n = ips[0]
        assert a == ipa.IPv6Address('2001:db8:690:f00b::')
        assert n == ipa.IPv6Network('2001:db8:690:f00b::/64')
        a, n = ips[1]
        assert a == ipa.IPv6Address('2001:db8:690::1')
        assert n is None
        #
        # One IP should be found in this line, parsed as IPv6Interface
        ip_cidr = 'ipv6 address 2001:db8:690:42::3/64'
        dl = DocumentLine(1, ip_cidr)
        ips = list(dl._gen_ip_addrs_nets())
        a, n = ips[0]
        assert a == ipa.IPv6Address('2001:db8:690:42::3')
        assert n == ipa.IPv6Network('2001:db8:690:42::/64')
        #
        # A default route case
        ip_route = 'ipv6 route ::/0 Gig0/0/0 2001:db8:690::1'
        dl = DocumentLine(1, ip_route)
        ips = list(dl._gen_ip_addrs_nets())
        assert len(ips) == 2
        a, n = ips[0]
        assert a == ipa.IPv6Address('::')
        assert n == ipa.IPv6Network('::/0')
        a, n = ips[1]
        assert a == ipa.IPv6Address('2001:db8:690::1')
        assert n is None

    def test_ipv6_has_ip(self):
        """Test IPv6 address / network matching"""
        #
        # Two IPs should be found in this line, one parsed as IPv6Network, one as IPv6Address
        ip_route = 'ipv6 route 2001:db8:690:f00b::/64 Tunnel6 2001:db8:690::1'
        dl = DocumentLine(1, ip_route)
        assert dl.has_ip(ipa.IPv6Address('2001:db8:690:f00b::'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00b::14'))
        assert dl.has_ip(ipa.IPv6Address('2001:db8:690::1'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00d::14'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690::2'))
        assert not dl.has_ip(ipa.IPv4Address('192.0.2.1'))
        assert dl.has_ip(ipa.IPv6Network('2001:db8:690:f00b::/64'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690::/64'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690:f00d::/64'))
        assert not dl.has_ip(ipa.IPv4Network('192.0.2.0/24'))
        assert not dl.has_ip(ipa.IPv6Interface('2001:db8:690:f00b::1/64'))
        assert not dl.has_ip(ipa.IPv4Interface('192.0.2.1/24'))
        #
        # One IP should be found in this line, parsed as IPv6Interface
        ip_cidr = 'ipv6 address 2001:db8:690:42::3/64'
        dl = DocumentLine(1, ip_cidr)
        assert dl.has_ip(ipa.IPv6Address('2001:db8:690:42::3'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00d::3'))
        assert not dl.has_ip(ipa.IPv4Address('192.0.2.1'))
        assert dl.has_ip(ipa.IPv6Network('2001:db8:690:42::/64'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690:f00d::/64'))
        assert not dl.has_ip(ipa.IPv6Network('::/0'))
        assert not dl.has_ip(ipa.IPv4Network('192.0.2.0/24'))
        assert dl.has_ip(ipa.IPv6Interface('2001:db8:690:42::3/64'))
        assert not dl.has_ip(ipa.IPv6Interface('2001:db8:690:42::2/64'))
        assert not dl.has_ip(ipa.IPv6Interface('2001:db8:690:f00d::2/64'))
        assert not dl.has_ip(ipa.IPv4Interface('192.0.2.1/24'))
        #
        # A default route case
        ip_route = 'ipv6 route ::/0 Gig0/0/0 2001:db8:690::1'
        dl = DocumentLine(1, ip_route)
        assert dl.has_ip(ipa.IPv6Address('2001:db8:690::1'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00d::3'))
        assert not dl.has_ip(ipa.IPv4Address('192.0.2.1'))
        assert dl.has_ip(ipa.IPv6Network('::/0'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690::/64'))
        assert not dl.has_ip(ipa.IPv4Network('192.0.2.0/24'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690:f00d::/64'))
        assert not dl.has_ip(ipa.IPv4Interface('192.0.2.1/24'))

    def test_ipv4_parsing(self):
        """Test IPv4 address / network parsing and conversion to ipaddress objects"""
        #
        # Two IPs should be found in this line, one parsed as IPv4Network, one as IPv4Address
        ip_route = 'ip route 203.0.113.0 255.255.255.0 192.0.2.233'
        dl = DocumentLine(1, ip_route)
        ips = list(dl._gen_ip_addrs_nets())
        assert len(ips) == 2
        a, n = ips[0]
        assert a == ipa.IPv4Address('203.0.113.0')
        assert n == ipa.IPv4Network('203.0.113.0/24')
        a, n = ips[1]
        assert a == ipa.IPv4Address('192.0.2.233')
        assert n is None
        #
        # One IP should be found in this line, parsed as IPv4Interface
        ip_cidr = 'ip address 203.0.113.129/25'
        dl = DocumentLine(1, ip_cidr)
        ips = list(dl._gen_ip_addrs_nets())
        a, n = ips[0]
        assert a == ipa.IPv4Address('203.0.113.129')
        assert n == ipa.IPv4Network('203.0.113.128/25')
        #
        # A default route case
        ip_route = 'ip route 0.0.0.0 0.0.0.0 192.0.2.233'
        dl = DocumentLine(1, ip_route)
        ips = list(dl._gen_ip_addrs_nets())
        assert len(ips) == 2
        a, n = ips[0]
        assert a == ipa.IPv4Address('0.0.0.0')
        assert n == ipa.IPv4Network('0.0.0.0/0')
        a, n = ips[1]
        assert a == ipa.IPv4Address('192.0.2.233')
        assert n is None

    def test_ipv4_has_ip(self):
        """Test IPv4 address / network matching"""
        #
        # Two IPs should be found in this line, one parsed as IPv4Network, one as IPv4Address
        ip_route = 'ip route 203.0.113.0 255.255.255.0 192.0.2.233'
        dl = DocumentLine(1, ip_route)
        assert dl.has_ip(ipa.IPv4Address('203.0.113.0'))
        assert dl.has_ip(ipa.IPv4Address('192.0.2.233'))
        assert not dl.has_ip(ipa.IPv4Address('203.0.113.1'))
        assert not dl.has_ip(ipa.IPv4Address('192.0.2.0'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00b::14'))
        assert dl.has_ip(ipa.IPv4Network('203.0.113.0/24'))
        assert not dl.has_ip(ipa.IPv4Network('203.0.113.128/29'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690:f00b::/64'))
        assert not dl.has_ip(ipa.IPv4Interface('203.0.113.1/24'))
        assert not dl.has_ip(ipa.IPv4Interface('203.0.113.1/24'))
        assert not dl.has_ip(ipa.IPv6Interface('2001:db8:690:f00b::1/64'))
        #
        # One IP should be found in this line, parsed as IPv4Interface
        ip_cidr = 'ip address 203.0.113.129/25'
        dl = DocumentLine(1, ip_cidr)
        assert dl.has_ip(ipa.IPv4Address('203.0.113.129'))
        assert not dl.has_ip(ipa.IPv4Address('203.0.113.130'))
        assert not dl.has_ip(ipa.IPv4Address('203.0.113.127'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00b::14'))
        assert dl.has_ip(ipa.IPv4Network('203.0.113.128/25'))
        assert not dl.has_ip(ipa.IPv4Network('203.0.113.192/26'))
        assert not dl.has_ip(ipa.IPv4Network('192.0.2.0/26'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690:f00b::/64'))
        assert dl.has_ip(ipa.IPv4Interface('203.0.113.129/25'))
        assert not dl.has_ip(ipa.IPv4Interface('203.0.113.128/25'))
        assert not dl.has_ip(ipa.IPv4Interface('203.0.113.0/24'))
        assert not dl.has_ip(ipa.IPv6Interface('2001:db8:690:f00b::1/64'))
        #
        # A default route case
        ip_route = 'ip route 0.0.0.0 0.0.0.0 192.0.2.233'
        dl = DocumentLine(1, ip_route)
        assert dl.has_ip(ipa.IPv4Address('0.0.0.0'))
        assert dl.has_ip(ipa.IPv4Address('192.0.2.233'))
        assert not dl.has_ip(ipa.IPv4Address('1.1.1.1'))
        assert not dl.has_ip(ipa.IPv6Address('2001:db8:690:f00b::14'))
        assert dl.has_ip(ipa.IPv4Network('0.0.0.0/0'))
        assert not dl.has_ip(ipa.IPv4Network('198.51.100.0/24'))
        assert not dl.has_ip(ipa.IPv6Network('2001:db8:690:f00b::/64'))

    def test_identity_equality(self):
        """Test equality, identity, and hashing functions"""
        test_line = 'ip route 203.0.113.0 255.255.255.0 192.0.2.233'
        dl1 = DocumentLine(1, test_line)
        dl2 = DocumentLine(1, test_line)
        assert dl1 == dl2
        assert dl1 is not dl2
        assert hash(dl1) == hash(dl2)
        assert len({dl1, dl2}) == 1
        dl2 = DocumentLine(2, test_line)
        assert dl1 != dl2
        assert hash(dl1) != hash(dl2)
        assert len({dl1, dl2}) == 2

    def test_string_method_passthru(self):
        """Test string method passthrough"""
        test_line = ' ip route 203.0.113.0 255.255.255.0 192.0.2.233'
        dl = DocumentLine(1, test_line)
        assert dl.startswith(test_line[:4])
        assert dl.endswith(test_line[-4:])
        assert len(dl.split()) == 5
        assert '|'.join(dl.split()) == test_line.lstrip().replace(' ', '|')
        assert str(dl) == test_line
        assert dl.lstrip() == test_line[1:]
        assert 'foobr' not in dl
        assert '203.0.113.0' in dl

    def test_gen(self):
        """Test computation of the 'gen', 'parent', 'children', and 'all_descendants' attributes"""
        lines = ['interface GigabitEthernet0/0/0',
                 ' description Gig0/0/0',
                 '  description-modifier foobar',
                 ' ip address 192.0.2.103 192.0.2.254']
        dl_list = [DocumentLine(1, lines[0]), DocumentLine(2, lines[1])]
        dl_list[1].parent = dl_list[0]
        dl_list.append(DocumentLine(3, lines[2], parent=dl_list[1]))
        dl_list.append(DocumentLine(3, lines[3], parent=dl_list[0]))
        dl_list[0].children = [dl_list[1], dl_list[3]]
        dl_list[1].children = [dl_list[2]]
        assert dl_list[0].gen == 1
        assert dl_list[1].gen == 2
        assert dl_list[2].gen == 3
        assert dl_list[3].gen == 2
        assert dl_list[0].parent is None
        assert dl_list[1].parent == dl_list[0]
        assert dl_list[2].parent == dl_list[1]
        assert dl_list[0].ancestors == []
        assert dl_list[1].ancestors == dl_list[0:1]
        assert dl_list[2].ancestors == dl_list[0:2]
        assert dl_list[3].ancestors == dl_list[0:1]
        assert dl_list[0].children == [dl_list[1], dl_list[3]]
        assert dl_list[1].children == [dl_list[2]]
        assert dl_list[2].children == []
        assert dl_list[3].children == []
        assert dl_list[0].all_descendants == dl_list[1:4]
        assert dl_list[1].all_descendants == dl_list[2:3]
        assert dl_list[2].all_descendants == []
        assert dl_list[3].all_descendants == []

    def test_is_comment(self):
        """Test 'is_comment" attribute"""
        test_line = '!ip route 203.0.113.0 255.255.255.0 192.0.2.233'
        assert DocumentLine(1, test_line).is_comment
        assert not DocumentLine(1, test_line[1:]).is_comment
        test_line = ' #ip route 203.0.113.0 255.255.255.0 192.0.2.233'
        assert DocumentLine(1, test_line).is_comment
        assert not DocumentLine(1, test_line[2:]).is_comment

    def test_family(self):
        """Test family() function and returning familial lines"""
        lines = ['interface GigabitEthernet0/0/0',
                 ' description Gig0/0/0',
                 '  description-modifier foobar',
                 ' ip address 192.0.2.103 255.255.255.254']
        dl_list = [DocumentLine(1, lines[0]), DocumentLine(2, lines[1])]
        dl_list[1].parent = dl_list[0]
        dl_list.append(DocumentLine(3, lines[2], parent=dl_list[1]))
        dl_list.append(DocumentLine(3, lines[3], parent=dl_list[0]))
        dl_list[0].children = [dl_list[1], dl_list[3]]
        dl_list[1].children = [dl_list[2]]
        assert dl_list[0].family() == dl_list
        assert dl_list[1].family() == dl_list[0:3]
        assert dl_list[2].family() == dl_list[0:3]
        assert dl_list[3].family() == [dl_list[0], dl_list[3]]
        assert dl_list[0].family(include_ancestors=False) == dl_list
        assert dl_list[1].family(include_ancestors=False) == dl_list[1:3]
        assert dl_list[2].family(include_ancestors=False) == dl_list[2:3]
        assert dl_list[3].family(include_ancestors=False) == dl_list[3:4]
        assert (dl_list[0].family(include_all_descendants=False) == \
                [dl_list[0], dl_list[1], dl_list[3]])
        assert dl_list[1].family(include_all_descendants=False) == dl_list[0:3]
        assert dl_list[2].family(include_all_descendants=False) == dl_list[0:3]
        assert dl_list[3].family(include_all_descendants=False) == [dl_list[0], dl_list[3]]
        assert dl_list[0].family(include_children=False) == dl_list[0:1]
        assert dl_list[1].family(include_children=False) == dl_list[0:2]
        assert dl_list[2].family(include_children=False) == dl_list[0:3]
        assert dl_list[3].family(include_children=False) == [dl_list[0], dl_list[3]]

    def test_ipv6_has_ip_valueerror(self):
        """Test invalid argument supplied to has_ip()"""
        ip_route = 'ipv6 route 2001:db8:690:f00b::/64 Tunnel6 2001:db8:690::1'
        dl = DocumentLine(1, ip_route)
        with self.assertRaises(ValueError):
            dl.has_ip(1)

    def test_repr(self):
        """Test repr string"""
        lines = ['interface GigabitEthernet0/0/0',
                 ' description Gig0/0/0',
                 '  description-modifier foobar',
                 ' ip address 192.0.2.103 192.0.2.254']
        dl_list = [DocumentLine(1, lines[0]), DocumentLine(2, lines[1])]
        dl_list[1].parent = dl_list[0]
        dl_list.append(DocumentLine(3, lines[2], parent=dl_list[1]))
        dl_list.append(DocumentLine(4, lines[3], parent=dl_list[0]))
        dl_list[0].children = [dl_list[1], dl_list[3]]
        dl_list[1].children = [dl_list[2]]
        r = repr(dl_list[0])
        assert r.startswith('<DocumentLine')
        assert 'num_children=2' in r
        assert 'gen=1' in r
        assert 'line_num=1' in r
        assert lines[0] in r
        r = repr(dl_list[1])
        assert 'num_children=1' in r
        assert 'gen=2' in r
        assert 'line_num=2' in r
        assert lines[1] in r
        r = repr(dl_list[2])
        assert 'num_children=0' in r
        assert 'gen=3' in r
        assert 'line_num=3' in r
        assert lines[2] in r
        r = repr(dl_list[3])
        assert 'num_children=0' in r
        assert 'gen=2' in r
        assert 'line_num=4' in r
        assert lines[3] in r

    def test_immutability(self):
        """Test immutability of line, line_num, ip_addrs, and ip_nets"""
        lines = ['interface GigabitEthernet0/0/0',
                 ' description Gig0/0/0',
                 '  description-modifier foobar',
                 ' ip address 192.0.2.103 192.0.2.254']
        dl_list = [DocumentLine(1, lines[0]), DocumentLine(2, lines[1])]
        with self.assertRaises(AttributeError):
            dl_list[0].line = 'foobr'
        with self.assertRaises(AttributeError):
            dl_list[0].line_num = 31337
        with self.assertRaises(AttributeError):
            dl_list[0].ip_addrs = {}
        with self.assertRaises(AttributeError):
            dl_list[0].ip_nets = {}

    def test_re_methods(self):
        """Test re_search, re_match, re_fullmatch"""
        line = 'router pythonprotocol GRAIL'
        dl = DocumentLine(1, line)
        r_valid = re.compile('grail', re.IGNORECASE)
        r_invalid = re.compile('0/0/0')
        assert isinstance(dl.re_search(r_valid), re.Match)
        assert dl.re_search(r_invalid, re.IGNORECASE) is None
        assert isinstance(dl.re_search('python'), re.Match)
        assert dl.re_search('midget') is None
        with self.assertRaises(ValueError):
            dl.re_search(None)
        assert isinstance(dl.re_match('router'), re.Match)
        assert dl.re_match('python') is None
        with self.assertRaises(ValueError):
            dl.re_match(None)
        assert isinstance(dl.re_fullmatch('router python.*'), re.Match)
        assert dl.re_fullmatch('router python') is None
        with self.assertRaises(ValueError):
            dl.re_fullmatch(None)
