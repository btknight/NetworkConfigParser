from DocumentLine import DocumentLine
from operator import attrgetter
import re
from typing import List, Callable, Iterable, Any, Tuple

def identity(x: Any) -> Any:
    """Identity function. Returns the first argument unmodified."""
    return x

def find_lines(doc_lines: List[DocumentLine],
               search_spec: Callable[[DocumentLine], bool] | Iterable[Callable[[DocumentLine], bool]],
               recurse_search: bool = True,
               convert_result: Callable[[DocumentLine], Any] = identity,
               convert_family: Callable[[DocumentLine], Any] = identity,
               flatten_family: bool = True,
               suppress_common_ancestors: bool = True,
               include_ancestors: bool = False,
               include_children: bool = False,
               include_all_descendants: bool = False) -> List[DocumentLine] | List[List[DocumentLine]] | None:
    """Finds lines that match a supplied callback function or functions.

    Optionally, returns the ancestors, immediate children, or all descendants of the matches.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        search_spec:
            A function or Iterable of functions that take a DocumentLine as input and returns a bool indicating a match.
            If an Iterable is supplied, it will search each match in successive generations.
        recurse_search:
            If set to False, and search_spec is an iterable, only immediate children of the previous match
            will be searched for the next term. If True, all descendants of the previous match will be searched.
        convert_result:
            If specified, run the supplied function to convert matches in the output list. Default is to return the
            DocumentLine object.
        convert_family:
            If specified, and an include_* parameter is set to True, run the supplied function to convert family lines
            other than the matched line in the output list. Default is to return DocumentLine objects.
        flatten_family:
            If False, returns a list of lists where the second order list contains the match, plus any family lines if
            specified. If True, the list of matches and any family members is flattened into a single list.
            Default is True.
        suppress_common_ancestors:
            If flatten_family is True and include_ancestors is True, setting this to True ensures common ancestors of
            adjacent matches will not be repeated. If False, common ancestors will be repeated.
            See documentation for common_line_suppressor() for more info.
        include_ancestors:
            Set this to True if the ancestors of the matching object should be returned. Default is False.
        include_children:
            Set this to True if the immediate children of the matching object should be returned. Default is False.
            Setting this to False implies include_all_descendants=False.
        include_all_descendants:
            Set this to True if the grandchildren, great-grandchildren, etc. of the matching object should be
            returned. Default is False.

    Returns:
        A list of matching DocumentLines, their ancestors and their descendants, ordered in the same way they were read
        from the document. If flatten_family is False, returns a list of lists instead. If no matches were found,
        returns None.

    Raises:
        ValueError:
            Raised if search_spec is not an iterable or callable.
    """
    passthru_names = ['convert_', 'suppress_', 'include_', 'flatten_']
    passthru_opts = {k: v for k, v in locals().items() if any(k.startswith(opt) for opt in passthru_names)}
    #
    # Handle the case where search_spec is an iterable.
    if isiterable(search_spec) and all(callable(i) for i in search_spec):
        search_spec = [i for i in search_spec]
        #
        # For each search callable except for the last
        for search_fn in search_spec[:-1]:
            #
            # Find matching descendant lines, omitting the matched line ("include_self=False")
            doc_lines = _find_lines(doc_lines, search_fn, suppress_common_ancestors=False, include_ancestors=False,
                                    include_self=False, include_children=True, include_all_descendants=recurse_search)
            #
            # If no matches, return None
            if len(doc_lines) == 0:
                return None
        #
        # Set search_spec to the last term, and exit this if statement - this runs the final match with user-specified
        # options
        search_spec = search_spec[-1]
    #
    # Raise ValueError if not all members in the iterable are callable.
    elif isiterable(search_spec):
        non_callable = [str((i, type(i))) for i in search_spec if not callable(i)]
        raise ValueError(f'find_lines: Not all objects in the iterable are callables: {", ".join(non_callable)}')
    #
    # Handle search_spec that is neither iterable nor callable.
    elif not callable(search_spec):
        raise ValueError(f'find_lines: Supplied object is {type(search_spec)}; allowed objects are callables '
                         'or list of callables. Are you looking for find_lines_regex()?')
    #
    # Process the final search_spec if it was iterable, or the search_spec itself if it was a single callable.
    result = _find_lines(doc_lines, search_spec, **passthru_opts)
    if len(result) == 0:
        return None
    return result

