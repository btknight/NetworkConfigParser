"""Defines the DocumentLine object, a node in a familial tree describing a structured document layout."""
import ipaddress as ipa
import logging
import re
from typing import Optional, List, Set


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
    def __init__(self, line_num: int, line: str, parent: Optional[object] = None):
        self.line_num = line_num
        self.line = line
        self.parent = parent
        self.children: List[object] = []
        self.ip_addrs: Set[ipa.IPv4Address | ipa.IPv6Address] = set()
        self.ip_nets: Set[ipa.IPv4Network | ipa.IPv6Network] = set()
        self._parse_ips(line)

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
        addr_match = False
        net_match = False
        match type(ip_obj):
            case ipa.IPv4Address | ipa.IPv6Address:
                addr_match = any(i == ip_obj for i in self.ip_addrs if i.version == ip_obj.version)
                net_match =  any(ip_obj in i for i in self.ip_nets  if i.version == ip_obj.version)
            case ipa.IPv4Network | ipa.IPv6Network:
                addr_match = any(i in ip_obj for i in self.ip_addrs if i.version == ip_obj.version)
                net_match =  any(ip_obj == i for i in self.ip_nets  if i.version == ip_obj.version)
            case ipa.IPv4Interface | ipa.IPv6Interface:
                addr_match = any(i == ip_obj.ip or i in ip_obj.network for i in self.ip_addrs
                                 if i.version == ip_obj.version)
                net_match =  any(ip_obj.network == i for i in self.ip_nets if i.version == ip_obj.version)
            case _:
                raise ValueError(f'ip_obj is a {type(ip_obj)} and not an ipaddress.IPv[46]Address, Network, or '
                                 'Interface. Don\'t forget to import the ipaddress module and supply your value to the '
                                 'desired object.')
        return addr_match or net_match

    def _parse_ips(self, line) -> None:
        """Search for IP addresses or IP networks in this line."""
        if line == '':
            return
        new_start = 0
        #
        # IPv6 network case
        if m := re.search(r'([0-9A-Fa-f]*:[0-9A-Fa-f:]+/\d+)', line):
            self._add_ip_net(m.group(1))
            new_start = m.end(1) + 1
        #
        # IPv6 address case, with no slash
        elif m := re.search(r'([0-9A-Fa-f]*:[0-9A-Fa-f:]+)', line):
            self._add_ip_addr(m.group(1))
            new_start = m.end(1) + 1
        #
        # IPv4 network case, with slash
        elif m := re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', line):
            self._add_ip_net(m.group(1))
            new_start = m.end(1) + 1
        #
        # IPv4 network case, with address and netmask separated by a space
        elif m := re.search(r'(\d+\.\d+\.\d+\.\d+ \d+\.\d+\.\d+\.\d+)', line):
            s = '/'.join(m.group(1).split())
            self._add_ip_net(s)
            new_start = m.end(1) + 1
        #
        # IPv4 address case
        elif m := re.search(r'(\d+\.\d+\.\d+\.\d+)', line):
            self._add_ip_addr(m.group(1))
            new_start = m.end(1) + 1
        #
        # If a match was found, continue parsing the line for any additional matches
        if new_start > 0:
            self._parse_ips(line[new_start:])

    def _add_ip_addr(self, ip):
        """Attempt to add what looks like an IP address to the tracking set."""
        try:
            self.ip_addrs.add(ipa.ip_address(ip))
            logging.debug(f'DocumentLine: adding IP address "{ip}"')
        except ValueError:
            pass

    def _add_ip_net(self, ip):
        """Attempt to add what looks like an IP network to the tracking set. Include both address and network."""
        net_fail = False
        try:
            ip_net = ipa.ip_network(ip, strict=True)
            logging.debug(f'DocumentLine: adding IP network "{ip}"')
            self.ip_nets.add(ip_net)
            self.ip_addrs.add(ip_net.network_address)
        except (ipa.AddressValueError, ValueError):
            net_fail = True
        if net_fail:
            try:
                ip_intf = ipa.ip_interface(ip)
                logging.debug(f'DocumentLine: adding IP interface "{ip}"')
                self.ip_nets.add(ip_intf.network)
                self.ip_addrs.add(ip_intf.ip)
            except ValueError:
                pass

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

    def __hash__(self):
        return hash(self.line)

    def __str__(self):
        return self.line

    def __repr__(self):
        return f'<{self.__class__.__name__} gen={self.gen} num_children={len(self.children)} '\
               f'num_ip_addrs={len(self.ip_addrs)} num_ip_nets={len(self.ip_nets)} line_num={self.line_num}: '\
               f'"{self.line}">'

    def __getattr__(self, item):
        """Pass unknown attributes and method calls to self.line for text manipulation and validation.

        Args:
            item:
                Name of the attribute to pass to self.line

        Returns:
            Attribute or method from self.line that was called
        """
        return getattr(self.line, item)
