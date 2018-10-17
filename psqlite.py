import psycopg2
import os
import re
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, ForeignKey, Date, Float
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

url = 'postgresql://localhost:5432/stockinfo'

datadir = '/Users/joseph/'
sh = datadir + '000001.csv'
sz = datadir + '399106.csv'


def connect():
    con = sqlalchemy.create_engine(url, client_encoding='utf8')
    meta = sqlalchemy.MetaData(bind=con, reflect=True)
    return con, meta


class csvread(object):

    def __init__(self, csv):
        with open(csv, 'rb') as reader:
            reader = reader.read()
            rows = reader.decode('utf-8', 'ignore').split('\n')[1:]
            rows = [row.split(',') for row in rows]
            self.rows = rows
        # print(rows)

    def __repr__(self):
        return self.rows

    __str__ = __repr__

# if __name__=='__main__':
# 	csvread(os.path.join(datadir,sh))
# 	csvread(os.path.join(datadir,sz))


def treat_row(row):
    date = datetime.strptime(row[0], '%Y-%m-%d')
    price = float(row[3])
    amount = float(row[10])
    value = float(row[11])
    return (date, price, amount, value)


class Shanghai(Column):
    __tablename__ = 'shanghai'
    date = Column(Date, primary_key=True)
    price = Column(Float)
    amount = Column(Float)
    value = Column(Float)


class Shenzhen(Column):
    __tablename__ = 'shanghai'
    date = Column(Date, primary_key=True)
    price = Column(Float)
    amount = Column(Float)
    value = Column(Float)

    def __init__(self, date, price, amount, value):
        self.date = date
        self.price = price
        self.amount = amount
        self.value = value

    def __repr__(self):
        return "%s,%s" % (self.date, self.value)

    __str__ = __repr__


class Hushen(Column):
    __tablename__ = 'hushen'
    date = Column(Date, primary_key=True)
    amount = Column(Float)


engine = create_engine(url)
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)()

if __name__ == "__main__":
    # print(csvread(sz).rows[0])
    for row in csvread(sz).rows:
        print(row)
        data = treat_row(row)
        print(data)
        item = Shenzhen(*data)
        print(item)
        session.add(item)
    session.commit()
    print('done')

    # print(csvread.treat_row(csvread(sz).rows[0]))
