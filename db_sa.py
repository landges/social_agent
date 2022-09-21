from sqlalchemy import Table, Index, Integer, String, Column, Text, \
    DateTime, Boolean, PrimaryKeyConstraint, \
    UniqueConstraint, ForeignKeyConstraint, ForeignKey, \
    create_engine, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship

Base = declarative_base()
engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost/social_agent")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    user_code = Column(String(100), nullable=False)
    dis_id = Column(BigInteger(), nullable=False)
    created_on = Column(DateTime(), default=datetime.now)
    join_on = Column(DateTime(), default=datetime.now)


class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    dis_id = Column(BigInteger(), nullable=False)
    user_id = Column(Integer(), ForeignKey('users.id'))
    content = Column(String(1000), nullable=False)
    parent_id = Column(Integer(), ForeignKey('messages.id', ondelete='SET NULL'), nullable=True, )
    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)
    is_swear = Column(Boolean(), default=False)
    is_ads = Column(Boolean(), default=False)
    user = relationship("User")


class UserEmbedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer(), ForeignKey('users.id'))
    total_msg = Column(Integer, default=0)
    swear_count = Column(Integer, default=0)
    ads_count = Column(Integer, default=0)
    score = Column(Integer, default=0)
    user = relationship("User")


def add_column(engine, table_name, column):
    column_name = column.name
    column_type = column.type.compile(dialect=engine.dialect)
    engine.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')


# add_column(engine, UserEmbedding.__tablename__, UserEmbedding.score)
Base.metadata.create_all(engine)
