import sqlite3
import os
import re

basedir=os.path.abspath(os.path.dirname(__name__))
datadir=os.path.join(basedir,'stock.db')
filedir=os.path.join(basedir,'static')
conn=sqlite3.connect(datadir)
c=conn.cursor()

def parse(row):
	row=re.sub('\r','',row)
	row=row.replace("'",'')
	row=row.split(',')
	data_row=[row[0],row[1],float(row[6]),float(row[3]),float(row[5]),float(row[4]),*row[8:]]
	data_row=data_row[:2]+list(map(lambda x:float(x) if x else x,data_row[2:]))
	return [data_row[0],data_row[-1]]

def combine(csv1,csv2):
	matrix1=read(csv1)
	matrix2=read(csv2)
	dict1=dict([parse(row) for row in matrix1])
	dict2=dict([parse(row) for row in matrix2])
	dict3={}
	for key in dict1:
		try:
			dict3[key]=dict1[key]+dict2[key]
		except KeyError:
			print('%s not available in second dict'%(key))
	tuple=list(dict3.items())[::-1]
	return tuple

def test():
	data=combine('000001.csv','399106.csv')
	conn=sqlite3.connect('database.db')
	c=conn.cursor()
	for item in data:
		try:
			c.execute('insert into datas values(?,?)',item)
		except BaseException as e:
			print(e)
	conn.commit()
	conn.close()
	print('done')

def read(database='database.db'):
	conn=sqlite3.connect(database)
	c=conn.cursor()
	all=c.execute('select * from datas')
	return all
	return [i for i in all]

def init(filename='database.db'):
	conn=sqlite3.connect(filename)
	c=conn.cursor()
	c.execute('create table datas (date string primary key not NULL, amount float )')
	print('done')

def write(rows,filename='06.db'):
	conn=sqlite3.connect(os.path.join(basedir,filename))
	c=conn.cursor()
	for row in rows:
		parsed=parse(row)
		print(parsed)
		try:
			c.execute("insert into stock values (?,?,?,?,?,?,?,?,?,?)",parsed)
		except BaseException as e:
			print(e)

	conn.commit()
	conn.close()
	print('done')


