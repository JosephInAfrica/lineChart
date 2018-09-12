def movingaverage(data,days=5):
    ma=[]
    sum=0
    for i in range(days-1,len(data)):
        for j in range(days):
            sum=sum+data[i-j][1]
        avg=sum/days
        value=data[i]
        ma.append((data[i][0],value))
    return ma

list=[(1,2),(3,4),(5,6),(7,8)]

print(movingaverage(list,2))

