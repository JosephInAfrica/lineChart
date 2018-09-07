import requests,sqlite3
from bs4 import BeautifulSoup as Soup
import os,re
from jinja2 import Template
import time
from datetime import datetime
from flask import Flask,render_template
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import Required

app=Flask(__name__)

app.config['SECRET_KEY']='hard to guess string'

basedir=os.path.abspath(os.path.dirname(__file__))
cachedir=os.path.join(basedir,'cache')
templates_dir=os.path.join(basedir,'templates')
shanghai="http://quotes.money.163.com/trade/lsjysj_zhishu_000001.html"
shenzhen="http://quotes.money.163.com/trade/lsjysj_zhishu_399106.html"
headers={'accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
"Accept-Encoding":"gzip,deflate",
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}


class noForm(FlaskForm):
	no=IntegerField('how many recent days do you want the graph to cover?',validators=[Required()])
	submit=SubmitField('Submit')



@app.route('/',methods=['GET','POST'])
def index():
	form=noForm()
	a=updater('database.db')
	data=a.fetch_all()

	if form.validate_on_submit():
		days=form.no.data
		return render_template('index.html',chart=data[-days:],form=form)
	return render_template("index.html",chart=data[-1000:],form=form)


def url_to_name(url):
	url=re.sub('[:/\.]|html|','',url)
	url=re.sub('httpquotesmoney163comtradelsjysj','',url)
	return datetime.today().strftime('%Y-%m-%d')+url

 
# def render(chart):
# 	with open(os.path.join(templates_dir,'index.html'),'r') as file:
# 		temp=Template(file.read())
# 		result=temp.render(chart=chart)
# 		print(result)
# 		return result

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
		self.conn.close()

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
		for i in sorted(combined.keys(),reverse=True):
			datei=datetime.strptime(str(i),'%Y%m%d')
			date_in_string=datetime.strftime(datei,'%Y-%m-%d')
			if datei in self.available_dates:
				break
			# print(i,combined[i],)
			self.cursor.execute('insert into datas values (?,?)',(date_in_string,combined[i]))
			self.conn.commit()

			print(date_in_string,combined[i],'newly inserted')
		# self.conn.close()

	def connect(self):
		conn=sqlite3.connect(self.database)
		c=conn.cursor()
		self.conn=conn
		self.cursor=conn.cursor()

	def fetch_available(self):
		self.available_dates=[datetime.strptime(i[0],'%Y-%m-%d') for i in list(self.cursor.execute('select date from datas'))]
	# this func could combine with the downside one.

	def fetch_all(self):
		all=[i for i in self.cursor.execute('select * from datas order by date')]
		self.available=all

if __name__=='__main__':
	app.run(debug=True)
