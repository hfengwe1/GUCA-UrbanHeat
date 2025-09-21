# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 14:23:15 2023
This code is for calculating an (5-day heatwave) index that combines heatwave characteristics: frequency, duration, and intensity
Customized ranges are applied to map the three variables into [0,1] and then combine them with equal weights. 

@author: Fengwei
"""


import numpy as np
import pandas  as pd
import os

## set working directory 
os.getcwd()
os.chdir('C:\\pyGUCA')


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
df_HI = pd.read_excel('Output/Heatwave/HeatIndex_'+ stat_i +'.xlsx')
    # whether heat index is greater than the local threshold value
Exceed_HI = pd.read_excel('Output/Heatwave/Count_HI_'+ stat_i +'.xlsx')

    # heat day counts
hDay_HI = pd.read_excel('Output/Heatwave/hDay_HI_'+ stat_i +'.xlsx')
    # heatwave event counts
event_HI = pd.read_excel('Output/Heatwave/event_HI_'+ stat_i +'.xlsx')
ltpv_HI = pd.read_excel('Output/Heatwave/ltpv_HI_'+ stat_i +'.xlsx')


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


#######################
#### Normalization ####
#######################

## only consider the last 20 years 
t = 20
maxf = 2; minf = 0
maxd = 10; mind = 5
maxi = 50; mini = 30



df3 = out[out["Y"]>= (2022-t+1)] # since 2003
df3.loc[:, "Dur_sum"] = df3["Duration"]*df3["Frequency"]  # sum of the heatwave days 
df3.loc[:, "Int_sum"] = df3["Intensity"]*df3["Frequency"]  # sum of the heatwave temperature 

df4 = df3.loc[:,["City", "Dur_sum", "Int_sum", "Frequency"]].groupby(["City"]).sum() # also sum of the heatwave events 
df4.loc[:,"Dur_avg"] = df4["Dur_sum"]/df4["Frequency"]
df4.loc[:,"Int_avg"] = df4["Int_sum"]/df4["Frequency"]
df4.loc[:,"Freq_avg"] = df4["Frequency"]/t
df4 = df4.reset_index(level = ["City"])
# duration, intensity are calculated using weitghted average by the # of events 
df5 = df4.loc[:,["City", "Dur_avg", "Int_avg", "Freq_avg"]]

def normalize(max, min, data): # data is an array
    
    normal = (data - min)/(max-min)
    return normal

freqAvg = df4['Freq_avg']
intAvg = df4['Int_avg']
durAvg = df4['Dur_avg']


df5.loc[:, "Dur_N"] = normalize(maxd, mind, durAvg)
df5.loc[:, "Int_N"] = normalize(maxi, mini, intAvg)
df5.loc[:, "Freq_N"] = normalize(maxf, minf, freqAvg)
df5.loc[:, "WeightedIndex"] = df5.loc[:, ["Dur_N", "Int_N", "Freq_N"]].sum(axis =1)*(1/3)

df5.to_excel('Output/HeatIndex/Heatwave_'+ stat_i + '_' + str(hotDays_th)+'D_cityMetrics.xlsx', index=True)


