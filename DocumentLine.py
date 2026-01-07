import logging
from typing import Optional, List


class DocumentLine(object):
    """Represents a single line in a document."""
    def __init__(self, line_num: int, line: str, parent: Optional[object] = None):
        self.line_num = line_num
        self.line = line
        self.parent = parent
        self.children = []

    @property
    def depth(self) -> int:
        """The depth level of the line, indexed from 1."""
        if self.parent is None:
            return 1
        return self.parent.depth + 1

    @property
    def ancestors(self) -> List[object]:
        """List of ancestors of this object."""
        if self.parent is None:
            return []
        return self.parent.ancestors + [self.parent]

    @property
    def all_descendants(self) -> List[object]:
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.all_descendants)
        return descendants

    def fam(self,
            include_ancestors: bool = True,
            include_self: bool = True,
            include_children: bool = True,
            include_all_descendants: bool = True,
            include_siblings: bool = False,
            include_cousins_maxdepth: Optional[int] = None) -> List[object]:
        """Returns a list of family members associated with this node."""
        if include_siblings:
            include_cousins_maxdepth = 1
        if include_cousins_maxdepth is not None and include_cousins_maxdepth < 0:
            raise ValueError(f'fam: include_cousins_maxdepth must be 0 or greater')
        def at_cousin_level(c: Optional[int]) -> bool:
            return c is not None and c == 0
        if include_cousins_maxdepth is not None:
            #
            # If we are not at the cousin level we need to be, and this node has a parent, take one more step through
            # the parent hierarchy
            if self.parent is not None and not at_cousin_level(include_cousins_maxdepth):
                return self.parent.fam(include_ancestors=include_ancestors,
                                       include_self=include_self,
                                       include_cousins_maxdepth=include_cousins_maxdepth - 1)
            #
            # Otherwise we are at the right level, include all descendants from this node
            include_all_descendants = True
        family = []
        if include_ancestors:
            family.extend(self.ancestors)
        if include_self:
            family.append(self)
        if include_children and not include_all_descendants:
            family.extend(self.children)
        elif include_all_descendants:
            family.extend(self.all_descendants)
        return family

    def __eq__(self, other):
        return self.line == other.line

    def __hash__(self):
        return hash(self.line)

    def __str__(self):
        return self.line

    def __repr__(self):
        return f'<DocumentNode depth={self.depth} num_children={len(self.children)} line_num={self.line_num}: "{self.line}"'
