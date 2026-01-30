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

Object Representation
^^^^^^^^^^^^^^^^^^^^^

A DocumentLine object represents a line from a configuration document. Continuing with the above:

.. code-block:: python

    documentline = doc_lines[0]

    str(documentline)
    documentline.line

Calling str() on the DocumentLine object or accessing the ``line`` attribute gives the original line.

.. code-block:: python

    documentline.ancestors

The ``ancestors`` attribute gives the list of ancestors of the object, i.e. ``['interface Eth0/0']`` if called on ``description Ethernet interface``.

.. code-block:: python

    documentline.children
    documentline.all_descendants

The ``children`` attribute provides a list of immediate children; ``all_descendants`` gives all descendants of the
object.

.. code-block:: python

    documentline.ip_addrs

``ip_addrs`` contains a set of IPv4Address and/or IPv6Address objects found in the line.

.. code-block:: python

    documentline.ip_nets

``ip_nets`` is similar to the above, except IPv4Network / IPv6Network objects.

Searching
^^^^^^^^^

.. code-block:: python

    search_result = find_lines(doc_lines, search_expression)

Searches for lines in a list of DocumentLine objects.

For the search parameter, ``find_lines()`` accepts:

* a string regular expression
* a compiled regular expression
* a function taking a DocumentLine as its sole argument and returning a boolean indicating a match
* a list of any combination of the above items, for matching children with particular parents

Returns a list of matching lines.

Can also return ancestor and descendant lines if ``include_ancestors``, ``include_children``, or
``include_all_descendants`` are set to True.

.. code-block:: python

    search_term = parent_child_cb('parent_criteria', 'child_criteria')
    find_lines(doc_lines, search_term)

Matches a parent line containing a specific child. ``parent_child_cb()`` returns a search function to supply to
``find_lines()``.

For More
^^^^^^^^

The above is not an exhaustive list of all functions, methods, or parameters available.

Please see :doc:`notebooks/examples` for further discussion and examples of usage.

Documentation
-------------

Full documentation is available at `Read The Docs`_.

.. _Read The Docs: https://networkconfigparser.readthedocs.io/en/latest/

Issues
------

Please report issues to the `GitHub issue tracker`_.

.. _GitHub issue tracker: https://github.com/btknight/NetworkConfigParser/issues

Contributing
------------

There are no guidelines yet for contributing to development. This will be addressed as the project develops and
unfolds. Drop me a line via email or send me a pull request via GitHub, and we'll talk.

License
-------

GPLv3

Credit / Blame
--------------

Brian Knight <ncp.codelab @at@ knight-networks.com>

Many thanks to Ben Wells and Ben Julson at Sinch Voice for reviewing the code and for their comments.
