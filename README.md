# NetworkConfigParser

A small module to parse structured documents, like Cisco or Juniper network device configurations. Maintains
familial relationships among lines for ease of further parsing and analysis. Parses IP addresses for easier matching
using the ipaddress library.

# Intended Purpose

- Auditing Cisco or Juniper network device configurations
- Extracting key configuration elements for importing into a Configuration Management System

---

# Quick Start and Examples

Install the package with your package manager of choice:
```pip install NetworkConfigParser```

Import the module, load a network device configuration, and start searching within it:

```from networkconfigparser import *

doc_lines = parse_from_file('example-device-config.txt')

search_result = find_lines(doc_lines, r'^interface ')
```

---

# Quick Overview

## Configuration parsing

`doc_lines = parse_from_file(filename)`
`doc_lines = parse_from_str_list(lines_list)`
`doc_lines = parse_from_str(concatenated_lines)`

Used to parse the configuration into a list of DocumentLine objects.

## Representation

`DocumentLine(line_num, line)`

Object representing a line from a configuration document.

`str(DocumentLine)`

The original line from the document.

`DocumentLine.ancestors`

List of ancestors of the object, i.e. `['interface Eth0/0']` if called on ` description Ethernet interface`.

`DocumentLine.children`
`DocumentLine.all_descendants`

List of immediate children or all descendants of the object.

`DocumentLine.ip_addrs`

Sets of IPv4Address / IPv6Address objects found in the line.

`DocumentLine.ip_nets`

Same as above, except IPv4Network / IPv6Network objects.

## Searching

`find_lines(doc_lines, search_expression)`

Searches for lines in a list of DocumentLine objects. For the search parameter, `find_lines()` accepts:
- a string regular expression
- a compiled regular expression
- a function taking a DocumentLine as its sole argument and returning a boolean indicating a match
- a list of any combination of the above items, for matching children with particular parents

`parent_child_cb('parent_criteria', 'child_criteria')`

Matches a parent line containing a specific child. Returns a search function to supply to `find_lines()`.

## For More

The above is not a conclusive list of all functions, methods, or parameters available.

Please see the README-examples.ipynb notebook for further discussion and examples of usage.

# Issues

# Contributing

# License

GPLv3

# Credits

Brian Knight <ncp.codelab @at@ knight-networks.com>
