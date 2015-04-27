#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 06:16:32 2015

@author: Roger
"""

LIMIT = 10


import facebook, numpy as np, matplotlib.pyplot as plt
from pandas import DataFrame
from datetime import datetime 
from matplotlib.ticker import FuncFormatter


chris = ('CVHILLforAmerica', 'Christopher Hill')
ted = ('tedcruzpage', 'Ted Cruz')
marco = ('MarcoRubio', 'Marco Rubio')
rand = ('RandPaul', 'Rand Paul')
jeb = ('jebbush', 'Jeb Bush')
hillary = ('hillaryclinton', 'Hillary Clinton')


runners = ['chris', 'ted', 'marco', 'rand', 'hillary']


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


def splitLine(ax, x, y, splitNum, style1, style2):
    '''Creates a two styled line given;
    ax = an axis
    x  = an array of x coordinates for 2D Line
    y  = an array of y coordinates for 2D Line
    splitNum = index number to split Line by x tick
    style1 = dictionary for left part of Line
    style2 = dictionary for right part of Line
    '''
    split = x[splitNum]
    low_mask = x <= split
    upper_mask = x >= split
    
    lower, = ax.plot(x[low_mask], y[low_mask], **style1)
    upper, = ax.plot(x[upper_mask], y[upper_mask], **style2)
    
    return lower, upper


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
    
    
    
    earlyLike  = {'color': 'r', 'lw': 1, 'ls': '--'}
    agedLike   = {'color': 'r', 'lw': 2, 'ls': '-', 'label': 'Likes'}
    earlyShare = {'color': 'b', 'lw': 1, 'ls': '--'}
    agedShare  = {'color': 'b', 'lw': 2, 'ls': '-', 'label': 'Shares'}
    
    fig, ax = plt.subplots()

    splitLine(ax, np.array(range(LIMIT)), np.array(r['Likes']), 1, earlyLike, agedLike)
    splitLine(ax, np.array(range(LIMIT)), np.array(r['Shares']), 1, earlyShare, agedShare)

    LNull = plt.Line2D(range(LIMIT), r['Shares'], ls='--', label='Recent Data\n(Early collection)', color='k')
    ax.add_line(LNull)
    ax.legend(bbox_to_anchor=(1.5,1))
    
    ax.set_xticklabels(newTimes, rotation=60)
    ax.xaxis.set_major_formatter(xFormatter)
    ax.yaxis.set_major_formatter(yFormatter)
    ax.set_title(runner + ' Facebook Feedback')


    plt.show()
    
    fig.savefig(x + '.png', bbox_inches='tight')