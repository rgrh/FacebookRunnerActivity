#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Fri May 08 17:08:44 2015

@author: Roger
"""


CHART_LIMIT = 10


import facebook, numpy as np, matplotlib.pyplot as plt
from pandas import DataFrame
from datetime import datetime 
from matplotlib.ticker import FuncFormatter
from string import lower



def readRunners():
    runnerFile = 'runners.csv'
    fileObj = open(runnerFile,'r')
    header = fileObj.readline().strip()
    
    runners = []
    for line in fileObj.readlines():
        runner, page, govPage = line.strip().split(',')
        if govPage == '' or str(govPage) == '0':
            govPage = False
        else:
            govPage = True
    
        entry = {'runner': runner,
                 'page': page,
                 'govPage': govPage}
        runners.append(entry)
        
    fileObj.close()
    return runners


def readToken():
    '''
    Reads in the Facebook Token.
    To obtain a facebook token, 
        - login to facebook through a web browser
        - then visit, https://developers.facebook.com/tools/explorer/
        - click "Get Token" button on top right
        - click "Get Access Token"
        - copy ugly string from "Access Token: " field
        - save to file facebookToken.txt
    '''
    fbTokenFile = 'facebookToken.txt'
    fileObj = open(fbTokenFile, 'r')
    fbToken = fileObj.readline()
    fileObj.close()
    return fbToken


##
## Format fields
##
def fmtShares(Dict):
    if type(Dict) == dict:
        return Dict['count']
    else:
        return 0

def fmtLikes(objID):
    return fbGraph.get_object(objID + '/likes', summary=True)['summary']['total_count']

def fmtDate(timeStr):
    date, time = timeStr.split('T')
    time = str(time)[:8]
    dtTimeStr = str(date) + ' ' + time
    fmt = "%Y-%m-%d %H:%M:%S"
    d = datetime.strptime(dtTimeStr,fmt)
    return d.strftime("%m %d %Y")


def getPostData(fbGraph, entry):
    global CHART_LIMIT
    posts = fbGraph.get_object(entry['page'] + '/posts', limit=CHART_LIMIT*15)['data']
        
    frame = DataFrame(posts)
    ##Later, maybe output this frame for further study
    
    postData = DataFrame(columns=('Date', 'Likes', 'Shares'))
    postData['Shares'] = frame['shares'].map(fmtShares)
    postData['Likes']  = frame['id'].map(fmtLikes)
    postData['Date']   = frame['created_time'].map(fmtDate)
    
    postData = postData.groupby(by='Date', sort=False).mean()
    postData = postData.head(n=CHART_LIMIT)
    postData.fillna(value=0)
    return postData


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
    if x >= len(dates):
        return ''
    month, day, year = dates[int(x)].split(' ')
    return month + '/' + day + "\n " + year


def fmtYlabels(y, pos):
    '''y=value, pos=position'''
    y = int(y)
    return "{:,}".format(y)



if __name__ == '__main__':
    
    xFormatter = FuncFormatter(fmtXlabels)
    yFormatter = FuncFormatter(fmtYlabels)
    runners = readRunners()
    fbToken = readToken()
    fbGraph = facebook.GraphAPI(fbToken)
    
    for runner in runners:#[:1]:
        if lower(runner['page']) == 'null':
             continue
        
        feedback = getPostData(fbGraph, runner)
        dates = feedback.index.tolist()
        
        earlyLike  = {'color': 'r', 'lw': 1, 'ls': '--'}
        agedLike   = {'color': 'r', 'lw': 2, 'ls': '-', 'label': 'Likes'}
        earlyShare = {'color': 'b', 'lw': 1, 'ls': '--'}
        agedShare  = {'color': 'b', 'lw': 2, 'ls': '-', 'label': 'Shares'}
        
        fig, ax = plt.subplots()
    
        splitLine(ax, np.array(range(CHART_LIMIT)),
                  np.array(feedback['Likes']), 1,
                  earlyLike, agedLike)
        splitLine(ax, np.array(range(CHART_LIMIT)),
                  np.array(feedback['Shares']), 1,
                  earlyShare, agedShare)
    
        earlyData = plt.Line2D(range(CHART_LIMIT),
                               feedback['Shares'], ls='--',
                               label='Recent Data\n(Early collection)',
                               color='k')
        
        ax.add_line(earlyData)
        ax.legend(bbox_to_anchor=(1.5,1))
        
        ax.set_xticklabels(dates, rotation=60)
        ax.xaxis.set_major_formatter(xFormatter)
        ax.yaxis.set_major_formatter(yFormatter)
        ax.set_title(runner['runner'] + ' Facebook Feedback')
        plt.annotate('[Source: http://www.facebook.com/' + runner['page'] + ']',
                     (0,0), (0, -60), xycoords='axes fraction',
                     textcoords='offset points', va='top')
        
        if runner['govPage']:
            plt.annotate('*Government Sponsored Page',
                         (0,0), (0, -70), xycoords='axes fraction',
                         textcoords='offset points', va='top')
    
        plt.show()
        fig.savefig(runner['runner'].replace(' ','_') + '.png',
                    bbox_inches='tight')