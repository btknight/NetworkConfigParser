"""Defines the DocumentLine object, a node in a familial tree describing a structured document
layout."""
import ipaddress as ipa
from operator import attrgetter
import logging
import re
from typing import Optional, List, Callable, Iterator, Tuple


IPAddrAndNet = Tuple[ipa.IPv4Address | ipa.IPv6Address, ipa.IPv4Network | ipa.IPv6Network | None]


class DocumentLine:
    """Represents a single line in a document.

    Manages the lineage of a line of text from a structured document, like a Cisco or Juniper
    configuration file. Retains links to parent and child items.

    This object passes undefined method calls to the 'line' attribute, the line of text, making
    working with text simpler:

    .. code-block:: python

        >>> dl = DocumentLine(1, 'interface TenGigE0/0/0/0')
        >>> dl.startswith('interface ')
        Out[2]: True
        >>> 'TenGig' in dl
        Out[3]: True
        >>> dl.endswith('The Spanish Inquisition')
        Out[4]: False

    Parameters:
        line_num:
            An int indicating the line number of the line in the source document.
        line:
            The text of the line.
        parent:
            The DocumentLine object that is the immediate parent of this object. Defaults to None.
            Can be set after object creation.
    """
    _ip_patterns = {
        'ipv6_net': re.compile(r'([0-9A-Fa-f]{0,4}:[0-9A-Fa-f]{0,4}:[0-9A-Fa-f:]*/\d+)'),
        'ipv6_addr': re.compile(r'([0-9A-Fa-f]{0,4}:[0-9A-Fa-f]{0,4}:[0-9A-Fa-f:]*)'),
        'snmp_oid': re.compile(r'\d+\.\d+\.\d+\.\d+\.'),
        'ipv4_cidr': re.compile(r'(?<![\.\-])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})'),
        'ipv4_addr_netmask': re.compile(r'(?<![\.\-])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} '
                                        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\.\-])'),
        'ipv4_addr': re.compile(r'(?<![\.\-])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\.\-])'),
    }
    """Stores compiled re.Pattern objects for use in DocumentLine._gen_ip_addrs_nets()."""

    def __init__(self, line_num: int, line: str, parent: Optional[object] = None):
        self._line_num = line_num
        self._line = line
        self.parent = parent
        self.children: List[object] = []
        self._ips_parsed = False
        self._ip_addrs = None
        self._ip_nets = None

    @property
    def line_num(self):
        """An int indicating the line number of the line in the source document."""
        return self._line_num

    @property
    def line(self):
        """The text from the document. This value is rstrip()'ed when read in, so trailing spaces
        will not be present.
        """
        return self._line

    @property
    def ip_addrs(self):
        """A set of ipaddress.IPv[46]Address objects of IPs that were detected in this document
        line.

        This property method creates the set on first access.
        """
        if not self._ips_parsed:
            self._create_ip_sets()
        return self._ip_addrs

    @property
    def ip_nets(self):
        """A set of ipaddress.IPv[46]Network objects of IP networks that were detected in this
        document line.

        This property method creates the set on first access.
        """
        if not self._ips_parsed:
            self._create_ip_sets()
        return self._ip_nets

    @property
    def is_comment(self):
        """True if this line is a comment, e.g. starts with zero or more spaces followed by "!" or
        "#"."""
        comment_chars = ['!', '#']
        return any(self.line.lstrip().startswith(i) for i in comment_chars)

    @property
    def gen(self) -> int:
        """The generation level of the line. 1 indicates a top-level object, 2 indicates a child of
        a top-level object, 3 is a grandchild, and so on."""
        if self.parent is None:
            return 1
        return self.parent.gen + 1

    @property
    def ancestors(self) -> List[object]:
        """A list of DocumentLine objects of this object's ancestors, sorted from the top-level to
        the immediate parent."""
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

    @property
    def all_descendants(self) -> List[object]:
        """A list of all descendants of this object, ordered in the sequence in which they appear
        in the configuration."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.all_descendants)
        return descendants

    def re_match(self, pattern: str | re.Pattern, flags: int | re.RegexFlag = 0):
        """Runs a regular expression match on the document line.

        Equivalent to running re.match(pattern, self.line, flags). Handles compiled patterns as
        well as regular expression strings.

        Args:
            pattern:
                Regular expression to match, as a String or re.Pattern object
            flags:
                Flags to include to the call to re.match. Ignored if an re.Pattern is supplied.

        Returns:
            Result of call to re.match or pattern.match: re.Match object or None if no match
        """
        return self._re_dispatch('match', pattern, flags)

    def re_search(self, pattern: str | re.Pattern, flags: int | re.RegexFlag = 0):
        """Runs a regular expression search on the document line.

        Equivalent to running re.search(pattern, self.line, flags). Handles compiled patterns as
        well as regular expression strings.

        Args:
            pattern:
                Regular expression to search, as a String or re.Pattern object
            flags:
                Flags to include to the call to re.search. Ignored if an re.Pattern is supplied.

        Returns:
            Result of call to re.search or pattern.search: re.Match object or None if no search
        """
        return self._re_dispatch('search', pattern, flags)

    def re_fullmatch(self, pattern: str | re.Pattern, flags: int | re.RegexFlag = 0):
        """Runs a regular expression fullmatch on the document line.

        Equivalent to running re.fullmatch(pattern, self.line, flags). Handles compiled patterns as
        well as regular expression strings.

        Args:
            pattern:
                Regular expression to fullmatch, as a String or re.Pattern object
            flags:
                Flags to include to the call to re.fullmatch. Ignored if an re.Pattern is supplied.

        Returns:
            Result of call to re.fullmatch or pattern.fullmatch: re.Match object or None if no
            fullmatch
        """
        return self._re_dispatch('fullmatch', pattern, flags)

    def _re_dispatch(self, method_name: str, pattern: str | re.Pattern, /, *args, **kwargs):
        """Dispatches a method or function from the re module based on the pattern type supplied."""
        m = attrgetter(method_name)
        if isinstance(pattern, re.Pattern):
            return m(pattern)(self.line, *args, **kwargs)
        if isinstance(pattern, str):
            return m(re)(pattern, self.line, *args, **kwargs)
        raise ValueError(f're_search: pattern type {type(pattern)} is not supported')

    def family(self,
               include_ancestors: bool = True,
               include_self: bool = True,
               include_children: bool = True,
               include_all_descendants: bool = True) -> List[object]:
        """Provides a list of family objects, optionally including ancestors, itself, children, and
        all descendants.

        Args:
            include_ancestors:
                If False, omits all ancestors. Default is True.
            include_self:
                If False, omits itself from the result. Default is True.
            include_children:
                If False, omits immediate children. Default is True. Setting this to False sets
                include_all_descendants to False as well.
            include_all_descendants:
                If False, omits grandchildren, great-grandchildren, etc. Default is True. Setting
                this to True sets include_children to True as well.

        Returns:
            List of DocumentNode objects in order from top-level ancestors, to the object itself,
            to all descendants, in the same order as they were read by the parser.
        """
        #
        # If immediate children are not to be included, do not include all descendants.
        if not include_children:
            include_all_descendants = False
        #
        # If all descendants are to be returned, include immediate children as well.
        if include_all_descendants:
            include_children = True
        #
        family = []
        if include_ancestors:
            family.extend(self.ancestors)
        if include_self:
            family.append(self)
        if include_children and not include_all_descendants:
            family.extend(self.children)
        elif include_children and include_all_descendants:
            family.extend(self.all_descendants)  # All? NO! ALL!
        return family

    def has_ip(self,
               ip_obj: ipa.IPv4Address | ipa.IPv4Network | ipa.IPv4Interface | \
                       ipa.IPv6Address | ipa.IPv6Network | ipa.IPv6Interface) -> bool:
        """Searches for a match on a user-supplied ipaddress object.

        IPv[46]Address, Network, and Interface objects are supported.

        Args:
            ip_obj:
                ipaddress.IPv[46]Address, Network, or Interface object to compare.

        Returns:
            A bool indicating whether a match was found.

        Raises:
            ValueError:
                Raised if ip_obj is not a suitable object from the ipaddress library.
        """
        ip_match = False
        match type(ip_obj):
            case ipa.IPv4Address | ipa.IPv6Address:
                ip_match = ip_obj in self.ip_addrs
            case ipa.IPv4Network | ipa.IPv6Network:
                ip_match = ip_obj in self.ip_nets
            case ipa.IPv4Interface | ipa.IPv6Interface:
                ip_match = ip_obj.ip in self.ip_addrs and ip_obj.network in self.ip_nets
            case _:
                raise ValueError(f'ip_obj is a {type(ip_obj)} and not an ipaddress.IPv[46]Address, '
                                 'Network, or Interface')
        return ip_match

    def _create_ip_sets(self) -> None:
        """Creates the IP sets self.ip_addrs and self.ip_nets. Called by the accessor properties on
        first request."""
        addrs_nets = list(self._gen_ip_addrs_nets())
        self._ip_addrs = frozenset({a for a, _ in addrs_nets})
        self._ip_nets  = frozenset({n for _, n in addrs_nets if n is not None})
        self._ips_parsed = True

    def _gen_ip_addrs_nets(self) -> Iterator[IPAddrAndNet]:
        """Iterator that looks for IP addresses or IP networks in this line.

        If this document line has a term that looks like an IP address, this iterator will return
        that IP as an IPv[46]Address object. Additionally, if the IP looks more like a network
        statement (ex. '192.0.2.0/24', '192.0.2.0 255.255.255.0', '192.0.2.0 0.0.0.255',
        '2001:db8:690:42::/64'), an IPv[46]Network object will be returned also.

        Yields:
            A tuple (addr, net) where addr is an IPv[46]Address, and net is either an
            IPv[46]Network object or None if only an address was detected.
        """
        line = self.line
        def try_search_and_parse(pattern: re.Pattern,
                                 convert_fn: Callable[[str], Optional[IPAddrAndNet]],
                                 match_group: int = 1,
                                 match_transform: Callable[[str], str] = lambda x: x) \
                -> Optional[IPAddrAndNet]:
            """Attempts to parse an IP in the line that this object represents.

            Args:
                pattern:
                    Regular expression to match the IP address text.
                convert_fn:
                    The private function to be used to convert the string to an ipaddress object.
                    Use self._add_ip_net for networks and interfaces, self._add_ip_addr for single
                    addresses.
                match_group:
                    The match group to select from re.Match.
                match_transform:
                    The function to be used to transform the IP text from the re.Match result.
                    Defaults to an identity function that returns the identical string passed to it.

            Returns:
                The end index of the string that was matched, or None if there was no match or
                there was a failure of the ipaddress library to parse the extracted IP string.
                """
            nonlocal line
            m = re.search(pattern, line)
            if m:
                #
                # Extract the match
                ip = m.group(match_group)
                #
                # Run the user-supplied transform on the extracted object (used to add a / between
                # address and netmask from IOS configurations, so IPv4Network knows about netmask)
                ip = match_transform(ip)
                logging.debug('try_search_and_parse: Found re match %s', ip)
                #
                # If the conversion to an ipaddress object is successful
                if result := convert_fn(ip):
                    logging.debug('try_search_and_parse: %s converted to %s', ip, result)
                    #
                    # Shrink the line to the end of the matched term
                    end = m.end(match_group)
                    logging.debug('try_search_and_parse: New end is %s: "%s" || "%s"',
                                  end, line[:end], line[end:])
                    line = line[end:]
                    return result
                logging.debug('try_search_and_parse: failed to parse %s', ip)
            return None
        #
        # SNMP OIDs often look like IPs. If OID, exit.
        if re.search(self._ip_patterns['snmp_oid'], self.line):
            return
        #
        # Search in our copy of self.line
        while len(line) > 0:
            #
            # IPv6 network case
            if net_addr_t := try_search_and_parse(self._ip_patterns['ipv6_net'],
                                                  self._parse_ip_net):
                yield net_addr_t
            #
            # IPv6 address case, with no slash
            elif net_addr_t := try_search_and_parse(self._ip_patterns['ipv6_addr'],
                                                    self._parse_ip_addr):
                yield net_addr_t
            #
            # IPv4 network case, with slash
            elif net_addr_t := try_search_and_parse(self._ip_patterns['ipv4_cidr'],
                                                    self._parse_ip_net):
                yield net_addr_t
            #
            # IPv4 network case, with address and netmask separated by a space
            elif net_addr_t := try_search_and_parse(self._ip_patterns['ipv4_addr_netmask'],
                                           self._parse_ip_net,
                                           match_transform=lambda x: '/'.join(x.split())):
                yield net_addr_t
            #
            # IPv4 address case
            elif net_addr_t := try_search_and_parse(self._ip_patterns['ipv4_addr'],
                                                    self._parse_ip_addr):
                yield net_addr_t
            #
            # Otherwise no matches were found
            else:
                return

    @staticmethod
    def _parse_ip_addr(ip: str) -> Optional[IPAddrAndNet]:
        """Attempt to parse what looks like an IP address."""
        try:
            ip_addr = ipa.ip_address(ip)
        except ValueError:
            return None
        return ip_addr, None

    @staticmethod
    def _parse_ip_net(ip: str) -> Optional[IPAddrAndNet]:
        """Attempt to parse what looks like an IP network. Include both address and network."""
        net_fail = False
        try:
            ip_net = ipa.ip_network(ip, strict=True)
            ip_addr = ip_net.network_address
        except (ipa.AddressValueError, ipa.NetmaskValueError, ValueError):
            net_fail = True
        if net_fail:
            try:
                ip_intf = ipa.ip_interface(ip)
                ip_net = ip_intf.network
                ip_addr = ip_intf.ip
            except (ipa.AddressValueError, ipa.NetmaskValueError, ValueError):
                return None
        return ip_addr, ip_net

    def __contains__(self, item):
        return self.line.__contains__(item)

    def __format__(self, item):
        return self.line.__format__(item)

    def __iter__(self):
        return self.line.__iter__()

    def __getitem__(self, item):
        return self.line.__getitem__(item)

    def __sizeof__(self):
        return self.line.__sizeof__()

    def __len__(self):
        return self.line.__len__()

    def __mod__(self, item):
        return self.line.__mod__(item)

    def __mul__(self, item):
        return self.line.__mul__(item)

    def __rmul__(self, item):
        return self.line.__rmul__(item)

    def __eq__(self, other):
        if type(other) is type(self):
            return other.line_num == self._line_num and other.line == self._line
        return self._line == other

    def __hash__(self):
        return hash((self._line_num, self._line))

    def __str__(self):
        return self._line

    def __repr__(self):
        return f'<{self.__class__.__name__} gen={self.gen} num_children={len(self.children)} '\
               f'line_num={self._line_num}: "{self._line}">'

    def __getattr__(self, item):
        """Pass unknown attributes and method calls to self.line for text manipulation and
        validation.

        Args:
            item:
                Name of the attribute to pass to self.line

        Returns:
            Attribute or method from self.line that was called
        """
        return getattr(self._line, item)
