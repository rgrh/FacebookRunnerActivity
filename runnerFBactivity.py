#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 06:16:32 2015

@author: Roger
"""

LIMIT = 9


import facebook, numpy as np, pandas as pd, matplotlib.pyplot as plt
from pandas import DataFrame, Series
from datetime import datetime 
from matplotlib.ticker import FuncFormatter


hillary = ('hillaryclinton', 'Hillary Clinton')
ted = ('tedcruzpage', 'Ted Cruz')
marco = ('MarcoRubio', 'Marco Rubio')
rand = ('RandPaul', 'Rand Paul')
jeb = ('jebbush', 'Jeb Bush')

runners = ['hillary']#, 'ted', 'marco', 'rand', 'jeb']


#
# Read in facebook token.
'''To obtain a facebook token, 
    - login to facebook through a web browser
    - then visit, https://developers.facebook.com/tools/explorer/
    - click "Get Token" button on top right
    - click "Extended Permissions"
    - checkmark in "publish_actions"
    - click "Get Access Token"
    - copy ugly string from "Access Token: " field
    - save to file facebookToken.txt
'''
#
fbTokenFile = open('facebookToken.txt', 'r')
fbToken = fbTokenFile.readline()
fbTokenFile.close()


graph = facebook.GraphAPI(fbToken)



##
## Format fields
##
def fmtShares(Dict):
    if type(Dict) == dict:
        return Dict['count']
    else:
        return 0

def fmtLikes(objID):
    return graph.get_object(objID + '/likes', summary=True)['summary']['total_count']

def fmtDate(timeStr):
    date, time = timeStr.split('T')
    time = str(time)[:8]
    dtTimeStr = str(date) + ' ' + time
    fmt = "%Y-%m-%d %H:%M:%S"
    d = datetime.strptime(dtTimeStr,fmt)
    return d.strftime("%m %d %Y")



def getPostData(runner):
    global LIMIT
    rPosts = graph.get_object(runner + '/posts', limit=100)['data']
    
    
    frame = DataFrame(rPosts)
    frame['shares'] = frame['shares'].map(fmtShares)
    frame['likes'] = frame['id'].map(fmtLikes)
    frame['created_time'] = frame['created_time'].map(fmtDate)

    
    
    ##
    ## Collect chart data
    ##
    shares = frame['shares']
    likes = frame['likes']
    times = frame['created_time']

    
    ##
    ## Average multiple posts p/day
    ##
    i=0
    prev=''
    newShares = []
    newLikes = []
    global newTimes
    last = len(times) - 1
    for post in times:
        if prev == '':
            clctShares = (shares[i],)
            clctLikes = (likes[i],)
            prev = post
        elif i == last:
            if post == prev:
                clctShares = clctShares + (shares[i],)
                clctLikes = clctLikes + (likes[i],)
                newShares.append(int(round(np.average(clctShares))))
                newLikes.append(int(round(np.average(clctLikes))))
                newTimes.append(times[i])
            else:
                newShares.append(int(round(np.average(clctShares))))
                newLikes.append(int(round(np.average(clctLikes))))
                newTimes.append(times[i-1])
                newShares.append(shares[i])
                newLikes.append(likes[i])
                newTimes.append(times[i])
        elif post == prev:
            clctShares = clctShares + (shares[i],)
            clctLikes = clctLikes + (likes[i],)
        else:
            newShares.append(int(round(np.average(clctShares))))
            newLikes.append(int(round(np.average(clctLikes))))
            newTimes.append(times[i - 1])
            clctShares = (shares[i],)
            clctLikes = (likes[i],)
            prev = post
        i += 1
    
    
    try:
        r = DataFrame(columns=('Date', 'Likes', 'Shares'))
        r['Date'] = times
        r['Likes'] = likes
        r['Shares'] = shares
    except ValueError, e:
        print str(e)
        print 'runner: ' + runner
        print 'newTimes: ',
        print len(times)
        print times
        print 'newLikes: ',
        print len(likes)
        print likes
        print 'newShares: ',
        print len(shares)
        print shares
        
    r = r.groupby(by='Date', sort=False).mean()
    r = r.head(n=LIMIT)
    r.fillna(value=0)
    return r


def fmtXlabels(x, pos):
    '''x=value, pos=position'''
    if x >= len(newTimes):
        return ''
    month, day, year = newTimes[int(x)].split(' ')
    return month + '/' + day + "\n " + year


def fmtYlabels(y, pos):
    '''y=value, pos=position'''
    y = int(y)
    return "{:,}".format(y)

xFormatter = FuncFormatter(fmtXlabels)
yFormatter = FuncFormatter(fmtYlabels)

for x in runners:
    newTimes = []
    wall = eval(x)[0]
    runner = eval(x)[1]
    
    r = getPostData(wall)
    
    if len(newTimes) < LIMIT:
        LIMIT = len(newTimes)
    yLim = int(round(max(r['Likes'].max(), r['Shares'].max()) * 1.2))
    xLim = LIMIT
    L1 = plt.Line2D(range(LIMIT), r['Likes'], label='Likes', color='b')
    L2 = plt.Line2D(range(LIMIT), r['Shares'], label='Shares', color='r')
    fig = plt.figure()
    ax = fig.add_subplot(111, ylim=(0,yLim), xlim=(0,xLim))
    ax.add_line(L1)
    ax.add_line(L2)
    ax.legend()
    ax.set_xticklabels(newTimes, rotation=60)
    ax.xaxis.set_major_formatter(xFormatter)
    ax.yaxis.set_major_formatter(yFormatter)
    ax.set_title(runner + ' Facebook Feedback')
    fig.savefig(x + '.png', bbox_inches='tight')