from DocumentLine import DocumentLine
import re
from typing import List, Callable

def find_line_and_ancestors(doc_lines: List[DocumentLine],
                            search_fn: Callable[[DocumentLine], bool]) -> List[DocumentLine]:
    """Finds a line that matches a supplied callback function. Returns the line and its ancestors.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.

    Returns:
        A list of matching DocumentLines and their ancestors, ordered in the same way they were read from the document.
        """
    return _find_line(doc_lines, search_fn, find_children=False)


def find_line_and_descendants(doc_lines: List[DocumentLine],
                              search_fn: Callable[[DocumentLine], bool]) -> List[DocumentLine]:
    """Finds a line that matches a supplied callback function. Returns the line and its ancestors.

    Args:
        doc_lines:
            A list of DocumentLines to search.
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.

    Returns:
        A list of matching DocumentLines and their ancestors, ordered in the same way they were read from the document.
        """
    return _find_line(doc_lines, search_fn, find_ancestors=False)


def find_line_ancestors_descendants(doc_lines: List[DocumentLine],
                            search_fn: Callable[[DocumentLine], bool]) -> List[DocumentLine]:
    """Finds a line that matches a supplied callback function. Returns the line, its ancestors, and all of its
    descendants.

    Args:
        doc_lines:
            A list of DocumentLines to search.
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.

    Returns:
        A list of matching DocumentLines and their ancestors, ordered in the same way they were read from the document.
        """
    return _find_line(doc_lines, search_fn)

def _find_line(doc_lines: List[DocumentLine],
               search_fn: Callable[[DocumentLine], bool],
               suppress_common_ancestors: bool = True,
               **family_options) -> List[DocumentLine]:
    """Finds a line that matches a supplied callback function. Returns the line, its ancestors, and all of its
    descendants.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.
        suppress_common_ancestors:
            A bool set to True if common ancestors of adjacent objects should not be repeated. False if common ancestors
            should be repeated.
        family_options:
            A set of kwargs that are passed to the DocumentLine.family() function. Permitted parameters to family():
                include_ancestors (bool)
                include_self (bool)
                include_children (bool)
                include_all_descendants (bool)

    Returns:
        A list of matching DocumentLines, their ancestors and their descendants, ordered in the same way they were read
        from the document.
        """
    s = lambda x, y: x
    if suppress_common_ancestors:
        s = common_line_suppressor()
    return [j for i in doc_lines for j in s(i.family(**family_options), i) if search_fn(i)]

def find_objects(doc_lines: List[DocumentLine],
                 linespec: str | re.Pattern | List[str] | List[re.Pattern]) -> List[DocumentLine]:
    """Similar to CiscoConfParse.find_objects(). Performs a regular expression search for DocumentLine objects.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        linespec:
            A textual regular expression, compiled pattern, or list of expressions or patterns to be matched.

    Returns:
        A list of DocumentLines matching the linespec.

    Raises:
        ValueError:
            Raised if the supplied linespec does not match a supported object.
    """
    def convert_to_pattern(p):
        if p is re.Pattern:
            return p
        elif p is str:
            return re.compile(p)
        else:
            raise ValueError(f'find_objects: Got {type(linespec)} "{linespec}" for linespec; only strings and '
                             're.Pattern objects are supported')
    if linespec is list:
        patterns = [convert_to_pattern(i) for i in linespec]
    else:
        patterns = [convert_to_pattern(linespec)]
    return [i for i in doc_lines if any([re.search(p, str(i)) for p in patterns])]

def common_line_suppressor() -> Callable[[List[DocumentLine]], List[DocumentLine]]:
    """Supplies a closure that suppresses adjacent common lines in a list comprehension.

    Example:
        After searching for BGP neighbors, we want to include the ancestors of those lines like "router bgp 65536",
        "vrf EXAMPLE", etc. But we do not want those lines to be repeated for each successive object.

        Given the following:

        router bgp 65536
         vrf EXAMPLE
          neighbor 192.0.2.1
           remote-as 65537
          neighbor 192.0.2.2
           remote-as 65537

        bgp_lines = [j for i in doc_lines for j in i.family() if i.startswith('router bgp ')]
        bgp_nbr_lines = [i for i in bgp_lines if i.lstrip().startswith('neighbor ')]
        nbr_config_lines = [j for i in bgp_nbr_lines for j in i.family()]

        The result of nbr_config_lines would be as follows:

        router bgp 65536
         vrf EXAMPLE
          neighbor 192.0.2.1
           remote-as 65537
        router bgp 65536   <- line repeated
         vrf EXAMPLE       <- line repeated
          neighbor 192.0.2.2
           remote-as 65537

        The below suppresses those two repeated lines.

        s = common_ancestor_suppressor()
        nbr_config_lines = [j for i in bgp_nbr_lines for j in s(i.family())]

    Returns:
        A function to be used in a list comprehension that suppresses adjacent common lines.
    """
    previous_lines = []
    def suppress_common_lines(family_lines: List[DocumentLine]) -> List[DocumentLine]:
        """Suppresses adjacent common lines.

        Args:
            family_lines:
                List of DocumentLines to be filtered.

        Returns:
            Filtered list with common lines removed.
            """
        nonlocal previous_lines
        filtered_lines = [i for i in family_lines if i not in previous_lines]
        previous_lines = family_lines
        return filtered_lines
    return suppress_common_lines
