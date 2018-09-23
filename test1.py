from datetime import datetime,timedelta

print(datetime.today().__dir__())
now=datetime.now()

today3pm=now.replace(hour=15,minute=0,second=0,microsecond=0)

print(now.date()-timedelta(1))