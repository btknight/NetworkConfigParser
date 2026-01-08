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


def parse_autodetect(config: List[str]) -> List[DocumentLine]:
    """Parse a document, automatically detecting what type of parser to use."""
    #
    # We test whether the number of braced configuration lines meets a minimum number.
    minimum_match = 3     # Minimum number of each type of line to match the braced config style
    maximum_lines = 50    # Maximum number of lines of config to process
    braced_line_end_chars = {
        '{': 0,
        '}': 0,
        ';': 0,
    }
    lc = 0
    for line in config:
        #
        # Skip comments
        if line.startswith('#') or line.startswith('!'):
            continue
        #
        # Increment line counter
        lc += 1
        #
        # Look for line-ending characters
        for k in braced_line_end_chars.keys():
            if line.rstrip().endswith(k):
                braced_line_end_chars[k] += 1
        #
        # If we have hit the minimum match for the line ending chars, process as a braced config
        if all([i > minimum_match for i in braced_line_end_chars.values()]):
            return parse_braced(config)
        #
        # Break out of the loop if we have hit the maximum number of lines
        if lc == maximum_lines:
            break
    return parse_leading_spaces(config)


def parse_braced(config: List[str]) -> List[DocumentLine]:
    """Parse a document structured with braces and semicolons, similar to C code."""
    dn_list = []
    dn_stack: List[DocumentLine] = []
    for lc, line in zip(range(1, len(config) + 1), config):
        #
        # Remove whitespace and LF at the end of the line
        line = line.rstrip()
        #
        # Create a new DocumentLine object and add to the children list of the parent.
        current_dn = DocumentLine(lc, line)
        if len(dn_stack) > 0:
            current_dn.parent = dn_stack[-1]
            dn_stack[-1].children.append(current_dn)
        dn_list.append(current_dn)
        #
        # If line ends with an opening brace, add this item to the stack
        if line.endswith('{') and not line.lstrip().startswith('#'):
            dn_stack.append(current_dn)
        #
        # If line ends with a closing brace, pop the current item off the stack
        if line.endswith('}') and not line.lstrip().startswith('#'):
            dn_stack.pop()
    return dn_list


def parse_leading_spaces(config: List[str]) -> List[DocumentLine]:
    """Parse a document structured with leading spaces."""
    space_multiplier = None
    current_space_level = 0
    dn_list = []
    dn_stack: List[DocumentLine] = []
    current_dn = None
    banner_delimiter = None
    ignore_space_levels = False
    for lc, line in zip(range(1, len(config) + 1), config):
        #
        # Remove whitespace and LF at the end of the line
        line = line.rstrip()
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
        #
        # If ignore_space_levels is set, force new_space_level to 1 as long as there is a space at the beginning of the
        # line, or the line starts with 'end-'. This forces any length space to be associated as a child of the top-
        # level member.
        if ignore_space_levels and (line.startswith(' ') or line.startswith('end-')):
            new_space_level = 1
        elif ignore_space_levels:
            logging.warning(f'parse_lines: no end-set or end-policy encountered at line {lc}: {str(dn_stack[-1])}')
            ignore_space_levels = False
        #
        # If the current space level is less than the new space level, add the previous line to the stack.
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
        # Create a new DocumentLine object and add to the children list of the parent.
        current_dn = DocumentLine(lc, line)
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
        # Deal with route policies and sets.
        if line.startswith('route-policy ') or re.match(r'\w+-set ', line):
            ignore_space_levels = True
        if ignore_space_levels and line.startswith('end-'):
            ignore_space_levels = False
    return dn_list
