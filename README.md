# NetworkConfigParser

A small module to parse structured documents, like Cisco or Juniper network device configurations. Maintains
relationships among lines for ease of further parsing and analysis.

## Quick Start and Examples

### Example 1: Finding interfaces on a Cisco IOS router that are shut down

1. Read in your config

`doc_lines = parse_from_file('config-filename.conf')`

2. Find lines with "shutdown" in them. Here, we include also the ancestor lines, which are the "interface IntfName0" lines.

`intf_and_shutdown_lines = find_line_and_ancestors(doc_lines, lambda o: o.lstrip() == 'shutdown')`

3. The list now may contain something similar to:

`interface GigabitEthernet0/0/0
 shutdown
interface GigabitEthernet0/0/2
 shutdown
interface GigabitEthernet0/0/3
 shutdown`

### Example 2: Find references to an interface name

1. Read in your config

`doc_lines = parse_from_file('config-filename.conf')`

2. Find lines with the interface name in them, including only the ancestor lines

`shutdown_lines = find_line_and_ancestors(doc_lines, lambda o: 'GigabitEthernet0/0/0' in o)`

3. The list now may contain something similar to:

`interface GigabitEthernet0/0/0
router isis ISIS-INSTANCE
 interface GigabitEthernet0/0/0
mpls ldp
 interface GigabitEthernet0/0/0`

### Example 3: Find route policies and their contents

1. Read in your config - see above
2. Find lines with the interface name in them, including only the ancestor lines

`rp_lines = find_line_ancestors_descendants(doc_lines, lambda o: o.startswith('route-policy') or o.startswith('route-map'))`

3. The list `rp_lines` now may contain something similar to:

`route-map BGP-TO-OSPF deny 10
 match ip address prefix-list BLOCK-PREFIX
route-map BGP-TO-OSPF deny 20
 set metric 100`

Or for an IOS XR device:

`route-policy BGP-TO-OSPF
 if destination not in BLOCK-PREFIX then
  set metric 100
 else
  drop
 endif
end-policy`

### Find IOS XR BGP neighbors that do not have a particular route-policy configured

Here we include descendants only.

`doc_lines = parse_from_file('config-filename.conf')
router_bgp_lines = find_line_and_descendants(doc_lines, lambda o: o.startswith('router bgp '))
nbr_lines = find_line_and_descendants(router_bgp_lines, lambda o: o.lstrip().startswith('neighbor ') and not
  any(['route-policy OSPF-TO-BGP' in i for i in o.all_descendants])`

### Find top-level statements only

`doc_lines = parse_from_file('config-filename.conf')
top_level_lines = [i for i in doc_lines if i.gen == 1]`

## Why the author wrote this library / Critiques of the current state of things

- Most libraries include a filter() or find_objects() method, which constrains searching to what is supported by the
- method. A more flexible way is to include objects based on a callback function, where the user has a freer hand in
- specifying match criteria. Common methods are included to preserve existing functionality.

- More than one library supports insert and deletion in an object-based tree. Here, we use a simple list. List
- comprehensions are used to filter the list. List mechanics may be used to insert new lines.

- Other library objects tend not to be Pythonic. Here, care is taken to make standard methods work as expected, like
- `str(line_object)` and `line_object.startswith('route-policy ')`.

- No parsing is done to recognize the elements within a line. Only the familial relationship is tracked.
- Since there is great variability even within a vendor's OS offerings, that further parsing is left to the user.
