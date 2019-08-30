import pandas as pd
import numpy as np
from os import listdir
import os
from os.path import isfile, join
from pathlib import Path
import plotly
import plotly.graph_objs as go
import multiprocessing
import time

import itertools
from getIndexList import getIndexList
from zstat import errorPlot

def plotlyPlot(df, varName, windowssize = 750, cond = 1):
    height = windowssize-1
    df = df.iloc[height:]

    df = df.fillna(0)

    if varName == "sigma":
        df['garch_' + varName].iloc[:height] = np.NaN
        df['garch_' + varName + '_lb'].iloc[:height] = np.NaN
        df['garch_' + varName + '_ub'].iloc[:height] = np.NaN

    garch_upper_bound = go.Scatter(
        name='GARCH ' + varName + ' Upper Bound',
        x=df.index.tolist(),
        y=df['garch_' + varName + '_ub'],
        showlegend=False,
        hoverlabel = dict(namelength = -1),
        mode='lines',
        marker=dict(color="#444"),
        line=dict(width=0,color='rgb(31, 119, 180)'),
        fillcolor='rgba(31, 119, 180, 0.3)',
        fill='tonexty' )

    garch_trace = go.Scatter(
        name='GARCH_' + varName,
        x=df.index.tolist(),
        y=df['garch_' + varName],
        hoverlabel = dict(namelength = -1),
        mode='lines',
        line=dict(color='rgb(31, 119, 180)')
        )

    garch_lower_bound = go.Scatter(
        name='GARCH ' + varName + ' Lower Bound',
        x=df.index.tolist(),
        y=df['garch_' + varName + '_lb'],
        showlegend=False,
        hoverlabel = dict(namelength = -1),
        marker=dict(color="#444"),
        line=dict(width=0,color='rgb(31, 119, 180)'),
        mode='lines'
     )


    cir_upper_bound = go.Scatter(
        name='CIR ' + varName + ' Upper Bound',
        x=df.index.tolist(),
        y=df['cir_' + varName + '_ub'],
        showlegend=False,
        hoverlabel = dict(namelength = -1),
        mode='lines',
        marker=dict(color="#444"),
        line=dict(width=0),
        fillcolor='rgba(255, 127, 14, 0.3)',
        fill='tonexty' )

    cir_trace = go.Scatter(
        name='CIR_' + varName,
        x=df.index.tolist(),
        y=df['cir_' + varName],
        hoverlabel = dict(namelength = -1),
        mode='lines',
        line=dict(color='rgb(255, 127, 14)')
         )

    cir_lower_bound = go.Scatter(
        name='CIR ' + varName + ' Lower Bound',
        x=df.index.tolist(),
        y=df['cir_' + varName + '_lb'],
        showlegend=False,
        hoverlabel = dict(namelength = -1),
        marker=dict(color="#444"),
        line=dict(width=0),
        mode='lines' )

    leakage_trace = go.Scatter(
        name='CIR_leakage',
        x=df.index.tolist(),
        y=df['cir_leakage'],
        hoverlabel = dict(namelength = -1),
        mode='lines',
        line=dict(color='rgb(165, 165, 165)'),
        yaxis='y2'
         )
    # Trace order can be important
    # with continuous error bars
    if not cond and varName == "sigma":
        data = [cir_lower_bound, cir_upper_bound, cir_trace,leakage_trace]
    else:
        data = [garch_trace, cir_trace, garch_lower_bound,  garch_upper_bound, cir_lower_bound, cir_upper_bound,leakage_trace]
    return data
    '''layout = go.Layout(
        yaxis=dict(title='Wind speed (m/s)'),
        title='Continuous, variable value error bars',
        legend=dict(orientation="h"))
    fig = go.Figure(data=data, layout=layout)'''

