#!/usr/bin/env python
# -*- coding: utf-8 -*-
from time import time
import weakref
from collections import defaultdict

live_refs = defaultdict(weakref.WeakKeyDictionary)


class object_ref(object):

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        live_refs[cls][obj] = time()
        return obj
