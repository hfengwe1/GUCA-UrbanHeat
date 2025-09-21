# -*- coding: utf-8 -*-
"""
Created on Wed Nov 15 14:23:15 2023
This code calculate a heat hazard index (HHI) that combines land surface temperature (LST), Urbna heat island (UHI), and heatwave index.
The three variables are mapped to [0,1] using customized upper ad lower bounds. 
As per the discussion in the group project meeting, The weights for combining the three metrics are: 0.4, 0.2, 0.4, respectively. 
@author: Fengwei
"""

import numpy as np
import pandas  as pd
import os

## set working directory 
os.getcwd()
os.chdir('C:\\pyGUCA')

# hotDays_th = 2 # 2-day heatwave definition
hotDays_th = 5 # 5-day heatwave definition

cities = ['Abuja', 'Amman', 'Beijing', 'Berlin', 'Bogota', 'Jakarta', 'Kinshasa', 'Mogadishu', 'Mumbai',
          'PanamaCity', 'RioDeJaneiro', 'Shenzhen']## city names
###### summer maximum Land surface temperature
lst = pd.read_csv('Output/LST_Statistics/maskedUrban/LST_MaxDay_maskedNonUrb_Summer.csv')
dfLST = lst.loc[:,['Name', 'Mean']].rename(columns = {'Name': 'City', 'Mean': 'meanLST'
                                                      }).set_index('City')


###### summer surface UHI temperature
uhi = pd.read_csv('Output/UHI_Statistics/UHI_warm_months.csv')
dfUHI = uhi.loc[:,['Name', 'mean']].rename(columns = {'Name': 'City', 'mean': 'meanUHI'
                                                    }).set_index('City') 

###### heatwave composite index
dfHW = pd.read_excel('Output/Heatwave/Heatwave_Max_' + str(hotDays_th)+'D_cityMetrics.xlsx', index_col = 0
                    ).loc[:, ['City','WeightedIndex']].rename(columns = {'WeightedIndex': 'HW_i'}).set_index('City')


#####################
### Normalization ###
#####################

def normalize(data, max, min): # data is an array
    normal = (data - min)/(max-min)
    for i in range(len(normal)):
        if normal[i] >=1:
            normal[i] = 1
        elif normal[i] <0:
            normal[i] = 0
            
    return normal

# normalization based on user-defined ranges
max_lst = 50; min_lst = 30;
max_UHI = 5; min_UHI = 0; 
w = [2/5,1/5,2/5] # weights for combining metrics
# w = [3/8,1/4,3/8] # weights for combining metrics

dfHI = pd.concat([dfLST, dfUHI, dfHW], axis =1)
dfHI.loc[:, "LST_N"] = normalize(dfHI['meanLST'], max_lst, min_lst )
dfHI.loc[:, "UHI_N"] = normalize(dfHI['meanUHI'], max_UHI, min_UHI)
dfHI.loc[:, "HW_N"] = normalize(dfHI['HW_i'], 1, 0)
dfHI.loc[:, "HHI_indx"] = (dfHI.loc[:, ["LST_N", "UHI_N", "HW_N"]]*w).sum(axis =1)

dfHI.to_excel('Output/HHI_' + str(hotDays_th)+'D_w_reference_0821_pt20.xlsx', index=True)
