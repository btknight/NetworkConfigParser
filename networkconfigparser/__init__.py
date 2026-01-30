"""NetworkConfigParser is a small module to parse structured documents, like Cisco or Juniper
network device configurations. Maintains familial relationships among lines for ease of further
parsing and analysis. Parses IP addresses for easier matching using the ipaddress library.

Quick Start
-----------

Example: We want to find interfaces on a Cisco IOS router that are shut down.


.. code-block:: python

    # Read in your config
    doc_lines = parse_from_file('config-filename.conf')

    # Find lines with "shutdown" in them
    shutdown_lines = [i for i in doc_lines if i.lstrip() == 'shutdown']

    # shutdown_lines consists of only the lines " shutdown" at present. To include the "interface"
    # lines:
    intf_and_shutdown_lines = [j for i in shutdown_lines for j in i.family()]

Now intf_and_shutdown_lines contains something similar to:

.. code-block:: text

    interface GigabitEthernet0/0/0
     shutdown
    interface GigabitEthernet0/0/1
     shutdown
    interface GigabitEthernet0/0/2
     shutdown

About Leading Space Structured Configuration
--------------------------------------------

Lines from a configuration document are read into an object, DocumentLine, which maintains the
connections between configuration directives. Consider the following example:

.. code-block:: text

    01: |router bgp 65500
    02: | bgp router-id 192.0.2.1
    03: | address-family ipv4 unicast
    04: |  network 192.0.2.16/29
    05: | !
    06: | neighbor 192.0.2.2
    07: |  remote-as 65500
    08: |  description iBGP peer EXAMPLE_ROUTER_02
    09: |  address-family ipv4 unicast
    10: |   route-reflector-client
    11: |   next-hop-self
    12: |   soft-reconfiguration inbound always

The first line would be parsed as a top-level object, generation number 1, with no parents of its
own. However it would have 4 children lines: 02, 03, 05, and 06. Each of those child lines is
prefixed with one space, indicating that they are sub-directives within the configuration section
"router bgp 65500".

The second line would be parsed as a child object of line 01. Its 'parent' attribute would be line
01. It would have no children of its own.

The third line would also be parsed as a child object of line 01. However, this object would have a
child of its own, line 04. The reason is line 04 has an additional space in front, indicating it is
a sub-directive of line 03.
"""
from networkconfigparser.documentline import DocumentLine
from networkconfigparser.parser import parse_from_file, parse_from_str_list, parse_from_str
from networkconfigparser.search_helpers import find_lines, parent_child_cb

__version__ = "0.3"
