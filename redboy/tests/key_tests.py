# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Tests the Key class"""
import mock
from redboy.key import Key

@mock.patch('uuid.UUID.hex', "test_uuid")
def test_no_provided_key():
    """Test that the uuid is used for the key when None is provided."""
    test_key = Key(pool_name="test", prefix="test")
    assert test_key.key == "test_uuid", \
        "UUID.uuid4 is not called when generating empty key"

def test_key_string():
    """Test to make sure the str(Key) generates the prefix + key"""
    prefix = "prefix_test"
    key = "prefix_key"
    assert str(Key(pool_name="test", prefix=prefix, key=key)) == prefix + key, \
        "Casting Key to string doesn't match its prefix + key"
