# -*- coding: utf-8 -*-
from __future__ import absolute_import

from difflib import SequenceMatcher


def fmatch_iter(needle, haystack, min_ratio=0.6):
    for key in haystack:
        ratio = SequenceMatcher(None, needle, key).ratio()
        if ratio >= min_ratio:
            yield ratio, key


def fmatch_best(needle, haystack, min_ratio=0.6):
    try:
        return sorted(
            fmatch_iter(needle, haystack, min_ratio), reverse=True,
        )[0][1]
    except IndexError:
        pass