def indexPlot(params):

    SDint = params[0]
    day = params[1]
    index = params[2]
    mode = params[3]

    MA = str(day)
    SD = str(int(SDint*100))

    folderString = "SD{}/day{}/{}/".format(SD,MA,mode)

    originPath = "updating/result/{}".format(folderString)

    names = "day{}_SD{}_{}.csv".format(MA,SD,index)

    outputPath = "updating/plotly/{}{}/".format(folderString,index)
    if not os.path.exists(outputPath): #for unknown reason, multiprocess does not support exist_ok = True
        Path(outputPath).mkdir(parents=True, exist_ok=True)

    condDataframe = pd.read_csv(originPath + names , usecols=[0,31], index_col=0, na_values=["null"])
    print(names)
    if condDataframe["garch_sigma"].sum()<0:
        sigmaCondition = 0 #if sigma<0
    else:
        sigmaCondition = 1
    firstDate = condDataframe.index[0]
    lastDate = condDataframe.index[-1]

    kappa = pd.read_csv(originPath + names , usecols=[0,5,6,8,9,11,13,14], index_col=0, na_values=["null"])
    theta = pd.read_csv(originPath + names , usecols=[0,5,16,18,19,21,23,24], index_col=0, na_values=["null"])
    sigma = pd.read_csv(originPath + names , usecols=[0,5,26,28,29,31,33,34], index_col=0, na_values=["null"])
    varList = ["kappa","theta","sigma"]
    dfList = [kappa,theta,sigma]
    #varList = ["sigma"]
    #dfList = [sigma]


    for varName, dfName in zip(varList, dfList):
        titlestring = "{}_MA{}_SD{}_{}_{} ({} to {})".format(mode,MA,SDint,index,varName, firstDate, lastDate)
        garchdiff = (dfName['garch_' + varName + '_ub']- dfName['garch_' + varName])
        cirdiff = (dfName['cir_' + varName + '_ub']- dfName['cir_' + varName])
        garch25sd = (garchdiff.quantile(0.97) )/1.96*2.5
        cir25sd = (cirdiff.quantile(0.97) )/1.96*2.5
        garchmax =  garch25sd + dfName['garch_' + varName].quantile(0.97)
        circhmax =  cir25sd + dfName['cir_' + varName].quantile(0.97)
        garchmin =  -garch25sd + dfName['garch_' + varName].quantile(0.03)
        circhmin =  -cir25sd + dfName['cir_' + varName].quantile(0.03)
        yrangemax = max(garchmax, circhmax)
        yrangemin = max(0, min(garchmin, circhmin))
        data = plotlyPlot(df=dfName, varName=varName,cond = sigmaCondition)
        if varName == "sigma":
            layout = go.Layout(
                yaxis=dict(title=varName, rangemode='nonnegative'),
                title=titlestring,
                legend=dict(orientation="h"),
                yaxis2=dict(
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    showline=False,
                    range=[0, 1]
                ))
        else:
            layout = go.Layout(
                yaxis=dict(title=varName, rangemode='nonnegative', range=[yrangemin, yrangemax]),
                title=titlestring,
                legend=dict(orientation="h"),
                yaxis2=dict(
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    showline=False,
                    range=[0, 1]
                ))
        fig = go.Figure(data=data, layout=layout)
        '''plotly.offline.plot(fig, filename=outputPath + varName + ".html", auto_open=False)'''

        aPlot = plotly.offline.plot(fig, include_plotlyjs=False, show_link=False, output_type='div')
        with open(outputPath + varName + ".html", 'w') as f:
            f.write(aPlot)
    print("index")
    print(outputPath)

def indexPlotMode(params):
    plotType = params[4]
    if plotType == "normal":
        indexPlot(params)
    elif plotType == "z":
        errorPlot(params)

def callPlotly():
    start = time.time()
    dayList = [30,50,60,90,120]
    sdList = [1.5,1.75,2,2.5]
    indexList = getIndexList()
    #indexList = ["HSI","IXIC","N225"]
    modeList = ["expand","roll"]
    #plotType = ["normal","z"]
    plotType = ["normal"]
    paramList = list(itertools.product(sdList,dayList,indexList,modeList,plotType))

    #for param in paramList:
    #    indexPlot(param)
    cpuCount = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=cpuCount-1)
    pool.map(indexPlotMode , paramList)

    end = time.time()
    elapsed = end - start
    print("time used: " + str(elapsed))
    return 0

if __name__ == '__main__':
    callPlotly()