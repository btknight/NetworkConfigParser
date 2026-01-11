# NetworkConfigParser

A small module to parse structured documents, like Cisco or Juniper network device configurations. Maintains
relationships among lines for ease of further parsing and analysis. Parses IP addresses for easier matching using the 
ipaddress library.

## Quick Start and Examples

---

### Example 1: Finding interfaces on a Cisco IOS router that are shut down

1. Read in your config

```$ cat config-filename.conf
interface GigabitEthernet0/0/0
 description Gig0/0/0 BIGROUTER1 Gig0/0/0/0
 ip address 192.0.2.103 192.0.2.254
 load-interval 30
 no negotiation auto
 bfd interval 50 min_rx 50 multiplier 3
 crypto map IPSEC-VPN
!
interface GigabitEthernet0/0/1
 description Gig0/0/1 BIGROUTER2 Gig0/0/0/0
 ip address 192.0.2.105 192.0.2.254
 load-interval 30
 no negotiation auto
 bfd interval 50 min_rx 50 multiplier 3
 crypto map IPSEC-VPN
!
interface GigabitEthernet0/0/2
 no ip address
 shutdown
 negotiation auto
!
interface GigabitEthernet0/0/3
 no ip address
 shutdown
 negotiation auto
!
interface GigabitEthernet0/0/4
 no ip address
 shutdown
 negotiation auto
!
interface GigabitEthernet0/0/5
 no ip address
 shutdown
 negotiation auto
```

`doc_lines = parse_from_file('config-filename.conf')`

2. Find lines with "shutdown" in them. By default, all parent and child lines are included, so we will also get the
2. interface name.

`intf_and_shutdown_lines = find_line(doc_lines, lambda o: o.lstrip() == 'shutdown')`

3. The list now may contain something similar to:

```
interface GigabitEthernet0/0/0
 shutdown
interface GigabitEthernet0/0/2
 shutdown
interface GigabitEthernet0/0/3
 shutdown
```

---

### Example 2: Find references to an interface name

1. Read in your config

```
doc_lines = parse_from_file('config-filename.conf')
```

2. Find lines with the interface name in them, including only the ancestor lines

`shutdown_lines = find_line(doc_lines, lambda o: 'GigabitEthernet0/0/0' in o, include_children=False)`

3. The list now may contain something similar to:

```
interface GigabitEthernet0/0/0
router isis ISIS-INSTANCE
 interface GigabitEthernet0/0/0
mpls ldp
 interface GigabitEthernet0/0/0
```

---

### Example 3: Find objects matching an IP network

1. Read in your config - see above
2. Find lines with the desired IP network in them


```
ip_net = ipaddress.ip_network('192.0.2.0/24')
ip_lines = find_line(doc_lines, lambda o: o.has_ip(ip_net) and not o.is_comment, include_ancestors=False,
                     include_children=False)
```

---

### Example 4: Extracting all IP addresses and networks referenced in a configuration

IPs are easy to gather with a set comprehension (shown below) or a list comprehension.

```
all_ip_addrs = {j for i in doc_lines for j in i.ip_addrs if not i.is_comment}
all_ip_nets =  {j for i in doc_lines for j in i.ip_nets  if not i.is_comment}
```

---

### Example 5: Find route policies and their contents

Find lines with the "route-policy" term in them, including only the ancestor lines:

```
rp_lines = find_line_ancestors_descendants(doc_lines, lambda o: o.startswith('route-policy') or o.startswith('route-map'))
```

The list `rp_lines` now may contain something similar to:

```
route-map BGP-TO-OSPF deny 10
 match ip address prefix-list BLOCK-PREFIX
route-map BGP-TO-OSPF deny 20
 set metric 100
```

Or for an IOS XR device:

```
route-policy BGP-TO-OSPF
 if destination not in BLOCK-PREFIX then
  set metric 100
 else
  drop
 endif
end-policy
```

---

### Example 6: Find IOS XR BGP neighbors that do not have a particular route-policy configured

Here we include descendants only.

```
doc_lines = parse_from_file('config-filename.conf')
router_bgp_lines = find_line(doc_lines, lambda o: o.startswith('router bgp '))
nbr_lines = find_line_and_descendants(router_bgp_lines, lambda o: o.lstrip().startswith('neighbor ') and not
  any(['route-policy OSPF-TO-BGP' in i for i in o.all_descendants])
```

---

### Example 7: Find top-level statements only

```
doc_lines = parse_from_file('config-filename.conf')
top_level_lines = [i for i in doc_lines if i.gen == 1]
```

---

## Why the author wrote this library / Critiques of the current state of things

- Most libraries include a filter() or find_objects() function or method, which constrains searching the tree to what
- is supported by the method. A more flexible way is to include objects based on a callback function, where the user
- has a freer hand in specifying match criteria. Though the use of list comprehensions to filter the list is strongly
- encouraged, common and familiar methods are included to preserve existing functionality.

- More than one library supports inserts and changes in an object-based tree. NetworkConfigParser does not support this.
- The goal of this library is to enable easy querying of the document and its structure. We use a simple list to
- store the objects, so standard list comprehensions can be used to query the data. If the user needs to add or change
- configuration and have the document tree update itself, the user is encouraged to stick with the library that they
- use today. Or a list comprehension can easily project the matching element and its family into a list of strings, and
- the user may add the desired elements to that list.

- Other library objects tend to be less Pythonic, making access to search tools clunky. Here, care is taken to make
- string methods work as expected. Unfortunately, `str(line_object)` is still required to get the line of text. But
- other string methods such as `line_object.startswith('route-policy ')` or `'description' in line_object` work
- transparently.

- In other libraries, working with IP addresses can be difficult. IP networks and addresses are essential to daily life
- as a network administrator. This library parses each line of text for IP addresses and networks, converts them to
- objects from the standard Python ipaddress library, and stores those in sets with the associated line. Searching for
- lines that match an IP address or network becomes simpler and more deterministic.

- No other parsing is done to recognize the elements within a line. Only the familial relationship is tracked.
- Since there is great variability in configuration directives even within a vendor's OS offerings, that further
- parsing is left to the user. This keeps NetworkConfigParser's implementation and API from growing too far, and keeps
- the module size small.
