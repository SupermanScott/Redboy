# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Redboy: View implementation"""

from redboy import get_pool
from redboy.record import Record

class View(object):
    """A View is a set of Records. The how of the ordering is determined by Subclasses"""
    def __init__(self, view_key, record_class=None):
        """view_key is the redboy.key.Key for the set of records and
        record_class is the Record implementation."""
        record_class = record_class or Record
        self.key, self.record_class = view_key, record_class

    def append(self, record, new_record):
        """Add the Record to the View"""
        raise NotImplemented("Use a Subclass to append to the View")

    def __iter__(self):
        connection_pool = get_pool(self.key.pool_name)
        for x in xrange(0, len(self)):
            record_key = connection_pool.lindex(str(self.key), x)
            yield self.record_class().load(record_key)

    def __getitem__(self, key):
        record_key = get_pool(self.key.pool_name).lindex(str(self.key), key)
        return self.record_class().load(record_key)

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.key)

    def __len__(self):
        return get_pool(self.key.pool_name).llen(str(self.key))

class Stack(View):
    """A Stack is a set of records that is First In Last Out"""
    def append(self, record, new_record):
        if new_record:
            get_pool(self.key.pool_name).lpush(str(self.key), record.key.key)

class Queue(View):
    """A Queue is a set of Records ordered by when they were appended"""
    def append(self, record, new_record):
        """Add the Record to the View"""
        # Save the records, non-prefix version.
        if new_record:
            get_pool(self.key.pool_name).rpush(str(self.key), record.key.key)

class Score(object):
    """A Score view is a set of Records ordered by a score function"""
    def __init__(self, view_key, score_function, reverse=False, record_class=None):
        """view_key is the redboy.key.Key for the set of records and
        record_class is the Record implementation."""
        record_class = record_class or Record
        self.key, self.record_class = view_key, record_class
        self.score = score_function
        self.reverse = reverse

    def append(self, record, new_record):
        """Add the Record to the View"""
        score = self.score(record)
        get_pool(self.key.pool_name).zadd(str(self.key), score, record.key.key)

    def __iter__(self):
        connection_pool = get_pool(self.key.pool_name)
        for x in xrange(0, len(self)):
            record_key = connection_pool.zrange(
                str(self.key),
                x,
                x,
                self.reverse)
            yield self.record_class().load(record_key[0])

    def __getitem__(self, key):
        record_key = get_pool(self.key.pool_name).zrange(
            str(self.key),
            key,
            key,
            self.reverse)
        return self.record_class().load(record_key[0])

    def __repr__(self):
        return "%s: %s" % (self.__class__.__name__, self.key)

    def __len__(self):
        return get_pool(self.key.pool_name).zcard(str(self.key))
