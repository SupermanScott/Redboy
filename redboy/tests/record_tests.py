# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Tests for the Record class"""
import mock
import nose
import redboy
import redboy.record as record

def setup_function():
    """Mock the redis database access"""
    record.get_pool = mock.Mock(name="redis", return_value=mock.Mock(name="redis_client"))

@nose.with_setup(setup_function)
def test_new_record():
    new_record = record.Record(name="scott", email="scott@scottreynolds.us")
    assert "name" in new_record, "First name is missing from record"
    assert "email" in new_record, "Email is missing from record"

    assert "name" in new_record._modified, "name isn't marked for insertation"
    assert "email" in new_record._modified, "email isn't marked for insertation"

    assert not new_record._deleted, "fields shouldn't be marked for deletion"

    assert not new_record.key, "Records key should not be set"

    new_record.save()

    assert record.get_pool.assert_once_called_with(new_record._pool_name), \
        "Record should have called get_pool once with pool_name"

    new_record.key = record.Key(pool_name="test_pool")
    new_record.save()
    assert record.get_pool.assert_once_called_with(new_record.key.pool_name), \
        "Record should have called get_pool once with key's pool_name"
