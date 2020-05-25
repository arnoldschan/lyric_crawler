from __future__ import absolute_import

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base

import os


MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
MYSQL_URL = os.environ['MYSQL_URL']
MYSQL_DB_NAME = os.environ['MYSQL_DB_NAME']

engine = create_engine(
    f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_URL}/{MYSQL_DB_NAME}',
    encoding="utf-8",
    echo=False,
    poolclass=NullPool)
ORMBaseClass = declarative_base()

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine))


def get_or_create_object(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance
