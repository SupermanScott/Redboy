# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#
"""Example of a User Model"""
from redboy.record import Record, MirroredRecord
from redboy.key import Key
from redboy.view import Queue, Stack, Score
from time import time

import redboy.exceptions as exc

user_prefix = "user:"
view_prefix = "created:"
pool_name = "database"

class UserEmail(MirroredRecord):
    """Mirrored Record allows for fetching by user email"""
    def mirror_key(self, parent_record):
        assert isinstance(parent_record, Record)
        if 'email' in parent_record:
            return self.make_key(parent_record['email'])

    def make_key(self, key=None):
        return Key(pool_name, "user:email:", key)

score_function = lambda x: x['created']

user_view = Queue(Key(pool_name, view_prefix, "users"))
stack_view = Stack(Key(pool_name, "reverse_created:", "users"))
scored_view = Score(Key(pool_name, "created_date:", "users"), score_function, True)


class User(Record):
    _required = ('email',)
    _prefix = user_prefix
    _pool_name = pool_name
    _views = (
        user_view,
        stack_view,
        scored_view,
        )
    _mirrors = (UserEmail(),)

def main():
    scott = User(first_name="Scott", last_name="Reynolds", created=time())
    try:
        scott.save()
    except exc.ErrorMissingField, missing:
        # Should happen because missing email
        print missing

    scott['email'] = 'scott@scottreynolds.us'
    scott.save()

    scott['first_name'] = 'scott'
    assert scott['first_name'] != User().load(scott.key)['first_name'], \
        "Name has now changed"

    scott.save()
    assert scott['first_name'] == User().load(scott.key)['first_name'], \
        "Changed name is now saved to the database"

    thomas_jeffereson = User(first_name="thomas", last_name="jefferson",
                             email="no-replay@us.gov", created=time()).save()
    assert thomas_jeffereson['first_name'] == UserEmail().load(thomas_jeffereson['email'])['first_name']

    assert len(user_view) == 2, "Only two users in the view"
    assert len(stack_view) == 2, "Only two users in the stack view"
    assert len(scored_view) == 2, "Only two users in the scored view"

    assert user_view[0]['first_name'] == scott['first_name']
    assert stack_view[0]['first_name'] == thomas_jeffereson['first_name']

    for user in user_view:
        print user

    for user in scored_view:
        print user

    # Clean up
    scott.remove()
    thomas_jeffereson.remove()

if __name__ == '__main__':
    main()
