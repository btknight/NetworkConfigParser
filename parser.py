"""Parses the sections of a config file."""
from DocumentLine import *
import logging
import re
from typing import List


def num_leading_spaces(s: str) -> int:
    i = 0
    while s.startswith(" "):
        i += 1
        s = s[1:]
    return i


def parse_lines(config: List[str]) -> List[DocumentLine]:
    """Parse the configuration and build the document tree."""
    space_multiplier = None
    current_space_level = 0
    dn_list = []
    dn_stack: List[DocumentLine] = []
    current_dn = None
    banner_delimiter = None
    for lc, line in zip(range(1, len(config) + 1), config):
        #
        # Count the number of spaces in the first line with a non-zero number of spaces. This is our space multiplier.
        if space_multiplier is None and line.startswith(" "):
            space_multiplier = num_leading_spaces(line)
            logging.debug(f'parse_lines: space_multiplier = {space_multiplier}')
        #
        # If the current space level is less than the number of spaces on this new line, this is a new section
        # and the last line should be placed on the dn_stack.
        if space_multiplier is not None:
            new_space_level = num_leading_spaces(line) // space_multiplier
        else:
            new_space_level = 0

        if current_space_level < new_space_level:
            if current_space_level + 1 != new_space_level:
                logging.warning(f'parse_lines: new space level is greater than one level deeper than expected on line {lc}')
            dn_stack.append(current_dn)
            logging.debug(f'parse_lines: space_level {current_space_level} -> {new_space_level}: incr')
            logging.debug(f'parse_lines: dn_stack: [{dn_stack}]')
        #
        # If the current space level is greater than the number of spaces on this new line, this is an end to the
        # current section and the sections should be popped to match.
        if current_space_level > new_space_level:
            dn_stack = dn_stack[0:new_space_level]
            logging.debug(f'parse_lines: space_level {current_space_level} -> {new_space_level}: decr')
            logging.debug(f'parse_lines: dn_stack: [{dn_stack}]')
            ignore_space_levels = False
        #
        # Set current space level
        current_space_level = new_space_level
        #
        # Create a new DocumentNode for this line and add to the children list of the parent.
        current_dn = DocumentLine(lc, line.rstrip())
        if len(dn_stack) > 0:
            current_dn.parent = dn_stack[-1]
            dn_stack[-1].children.append(current_dn)
        dn_list.append(current_dn)
        #
        # Deal with banners.
        if line.startswith('banner '):
            banner_delimiter = re.match(r'^banner \S+ (\S+)', line).group(1)
            dn_stack.append(current_dn)
            continue
        if banner_delimiter is not None and banner_delimiter in line:
            banner_delimiter = None
            dn_stack.pop()
        #
        # Deal with route policies.
        if line.startswith('route-policy '):
            ignore_space_levels = True
    return dn_list
