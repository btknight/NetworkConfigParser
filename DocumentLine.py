"""Defines the DocumentLine object, a node in a familial tree describing a structured document layout."""
import ipaddress as ipa
import logging
import re
from typing import Optional, List, Callable, Iterator, Tuple


IPAddrAndNet = Tuple[ipa.IPv4Address | ipa.IPv6Address, ipa.IPv4Network | ipa.IPv6Network | None]


class DocumentLine(object):
    """Represents a single line in a document.

    Manages the lineage of a line of text from a structured document, like a Cisco or Juniper configuration file. This
    retains links to parent and child items. If this item is desired as part of a search, but the ancestor or
    descendant items are required also, this object can retrieve those.

    This object passes undefined method calls to the 'line' attribute, the line of text, making working with text
    simpler.

    Attributes
    ----------
    line:
        A str containing the text of the line.
    line_num:
        int line number from the original document.
    parent:
        The parent DocumentLine object for this object, otherwise None if there is this is a top-level object.
    children:
        A list of DocumentLine objects that are this object's children.
    gen:
        An int, starting from 1, indicating the generation level of the object. 1 indicates a top-level object,
        2 indicates a child of a top-level object, 3 is a grandchild, and so on.
    ancestors:
        A list of DocumentLine objects of this object's ancestors, sorted from top-level object to this object's parent.
    all_descendants:
        A list of DocumentLine objects of all children, grandchildren, great-grandchildren, etc. of this object,
        ordered in the sequence in which they appear in the configuration.

    Methods
    -------
    family:
        Returns a list of family objects, optionally including ancestors, itself, children, and all descendants.
    """
    #
    # Stores compiled re.Pattern objects for use in DocumentLine._gen_ip_addrs_nets().
    ip_patterns = {
        'ipv6_net': re.compile(r'([0-9A-Fa-f]{0,4}:[0-9A-Fa-f]{0,4}:[0-9A-Fa-f:]*/\d+)'),
        'ipv6_addr': re.compile(r'([0-9A-Fa-f]{0,4}:[0-9A-Fa-f]{0,4}:[0-9A-Fa-f:]*)'),
        'snmp_oid': re.compile(r'\d+\.\d+\.\d+\.\d+\.'),
        'ipv4_cidr': re.compile(r'(?<![\.\-])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})'),
        'ipv4_addr_netmask': re.compile(r'(?<![\.\-])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\.\-])'),
        'ipv4_addr': re.compile(r'(?<![\.\-])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\.\-])'),
    }

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
        return self._line_num

    @property
    def line(self):
        return self._line

    @property
    def ip_addrs(self):
        """Returns a set of IPv[46]Address objects that were parsed in this document line.

        This property method creates the set on first access.

        Returns:
            A set of IPv[46]Address objects.
        """
        if not self._ips_parsed:
            self._create_ip_sets()
        return self._ip_addrs

    @property
    def ip_nets(self):
        """Returns a set of IPv[46]Network objects that were parsed in this document line.

        This property method creates the set on first access.

        Returns:
            A set of IPv[46]Network objects.
        """
        if not self._ips_parsed:
            self._create_ip_sets()
        return self._ip_nets

    @property
    def is_comment(self):
        """True if this line is a comment.

        Returns:
            A bool indicating if the line is a comment."""
        comment_chars = ['!', '#']
        return any(self.line.lstrip().startswith(i) for i in comment_chars)

    @property
    def gen(self) -> int:
        """The generation level of the line.

        1 indicates a top-level object, 2 indicates a child of a top-level object, 3 is a grandchild, and so on.

        Returns:
            Integer of the generation level
        """
        if self.parent is None:
            return 1
        return self.parent.gen + 1

    @property
    def ancestors(self) -> List[object]:
        """A list of DocumentLine objects of this object's ancestors.

        Returns:
            A list of ancestors of this object, sorted from the top-level to the immediate parent.
        """
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

    @property
    def all_descendants(self) -> List[object]:
        """Returns all descendants of this object.

        Returns:
            List of DocumentLine objects of all children, grandchildren, great-grandchildren, etc. of this
            object, ordered in the sequence in which they appear in the configuration.
        """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.all_descendants)
        return descendants

    def family(self,
               include_ancestors: bool = True,
               include_children: bool = True,
               include_all_descendants: bool = True) -> List[object]:
        """Provides a list of family objects, optionally including ancestors, itself, children, and all descendants.

        Args:
            include_ancestors:
                A bool indicating whether to include ancestors. Default is True.
            include_children:
                A bool indicating whether to include immediate children of this object. Default is True.
            include_all_descendants:
                A bool indicating whether to include grandchildren, great-grandchildren, etc of this object. Default is
                True.

        Returns:
            List of DocumentNode objects in order from top-level ancestors, to the object itself, to all descendants,
            in the same order as they were read by the parser.
        """
        family = []
        if include_ancestors:
            family.extend(self.ancestors)
        family.append(self)
        if include_children and not include_all_descendants:
            family.extend(self.children)
        elif include_children and include_all_descendants:
            family.extend(self.all_descendants)  # All? NO! ALL!
        return family

    def has_ip(self,
               ip_obj: ipa.IPv4Address | ipa.IPv4Network | ipa.IPv6Interface | ipa.IPv6Address | ipa.IPv6Network | \
                       ipa.IPv6Interface) -> bool:
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
                raise ValueError(f'ip_obj is a {type(ip_obj)} and not an ipaddress.IPv[46]Address, Network, or '
                                 'Interface')
        return ip_match

    def _create_ip_sets(self) -> None:
        """Creates the IP sets self.ip_addrs and self.ip_nets. Called by the accessor properties on first request."""
        addrs_nets = [i for i in self._gen_ip_addrs_nets()]
        self._ip_addrs = frozenset({a for a, _ in addrs_nets})
        self._ip_nets  = frozenset({n for _, n in addrs_nets if n is not None})
        self._ips_parsed = True
        return

    def _gen_ip_addrs_nets(self) -> Iterator[IPAddrAndNet]:
        """Iterator that looks for IP addresses or IP networks in this line.

        If this document line has a term that looks like an IP address, this iterator will return that IP as an
        IPv[46]Address object. Additionally, if the IP looks more like a network statement (ex. '192.0.2.0/24',
        '192.0.2.0 255.255.255.0', '192.0.2.0 0.0.0.255', '2001:db8:690:42::/64'), an IPv[46]Network object will be
        returned also.

        Yields:
            A tuple (addr, net) where addr is an IPv[46]Address, and net is either an IPv[46]Network object or None
            if only an address was detected.
        """
        line = self.line
        def try_search_and_parse(pattern: re.Pattern,
                                 convert_fn: Callable[[str], Optional[IPAddrAndNet]],
                                 match_group: int = 1,
                                 match_transform: Callable[[str], str] = lambda x: x) -> Optional[IPAddrAndNet]:
            """Attempts to parse an IP in the line that this object represents.

            Args:
                pattern:
                    Regular expression to match the IP address text.
                convert_fn:
                    The private function to be used to convert the string to an ipaddress object. Use self._add_ip_net
                    for networks and interfaces, self._add_ip_addr for single addresses.
                match_group:
                    The match group to select from re.Match.
                match_transform:
                    The function to be used to transform the IP text from the re.Match result. Defaults to an identity
                    function that returns the identical string passed to it.

            Returns:
                The end index of the string that was matched, or None if there was no match or there was a
                failure of the ipaddress library to parse the extracted IP string.
                """
            nonlocal line
            m = re.search(pattern, line)
            if m:
                #
                # Extract the match
                ip = m.group(match_group)
                #
                # Run the user-supplied transform on the extracted object (used to add a / between address and netmask
                # from IOS configurations, so IPv4Network knows about netmask)
                ip = match_transform(ip)
                logging.debug(f'try_search_and_parse: Found re match {ip}')
                #
                # If the conversion to an ipaddress object is successful
                if result := convert_fn(ip):
                    logging.debug(f'try_search_and_parse: {ip} converted to {result}')
                    #
                    # Shrink the line to the end of the matched term
                    end = m.end(match_group)
                    logging.debug(f'try_search_and_parse: New end is {end}: "{line[:end]}" || "{line[end:]}"')
                    line = line[end:]
                    return result
                logging.debug(f'try_search_and_parse: failed to parse {ip}')
            return None
        #
        # SNMP OIDs often look like IPs. If OID, exit.
        if re.search(self.ip_patterns['snmp_oid'], self.line):
            return
        #
        # Search in our copy of self.line
        while len(line) > 0:
            #
            # IPv6 network case
            if net_addr_t := try_search_and_parse(self.ip_patterns['ipv6_net'], self._parse_ip_net):
                yield net_addr_t
            #
            # IPv6 address case, with no slash
            elif net_addr_t := try_search_and_parse(self.ip_patterns['ipv6_addr'], self._parse_ip_addr):
                yield net_addr_t
            #
            # IPv4 network case, with slash
            elif net_addr_t := try_search_and_parse(self.ip_patterns['ipv4_cidr'], self._parse_ip_net):
                yield net_addr_t
            #
            # IPv4 network case, with address and netmask separated by a space
            elif net_addr_t := try_search_and_parse(self.ip_patterns['ipv4_addr_netmask'],
                                           self._parse_ip_net,
                                           match_transform=lambda x: '/'.join(x.split())):
                yield net_addr_t
            #
            # IPv4 address case
            elif net_addr_t := try_search_and_parse(self.ip_patterns['ipv4_addr'], self._parse_ip_addr):
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
        """Pass unknown attributes and method calls to self.line for text manipulation and validation.

        Args:
            item:
                Name of the attribute to pass to self.line

        Returns:
            Attribute or method from self.line that was called
        """
        return getattr(self._line, item)
