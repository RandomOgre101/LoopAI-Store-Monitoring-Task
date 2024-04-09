from .db_connection import Base
from sqlalchemy import Column, String, BigInteger, Integer
from sqlalchemy.sql.sqltypes import TIME, TIMESTAMP


class StoreStatus(Base):
    __tablename__ = "storeStatus"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger, nullable=False)
    status = Column(String, nullable=False)
    timestamp_utc = Column(TIMESTAMP, nullable=False)


class WorkHours(Base):
    __tablename__ = "workHours"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger, nullable=False)
    day = Column(Integer, nullable=False)
    start_time_local = Column(TIME, nullable=False)
    end_time_local = Column(TIME, nullable=False)


class Timezone(Base):
    __tablename__ = "timezone"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(BigInteger, nullable=False)
    timezone_str = Column(String, nullable=False)