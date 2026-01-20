# NetworkConfigParser

A small module to parse structured documents, like Cisco or Juniper network device configurations. Maintains
relationships among lines for ease of further parsing and analysis. Parses IP addresses for easier matching using the 
ipaddress library.

## Quick Start and Examples

Please see the README-examples.ipynb notebook for discussion and examples of usage.

---

## Why the author wrote this library / Critiques of the current state of things

- Most libraries include a filter() or find_objects() function or method, which constrains searching the tree to what
is supported by the method, typically regular expressions. A more flexible way is to support callback functions as
well as regular expressions. With functions, the user has a freer hand in specifying match criteria.

- More than one library supports inserts and changes in an object-based tree. NetworkConfigParser does not support this.
The goal of this library is to enable easy and flexible querying of the document and its structure. We use a simple
list to store the objects, so standard list comprehensions can be used to query the data. If the user needs to add or
change configuration and have the document tree update itself, the user is encouraged to stick with the library that
they use today. Or, a list comprehension can easily project the matching element and its family into a list of strings,
and the user may add the desired elements to that list. That list may then be re-parsed into DocumentLine objects.

- Other library objects tend to be less Pythonic, making access to search tools clunky. Here, care is taken to make
string methods work as expected, such as `line_object.startswith('route-policy ')` or `'description' in line_object`. 
Because the regular expression library does not perform a str() on text to be matched, DocumentLine has wrapper methods
re_search(), re_match(), and re_fullmatch() included for less clunky searching.

- In other libraries, working with IP addresses can be difficult. IP networks and addresses are essential to daily life
as a network administrator. This library parses each line of text for IP addresses and networks, converts them to
objects from the standard Python ipaddress library, and stores those in sets with the associated line. Searching for
lines that match an IP address or network becomes simpler, more deterministic, and more flexible.

- No other parsing is done to recognize the elements within a line. Only the familial relationship is tracked.
Since there is great variability in configuration directives even within a vendor's OS family line, that further
parsing is left to the user. This keeps NetworkConfigParser's implementation and API from growing too far, and keeps
the module size small.
