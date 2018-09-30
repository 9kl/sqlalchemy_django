# -*- coding: utf-8 -*-

'''
Created on 2017-6-22
@author: hshl.ltd
'''

from __future__ import absolute_import, unicode_literals

import warnings

from sqlalchemy import orm
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from django.conf import settings
from django.dispatch import receiver
from django.core.signals import request_finished
from django.core.exceptions import ImproperlyConfigured

from sqlalchemy_django.middleware import get_current_request


class BaseQuery(orm.Query):

    def get_or_404(self, ident):
        pass

    def first_or_404(self):
        return self.first()

    def first_dict(self):
        row = self.first()
        return None if row is None else row.to_dict()

    def all_dict(self):
        rows = self.all()
        if rows is None:
            return None
        return [row.to_dict() for row in rows]


class Model(object):
    #: Query class used by :attr:`query`.
    #: Defaults to :class:`SQLAlchemy.Query`, which defaults to :class:`BaseQuery`.
    query_class = None

    #: Convenience property to query the database for instances of this model using the current session.
    #: Equivalent to ``db.session.query(Model)`` unless :attr:`query_class` has been changed.
    query = None

    # http://ju.outofmemory.cn/entry/200879
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def merge(self, obj):
        if isinstance(obj, dict):
            for key, value in obj.iteritems():
                if hasattr(self, key):
                    setattr(self, key, value)


class SQLAlchemy(object):
    """django SQLAlchemy主要是把sqlalchemy与web request绑定实现session的自动化管理"""

    def __init__(self, session_options=None, metadata=None,
                 query_class=BaseQuery, model_class=Model, bind_key='default'):

        self.config = self.init_config(bind_key)

        self.Query = query_class
        self.Session = self.create_scoped_session(session_options)
        self.Model = self.make_declarative_base(model_class, metadata)

        @receiver(request_finished, weak=False)
        def shutdown_session(sender, **kwargs):
            try:
                if self.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']:
                    self.Session.commit()
                self.Session.remove()
            except Exception as e:
                print(e)

    def get_session(self):
        session = self.Session()
        return session

    @property
    def metadata(self):
        return self.Model.metadata

    def create_scoped_session(self, options=None):
        if options is None:
            options = {}

        options.setdefault('query_cls', self.Query)
        return orm.scoped_session(self.create_session(options), scopefunc=get_current_request)

    def create_session(self, options):
        engine = create_engine(
            self.config['SQLALCHEMY_DATABASE_URI'], echo=self.config['SQLALCHEMY_ECHO'], pool_size=self.config['SQLALCHEMY_POOL_SIZE'])
        return orm.sessionmaker(bind=engine, **options)

    def make_declarative_base(self, model, metadata=None):
        """Creates the declarative base."""

        base = declarative_base(cls=model, metadata=metadata)
        if not getattr(base, 'query_class', None):
            base.query_class = self.Query
        return base

    def init_config(self, bind_key):
        if not hasattr(settings, 'SQLALCHEMY_DATABASES'):
            raise ImproperlyConfigured(
                "SQLALCHEMY_DATABASES not find in settings"
            )

        sqlalchemy_config = settings.SQLALCHEMY_DATABASES
        if bind_key not in sqlalchemy_config:
            raise ImproperlyConfigured(
                "SQLALCHEMY_DATABASES not find in settings"
            )
        bind_config = sqlalchemy_config[bind_key]
        bind_config.setdefault('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
        bind_config.setdefault('SQLALCHEMY_BINDS', None)
        bind_config.setdefault('SQLALCHEMY_NATIVE_UNICODE', None)
        bind_config.setdefault('SQLALCHEMY_ECHO', True)
        bind_config.setdefault('SQLALCHEMY_RECORD_QUERIES', None)
        bind_config.setdefault('SQLALCHEMY_POOL_SIZE', None)
        bind_config.setdefault('SQLALCHEMY_POOL_TIMEOUT', None)
        bind_config.setdefault('SQLALCHEMY_POOL_RECYCLE', None)
        bind_config.setdefault('SQLALCHEMY_MAX_OVERFLOW', None)
        bind_config.setdefault('SQLALCHEMY_COMMIT_ON_TEARDOWN', True)
        return bind_config
