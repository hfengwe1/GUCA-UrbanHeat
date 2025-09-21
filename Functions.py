# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 14:38:25 2023

@author: Fengwei
"""
import numpy as np
import pandas  as pd
from metpy.units import units
import metpy.calc as mpcalc


## read csv file and slice 'Date' column into 'Year', 'Month', and 'Day'.
def readFile(file):
   df = pd.read_csv(file)
   df['Year'] = df['Date'].map(lambda x: str(x)[0:4]).astype(int) ## read year as string and convert it to int.
   df['Month'] = df['Date'].map(lambda x: str(x)[4:6]).astype(int)
   df['Day'] = df['Date'].map(lambda x: str(x)[6:8]).astype(int)
   return df

    
def String_to_DateTime(df, colname):    
    df[colname] = pd.to_datetime(df[colname], format= '%Y%m%d', errors = 'coerce')
    return df


## LTPV: Long-term percentile value  (1980 to 2020)
def LTPV(df,yRange, cities):
    df1 = df[cities][(df['Year']>= yRange[0]) & (df['Year']<= yRange[1])] ## select data from yRange 
    stat = df1.quantile([0.5, 0.9, 0.95,0.975, 0.99]) ## 50%, 90%, 95%, 97.5%, and 99% of the measurement
    return stat

def HeatIndex(dfT, dfTdp, cities):
    dict_hi = {}
    for i in range(len(cities)):
        Temp = dfT[cities[i]].to_numpy()*units.degC # air temperature 
        Dewpt = dfTdp[cities[i]].to_numpy()*units.degC # dewpoint temporature
        metRh = mpcalc.relative_humidity_from_dewpoint(Temp, Dewpt)  # relative humidity (fraction)
        HI = mpcalc.heat_index(Temp, metRh,False).to(units.degC)  # convert fahrenheit to Celcsius
        dict_hi[cities[i]] = HI
    
    df_hi = pd.DataFrame.from_dict(dict_hi)
    df_HI = pd.concat([df_hi, dfT[['Date', 'Year', 'Month', 'Day']]], axis=1, join="inner")
    df = String_to_DateTime(df_HI, 'Date')
    return df


## Indices
## Annual Cumulative Heat days 

def Events(df, th, cities):
    Exceed = df[cities] >= th
    Exceed['Year'] = df['Year']
    hDay = Exceed.groupby(['Year']).sum()
    
    ## Initilization
    Start = []
    End = []
    Duration = []
    ID = []
    for i in range(len(cities)): ## loop through the cities
        nrow = len(df)
        n = 0
        hw_id = 0 

        for j in np.arange(1,nrow): ## start from day 2 to prevent indexing error
        ## not a heat day
            if list(Exceed[cities[i]])[j] == 0 and n == 0:
                pass
               # n = 0
               # print('case', 4)
               
        ## the start date of the event; record start end and duration
            elif list(Exceed[cities[i]])[j] == 1 and n == 0 :  
               # print('case', '1') # start of an event
               ID.append(cities[i]+ '_' +str(hw_id))  ## save ID
               Start.append(df['Date'][j]) ## save start date
               n += 1  ## counting heatwave days
               End.append(df['Date'][j]) ## save end date
               Duration.append(n)  ## save event duration
               
        ## heat continues
            elif list(Exceed[cities[i]])[j]  == 1 and n != 0: 
               n += 1  ## keep counting
               # print('case', 2)

        ## end of the heatwave event              
            elif list(Exceed[cities[i]])[j] == 0 and n > 0 : ## the end date of the event 
               End[-1] = df['Date'][j] ## update end date
               Duration[-1] = n  ## update event duration
               n = 0       ## reset n
               hw_id += 1  ## new id for the next event
               # print('case', 3)

            elif list(Exceed[cities[i]])[j]  == 1 and n > 0 and j+1 == nrow: ## event continues at the end of the records
               n += 1  ## keep counting
               End[-1] = df['Date'][j] ## update end date
               Duration[-1] = n  ## update event duration

              
            else:
               print('Error: This is an exception:',cities[i], 'Row', j )
               # print('case', 5)
    Event = pd.DataFrame.from_dict({'ID':ID, 'Start':Start, "End":End, "Duration":Duration})
                
    return Exceed, hDay, Event



    
