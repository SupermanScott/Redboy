# -*- coding: utf-8 -*-
#
# © 2012 Scott Reynolds
# Author: Scott Reynolds <scott@scottreynolds.us>
#

"""Redboy: Exceptions"""

class RedboyException(Exception):
    """Base Exception that all Redboy Exceptions extend"""
    pass

class ErrorMissingField(RedboyException):
    """Missing a required field"""
    pass

class ErrorMissingKey(RedboyException):
    """No key to save the data too"""
    pass
