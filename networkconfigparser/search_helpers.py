"""A set of functions to assist with searching in a list of DocumentLine objects."""
from operator import attrgetter
import re
from typing import List, Callable, Iterable, Any
from networkconfigparser.documentline import DocumentLine

SearchTerm = Callable[[DocumentLine], bool] | str | re.Pattern

def identity(x: Any) -> Any:
    """Identity function. Returns the first argument unmodified."""
    return x


def convert_search_spec_to_cb(search_spec: SearchTerm | Iterable[SearchTerm],
                              regex_flags: int | re.RegexFlag = 0,
                              term_num: int | None = None) \
        -> Callable[[DocumentLine], bool] | Iterable[Callable[[DocumentLine], bool]]:
    """Converts a find_lines() search term to a callback function.

    Args:
        search_spec:
            User-supplied input to find_lines(). Can be a str, re.Pattern, callable, or iterable of
            those.
        regex_flags:
            Flags to add to regex searches.
        term_num:
            Index of the term in the iterable. Used internally for error message generation only.

    Returns:
        A callable or list of callables for searching.

    Raises:
        ValueError if any argument is not a str, re.Pattern, or callable.
    """
    #
    # Handle iterables by performing a list comprehension
    if is_iterable_search_term(search_spec):
        if len(search_spec) == 0:
            raise ValueError('convert_search_spec_to_cb: search_spec cannot be an empty list')
        return [convert_search_spec_to_cb(t, regex_flags, term_num=i) for i, t in
                zip(range(len(search_spec)), search_spec)]
    #
    # Handle unsupported terms
    if not callable(search_spec) and not is_regex(search_spec):
        term_index = f'term index {term_num}: ' if term_num is not None else ''
        raise ValueError(f'convert_search_spec_to_cb: {term_index}{type(search_spec)} is not '
                         'supported')
    #
    # Pass through callables
    if callable(search_spec):
        return search_spec
    #
    # Handle regexes
    return re_search_cb(search_spec, regex_flags)


def find_lines(doc_lines: List[DocumentLine] | None,
               search_spec: SearchTerm | Iterable[SearchTerm],
               /,
               regex_flags: int | re.RegexFlag = 0,
               regex_group: int | None = None,
               recurse_search: bool = True,
               convert_match: Callable[[DocumentLine], Any] = identity,
               convert_family: Callable[[DocumentLine], Any] = identity,
               flatten_family: bool = True,
               suppress_common_ancestors: bool = True,
               include_ancestors: bool = False,
               include_children: bool = False,
               include_all_descendants: bool = False) \
        -> List[DocumentLine] | List[List[DocumentLine]] | None:
    """Finds lines that match a supplied search specification.

    Optionally, returns the ancestors, immediate children, or all descendants of the matches.

    Search terms may be the following:
        * A regular expression string
        * An re.Pattern object
        * A callable function taking a DocumentLine as input and returning a bool to indicate a
          successful match
        * An iterable containing any combination of the three inputs above

    If the search term is an iterable, each term will be matched in successive generations: if the
    first term matches a top-level object, the second term will be searched in the first term's
    children or all descendants (depending on the setting of recurse_search), and so on.

    Args:
        doc_lines:
            A list of DocumentLines to search. If this is None, in the case of a previous search
            fed into a new search, this function immediately returns None.
        search_spec:
            A search term or Iterable thereof. See discussion above.
        regex_flags:
            If any search terms are strings or re.Patterns, these flags will be passed to re.search.
            Default is no flags.
        regex_group:
            If the final search term has a group defined in the regex string, this option will
            return the regex group from the re.Match object instead of the DocumentLine object.
            Default is not to do this. Cannot be combined with convert_match.
        recurse_search:
            If set to False, and search_spec is an iterable, only immediate children of the previous
            match will be searched for the next term. If True, all descendants of the previous match
            will be searched.
        convert_match:
            If specified, run the supplied function to convert matches in the output list. Default
            is to return the DocumentLine object.
        convert_family:
            If specified, and an include_* parameter is set to True, run the supplied function to
            convert family lines other than the matched line in the output list. Default is to
            return DocumentLine objects.
        flatten_family:
            If False, returns a list of lists where the second order list contains the match, plus
            any family lines if specified. If True, the list of matches and any family members is
            flattened into a single list. Default is True.
        suppress_common_ancestors:
            If flatten_family is True and include_ancestors is True, setting this to True ensures
            common ancestors of adjacent matches will not be repeated. If False, common ancestors
            will be repeated. See documentation for common_line_suppressor() for more info.
        include_ancestors:
            Set this to True if the ancestors of the matching object should be returned. Default is
            False.
        include_children:
            Set this to True if the immediate children of the matching object should be returned.
            Default is False. Setting this to False implies include_all_descendants=False.
        include_all_descendants:
            Set this to True if the grandchildren, great-grandchildren, etc. of the matching object
            should be returned. Default is False.

    Returns:
        A list of matching DocumentLines, their ancestors and their descendants, ordered in the same
        way they were read from the document. If flatten_family is False, returns a list of lists
        instead. If no matches were found, returns None.

    Raises:
        ValueError:
            Raised if search_spec is not an iterable or callable.
    """
    #
    # Technically, this function only handles marshaling search terms to callbacks, and executing an
    # iterable of callbacks. find_lines_with_cb() handles the actual search execution for each term.
    if doc_lines is None:
        return None
    #
    def final_term():
        if is_iterable_search_term(search_spec):
            return search_spec[-1]
        return search_spec
    #
    # Deal with regex_group and convert_match.
    if regex_group:
        #
        # Get final term of search_spec if it is an iterable
        ft = final_term()
        if not is_regex(ft):
            final_term_of = 'final term of ' if is_iterable_search_term(search_spec) else ''
            raise ValueError(f'find_lines: {final_term_of}search_spec is not a regular '
                             f'expression: {type(ft)}')
        if convert_match is not identity:
            raise ValueError('find_lines: both group and convert_match are specified - use one or '
                             'the other')
        def regex_group_match(x: DocumentLine) -> bool:
            return x.re_search(ft, regex_flags).group(regex_group)
        convert_match = regex_group_match
    #
    # Convert search_term to a callable or to a list of callables.
    search_spec = convert_search_spec_to_cb(search_spec, regex_flags)
    #
    # Gather passthrough options.
    passthru_names = ['convert_', 'suppress_', 'include_', 'flatten_']
    passthru_opts = {k: v for k, v in locals().items() if any(k.startswith(opt) for opt in
                                                              passthru_names)}
    #
    # Iterate over search_spec.
    if is_iterable_search_term(search_spec):
        search_spec = list(search_spec)
        #
        # For each search function except for the last
        for search_fn in search_spec[:-1]:
            #
            # Narrow doc_lines by matching successive descendant lines of the last search.
            # Omit the matched line itself ("include_self=False"), get only the children of the
            # match.
            doc_lines = find_lines_with_cb(doc_lines,
                                           search_fn,
                                           suppress_common_ancestors=False,
                                           include_ancestors=False,
                                           include_self=False,
                                           include_children=True,
                                           include_all_descendants=recurse_search)
    #
    # Process the final search_spec if it was iterable, or the search_spec itself if it was a single
    # callable.
    result = find_lines_with_cb(doc_lines, final_term(), **passthru_opts)
    if len(result) == 0:
        return None
    return result

