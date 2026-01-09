from DocumentLine import DocumentLine
from typing import List, Callable

def find_line_and_ancestors(doc_lines: List[DocumentLine],
                            search_fn: Callable[[DocumentLine], bool]) -> List[DocumentLine]:
    """Finds a line that matches a supplied callback function. Returns the line and its ancestors.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search
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
            A list of DocumentLines to search
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
            A list of DocumentLines to search
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.

    Returns:
        A list of matching DocumentLines and their ancestors, ordered in the same way they were read from the document.
        """
    return _find_line(doc_lines, search_fn)

def _find_line(doc_lines: List[DocumentLine],
               search_fn: Callable[[DocumentLine], bool],
               **family_options) -> List[DocumentLine]:
    """Finds a line that matches a supplied callback function. Returns the line, its ancestors, and all of its
    descendants.

    Args:
        doc_lines (List[DocumentLine]):
            A list of DocumentLines to search
        search_fn:
            A function that takes a DocumentLine as input and returns a bool indicating a match.
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
    return [j for i in doc_lines for j in i.family(**family_options) if search_fn(i)]