def find_lines_regex(doc_lines: List[DocumentLine],
                     regex_spec: str | re.Pattern | Iterable[str | re.Pattern],
                     recurse_search: bool = True,
                     group: int | None = None,
                     convert_result: Callable[[DocumentLine], Any] = identity,
                     convert_family: Callable[[DocumentLine], Any] = identity,
                     flatten_family: bool = True,
                     suppress_common_ancestors: bool = True,
                     include_ancestors: bool = False,
                     include_children: bool = False,
                     include_all_descendants: bool = False) -> List[DocumentLine] | List[List[DocumentLine]] | None:
    """Finds lines that match a regular expression.

    Optionally, returns the ancestors, immediate children, or all descendants of the matches.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        regex_spec:
            A str, re.Pattern, or Iterable of those to search in doc_lines. If an Iterable is supplied, it will search
            each match in successive generations.
        recurse_search:
            If set to False, and regex_spec is an iterable, only immediate children of the previous match
            will be searched for the next term. If True, all descendants of the previous match will be searched.
        group:
            If specified, returns the string matching the regular expression group from the final re.Match object as a
            result. May not be used if convert_result is also set. Default is None.
        convert_result:
            If specified, run the supplied function to convert matches in the output list. May not be used if group is
            set. Default is to return the DocumentLine object.
        convert_family:
            If specified, and an include_* parameter is set to True, run the supplied function to convert family lines
            other than the matched line in the output list. Default is to return DocumentLine objects.
        flatten_family:
            If False, returns a list of lists where the second order list contains the match, plus any family lines if
            specified. If True, the list of matches and any family members is flattened into a single list.
            Default is True.
        suppress_common_ancestors:
            If flatten_family is True and include_ancestors is True, setting this to True ensures common ancestors of
            adjacent matches will not be repeated. If False, common ancestors will be repeated.
            See documentation for common_line_suppressor() for more info.
        include_ancestors:
            Set this to True if the ancestors of the matching object should be returned. Default is False.
        include_children:
            Set this to True if the immediate children of the matching object should be returned. Default is False.
            Setting this to False implies include_all_descendants=False.
        include_all_descendants:
            Set this to True if the grandchildren, great-grandchildren, etc. of the matching object should be
            returned. Default is False.

    Returns:
        A list of matching DocumentLines, their ancestors and their descendants, ordered in the same way they were read
        from the document. If flatten_family is False, returns a list of lists instead. If no matches were found,
        returns None.

    Raises:
        ValueError:
            Raised if regex_spec is not a str, re.Pattern, or iterable. Also raised if group and convert_result are set
            together.
    """
    def is_re_term(x):
        return isinstance(x, str) or isinstance(x, re.Pattern)
    def is_re_iterable(x):
        return isiterable(x) and not is_re_term(x)
    #
    # Map regex_spec to callables.
    if is_re_iterable(regex_spec) and all(is_re_term(i) for i in regex_spec):
        regex_spec = [i for i in regex_spec]
        search_spec = [re_search_cb(i) for i in regex_spec]
        final_term = regex_spec[-1]
    #
    # Handle iterables that don't have all strings.
    elif is_re_iterable(regex_spec):
        non_str = [str((i, type(i))) for i in regex_spec if not is_re_term(i)]
        raise ValueError(f'find_lines: Not all objects in the iterable are valid regex terms: {", ".join(non_str)}')
    #
    # Handle str or re.Pattern.
    elif is_re_term(regex_spec):
        search_spec = re_search_cb(regex_spec)
        final_term = regex_spec
    else:
        raise ValueError(f'find_lines_regex: Supplied object is {type(regex_spec)}; allowed objects are str, '
                             're.Pattern, or List[str | re.Pattern]')
    #
    # Deal with group and convert_result.
    if group and not convert_result == identity:
        raise ValueError(f'find_lines_regex: both group and convert_result are specified - use one or the other')
    elif group:
        convert_result = lambda x: re_search_dl(final_term, x).group(group)
    #
    # Gather passthru options.
    passthru_names = ['recurse_', 'convert_', 'suppress_', 'include_', 'flatten_']
    passthru_opts = {k: v for k, v in locals().items() if any(k.startswith(opt) for opt in passthru_names)}
    #
    # Call find_lines() to perform the matching.
    return find_lines(doc_lines, search_spec, **passthru_opts)

