"""Parses the sections of a config document."""
from collections import namedtuple
import logging
import re
from typing import List
from networkconfigparser.documentline import DocumentLine


def num_leading_spaces(s: str) -> int:
    """Counts the number of leading spaces.

    Args:
        s: The string that may have leading spaces to count

    Returns:
        An int of the number of counted leading spaces.
    """
    i = 0
    while s.startswith(" "):
        i += 1
        s = s[1:]
    return i


def parse_autodetect(doc_lines: List[str]) -> List[DocumentLine]:
    """Parse a document, automatically detecting what type of parser to use.

    This method, at present, searches for brace characters '{' and '}' to detect whether
    parse_braced() should be used. If a minimum number of lines is found to have both opening and
    closing braces at the end, parse_braced() is used. Otherwise, the document is assumed to be
    structured with leading spaces and parse_leading_spaces() is used.

    Args:
        doc_lines: A list of lines from the document, one line per list entry.

    Returns:
        A list of DocumentLines as parsed by either parse_braced() or parse_leading_spaces().
    """
    #
    # We test whether the number of braced configuration lines meets a minimum number.
    minimum_match = 3     # Minimum number of each type of line to match the braced config style
    maximum_lines = 50    # Maximum number of lines of config to process
    braced_line_end_chars = {
        '{': 0,
        '}': 0,
        # ';': 0,  # This code once checked for semicolons but was removed to handle UBNT configs
    }
    lc = 0
    for line in doc_lines[:maximum_lines]:
        #
        # Skip comments
        if line.startswith('#') or line.startswith('!'):
            continue
        #
        # Increment line counter
        lc += 1
        #
        # Look for line-ending characters
        for k in braced_line_end_chars:
            if line.rstrip().endswith(k):
                braced_line_end_chars[k] += 1
        #
        # If we have hit the minimum match for all line ending chars, process as a braced config
        if all(i > minimum_match for i in braced_line_end_chars.values()):
            return parse_braced(doc_lines)
    return parse_leading_spaces(doc_lines)


def parse_braced(doc_lines: List[str]) -> List[DocumentLine]:
    """Parse a document structured with braces and semicolons, similar to C code.

    This parser should be used for JunOS-like configurations, including but not limited to JunOS
    itself, UBNT, Versa Networks, and Ribbon Neptune. Can be called directly, or can be called via
    parse_autodetect().

    Args:
        doc_lines: A list of lines from the document, one line per list entry.

    Returns:
        A list of DocumentLine objects.
    """
    dn_list = []
    dn_stack: List[DocumentLine] = []
    for lc, line in zip(range(1, len(doc_lines) + 1), doc_lines):
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
            logging.debug('parse_braced: section "%s" opening', current_dn.lstrip())
            dn_stack.append(current_dn)
            logging.debug('parse_braced: dn_stack: %s', dn_stack)
        #
        # If line ends with a closing brace, pop the current item off the stack
        if line.endswith('}') and not line.lstrip().startswith('#'):
            logging.debug('parse_braced: section "%s" closing', dn_stack[-1].lstrip())
            dn_stack.pop()
            logging.debug('parse_braced: dn_stack: %s', dn_stack)
    return dn_list


