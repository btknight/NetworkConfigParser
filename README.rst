NetworkConfigParser README
==========================

NetworkConfigParser is a small module to parse structured documents, like Cisco or Juniper network device
configurations. Maintains familial relationships among lines for ease of further parsing and analysis. Parses IP
addresses for easier matching using the ipaddress library.

Intended Purpose
----------------

- Auditing Cisco or Juniper network device configurations
- Extracting key configuration elements for importing into a Configuration Management System

Quick Start and Examples
------------------------

Install the package with your package manager of choice:

``pip install NetworkConfigParser``

Import the module, load a network device configuration, and start searching within it:

.. code-block:: python

    from networkconfigparser import *

    doc_lines = parse_from_file('example-device-config.txt')

    search_result = find_lines(doc_lines, r'^interface ')

Configuration parsing
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    doc_lines = parse_from_file(filename)
    doc_lines = parse_from_str_list(lines_list)
    doc_lines = parse_from_str(concatenated_lines)

Used to parse the configuration into a list of DocumentLine objects.

Representation
^^^^^^^^^^^^^^

A DocumentLine object represents a line from a configuration document.

.. code-block:: python

    documentline = doc_lines[0]

    str(documentline)

The original line from the document.

.. code-block:: python

    documentline.ancestors

List of ancestors of the object, i.e. ``['interface Eth0/0']`` if called on ` description Ethernet interface`.

.. code-block:: python

    documentline.children
    documentline.all_descendants

List of immediate children or all descendants of the object.

.. code-block:: python

    DocumentLine.ip_addrs

Sets of IPv4Address or IPv6Address objects found in the line.

.. code-block:: python

    DocumentLine.ip_nets

Same as above, except IPv4Network / IPv6Network objects.

Searching
^^^^^^^^^

.. code-block:: python

    find_lines(doc_lines, search_expression)

Searches for lines in a list of DocumentLine objects.

For the search parameter, ``find_lines()`` accepts:
- a string regular expression
- a compiled regular expression
- a function taking a DocumentLine as its sole argument and returning a boolean indicating a match
- a list of any combination of the above items, for matching children with particular parents

.. code-block:: python

    search_term = parent_child_cb('parent_criteria', 'child_criteria')
    find_lines(doc_lines, search_term)

Matches a parent line containing a specific child. Returns a search function to supply to `find_lines()`.

For More
^^^^^^^^

The above is not a conclusive list of all functions, methods, or parameters available.

Please see the README-examples.ipynb notebook for further discussion and examples of usage.

Issues
------

Contributing
------------

License
-------

GPLv3

Credits
-------

Brian Knight <ncp.codelab @at@ knight-networks.com>
