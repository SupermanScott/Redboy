# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Example of a User Model"""
from redboy.record import Record
from redboy.key import Key

import redboy.exceptions as exc

class User(Record):
    _required = ('email',)
    _prefix = "user:"
    _pool_name = "database"

class UserKey(Key):
    def __init__(self, key=None):
        Key.__init__(self, User._pool_name, User._prefix, key)

def main():
    scott = User(first_name="Scott", last_name="Reynolds")
    try:
        scott.save()
    except exc.ErrorMissingField, missing:
        # Should happen because missing email
        print missing

    scott['email'] = 'scott@scottreynolds.us'
    scott.save()

    scott['first_name'] = 'scott'
    assert scott['first_name'] != User().load(scott.key), \
        "Name has now changed"

    scott.save()
    assert scott['first_name'] == User().load(scott.key), \
        "Changed name is now saved to the database"