def parse_leading_spaces(doc_lines: List[str]) -> List[DocumentLine]:
    """Parse a document structured with leading spaces.

    This parser should be used for Cisco-type configurations, including but not limited to Cisco
    IOS, IOS XE, and IOS XR, Arista, and others. Can be called directly, or can be called via
    parse_autodetect().

    Args:
        doc_lines: A list of lines from the document, one line per list entry.

    Returns:
        A list of DocumentLine objects.
    """
    dn_list = []
    #
    # StackMember tuple is used to store the parent object on the ancestor stack, along with the
    # expected number of spaces its children lines will have.
    StackMember = namedtuple('StackMember', ['child_space_level', 'ancestor'])
    dn_stack: List[StackMember] = []
    current_dn = None
    banner_delimiter = None
    in_policy_set_section = False
    def current_space_level():
        """Return the current space level as determined by the most recent StackMember at the end
        of the stack."""
        if len(dn_stack) == 0:
            return 0
        return dn_stack[-1].child_space_level
    def ignore_spaces():
        """Return True if exceptional circumstances are in effect that should cause the parser not
        to apply familial logic based on leading spaces."""
        return banner_delimiter is not None or in_policy_set_section
    for lc, line in zip(range(1, len(doc_lines) + 1), doc_lines):
        #
        # Remove whitespace and LF at the end of the line
        line = line.rstrip()
        #
        # If the current space level is less than the number of spaces on this new line, this is a
        # new section and the last line should be placed on the dn_stack.
        new_space_level = num_leading_spaces(line)
        #
        # If in_policy_set_section is set, and the line starts with something other than a space or
        # an end-policy / end-set marker, log a warning and pop the last member off the stack.
        if in_policy_set_section and not (line.startswith(' ') or line.startswith('end-')):
            logging.warning('parse_leading_spaces: no end-set or end-policy encountered at line %s '
                            'within section %s',
                            lc,
                            str(dn_stack[-1].ancestor))
            dn_stack.pop()
            in_policy_set_section = False
        #
        # If the current space level is less than the new space level, add the previous line to the
        # stack.
        if not ignore_spaces() and current_space_level() < new_space_level and \
                current_dn is not None:
            logging.debug('parse_leading_spaces: space_level %s -> %s: incr',
                          current_space_level(), new_space_level)
            dn_stack.append(StackMember(new_space_level, current_dn))
            logging.debug('parse_leading_spaces: dn_stack: %s', dn_stack)
        #
        # If the current space level is greater than the number of spaces on this new line, this is
        # an end to the current section and the sections should be popped to match.
        if not ignore_spaces() and current_space_level() > new_space_level:
            logging.debug('parse_leading_spaces: space_level %s -> %s: decr',
                          current_space_level(), new_space_level)
            while current_space_level() > new_space_level:
                dn_stack.pop()
            logging.debug('parse_leading_spaces: dn_stack: %s', dn_stack)
        #
        # Create a new DocumentLine object and add to the children list of the parent.
        current_dn = DocumentLine(lc, line)
        if len(dn_stack) > 0:
            current_dn.parent = dn_stack[-1].ancestor
            dn_stack[-1].ancestor.children.append(current_dn)
        dn_list.append(current_dn)
        #
        # Exceptional Situations
        #
        # Deal with banners.
        if line.startswith('banner '):
            if m := re.match(r'^banner \S+ (\S+)$', line): # Cisco style
                banner_delimiter = m.group(1)
            elif re.match(r'^banner \S+$', line.strip()):  # Arista style
                banner_delimiter = 'EOF'
            dn_stack.append(StackMember(1, current_dn))
            logging.debug('parse_leading_spaces: found banner start, delimiter="%s"',
                          banner_delimiter)
            logging.debug('parse_leading_spaces: dn_stack: %s', dn_stack)
            continue
        if banner_delimiter is not None and (banner_delimiter in line or line in banner_delimiter):
            banner_delimiter = None
            dn_stack.pop()
            logging.debug('parse_leading_spaces: found banner end, delimiter="%s"',
                          banner_delimiter)
            logging.debug('parse_leading_spaces: dn_stack: %s', dn_stack)
        #
        # Deal with route policies and sets.
        if line.startswith('route-policy ') or re.match(r'\w+-set ', line):
            dn_stack.append(StackMember(1, current_dn))
            in_policy_set_section = True
            logging.debug('parse_leading_spaces: found IOSXR %s start', line.split()[0])
            logging.debug('parse_leading_spaces: dn_stack: %s', dn_stack)
        if in_policy_set_section and line.startswith('end-'):
            logging.debug('parse_leading_spaces: found IOSXR %s end',
                          dn_stack[-1].ancestor.split()[0])
            dn_stack.pop()
            in_policy_set_section = False
            logging.debug('parse_leading_spaces: dn_stack: %s', dn_stack)
    return dn_list

def parse_from_file(document_filename: str) -> List[DocumentLine]:
    """Parses a document stored in a file.

    Exactly equal to:

    .. code-block:: python

        with open(document_filename) as fh:
            text_lines = fh.readlines()
        return parse_from_str_list(text_lines)

    Args:
        document_filename: Full path of the file to open and read from

    Returns:
        A list of DocumentLine objects.
    """
    with open(document_filename, encoding='UTF-8') as fh:
        text_lines = fh.readlines()
    return parse_from_str_list(text_lines)

def parse_from_str_list(text_lines: List[str]) -> List[DocumentLine]:
    """Parses a document stored in a list of text.

    This passes the lines of text to parse_autodetect(), an internal function that determines
    whether the familial relationships are brace-delimited (Juniper-style) or space-delimited
    (Cisco-style).

    During processing, all lines are rstrip()'ed, so no trailing spaces are preserved.

    Args:
        text_lines: List of text to be parsed.

    Returns:
        A list of DocumentLine objects.
    """
    return parse_autodetect(text_lines)

def parse_from_str(text: str) -> List[DocumentLine]:
    """Parses a document stored in memory as a single string of text.

    Exactly equal to:

    .. code-block:: python

        return parse_from_str_list(text.split('\\\\n'))

    Args:
        text: Full text to be parsed.

    Returns:
        A list of DocumentLine objects.
    """
    return parse_from_str_list(text.split('\n'))
