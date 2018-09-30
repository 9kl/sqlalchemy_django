# -*- coding: utf-8 -*-

'''
Created on 2017-6-22
@author: hshl.ltd
'''

from __future__ import unicode_literals, print_function

import json

from sqlalchemy.ext.declarative import DeclarativeMeta


class SQLAlchemyEncoderError(Exception):
    pass


class SQLAlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
                    # raise SQLAlchemyEncoderError('%(field)s=%(data)s' % {'field': field, 'data': data})
            return fields
        return json.JSONEncoder.default(self, obj)
