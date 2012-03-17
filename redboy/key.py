# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#

"""Redboy: Key representation"""
import uuid

class Key(object):
    """
    A key determines how to extract the data from Redis. Maintains binary
    safe representation
    """
    def __init__(self, pool_name, prefix="", key=None):
        """Create a key that connects to the pool identified by pool_name with
        the prefix and a string key. The key can be None and the a uuid will be
        used in its place."""
        key = key or self._gen_uuid()
        self.pool_name = pool_name
        self.prefix = prefix
        self.key = key

    def _gen_uuid(self):
        """Generate a UUID for this object."""
        return uuid.uuid4().hex

    def _attrs(self):
        """Get attributes of this key."""
        return dict((attr, getattr(self, attr)) for attr in
                    ('pool_name', 'prefix', 'key',))

    def __str__(self):
        return self.prefix + self.key

    def __repr__(self):
        """Return a printable representation of this key."""
        return str(self._attrs())

    def __unicode__(self):
        """Return a unicode string of this key."""
        return unicode(str(self))