def _find_lines(doc_lines: List[DocumentLine],
                search_fn: Callable[[DocumentLine], bool],
                convert_result: Callable[[DocumentLine], Any] = identity,
                convert_family: Callable[[DocumentLine], Any] = identity,
                flatten_family: bool = True,
                suppress_common_ancestors: bool = True,
                **family_options) -> List[DocumentLine] | List[List[DocumentLine]]:
    """Finds lines that match a supplied callback function.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.
        convert_result:
            If specified, run the supplied function to convert matches in the output list. Default is to return the
            DocumentLine object.
        convert_family:
            If specified, and an include_* parameter is set to True, run the supplied function to convert family lines
            other than the matched line in the output list. Default is to return DocumentLine objects.
        flatten_family:
            If False, returns a list of lists where the second order list contains the match, plus any family lines if
            specified. If True, the list of matches and any family members is flattened into a single list.
            Default is True.
        suppress_common_ancestors:
            If flatten_family is True and include_ancestors is True, setting this to True ensures common ancestors of
            adjacent matches will not be repeated. If False, common ancestors will be repeated.
            See documentation for common_line_suppressor() for more info.
        family_options:
            A set of kwargs that are passed to the DocumentLine.family() function. Permitted parameters to family():
            include_ancestors:
                Set this to True if the ancestors of the matching object should be returned. Default is False.
            include_children:
                Set this to True if the immediate children of the matching object should be returned. Default is False.
                Setting this to False implies include_all_descendants=False.
            include_all_descendants:
                Set this to True if the grandchildren, great-grandchildren, etc. of the matching object should be
                returned. Default is False.

    Returns:
        A list of matching DocumentLines, their ancestors and their descendants, ordered in the same way they were read
        from the document. If flatten_family is False, returns a list of lists instead.
        """
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
    # If no include_ options to DocumentLine.family() are specified, return the matches, converting the result.
    if not any(family_options.values()):
        if flatten_family:
            return [convert_result(i) for i in matches]
        return [[convert_result(i)] for i in matches]

    #
    # Process family lines.
    #
    # Define a closure to apply conversions.
    def convert_line(o: DocumentLine) -> Any:
        if o in matches:
            return convert_result(o)
        return convert_family(o)
    #
    # Perform another comprehension to get the familial lines added to the result.
    if flatten_family:
        return [convert_line(j) for i in matches for j in s(i.family(**family_options))]
    return [[convert_line(j) for j in i.family(**family_options)] for i in matches]

def re_search_dl(regex: str | re.Pattern, dl_object: DocumentLine, *flags) -> re.Match | None:
    """Helper function to perform regex searches on DocumentLine objects.

    This simply converts the DocumentLine object to a str before running re.search.

    Args:
        regex:
            The str or compiled regular expression to pass to re.search.
        dl_object:
            The DocumentLine to search.
        flags:
            Optional flags to pass to re.search.

    Returns:
        The re.Match result from re.search.
    """
    return re.search(regex, str(dl_object), *flags)

def re_search_cb(regex: str | re.Pattern, *flags) -> Callable[[DocumentLine], bool]:
    """Helper function to provide an re.search callable suitable for feeding to find_lines().

    Args:
        regex:
            The str or compiled regular expression to pass to re.search.
        flags:
            Optional flags to pass to re.search.

    Returns:
        A callable that takes a DocumentLine as an argument and returns a bool indicating a match.
    """
    return lambda o: re_search_dl(regex, o, *flags) is not None

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
    result = find_lines_regex(doc_lines, linespec)
    if not result:
        return []
    return result

# TODO find_object_branches

