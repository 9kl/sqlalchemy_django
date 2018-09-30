# -*- coding: utf-8 -*-

'''
Created on 2017-6-22
@author: hshl.ltd
'''

# https://blndxp.wordpress.com/2016/03/04/django-get-current-user-anywhere-in-your-code-using-a-middleware/

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()


def get_current_request():
    """ returns the request object for this thread """
    return getattr(_thread_locals, "request", None)


def get_current_user():
    """ returns the current user, if exist, otherwise returns None """
    request = get_current_request()
    if request:
        return getattr(request, "user", None)


class SqlAlchemyMiddleware(object):
    """ Simple middleware that adds the request object in thread local storage."""

    def process_request(self, request):
        _thread_locals.request = request

    def process_response(self, request, response):
        return response
        """
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        return response
        """
