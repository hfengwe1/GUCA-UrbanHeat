# -*- coding: utf-8 -*-
"""
Created on Sun Nov  5 22:18:34 2023

@author: Fenwgei
"""

import numpy as np
import pandas  as pd
import os
from metpy.units import units
import metpy.calc as mpcalc
# import matplotlib.pyplot as plt

os.getcwd()
os.chdir('C:\\pyGUCA')

file = 'Data/AirTemp/AirTempDailyMin1964_2022.csv'
file2 = 'Data/AirTemp/DewPointTempDailyMin1964_2022.csv'
yRange = [1964,2020]  ## create a list of years for long-term statistics calculation. 

## read csv file and slice 'Date' column into 'Year', 'Month', and 'Day'.
def readFile(file):
   df = pd.read_csv(file)
   df['Year'] = df['Date'].map(lambda x: str(x)[0:4]).astype(int) ## read year as string and convert it to int.
   df['Month'] = df['Date'].map(lambda x: str(x)[4:6]).astype(int)
   df['Day'] = df['Date'].map(lambda x: str(x)[6:8]).astype(int)
   return df

## LTPV: Long-term percentile value  (1980 to 2020)
def LTPV(df,yRange, cities):
    df1 = df[cities][(df['Year']>= yRange[0]) & (df['Year']<= yRange[1])] ## select data from yRange 
    stat = df1.quantile([0.5, 0.9, 0.95,0.975, 0.99]) ## 50%, 90%, 95%, 97.5%, and 99% of the measurement
    return stat
    

## Indices
## Annual Cumulative Heat days 

def Events(df, th, cities):
    Count = df[cities] >= th
    Count['Year'] = df['Year']
    hDay = Count.groupby(['Year']).sum()
    
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
            if list(Count[cities[i]])[j] == 0 and n == 0:
                pass
               # n = 0
               # print('case', 4)
               
        ## the start date of the event; record start end and duration
            elif list(Count[cities[i]])[j] == 1 and n == 0 :  
               # print('case', '1') # start of an event
               ID.append(cities[i]+ '_' +str(hw_id))  ## save ID
               Start.append(df['Date'][j]) ## save start date
               n += 1  ## counting heatwave days
               End.append(df['Date'][j]) ## save end date
               Duration.append(n)  ## save event duration
               
        ## heat continues
            elif list(Count[cities[i]])[j]  == 1 and n != 0: 
               n += 1  ## keep counting
               # print('case', 2)

        ## end of the heatwave event              
            elif list(Count[cities[i]])[j] == 0 and n > 0 : ## the end date of the event 
               End[-1] = df['Date'][j] ## update end date
               Duration[-1] = n  ## update event duration
               n = 0       ## reset n
               hw_id += 1  ## new id for the next event
               # print('case', 3)

            elif list(Count[cities[i]])[j]  == 1 and n > 0 and j+1 == nrow: ## event continues at the end of the records
               n += 1  ## keep counting
               End[-1] = df['Date'][j] ## update end date
               Duration[-1] = n  ## update event duration

               # print('case', '2+')
            # elif list(Count[cities[i]])[j]  == 1 and n ==0  and j+1 == nrow: ## an event starts at the end of the records
            #    # print('case', '1')
            #    ID.append(cities[i]+ '_' +str(hw_id))  ## save ID
            #    Start.append(df['Date'][j]) ## save start date
            #    n += 1  ## counting heatwave days
               
            else:
               print('Error: This is an exception:',cities[i], 'Row', j )
               # print('case', 5)
    event = pd.DataFrame.from_dict({'ID':ID, 'Start':Start, "End":End, "Duration":Duration})
                
    return Count, hDay, event





## Air Temp 
dfT = readFile(file)
# dfT = df.drop(['Date'], axis=1) 

dfTdp = readFile(file2)

cities = ['Abuja', 'Amman', 'Beijing', 'Berlin', 'Bogota',
       'Jakarta', 'Kinshasa', 'Mogadishu', 'Mumbai', 'PanamaCity',
       'RioDeJaneiro', 'Shenzhen'] ## city names

ltpv = LTPV(dfT,yRange, cities) ## Temperature value at 50%, 90%, 95%, 97.5%, and 99% quantile
th = ltpv.loc[0.95]  ## 95% percentile value 


Count, hDay, event = Events(dfT, th, cities)
hDay.to_excel('Output/hDay.xlsx', index = False)
Count.to_excel('Output/Count.xlsx', index = False)
event.to_excel('Output/event.xlsx', index = False)
ltpv.to_excel('Output/ltpv.xlsx')

####################################################################
## Heat Index/Apparent Temperature (air temp + relative humidity)
####################################################################

HeatIndex = {}
for i in range(len(cities)):
    Temp = dfT[cities[i]].to_numpy()*units.degC # air temperature 
    Dewpt = dfTdp[cities[i]].to_numpy()*units.degC # dewpoint temporature
    metRh = mpcalc.relative_humidity_from_dewpoint(Temp, Dewpt)  # relative humidity (fraction)
    HI = mpcalc.heat_index(Temp, metRh,False).to(units.degC)  # convert fahrenheit to Celcsius
    HeatIndex[cities[i]] = HI

df_hi = pd.DataFrame.from_dict(HeatIndex)
df_HI = pd.concat([df_hi, dfT[['Date', 'Year', 'Month', 'Day']]], axis=1, join="inner")

ltpv_HI = LTPV(df_HI, yRange, cities)
th_HI = ltpv_HI.loc[0.95]  ## 95% percentile value 


# python program to check if a path exists
#if path doesn’t exist we create a new path
try:
   os.makedirs("Output/HeatIndex")
except FileExistsError:
   # directory already exists
   pass


## Calculate the duration of the extreme heat events based on Heat Index Temperature
Count_HI, hDay_HI, event_HI = Events(df_HI, th_HI, cities)
df_HI.to_excel('Output/HeatIndex/HeatIndex.xlsx',  index=False) # heatindex (apparent temperature)
hDay_HI.to_excel('Output/HeatIndex/hDay_HI.xlsx', index=False)  # count hot days
# Count_HI.to_excel('Output/HeatIndex/Count_HI.xlsx', index=False)
event_HI.to_excel('Output/HeatIndex/event_HI.xlsx', index=False) # heatwave start, end time and duration
ltpv_HI.to_excel('Output/HeatIndex/ltpv_HI.xlsx')                # temperature percentile values for selecting operational heatwave definition (applied 95%-value)




