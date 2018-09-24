import requests,sqlite3
from bs4 import BeautifulSoup as Soup
import os,re
from jinja2 import Template
import time,math
from datetime import datetime,timedelta


basedir=os.path.abspath(os.path.dirname(__file__))
cachedir=os.path.join(basedir,'cache')
templates_dir=os.path.join(basedir,'templates')
shanghai="http://quotes.money.163.com/trade/lsjysj_zhishu_000001.html"
shenzhen="http://quotes.money.163.com/trade/lsjysj_zhishu_399106.html"
headers={'accept':"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
"Accept-Encoding":"gzip,deflate",
"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}


def movingaverage(data,days=5):
    ma=[]
    for i in range(days-1,len(data)):
        sum=0
        for j in range(days):
            sum=sum+data[i-j][1]
        avg=round(sum/days,1)

        ma.append((data[i][0],avg))
    return ma



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
        print('parsing %s'%url)
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
        self.connect()
        self.update()


    def update(self):
        now=datetime.now()

        today3pm=now.replace(hour=15,minute=0,second=0,microsecond=0)

        self.available=[i for i in self.cursor.execute('select * from datas order by date')]
        self.available_dates=[i[0] for i in self.available]
        most_recent_data=datetime.strptime(self.available[-1][0],'%Y-%m-%d')
        # this is to check if today's info is updated.
        # if today's info is available. no need to bother.
        if now.date() == most_recent_data.date():
            print('up to date')
            return

        # if today is weekend. and this weeks' data has been updated. then don't bother.
        elif now.weekday()==5 or now.weekday()==6:
            if now.date()-most_recent_data.date()<timedelta(3) and most_recent_data.weekday()==4:
                print('Done with this week.')
                return

        # if today is weekday. and yesterday's updated. and now is not up to 3pm. don't bother.
        elif now<today3pm:

            if now.weekday()==0:
                if most_recent_data.date()==now.date()-timedelta(3):
                    print('not 3pm yet')
                    return
            elif most_recent_data.date()==now.date()-timedelta(1):
                print('not 3pm yet')
                return
        else:
                
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
                # date_in_string=datetime.strftime(datei,'%Y-%m-%d')
                if datei in self.available_dates:
                    break
                try:
                    self.cursor.execute('insert into datas values (?,?)',(date_in_string,combined[i]))
                except BaseException as e:
                    print(e)
                print(date_in_string,combined[i],'newly inserted')
            self.conn.commit()
            self.conn.close()

    def connect(self):
        conn=sqlite3.connect(self.database)
        c=conn.cursor()
        self.conn=conn
        self.cursor=conn.cursor()


a=DataHandler('database.db')
