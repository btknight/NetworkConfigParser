"""Provides a variety of methods to read in configurations."""
from parser import *
from typing import List

def read_config_from_file(filename: str) -> List[DocumentLine]:
    with open(filename) as fh:
        config = fh.readlines()
    return read_config_from_str_list(config)

def read_config_from_str_list(config: List[str]) -> List[DocumentLine]:
    return parse_lines(config)

def read_config_from_str(config: str) -> List[DocumentLine]:
    return read_config_from_str_list(config.split('\n'))
