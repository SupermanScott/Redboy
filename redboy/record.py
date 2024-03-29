# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Redboy: Record representation"""

from itertools import ifilterfalse as filternot
from redboy.key import Key
from redboy import get_pool

import redboy.exceptions as exc
import copy

class Record(dict):
    """A record is a collection of key:value pairs that map to a dictionary"""
    # A tuple of string field names that are required to be in the Record
    _required = ()

    # A tuple of string field names that are used to create unique Indices for
    # the Record
    _indices = ()

    # The prefix the record should be saved too.
    _prefix = ""

    # Pool name for the record's redis connection
    _pool_name = ""

    # Tuple of Views to save the Record into
    _views = ()

    # Tuple of alternative copies of this Record.
    _mirrors = ()

    def __init__(self, *args, **kwargs):
        dict.__init__(self)
        self._clean()

        for key, value in kwargs.iteritems():
            self[key] = value

        if not self._prefix:
            self._prefix = str.lower(self.__class__.__name__) + ":"

        if not self._pool_name:
            self._pool_name = str.lower(self.__class__.__name__)

    def load(self, key):
        """Load the Record on its key. key can be either an instance of Key or a
        string. In the latter case, it will be sent to Record.make_key"""
        if not isinstance(key, Key):
            key = self.make_key(key)

        self._clean()

        pool_name = key.pool_name or self._pool_name
        self._original = get_pool(pool_name).hgetall(str(key))

        self.revert()
        self.key = key

        return self

    def load_by_index(self, field, value):
        """Load the Record by the unqiue index. field must be contained in
        self._indices and is the value of the field. Constructs a key throught
        self.make_key()"""
        self._clean()
        key = self.make_index_key(field)
        return self.load(get_pool(key.pool_name).hget(str(key), value))

    def save(self):
        """Save the record, returns self."""
        if not self.valid():
            raise exc.ErrorMissingField("Missing required field(s):",
                                        self.missing())
        new_record = False
        if not hasattr(self, 'key') or not self.key:
            self.key = self.make_key()
            new_record = True

        assert isinstance(self.key, Key), "Bad record key in save()"

        # Marshal and save changes
        changes = self._marshal()
        self._save_internal(self.key, changes)

        try:
            try:
                # Save mirrors
                for mirror in self.get_mirrors():
                    mirror._save_internal(mirror.mirror_key(self), changes)
            finally:
                # Update Views
                for view in self.get_views():
                    view.record_class = self.__class__
                    view.append(self, new_record)
        finally:
            # Clean up internal state
            self._modified.clear()
            self._deleted.clear()
            self._original = copy.deepcopy(self._columns)

        return self

    def remove(self):
        """Remove this record from Redis."""
        pool_name = self.key.pool_name
        try:
            try:
                # Save mirrors
                for mirror in self.get_mirrors():
                    mirror.key = mirror.mirror_key(self)
                    mirror.remove()
            finally:
                # Update viewes
                for view in self.get_views():
                    view.record_class = self.__class__
                    view.remove(self)
        finally:
            pool = get_pool(pool_name)
            pool.delete(str(self.key))
            for index in self._indices:
                unqiue_field_key = self.make_index_key(index, self.key)
                pool.hdel(unqiue_field_key, self[index])
            self._clean()
        return self

    def make_key(self, key=None):
        """Makes a key from the provided string key"""
        if not self.key:
            return Key(self._pool_name, self._prefix, key)
        else:
            return Key(self.key._pool_name, self.key._prefix, key)

    def make_index_key(self, field, key=None):
        """Makes a new Key object for the unique index on field"""
        if isinstance(key, Key):
            starting_key = copy.copy(key)
        else:
            starting_key = self.make_key()

        starting_key.prefix += "byfield:"
        starting_key.key = field
        return starting_key

    def valid(self):
        """Return a boolean indicating whether the record is valid."""
        return len(self.missing()) == 0

    def missing(self):
        """Return a tuple of required items which are missing."""
        return tuple(filternot(self.get, self._required))

    def revert(self):
        """Revert changes, restoring to the state we were in when loaded."""
        for name, value in self._original.iteritems():
            dict.__setitem__(self, name, value)
            self._columns[name] = copy.copy(value)

        self._modified, self._deleted = {}, {}

    def get_views(self):
        """Return views this record should be stored in."""
        # @TODO: refactor this guy away!
        return self._views

    def get_mirrors(self):
        """Return mirrors this record should be stored in."""
        return [mirror if isinstance(mirror, type) else mirror
                for mirror in self._mirrors]

    def _save_internal(self, key, changes):
        """Internal save method."""
        if not key:
            return

        pool_name = key.pool_name or self._pool_name
        connection_pool = get_pool(pool_name)

        # Delete items
        if changes['deleted']:
            deleted_fields = []
            for field, old_value in changes['deleted']:
                deleted_fields.append(field)
                # Delete the record from the unique indices.
                if field in self._indices:
                    unique_field_key = self.make_index_key(field, key)
                    connection_pool.hdel(
                        str(unique_field_key),
                        old_value)

            # Remove the deleted field from hash
            deleted_fields = [x[0] for x in changes['deleted']]
            connection_pool.hdel(str(key), *deleted_fields)

        self._deleted.clear()

        # Update items
        if changes['changed']:
            # @TODO: Use Pipeline to protect this.
            for field, value, original_value in changes['changed']:
                connection_pool.hset(str(key), field, value)

                # Update the unique indexes
                if field in self._indices:
                    unique_field_key = self.make_index_key(field, key)

                    # Delete the old index.
                    if original_value:
                        connection_pool.hdel(
                            str(unique_field_key),
                            original_value)

                    # Add the new index.
                    connection_pool.hset(
                        str(unique_field_key),
                        value,
                        key.key)

    def _marshal(self):
        """Marshal deleted and changed columns."""
        return {'deleted': tuple((field , old_value,)
                                 for field, old_value in self._deleted.iteritems()
                                 if old_value),
                'changed': tuple((key, self._columns[key], self._original.get(key, None),)
                                 for key, mod_value in self._modified.iteritems()
                                 if mod_value)}

    def _clean(self):
        """Remove every item from the object"""
        map(self.__delitem__, self.keys())
        self._original, self._columns = {}, {}
        self._modified, self._deleted = {}, {}
        self.key = None

    def __setitem__(self, item, value):
        """Set an item, storing it into the _columns backing store."""
        if value is None:
            # @TODO: make this a call to self.__delitem__
            raise exc.ErrorInvalidValue("You may not set an item to None.")

        # If this doesn't change anything, don't record it
        _orig = self._original.get(item)
        if _orig and _orig == value:
            return

        dict.__setitem__(self, item, value)

        self._columns[item] = value

        if item in self._deleted:
            del self._deleted[item]

        self._modified[item] = True

    def __delitem__(self, item):
        dict.__delitem__(self, item)
        # Don't record this as a deletion if it wouldn't require a remove()
        self._deleted[item] = self._original.get(item, None)
        if item in self._modified:
            del self._modified[item]
        del self._columns[item]

class MirroredRecord(Record):

    """A mirrored (denormalized) record."""

    def mirror_key(self, parent_record):
        """Return the key this mirror should be saved into."""
        assert isinstance(parent_record, Record)
        raise exc.ErrorMissingKey("Please implement a mirror_key method.")

    def save(self):
        """Refuse to save this record."""
        raise exc.ErrorImmutable("Mirrored records are immutable.")
