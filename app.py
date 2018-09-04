import requests,sqlite3
from bs4 import BeautifulSoup as Soup
import os,re
from jinja2 import Template
import time
from datetime import datetime
from flask import Flask,render_template


app=Flask(__name__)

basedir=os.path.abspath(os.path.dirname(__file__))
cachedir=os.path.join(basedir,'cache')
templates_dir=os.path.join(basedir,'templates')
shanghai="http://quotes.money.163.com/trade/lsjysj_zhishu_000001.html"
shenzhen="http://quotes.money.163.com/trade/lsjysj_zhishu_399106.html"
headers={'accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
"Accept-Encoding":"gzip,deflate",
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}


@app.route('/',methods=['GET','POST'])
def index():
	a=updater('database.db')
	chart=a.fetch_all()[-1000:]
	print(chart)
	return render_template("index.html",chart=chart)


def url_to_name(url):
	url=re.sub('[:/\.]|html|','',url)
	url=re.sub('httpquotesmoney163comtradelsjysj','',url)
	return datetime.today().strftime('%Y-%m-%d')+url

 
def render(chart):
	with open(os.path.join(templates_dir,'index.html'),'r') as file:
		temp=Template(file.read())
		result=temp.render(chart=chart)
		print(result)
		return result

class parser(object):
	headers={'accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
	"Accept-Encoding":"gzip,deflate",
	"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}

	def __init__(self,url):
		self.url=url
		self.get_soup()
		self.get_rows()
		self.get_matrix()
		self.get_chart()

	def get_soup(self):
		url=self.url
		try:
			with open(os.path.join(cachedir,url_to_name(url)+".html"),'rb') as file:
				soup=Soup(file,"lxml")
				print('reading from cahce...\n')
		except:
			print("we have to download...")
			r=requests.get(url,headers=self.headers)
			print('done downloading')
			with open(os.path.join(cachedir,url_to_name(url)+".html"),'wb') as file:
				file.write(r.content)
			soup=Soup(r.content,"lxml")

		self.soup=soup

	def get_rows(self):
		self.rows=self.soup.select("div.inner_box > table > tr")

	def get_matrix(self):

		def treat_no(no):
			if '.' not in no:
				return int(no)
			return float(re.sub(',','',no))
		tds=[row.select('td') for row in self.rows]
		self.matrix=[[treat_no(i.contents[0]) for i in td] for td in tds]

	def get_chart(self):
		self.chart=[[row[0],row[-1]] for row in self.matrix]


class updater(object):
	shz=parser(shenzhen)
	ssh=parser(shanghai)

	def __init__(self,database):
		self.database=database
		self.connect()
		self.fetch_available()
		self.update()

	def update(self):
		shzdict=dict(self.shz.chart)
		sshdict=dict(self.ssh.chart)
		combined={}

		for i in shzdict:
			try:
				combined[i]=sshdict[i]+shzdict[i]
			except BaseException as e:
				print (e)
		self.today=combined

		for i in combined:
			datei=datetime.strptime(str(i),'%Y%m%d')
			date_in_string=datetime.strftime(datei,'%Y-%m-%d')
			if datei in self.available_dates:
				break
			self.cursor.execute('insert into datas values (?,?)',(date_in_string,combined[i]))
			self.conn.commit()
			self.conn.close()
			print(date_in_string,combined[i],'newly inserted')

	def connect(self):
		conn=sqlite3.connect(self.database)
		c=conn.cursor()
		self.conn=conn
		self.cursor=conn.cursor()


# download file into local machine. clear old cache if no useful item found.
	def fetch_available(self):
		self.available_dates=[datetime.strptime(i[0],'%Y-%m-%d') for i in list(self.cursor.execute('select date from datas'))]
	def fetch_all(self):
		all=[i for i in self.cursor.execute('select * from datas order by date')]
		return all


# def test():
	# a=updater('database.db')

	# c=a.connect()
	# for i in a.cursor.execute('select * from datas order by date'):
	# 	print(i)


if __name__=='__main__':
	app.run(debug=True)
