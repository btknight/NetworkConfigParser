import logging
from typing import Optional, List, Callable


class DocumentLine(object):
    """Represents a single line in a document."""
    def __init__(self, line_num: int, line: str, parent: Optional[object] = None):
        self.line_num = line_num
        self.line = line
        self.parent = parent
        self.children = []

    @property
    def depth(self) -> int:
        """The depth level of the line. 1 is a top-level object with no leading spaces, 2 is a child of a top-level
        object, and so on."""
        if self.parent is None:
            return 1
        return self.parent.depth + 1

    @property
    def ancestors(self) -> List[object]:
        """Returns all ancestors of this object: parents, grandparents, etc."""
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

    @property
    def all_descendants(self) -> List[object]:
        """Returns children and all their descendants."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.all_descendants)
        return descendants

    def family(self,
               include_ancestors: bool = True,
               include_self: bool = True,
               include_children: bool = True,
               include_all_descendants: bool = True,
               include_siblings: bool = False,
               include_cousins_maxdepth: Optional[int] = None,
               include_cousins_from: Optional[Callable[[object], bool]] = None) -> List[object]:
        """Returns a list of family members associated with this node."""
        #
        # include_siblings is an alias for include_cousins_maxdepth = 1.
        if include_siblings:
            include_cousins_maxdepth = 1
        #
        # A negative cousins max depth is not permitted
        if include_cousins_maxdepth is not None and include_cousins_maxdepth < 0:
            raise ValueError(f'family: include_cousins_maxdepth must be 0 or greater')
        def at_cousin_level(c: Optional[int]) -> bool:
            """Returns True if it is this object that should be returning the list of family members."""
            return c is not None and c == 0
        if include_cousins_maxdepth is not None:
            #
            # If we are not at the cousin level we need to be, and this node has a parent, take one more step up through
            # the parent hierarchy
            if self.parent is not None and not at_cousin_level(include_cousins_maxdepth):
                return self.parent.family(include_ancestors=include_ancestors,
                                          include_self=include_self,
                                          include_cousins_maxdepth=include_cousins_maxdepth - 1)
            #
            # Otherwise we are at the right level, include all descendants from this node
            include_all_descendants = True
        #
        # Deal with including cousins based on a callback test.
        if include_cousins_from is not None:
            matches_cb = include_cousins_from(self)
            if self.parent is not None and not matches_cb:
                return self.parent.family(include_ancestors=include_ancestors,
                                          include_self=include_self,
                                          include_cousins_maxdepth=include_cousins_maxdepth - 1)
            if self.parent is None and not matches_cb:
                raise ValueError('No matches found for supplied callback function')
            include_all_descendants = True
        family = []
        if include_ancestors:
            family.extend(self.ancestors)
        if include_self:
            family.append(self)
        if include_children and not include_all_descendants:
            family.extend(self.children)
        elif include_all_descendants:
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
        return f'<{self.__class__.__name__} depth={self.depth} num_children={len(self.children)} line_num={self.line_num}: "{self.line}">'

    def __getattr__(self, item):
        """Pass unknown attributes and method calls to self.line for text manipulation and validation."""
        return getattr(self.line, item)

