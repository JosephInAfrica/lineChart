import requests,sqlite3
from bs4 import BeautifulSoup as Soup
import os,re
from jinja2 import Template
import time,math
from datetime import datetime,timedelta
from flask import Flask,render_template,g
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired


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
    no=IntegerField('how many recent days do you want the graph to cover?',validators=[DataRequired()])
    submit=SubmitField('Submit')


def movingaverage(data,days=5):
    ma=[]
    for i in range(days-1,len(data)):
        sum=0
        for j in range(days):
            sum=sum+data[i-j][1]
        avg=round(sum/days,1)

        ma.append((data[i][0],avg))
    return ma

@app.route('/',methods=['GET','POST'])
def index():
    form=noForm()
    handler=DataHandler('database.db')
    origin=handler.available
    ma5=movingaverage(origin,5)
    ma20=movingaverage(origin,20)
    if form.validate_on_submit():
        days=form.no.data
        return render_template('index.html',origin=origin[-days:],ma5=ma5[-days:],ma20=ma20[-days:],form=form)
    return render_template("index.html",origin=origin[-300:],ma5=ma5[-300:],ma20=ma20[-300:],form=form)


@app.template_filter('yi')
def yi(amount):
    return math.trunc(amount/100000000)


def url_to_name(url):
    url=re.sub('[:/\.]|html|','',url)
    url=re.sub('httpquotesmoney163comtradelsjysj','',url)
    return datetime.today().strftime('%Y-%m-%d')+url


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
        r=requests.get(url,headers=self.headers)
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

class DataHandler(object):
    def __init__(self,database):
        self.database=database
        self.update()


    def update(self):
        conn=sqlite3.connect(self.database)
        cursor=conn.cursor()
        now=datetime.now()

        today3pm=now.replace(hour=15,minute=0,second=0,microsecond=0)

        self.available=[i for i in cursor.execute('select * from datas order by date')]
        self.available_dates=[i[0] for i in self.available]
        most_recent_data=datetime.strptime(self.available[-1][0],'%Y-%m-%d')


        if now.date() == most_recent_data.date():
            print('up to date')
            return
            
        # if today is weekend. and this weeks' data has been updated. then don't bother.
        elif now.weekday()==5 or now.weekday()==6 and now.date()-most_recent_data.date()<timedelta(3) and most_recent_data.weekday()==4:
            print('Done with this week.')
            
        # if today is monday and last friday has been updated.and not up to 3 pm .
        elif now<today3pm and now.weekday()==0 and most_recent_data.date()==now.date()-timedelta(3):
            print('not 3pm yet')
            return
        # if today is weekday. and yesterday's updated. and now is not up to 3pm. don't bother.
        elif now<today3pm and most_recent_data.date()==now.date()-timedelta(1):
            print('not 3pm yet')
            return

        else:
            print('updating')    
            shz=parser(shenzhen)
            ssh=parser(shanghai)
            shzdict=dict(shz.chart)
            sshdict=dict(ssh.chart)
            combined={}

            for i in shzdict:
                try:
                    combined[i]=sshdict[i]+shzdict[i]
                except BaseException as e:
                    print (e)
            self.today=combined
    # check from last element if info is already available. if not push new item. if yes stop iteration.
            for i in sorted(combined.keys(),reverse=True):
                datei=datetime.strftime(datetime.strptime(str(i),'%Y%m%d'),'%Y-%m-%d')
                print(datei)
                if datei in self.available_dates:
                    break
                try:
                    cursor.execute('insert into datas values (?,?)',(datei,combined[i]))
                except BaseException as e:
                    print(e)
                print(datei,combined[i],'newly inserted')
            conn.commit()
            self.available=[i for i in cursor.execute('select * from datas order by date')]
            conn.close()


if __name__=='__main__':
    app.run()
