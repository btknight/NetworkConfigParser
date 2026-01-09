"""Defines the DocumentLine object, a node in a familial tree describing a structured document layout."""
from typing import Optional, List


class DocumentLine(object):
    """Represents a single line in a document.

    Manages the lineage of a line of text from a structured document, like a Cisco or Juniper configuration file. This
    retains links to parent and child items. If this item is desired as part of a search, but the ancestor or
    descendant items are required also, this object can retrieve those.

    This object passes undefined method calls to the 'line' attribute, the line of text, making working with text
    simpler.

    Attributes
    ----------
    line:
        A str containing the text of the line.
    line_num:
        int line number from the original document.
    parent:
        The parent DocumentLine object for this object, otherwise None if there is this is a top-level object.
    children:
        A list of DocumentLine objects that are this object's children.
    gen:
        An int, starting from 1, indicating the generation level of the object. 1 indicates a top-level object,
        2 indicates a child of a top-level object, 3 is a grandchild, and so on.
    ancestors:
        A list of DocumentLine objects of this object's ancestors, sorted from top-level object to this object's parent.
    all_descendants:
        A list of DocumentLine objects of all children, grandchildren, great-grandchildren, etc. of this object,
        ordered in the sequence in which they appear in the configuration.

    Methods
    -------
    family:
        Returns a list of family objects, optionally including ancestors, itself, children, and all descendants.
    """
    def __init__(self, line_num: int, line: str, parent: Optional[object] = None):
        self.line_num = line_num
        self.line = line
        self.parent = parent
        self.children: List[object] = []

    @property
    def gen(self) -> int:
        """The generation level of the line.

        1 indicates a top-level object, 2 indicates a child of a top-level object, 3 is a grandchild, and so on.

        Returns:
            Integer of the generation level
        """
        if self.parent is None:
            return 1
        return self.parent.gen + 1

    @property
    def ancestors(self) -> List[object]:
        """A list of DocumentLine objects of this object's ancestors.

        Returns:
            A list of ancestors of this object, sorted from the top-level to the immediate parent.
        """
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

    @property
    def all_descendants(self) -> List[object]:
        """Returns all descendants of this object.

        Returns:
            List of DocumentLine objects of all children, grandchildren, great-grandchildren, etc. of this
            object, ordered in the sequence in which they appear in the configuration.
        """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.all_descendants)
        return descendants

    def family(self,
               include_ancestors: bool = True,
               include_children: bool = True,
               include_all_descendants: bool = True) -> List[object]:
        """Provides a list of family objects, optionally including ancestors, itself, children, and all descendants.

        Args:
            include_ancestors:
                A bool indicating whether to include ancestors. Default is True.
            include_children:
                A bool indicating whether to include immediate children of this object. Default is True.
            include_all_descendants:
                A bool indicating whether to include grandchildren, great-grandchildren, etc of this object. Default is
                True.

        Returns:
            List of DocumentNode objects in order from top-level ancestors, to the object itself, to all descendants,
            in the same order as they were read by the parser.
        """
        family = []
        if include_ancestors:
            family.extend(self.ancestors)
        family.append(self)
        if include_children and not include_all_descendants:
            family.extend(self.children)
        elif include_children and include_all_descendants:
            family.extend(self.all_descendants)  # All? NO! ALL!
        return family

    def __contains__(self, item):
        return self.line.__contains__(item)

    def __format__(self, item):
        return self.line.__format__(item)

    def __iter__(self):
        return self.line.__iter__()

    def __getitem__(self, item):
        return self.line.__getitem__(item)

    def __sizeof__(self):
        return self.line.__sizeof__()

    def __len__(self):
        return self.line.__len__()

    def __mod__(self, item):
        return self.line.__mod__(item)

    def __mul__(self, item):
        return self.line.__mul__(item)

    def __rmul__(self, item):
        return self.line.__rmul__(item)

    def __hash__(self):
        return hash(self.line)

    def __str__(self):
        return self.line

    def __repr__(self):
        return f'<{self.__class__.__name__} depth={self.gen} num_children={len(self.children)} line_num={self.line_num}: "{self.line}">'

    def __getattr__(self, item):
        """Pass unknown attributes and method calls to self.line for text manipulation and validation.

        Args:
            item:
                Name of the attribute to pass to self.line

        Returns:
            Attribute or method from self.line that was called
        """
        return getattr(self.line, item)