def find_parent_objects(doc_lines: List[DocumentLine],
                        parentspec: str | re.Pattern | List[str | re.Pattern],
                        childspec: str | re.Pattern | None = None,
                        recurse: bool = True,
                        negative_child_match: bool = False) -> List[DocumentLine]:
    """Similar to CiscoConfParse.find_parent_objects(). Performs a search for DocumentLine parent objects matching the
    parentspec and with children that match the childspec.

    Only the parent lines are returned.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        parentspec:
            str or re.Pattern to search for the parent line, or list of two patterns to match parent and child.
        childspec:
            str or re.Pattern to search in the child lines of the parent.
        recurse:
            True if all descendants are to be searched, False if only immediate children are to be searched.
        negative_child_match:
            If True, negates the child match; i.e. the returned parent has no children that match the childspec.

    Returns:
        A list of DocumentLines matching the parentspec. Children of the objects are not returned.

    Raises:
        ValueError:
            Raised if the supplied parentspec does not match a supported object, or parentspec is an iterable and
            childspec is not None.
    """
    #
    # Wrestle with the supplied input
    parentspec, childspec = _check_parentspec_childspec(parentspec, childspec)
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
        parent_match = re_search_dl(parentspec, o) is not None
        child_match = any(re_search_dl(childspec, c) is not None for c in child_getter(o))
        if negative_child_match:
            child_match = not child_match
        return parent_match and child_match
    #
    # Do the search
    result = find_lines(doc_lines, search_fn, recurse)
    if not result:
        return []
    return result

def find_parent_objects_wo_child(doc_lines: List[DocumentLine],
                                 parentspec: str | re.Pattern | List[str | re.Pattern],
                                 childspec: str | re.Pattern | None = None,
                                 recurse: bool = True) -> List[DocumentLine]:
    """Similar to CiscoConfParse.find_parent_objects_wo_child(). Performs a search for DocumentLine parent objects
    matching the parentspec and with children that do not match the childspec.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        parentspec:
            str or re.Pattern to search for the parent line, or list of two patterns to match parent and child.
        childspec:
            str or re.Pattern to search in the child lines of the parent.
        recurse:
            True if all descendants are to be searched, False if only immediate children are to be searched.

    Returns:
        A list of DocumentLines matching the parentspec. Children of the objects are not returned.

    Raises:
        ValueError:
            Raised if the supplied parentspec does not match a supported object, or parentspec is an iterable and
            childspec is not None.
    """
    return find_parent_objects(doc_lines, parentspec, childspec, recurse, negative_child_match=True)

def find_child_objects(doc_lines: List[DocumentLine],
                       parentspec: str | re.Pattern | List[str | re.Pattern],
                       childspec: str | re.Pattern | None = None,
                       recurse: bool = True) -> List[DocumentLine]:
    """Similar to CiscoConfParse.find_child_objects(). Performs a search for DocumentLine parent objects matching the
    parentspec and with children that match the childspec.

    Only the child lines are returned.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search.
        parentspec:
            str or re.Pattern to search for the parent line, or list of two patterns to match parent and child.
        childspec:
            str or re.Pattern to search in the child lines of the parent.
        recurse:
            True if all descendants are to be searched, False if only immediate children are to be searched.

    Returns:
        A list of DocumentLines matching the childspec. Parent objects are not returned.

    Raises:
        ValueError:
            Raised if the supplied parentspec does not match a supported object, or parentspec is an iterable and
            childspec is not None.
    """
    parentspec, childspec = _check_parentspec_childspec(parentspec, childspec)
    #
    # Assemble the search
    search_spec = [re_search_cb(parentspec), re_search_cb(childspec)]
    #
    # Do the search
    result = find_lines(doc_lines, search_spec, recurse, include_ancestors=False, include_children=False)
    if not result:
        return []
    return result

def _check_parentspec_childspec(parentspec: str | re.Pattern | Iterable[str | re.Pattern],
                                childspec: str | re.Pattern | None) -> Tuple[str | re.Pattern, str | re.Pattern]:
    """Helper method to validate and normalize input to CCP methods find_parent_object and find_child_object."""
    if isiterable(parentspec) and childspec is not None:
        raise ValueError('_check_parentspec_childspec: parentspec is iterable and childspec is set - must choose one '
                         'or the other')
    elif isiterable(parentspec) and not len(parentspec) == 2:
        raise ValueError('_check_parentspec_childspec: if parentspec is iterable, length must be 2')
    elif isiterable(parentspec):
        iterable = [i for i in parentspec]
        parentspec = iterable[0]
        childspec = iterable[1]
    return parentspec, childspec

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

        s = common_ancestor_suppressor() nbr_config_lines = [j for i in bgp_nbr_lines for j in s(i.family())]

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

def isiterable(obj: Any) -> bool:
    """Returns True if an object is iterable.

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
