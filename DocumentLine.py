"""Defines the DocumentLine object, a node in a familial tree describing a structured document layout."""
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
        """Returns all descendants: children, grandchildren, etc."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.all_descendants)
        return descendants

    def family(self,
               include_ancestors: bool = True,
               include_self: bool = True,
               include_children: bool = True,
               include_all_descendants: bool = True) -> List[object]:
        """Returns a list of family members associated with this node."""
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
