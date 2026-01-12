from parser import *
from search_helpers import *
from pprint import pprint
from unittest import TestCase

class TestSearchHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        config = """l2vpn
 bridge group COMMON
  bridge domain VLAN50
  bridge domain VLAN60
 bridge group UNCOMMON
  bridge domain FOOBR
  bridge domain VLAN70"""
        cls.config_lines = config.split('\n')
        cls.doc_lines = parse_from_str_list(cls.config_lines)
        #
        class Dummy(object):
            pass
        cls.test_str = 'COMMON'
        cls.test_pattern = re.compile(r'\d+')
        cls.test_cb = lambda x: 'foobar' in x
        cls.test_dummy = Dummy()

    def test_find_lines(self):
        pass
        # TODO case single search_spec regex and regex_group is 1
        # TODO case single search_spec cb and regex_group is 1
        # TODO case single search_spec dummy_object and regex_group is 1
        # TODO case search_spec iterable with final term regex and regex_group is 1
        # TODO case search_spec iterable with final term cb and regex_group is 1
        # TODO case search_spec iterable with final term dummy_object and regex_group is 1
        # TODO case group is 1, search_spec regex, and convert_result is cb
        # TODO case recurse_search is False, search_spec matches chain
        # TODO case recurse_search is False, search_spec does not match chain

    def test_convert_search_spec_to_cb(self):
        #
        # case search_spec is single str
        search_term = convert_search_spec_to_cb(self.test_str)
        #
        assert search_term(self.doc_lines[1])
        # case search_spec is single re.Pattern
        search_term = convert_search_spec_to_cb(self.test_pattern)
        assert search_term(self.doc_lines[2])
        #
        assert not search_term(self.doc_lines[1])
        # case search_spec is single invalid object
        with self.assertRaises(ValueError):
            convert_search_spec_to_cb(self.test_dummy)
        #
        # case search_spec is iterable len = 0
        with self.assertRaises(ValueError):
            convert_search_spec_to_cb([])
        #
        # case search_spec is iterable str len = 1
        search_term = convert_search_spec_to_cb([self.test_str])
        assert search_term[0](self.doc_lines[1])
        #
        # case search_spec is iterable mixed str and re.Pattern len = 2
        search_term = convert_search_spec_to_cb([self.test_str, self.test_pattern])
        assert search_term[0](self.doc_lines[1])
        assert search_term[1](self.doc_lines[2])
        #
        # case search_spec is iterable mixed str and re.Pattern len = 3
        search_term = convert_search_spec_to_cb(['l2vpn', self.test_str, self.test_pattern])
        assert search_term[0](self.doc_lines[0])
        assert search_term[1](self.doc_lines[1])
        assert search_term[2](self.doc_lines[2])
        #
        # case search_spec is iterable with non-str/non-re.Pattern term
        with self.assertRaises(ValueError):
            convert_search_spec_to_cb(['l2vpn', self.test_str, self.test_pattern, self.test_dummy])
        #
        # case search_spec is single cb
        cb = lambda x: 'un' in x.lower()
        assert cb == convert_search_spec_to_cb(cb)
        #
        # case search_spec is iterable cb len = 1
        assert cb == convert_search_spec_to_cb([cb])[0]
        #
        # case search_spec is iterable cb len = 2
        assert cb == convert_search_spec_to_cb(['vpn', cb])[1]
        #
        # case search_spec is iterable with non-cb term
        search_term = convert_search_spec_to_cb([lambda x: 'vpn' in x, self.test_str, self.test_pattern])
        assert search_term[0](self.doc_lines[0])
        assert search_term[1](self.doc_lines[1])
        assert search_term[2](self.doc_lines[2])
        #
        # case regex_flags is set
        search_term = convert_search_spec_to_cb(['L2VPN', 'DOMAIN'], re.IGNORECASE)
        assert search_term[1](self.doc_lines[2])
        assert search_term[0](self.doc_lines[0])

    def test_find_lines_with_cb(self):
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x)
        assert len(result) == 2
        assert isinstance(result[0], DocumentLine)
        # case convert_result is str
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x, convert_match=lambda x: str(x))
        assert isinstance(result[0], str)
        # case convert_family is str
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x, convert_family=lambda x: str(x),
                                    include_ancestors=False, include_children=True, include_all_descendants=False)
        assert isinstance(result[0], DocumentLine)
        assert isinstance(result[1], str)
        # case convert_result is str and convert_family is str
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x,
                                    convert_match=lambda x: str(x),
                                    convert_family=lambda x: str(x),
                                    include_ancestors=False, include_children=True, include_all_descendants=False)
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        # case flatten_family is False and include_* are True
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x,
                                    flatten_family=False,
                                    include_ancestors=True, include_all_descendants=True)
        assert result[0] == self.doc_lines[0:4]
        assert result[1] == [self.doc_lines[0]] + self.doc_lines[4:7]
        # case suppress_common_ancestors is False and include_* are True
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x,
                                    suppress_common_ancestors=False,
                                    include_ancestors=True, include_all_descendants=True)
        assert result[0:4] == self.doc_lines[0:4]
        assert result[4:8] == [self.doc_lines[0]] + self.doc_lines[4:7]
        # case suppress_common_ancestors is False and include_* are False
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x,
                                    suppress_common_ancestors=False)
        assert result[0] == self.doc_lines[1]
        assert result[1] == self.doc_lines[4]
        # case include_ancestors is True
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x, include_ancestors=True)
        assert result[0] == self.doc_lines[0]
        assert result[1] == self.doc_lines[1]
        # case include_self is False
        result = find_lines_with_cb(self.doc_lines, lambda x: 'group' in x, include_ancestors=True, include_self=False,
                                    include_all_descendants=True)
        assert result[0] == self.doc_lines[0]
        assert not result[1] == self.doc_lines[1]
        # case include_children is True
        result = find_lines_with_cb(self.doc_lines, lambda x: 'l2vpn' in x, include_children=True)
        assert result[0] == self.doc_lines[0]
        assert result[1] == self.doc_lines[1]
        assert result[2] == self.doc_lines[4]
        # case include_all_descendants is True
        result = find_lines_with_cb(self.doc_lines, lambda x: 'l2vpn' in x, include_all_descendants=True)
        assert result == self.doc_lines

    def test_re_search_dl(self):
        test_objs = [
            DocumentLine(1, 'Green Midget Cafe'),
            DocumentLine(2, 'Bletchley Park')
        ]
        #
        # case regex is str
        assert re_search_dl('MID(GET)', test_objs[0], re.IGNORECASE).group(1) == 'get'
        assert not re_search_dl('MID(GET)', test_objs[1], re.IGNORECASE)
        #
        # case regex is re.Pattern
        assert re_search_dl(self.test_pattern, self.doc_lines[2])
        assert not re_search_dl(self.test_pattern, self.doc_lines[1])

    def test_re_search_cb(self):
        cb = re_search_cb(self.test_str, re.IGNORECASE)
        assert not cb(self.doc_lines[0])
        assert cb(self.doc_lines[1])

    def test_parent_child_cb(self):
        with self.assertRaises(ValueError):
            parent_child_cb('parent', self.test_dummy)
        with self.assertRaises(ValueError):
            parent_child_cb(self.test_dummy, 'child')
        #
        # case match parent and 3rd gen item
        cb = parent_child_cb('l2vpn', 'FOOBR')
        result = [i for i in self.doc_lines if cb(i)]
        assert result == [self.config_lines[0]]
        #
        # case no match returned
        cb = parent_child_cb('l2vpn', 'FOOBAZ')
        result = [i for i in self.doc_lines if cb(i)]
        assert result == []
        #
        # case no recurse, no match returned
        cb = parent_child_cb('l2vpn', 'FOOBR', recurse=False)
        result = [i for i in self.doc_lines if cb(i)]
        assert result == []
        #
        # case no recurse, match returned
        cb = parent_child_cb('group', 'FOOBR', recurse=False)
        result = [i for i in self.doc_lines if cb(i)]
        assert result == [self.config_lines[4]]
        #
        # case negative child match
        cb = parent_child_cb('group', 'FOOBR', negative_child_match=True)
        result = [i for i in self.doc_lines if cb(i)]
        assert result == [self.config_lines[1]]

    def test_common_line_suppressor(self):
        config_lines = self.config_lines
        vlan_lines = find_lines(self.doc_lines, 'VLAN')
        #
        unsuppressed = [str(j) for i in vlan_lines for j in i.family()]
        first_match = config_lines[0:3]
        second_match = config_lines[0:2] + [config_lines[3]]
        third_match = [config_lines[0], config_lines[4], config_lines[6]]
        assert unsuppressed == first_match + second_match + third_match
        #
        s = common_line_suppressor()
        suppressed = [str(j) for i in vlan_lines for j in s(i.family())]
        assert suppressed == config_lines[0:5] + [config_lines[6]]

    def test_is_iterable_search_term(self):
        assert not is_iterable_search_term(self.test_str)
        assert not is_iterable_search_term(self.test_pattern)
        assert is_iterable_search_term([self.test_str])

    def test_isiterable(self):
        assert isiterable(self.test_str)
        assert not isiterable(self.test_pattern)
        assert isiterable([self.test_str])

    def test_is_regex(self):
        assert is_regex(self.test_str)
        assert is_regex(self.test_pattern)
        assert not is_regex([self.test_str])

    def test_identity(self):
        assert identity(self.test_pattern) == self.test_pattern
        assert identity(self.test_pattern) is self.test_pattern
