# sqlalchemy_django
在django中使用[sqlalchemy](https:://www.sqlalchemy.org 'sqlalchemy')，模仿flask sqlalchemy的实现方式。

## 安装
    pip install sqlalchemy-django
    
## 配置 
### django settings.py

    # 在MIDDLEWARE_CLASSES中添加'sqlalchemy_django.middleware.SqlAlchemyMiddleware'
    MIDDLEWARE_CLASSES = (
        ... ...
        'sqlalchemy_django.middleware.SqlAlchemyMiddleware',  # 添加此项
    )
    
    # SQLALCHEMY数据访问配置
    SQLALCHEMY_DATABASES = {
        'linkflood': {
            'SQLALCHEMY_DATABASE_URI': 'postgresql+psycopg2://postgres:123456@127.0.0.1:5432/test',
            'SQLALCHEMY_NATIVE_UNICODE': None,
            'SQLALCHEMY_ECHO': True,
            'SQLALCHEMY_RECORD_QUERIES': None,
            'SQLALCHEMY_POOL_SIZE': 20,
            'SQLALCHEMY_POOL_TIMEOUT': None,
            'SQLALCHEMY_POOL_RECYCLE': None,
            'SQLALCHEMY_MAX_OVERFLOW': None,
            'SQLALCHEMY_COMMIT_ON_TEARDOWN': True
        }
    }
    
## 示例
### 生成数据库映射类 (比如： db_linkflood.py)
    # coding: utf-8

    from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, SmallInteger, String, Table, Text
    from sqlalchemy.orm import relationship
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_django import SQLAlchemy

    db = SQLAlchemy(bind_key='linkflood')
    
    class StStbprpB(db.Model):
        __tablename__ = 'st_stbprp_b'

        stcd = Column(String, primary_key=True)
        stnm = Column(String(30), nullable=False)
        rvnm = Column(String(30))
        hnnm = Column(String(30))
        bsnm = Column(String(30))
        lgtd = Column(Numeric(10, 6), nullable=False)
        lttd = Column(Numeric(10, 6), nullable=False)
        ... ...
    
 ### 数据操作 （增、删、改、查、事务）
    # -*- coding: utf-8 -*-

    import sqlalchemy as sa
    from sqlalchemy import orm

    from bigtiger.core.exceptions import DBError, SuspiciousOperation, DBRefError
    from db_linkflood import (db, StStbprpB, StStbprpBGeom, StStsmtaskB, StAddvcdD)


    class StStbprpBModel(object):
        """测站基本属性表 Model"""

        def __init__(self):
            self.session = db.get_session()

        def _get_sorted(self, sort, order):
            if sort and order:
                return getattr(getattr(StStbprpB, sort), order)()
            return None

        def get_one(self, stcd):
            row = self.session.query(StStbprpB).filter(
                StStbprpB.stcd == stcd).first_dict()
            return row

        def get_all(self, sort=None, order=None):
            query = self.session.query(StStbprpB)
            _sorted = self._get_sorted(sort, order)
            if _sorted is not None:
                query = query.order_by(_sorted)
            rows = query.all_dict()
            return rows

        def add(self, entity):
            row = StStbprpB(**entity)
            self.session.add(row)
            self.session.commit()

        def modify(self, stcd, new_entity):
            self.session.query(StStbprpB).filter(
                StStbprpB.stcd == stcd).update(new_entity)
            self.session.commit()

        def delete(self, stcd):
            refs = self.get_refer(stcd)
            if refs:
                raise DBRefError(refs.pop())

            self.session.query(StStbprpB).filter(StStbprpB.stcd == stcd).delete()
            self.session.commit()

        def get_detail(self, stcd):
            row = self.session.query(StStbprpB, StAddvcdD.addvnm, StStsmtaskB.pfl, StStsmtaskB.zfl, StStsmtaskB.qfl, StStsmtaskB.soilfl).outerjoin(
                StAddvcdD, StStbprpB.addvcd == StAddvcdD.addvcd).outerjoin(
                    StStsmtaskB, StStbprpB.stcd == StStsmtaskB.stcd).filter(
                        StStbprpB.stcd == stcd).first()

            return dict(row.StStbprpB.to_dict(), addvnm=row.addvnm, pfl=row.pfl,
                        zfl=row.zfl, qfl=row.qfl, soilfl=row.soilfl)

        def tran_add(self, st_stbprp_b, st_stsmtask_b):
            try:
                row = StStbprpB(**st_stbprp_b)
                row1 = StStsmtaskB(**st_stsmtask_b)
                geom = self._get_stbprp_geom(
                    st_stbprp_b['stcd'], st_stbprp_b['stnm'], st_stbprp_b['lgtd'], st_stbprp_b['lttd'])
                self.session.add(row)
                self.session.add(row1)
                self.session.add(geom)

                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise DBError(u'事务添加数据失败，请重试。')

        def tran_modify(self, stcd, st_stbprp_b, st_stsmtask_b):
            new_stcd = st_stbprp_b['stcd']
            try:
                self.session.query(StStbprpB).filter(
                    StStbprpB.stcd == stcd).update(st_stbprp_b)

                self.session.query(StStsmtaskB).filter(
                    StStsmtaskB.stcd == new_stcd).update(st_stsmtask_b)

                self.session.query(StStbprpBGeom).filter(
                    StStbprpBGeom.stcd == stcd).delete()

                geom = self._get_stbprp_geom(
                    st_stbprp_b['stcd'], st_stbprp_b['stnm'], st_stbprp_b['lgtd'], st_stbprp_b['lttd'])

                self.session.add(geom)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise DBError(u'事务修改数据失败，请重试。')

        def tran_delete(self, pks):
            try:
                self.session.query(StStbprpB).filter(
                    StStbprpB.stcd.in_(pks)).delete(synchronize_session=False)
                self.session.query(StStbprpBGeom).filter(
                    StStbprpBGeom.stcd.in_(pks)).delete(synchronize_session=False)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise DBError(u'事务删除数据失败，请重试。')
                
