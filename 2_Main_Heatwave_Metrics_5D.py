# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 14:23:15 2023
This code generate 5-day heatwave characteristics
@author: Fengwei
"""


import numpy as np
import pandas  as pd
import os

## set working directory 
os.getcwd()
os.chdir('C:\\pyGUCA')

from Functions import readFile, Events, LTPV, String_to_DateTime, HeatIndex



###################
#### Read data ####
###################
stat_i = 'Max' # stat_i: {Min, Mean, Max}
yRange = [1964,2022]  ## create a list of years for long-term statistics calculation. 
hotDays_th = 5  ## heatwave is defined as a heat event lasting for X consequtive hot days  


    # Air Temp 
# file = 'Data/AirTemp/AirTempDaily'+ stat_i +'1964_2022.csv'
# file2 = 'Data/AirTemp/DewPointTempDaily'+ stat_i +'1964_2022.csv'


# dfT = readFile(file)
# dfTdp = readFile(file2)
cities = ['Abuja', 'Amman', 'Beijing', 'Berlin', 'Bogota', 'Jakarta', 'Kinshasa', 'Mogadishu', 'Mumbai',
          'PanamaCity', 'RioDeJaneiro', 'Shenzhen']## city names

#####################################################
#### Read heat index (aparent temperature) #####
#####################################################

    # heat index values
df_HI = pd.read_excel('Output/HeatIndex/HeatIndex_'+ stat_i +'.xlsx')
    # whether heat index is greater than the local threshold value
Exceed_HI = pd.read_excel('Output/HeatIndex/Count_HI_'+ stat_i +'.xlsx')

    # heat day counts
hDay_HI = pd.read_excel('Output/HeatIndex/hDay_HI_'+ stat_i +'.xlsx')
    # heatwave event counts
event_HI = pd.read_excel('Output/HeatIndex/event_HI_'+ stat_i +'.xlsx')
ltpv_HI = pd.read_excel('Output/HeatIndex/ltpv_HI_'+ stat_i +'.xlsx')


###################################################
###### Intensity Duration Frequency Analysis ######
###################################################

df = event_HI

# Split string column into two new columns
df[['City', 'id']] = df.ID.str.split("_", expand = True) # split "ID colume into city and id
Colnames = list(df_HI.columns) # column names

ltpv = ltpv_HI  ## percentile valeus in heat index values
th = ltpv.iloc[2,:]  ## 95% percentile value; 0:0.5, 1:0.9, 2:0.95, 3:0.975, 4:0.99

dateList = df_HI['Date'].tolist() # date

df[['Intensity','DeltaT']] = 0

for i in range(len(df)):
    start = df['Start'][i]
    s = dateList.index(start)
    dur = df['Duration'][i] # duration
    city = df['City'][i]
    if dur == 1:
        avgT = df_HI[city][s]
        deltaT = df_HI[city][s]-th[city]

    elif dur >1: 
        avgT = df_HI[city][np.arange(s,s+dur)].mean()
        deltaT = df_HI[city][np.arange(s,s+dur)].mean() - th[city]

    else: 
        pass
    df.loc[i, 'Intensity'] = avgT
    df.loc[i, 'DeltaT'] = deltaT
    
    
df2 = df.loc[df['Duration'] >= hotDays_th] # Temprature exceeds 95%-percentile value for at least 2 days
df2.loc[:, 'Y'] = df2.Start.dt.year

df_stat = df2.groupby(['City', 'Y'])[['Duration', 'Intensity','DeltaT']].mean()
df_stat['Frequency'] = df2.groupby(['City', 'Y'])['id'].count()
df_stat['Start'] = df2.groupby(['City', 'Y'])['Start'].min()
df_stat['End'] = df2.groupby(['City', 'Y'])['End'].max()
df_stat['Season'] = (df_stat['End'] - df_stat['Start']).dt.days
out = df_stat.reset_index(level = ["City", "Y"])

## Export Results
     ## Heat index 
out.to_excel('Output/HeatIndex/HeatIndex_FID_'+ stat_i + '_' + str(hotDays_th)+'D.xlsx', index=True)

