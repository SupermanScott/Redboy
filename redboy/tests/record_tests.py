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
    record_dict = {
        'name': 'scott',
        'email': 'scott@scottreynolds.us',
        'awesome': True,
        }
    redis_client_mock = mock.Mock(name="redis_client")
    redis_client_mock.hgetall = mock.Mock(return_value=record_dict)
    record.get_pool = mock.Mock(name="redis", return_value=redis_client_mock)

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

@nose.with_setup(setup_function)
def test_loading():
    loaded_record = record.Record().load(
        record.Key(pool_name="test_pool", prefix="test", key="scott"))

    assert record.get_pool.assert_once_called_with("test_pool"), \
        "Loading a record didn't call get_pool once with the right pool name"

    client = record.get_pool("test_pool")
    assert len(client.mock_calls) == 1, \
        "Redis Client should only be called once"
    assert client.mock_calls[0][0] == "hgetall", \
        "Call to Redis should be hgetall not %s" % (client.mock_calls[0][0],)
    assert client.mock_calls[0][1][0] == "testscott", \
        "HGetAll called with bad arg: %s" % (client.mock_calls[0][1][0],)

    assert not loaded_record._modified, \
        "Loaded record shouldn't have any modifications"
    assert not loaded_record._deleted, \
        "Loaded record shouldn't have any deletions"

    loaded_record['testing'] = 'Yes'

    assert 'testing' in loaded_record._modified, \
        "The key testing should be in modified storage"
    assert not loaded_record._deleted, \
        "Loaded record shouldn't have any deletions"

    del loaded_record['testing']
    assert 'testing' not in loaded_record._modified, \
        "Modified key should be removed."
    assert not loaded_record._deleted['testing'], \
        "Loaded record shouldn't have any deletions"

    loaded_record['testing'] = 'Yes Again!'
    loaded_record.save()

    del loaded_record['testing']
    assert loaded_record._deleted['testing'], \
        "del after saving should add testing to the deleted storage"

    loaded_record.save()
    assert 'testing' not in loaded_record, \
        "testing shouldn't be in the record"
