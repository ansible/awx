import datetime

from sqlalchemy import (Column, Integer, String, Text, DateTime,
                        Sequence, Boolean, ForeignKey, SmallInteger)
from sqlalchemy.orm import relation
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData

metadata = MetaData()
ModelBase = declarative_base(metadata=metadata)


class Queue(ModelBase):
    __tablename__ = 'kombu_queue'
    __table_args__ = {'sqlite_autoincrement': True, 'mysql_engine': 'InnoDB'}

    id = Column(Integer, Sequence('queue_id_sequence'), primary_key=True,
                autoincrement=True)
    name = Column(String(200), unique=True)
    messages = relation('Message', backref='queue', lazy='noload')

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '<Queue(%s)>' % (self.name)


class Message(ModelBase):
    __tablename__ = 'kombu_message'
    __table_args__ = {'sqlite_autoincrement': True, 'mysql_engine': 'InnoDB'}

    id = Column(Integer, Sequence('message_id_sequence'),
                primary_key=True, autoincrement=True)
    visible = Column(Boolean, default=True, index=True)
    sent_at = Column('timestamp', DateTime, nullable=True, index=True,
                     onupdate=datetime.datetime.now)
    payload = Column(Text, nullable=False)
    queue_id = Column(Integer, ForeignKey('kombu_queue.id',
                                          name='FK_kombu_message_queue'))
    version = Column(SmallInteger, nullable=False, default=1)

    __mapper_args__ = {'version_id_col': version}

    def __init__(self, payload, queue):
        self.payload = payload
        self.queue = queue

    def __str__(self):
        return '<Message(%s, %s, %s, %s)>' % (self.visible,
                                              self.sent_at,
                                              self.payload,
                                              self.queue_id)