def find_lines_with_cb(doc_lines: List[DocumentLine],
                       search_fn: Callable[[DocumentLine], bool],
                       /,
                       convert_match: Callable[[DocumentLine], Any] = identity,
                       convert_family: Callable[[DocumentLine], Any] = identity,
                       flatten_family: bool = True,
                       suppress_common_ancestors: bool = True,
                       include_ancestors: bool = False,
                       include_self: bool = True,
                       include_children: bool = False,
                       include_all_descendants: bool = False) \
        -> List[DocumentLine] | List[List[DocumentLine]]:
    """Finds lines that match a single callback function.

    Called by the more user-friendly function find_lines() to execute a search for a single term.
    Optionally returns ancestors and/or descendants of the match. Optionally converts the match
    itself or the family members to a different object.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.
        convert_match:
            If specified, run the supplied function to convert matches in the output list. Default
            is to return the DocumentLine object.
        convert_family:
            If specified, and an include_* parameter is set to True, run the supplied function to
            convert family lines other than the matched line in the output list. Default is to
            return DocumentLine objects.
        flatten_family:
            If False, returns a list of lists where the second order list contains the match, plus
            any family lines if specified. If True, the list of matches and any family members is
            flattened into a single list. Default is True.
        suppress_common_ancestors:
            If flatten_family is True and include_ancestors is True, setting this to True ensures
            common ancestors of adjacent matches will not be repeated. If False, common ancestors
            will be repeated. See documentation for common_line_suppressor() for more info.
        include_ancestors:
            Set this to True if the ancestors of the matching object should be returned. Default is
            False.
        include_self:
            Set this to False if the matched line itself should not be returned. Default is True.
            Used internally when find_lines() search_spec is an iterable.
        include_children:
            Set this to True if the immediate children of the matching object should be returned.
            Default is False.
        include_all_descendants:
            Set this to True if the grandchildren, great-grandchildren, etc. of the matching object
            should be returned. Default is False. Setting this to True implies
            include_children=True.

    Returns:
        A list of matching DocumentLines, their ancestors and their descendants, ordered in the same
        way they were read from the document. If flatten_family is False, returns a list of lists
        instead.
        """
    #
    # If all descendants are to be returned, include immediate children as well.
    if include_all_descendants:
        include_children = True
    #
    # Gather include options for DocumentLine.family()
    passthru_names = ['include_']
    passthru_opts = {k: v for k, v in locals().items() if any(k.startswith(opt) for opt in
                                                              passthru_names)}
    #
    # If suppress_common_ancestors is True, get a closure function to help suppress common lines.
    if suppress_common_ancestors:
        s = common_line_suppressor()
    else:
        s = identity
    #
    # Perform the comparison.
    matches = [i for i in doc_lines if search_fn(i)]
    #
    # If all include_ options to DocumentLine.family() are False, no family inclusions are
    # specified. Return the matches, converting the result.
    if not any(passthru_opts.values()):
        if flatten_family:
            return [convert_match(i) for i in matches]
        return [[convert_match(i)] for i in matches]
    #
    # Process family lines.
    #
    # Define a closure to apply conversions.
    def convert_line(o: DocumentLine) -> Any:
        if o in matches:
            return convert_match(o)
        return convert_family(o)
    #
    # Perform another comprehension to get the familial lines added to the result.
    if flatten_family:
        return [convert_line(j) for i in matches for j in s(i.family(**passthru_opts))]
    return [[convert_line(j) for j in i.family(**passthru_opts)] for i in matches]

def re_search_cb(regex: str | re.Pattern, flags: int | re.RegexFlag = 0) \
        -> Callable[[DocumentLine], bool]:
    """Helper function to provide an re.search callable suitable for feeding to find_lines().

    Args:
        regex:
            The str or compiled regular expression to pass to re.search.
        flags:
            Optional flags to pass to re.search.

    Returns:
        A callable that takes a DocumentLine as an argument and returns the result of re.search on
        the object's line
    """
    return lambda o: o.re_search(regex, flags)

def parent_child_cb(parent_spec: str | re.Pattern | Callable[[DocumentLine], bool],
                    child_spec: str | re.Pattern | Callable[[DocumentLine], bool],
                    regex_flags: int | re.RegexFlag = 0,
                    recurse: bool = True,
                    negative_child_match: bool = False) -> Callable[[DocumentLine], bool]:
    """Returns a search function for find_lines() that returns parent objects matching the
    parentspec and children matching the childspec.

    Only the parent lines are returned.

    Enables behavior similar to CiscoConfParse.find_parent_objects().

    Example:

    .. code-block:: python

        config = '''interface Ethernet0/0
                     address-family ipv4 unicast
                      metric 2200
                    interface Ethernet0/1
                     description metric not imperial
                    interface Ethernet0/2
                     shutdown'''
        search_fn = parent_child_cb('interface', 'metric')
        find_lines(doc_lines, search_fn)
        ['interface Ethernet0/0',
         'interface Ethernet0/1']

        search_fn = parent_child_cb('interface', 'metric', recurse=False)
        find_lines(doc_lines, search_fn)
        ['interface Ethernet0/1']

        search_fn = parent_child_cb('interface', 'metric', negative_child_match=True)
        find_lines(doc_lines, search_fn)
        ['interface Ethernet0/2']

    Args:
        parent_spec:
            str or re.Pattern to search for the parent line.
        child_spec:
            str or re.Pattern to search in the child lines of the parent.
        regex_flags:
            Flags to pass to re.search. Both parent_spec and child_spec are affected. If different
            flags are desired for each term, use re.compile() to provide an re.Pattern object.
            Default is no flags.
        recurse:
            True if all descendants are to be searched, False if only immediate children are to be
            searched. Default is True.
        negative_child_match:
            If True, negates the child match; i.e. the returned parent has no children that match
            the childspec. Default is False.

    Returns:
        Search function to feed to find_lines(). Causes find_lines() to return a list of
        DocumentLines matching the parentspec. Children of the objects are not returned.

    Raises:
        ValueError:
            Raised if the supplied parentspec does not match a supported object, or parentspec is
            an iterable and childspec is not None.
    """
    #
    # Test spec values
    if not is_regex(parent_spec):
        raise ValueError(f'parent_child_cb: {type(parent_spec)} is not a valid regex')
    if not is_regex(child_spec):
        raise ValueError(f'parent_child_cb: {type(child_spec)} is not a valid regex')
    #
    # If recurse is set, we look at all_descendants of the object
    if recurse:
        child_getter = attrgetter('all_descendants')
    #
    # Otherwise, we look at only the immediate children
    else:
        child_getter = attrgetter('children')
    #
    # Search function to pass to find_lines()
    def search_fn(o: DocumentLine) -> bool:
        parent_match = o.re_search(parent_spec, regex_flags) is not None
        child_match = any(c.re_search(child_spec, regex_flags) is not None for c in child_getter(o))
        if negative_child_match:
            child_match = not child_match
        return parent_match and child_match
    return search_fn

def common_line_suppressor() -> Callable[[List[DocumentLine]], List[DocumentLine]]:
    """Supplies a closure that suppresses adjacent common lines in a list comprehension.

    Example:
        After searching for BGP neighbors, we want to include the ancestors of those lines like
        "router bgp 65536", "vrf EXAMPLE", etc. But we do not want those lines to be repeated for
        each successive object.

        Given the following:

        .. code-block:: text

            router bgp 65536
             vrf EXAMPLE
              neighbor 192.0.2.1
               remote-as 65537
              neighbor 192.0.2.2
               remote-as 65537

        .. code-block:: python

            bgp_lines = [j for i in doc_lines for j in i.family() if i.startswith('router bgp ')]
            bgp_nbr_lines = [i for i in bgp_lines if i.lstrip().startswith('neighbor ')]
            nbr_config_lines = [j for i in bgp_nbr_lines for j in i.family()]

        The result of nbr_config_lines would be as follows:

        .. code-block:: text

            router bgp 65536
             vrf EXAMPLE
              neighbor 192.0.2.1
               remote-as 65537
            router bgp 65536   <- line repeated
             vrf EXAMPLE       <- line repeated
              neighbor 192.0.2.2
               remote-as 65537

        The below suppresses those two repeated lines.

        .. code-block:: text

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

def is_iterable_search_term(obj: Any) -> bool:
    """Returns True if an object is iterable and is not a string or re.Pattern.

    Args:
        obj:
            Any object to test iterability

    Returns:
        True if iterable, False if not
    """
    return isiterable(obj) and not is_regex(obj)

def isiterable(obj: Any) -> bool:
    """Returns True if an object is iterable and is not a string or re.Pattern.

    Args:
        obj:
            Any object to test iterability

    Returns:
        True if iterable, False if not
    """
    try:
        iter(obj)
    except TypeError:
        return False
    return True

def is_regex(obj: Any) -> bool:
    """Return True is an object is a string or re.Pattern.

    Args:
        obj:
            Any object to test

    Returns:
        True if regex, False if not
    """
    return isinstance(obj, (str, re.Pattern))
