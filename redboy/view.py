# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Redboy: View implementation"""

from redboy import get_pool
from redboy.record import Record

class QueueView(object):
    """A QueueView is a set of Records ordered by when they were appended"""
    def __init__(self, view_key, record_class):
        """view_key is the redboy.key.Key for the set of records and
        record_class is the Record implementation."""
        record_class = record_class or Record
        self.key, self.record_class = view_key, record_class

    def append(self, record, new_record):
        """Add the Record to the View"""
        # Save the records, non-prefix version.
        if new_record:
            get_pool(self.key.pool_name).rpush(str(self.key), record.key.key)

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
