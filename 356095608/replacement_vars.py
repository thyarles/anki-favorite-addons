import os

from .config import (
    file_replacements,
    file_regex,
    gc,
)
from .file_load_save import (
    pickleload_nestedlist_list,
)


def regular_replacements():
    return repl_regular


def regex_replacements():
    return repl_regex


def update_regular():
    global repl_regular
    repl_regular = {}
    loaded = pickleload_nestedlist_list(file_replacements)
    if loaded:
        for k, v in loaded:
            repl_regular[k] = v


def update_regex():
    global repl_regex
    repl_regex = {}
    loaded = pickleload_nestedlist_list(file_regex)
    if loaded:
        for k, v in loaded:
            repl_regex[k] = v


update_regular()
update_regex()
