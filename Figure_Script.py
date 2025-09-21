# -*- coding: utf-8 -*-
"""
Created on Sun Nov 19 22:57:14 2023

This is the script for generating Figures

@author: Fengwei
"""
import os
import subprocess

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 

## set working directory 
os.chdir('C:\\pyGUCA\Output\HeatIndex')
cwd = os.getcwd()
# Create the directory 
fig_Dir = os.path.join(cwd, 'Figure')
hotDays_th = 5  ## heatwave is defined as a heat event lasting for X consequtive hot days  

try:
    os.mkdir(fig_Dir)
    print("Folder %s created!" % fig_Dir)
except FileExistsError:
    print("Folder %s already exists" % fig_Dir) 

###################
#### Read data ####
###################
stat_i = 'Max' # stat_i: {Min, Mean, Max}

file = 'HeatIndex_FID_'+ stat_i + '_' + str(hotDays_th)+'D.xlsx'
df = pd.read_excel(file, index_col='City')
metric = ['Duration', 'Frequency', 'DeltaT']

# df.reset_index(inplace=True) # convert multi- indices as multi-columns
cities = ['Abuja', 'Amman', 'Beijing', 'Berlin', 'Bogota', 'Jakarta', 'Kinshasa', 'Mogadishu', 'Mumbai',
          'PanamaCity', 'RioDeJaneiro', 'Shenzhen'] # city names
fontsize = 10
s = pd.Series(['g','b', 'm'], index = metric)

for city in cities:
    df1 = df.loc[city]
  # time series
    plt.figure(); 
    # df1.plot(x ='Y', y = metric, color = s ); 
    df1.plot(x ='Y', y = metric); 

    plt.ylim(0,20); 
    plt.yticks(np.arange(0, 21, step= 5));
    plt.legend(loc='best')
    plt.ylabel('Value')
    plt.xlabel('Year')

    plt.title(city)
    figfile = os.path.join(cwd, 'Figure\Heat_'+ city +'.tif')
    plt.savefig(figfile)
    plt.close()

    ## Scatter Plots
for city in cities:
    df1 = df.loc[city]
    # scatter plot
    fig, ax = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(6, 6), layout="constrained")
    ax.scatter(df1[metric[0]], df1[metric[1]], df1[metric[2]])
   # Tweaking display region and labels
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_zlim(0, 5)
    ax.set_xlabel('Duration', fontsize=fontsize)
    ax.set_ylabel('Frequency', fontsize=fontsize)
    ax.set_zlabel('DeltaT', fontsize=fontsize, rotation=90)

    ax.set_title(city, fontsize=18, pad = -10)
    ax.set_box_aspect(aspect=None, zoom=0.9)
    figfile = os.path.join(cwd, 'Figure\ScatterP_Heat_'+ city +'.tif')
    # plt.tight_layout()
    plt.savefig(figfile, dpi=150)
    plt.close()
