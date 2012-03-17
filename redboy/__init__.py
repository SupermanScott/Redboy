# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#

"""Redboy, an object non-relational manager for Redis"""


import redis

_CONNECTIONS = {}

def add_pool(name, **kwargs):
    """Add a redis connection pool under the provided name."""
    _CONNECTIONS[name] = redis.StrictRedis(**kwargs)

def get_pool(name):
    """Return the requested pool or create one on localhost db=0."""
    if name not in _CONNECTIONS:
        add_pool(name)
    return _CONNECTIONS[name]
