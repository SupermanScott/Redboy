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

    assert loaded_record.key
    assert loaded_record.key.key == "scott"

    assert 'awesome' in loaded_record._original and 'awesome' in loaded_record, \
        "awesome key should be loaded into original"
    assert 'name' in loaded_record._original and 'name' in loaded_record, \
        "name should be in the original"
    assert 'email' in loaded_record._original and 'email' in loaded_record, \
        "email should bein the original"

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

@nose.with_setup(setup_function)
def test_saving():
    loaded_record = record.Record().load(
        record.Key(pool_name="test_pool", prefix="test", key="scott"))

    loaded_record['awesome'] = False
    assert 'awesome' in loaded_record._modified, \
        "awesome key should be setup for changes"
    assert 'awesome' not in loaded_record._deleted, \
        "awesome key should not be in the deleted storage"

    loaded_record.save()

    assert 'awesome' not in loaded_record._modified, \
        "awesome should not be in modified after save"
    assert 'awesome' in loaded_record and not loaded_record['awesome'], \
        "Awesome should be in the record and set to False"

    del loaded_record['awesome']
    loaded_record.save()
    assert 'awesome' not in loaded_record._deleted, \
        "awesome should be cleared from deleted storage"
    assert not loaded_record._deleted and not loaded_record._modified, \
        "loaded_record shouldn't have any new changes after save"

@nose.with_setup(setup_function)
def test_mirrors():
    loaded_record = record.Record().load(
        record.Key(pool_name="test_pool", prefix="test", key="scott"))

    mock_mirror = mock.Mock(name="mirror")
    mock_mirror.mirror_key = mock.Mock(name="mirror_key",
                                     return_value=record.Key(pool_name="test_pool",
                                                             key="mirror"))
    loaded_record.get_mirrors = mock.Mock(name="get_mirrors",
                                          return_value=[mock_mirror])
    loaded_record.save()

    assert mock_mirror.mock_calls[0][0] == '_save_internal', \
        "Mirror._save_internal should be called"
    assert mock_mirror.mock_calls[0][1][0].key == 'mirror', \
        "Mirror._save_internal key is wrong: %s" % \
        (mock_mirror.mock_calls[0][1][0],)

    changes = mock_mirror.mock_calls[0][1][1]
    assert not changes['deleted'] and not changes['changed'], \
        "Shouldn't be any changes: %s" % (changes,)

@nose.with_setup(setup_function)
def test_views():
    loaded_record = record.Record().load(
        record.Key(pool_name="test_pool", prefix="test", key="scott"))

    mock_view = mock.Mock(name="view")
    get_mock = mock.Mock(name="get_views", return_value=[mock_view])
    loaded_record.get_views = get_mock
    loaded_record.save()

    assert mock_view.mock_calls[0][0] == 'append', \
        "View append method should be called"
    assert mock_view.mock_calls[0][1][0] == loaded_record, \
        "View append should be called with the record"
    assert not mock_view.mock_calls[0][1][1], \
        "The call to append should tell the view it isn't a new record %s" % (str(mock_view.mock_calls[0][1]),)

    mock_view.reset_mock()

    new_record = record.Record()
    new_record.get_views = get_mock
    new_record.save()

    assert mock_view.mock_calls[0][0] == 'append', \
        "View append method should be called"
    assert mock_view.mock_calls[0][1][0] == new_record, \
        "View append should be called with the record"
    assert mock_view.mock_calls[0][1][1], \
        "The call to append should tell the view it is a new record"

@nose.with_setup(setup_function)
def test_removal():
    loaded_record = record.Record().load(
        record.Key(pool_name="test_pool", prefix="test", key="scott"))

    mock_view = mock.Mock(name="view")
    get_mock = mock.Mock(name="get_views", return_value=[mock_view])
    mock_mirror = mock.Mock(name="mirror")
    get_mirrors = mock.Mock(
        name="get_mirrors",
        return_value=[mock_mirror])

    loaded_record.get_views = get_mock
    loaded_record.get_mirrors = get_mirrors
    loaded_record.remove()

    assert mock_view.mock_calls[0][0] == 'remove', \
        "View remove should be called"
    assert mock_view.mock_calls[0][1][0] == loaded_record, \
        "View should be called with the record itself"

    assert mock_mirror.mock_calls[0][0] == 'mirror_key', \
        "Mirror should get its mirror key from record %s" % get_mirrors.mock_calls
    assert mock_mirror.mock_calls[1][0] == 'remove', \
        "Mock mirror should call delete on itself"
