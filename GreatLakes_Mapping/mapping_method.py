""" Automating coastal modeling mapping process """
import archook
archook.get_arcpy()
import arcpy
import os
import numpy as np
import pandas as pd
from dataIO import dbf2df, df2dbf

# Set working environment
WORKING_DIR = "P:/02/NY/Cayuga_Co_36011C/STUDY__TO90/TECHNICAL/ENG_FLOOD_HAZ_DEV/COASTAL/MAPPING"
arcpy.env.workspace = WORKING_DIR

####################################################################################
# PREPAIRING THE DATA ##############################################################
####################################################################################
# ASSIGN                                                                           #
# HYDROID numbers to Mapping_Method polygons where appropriate                     #
# for borrowed transects 'H_BORROWED' = "YES", otherwise 'H_BORROWED' = "NO"       #
#                                                                                  #
# RUN extract_whafis.py on all WHAFIS .OUT files in "County_State_CHAMP_s4" folder #
#                                                                                  #
# TURN OFF ALL FIELDS in S_CST_TSCT_LN                                             #
# ****EXCEPT****                                                                   #
#     HYDROID                                                                      #
#     GF_EROSION_LID                                                               #
#     GF_2PERCENT_RUNUP                                                            #
#                                                                                  #
# JOIN                                                                             #
# S_CST_TSCT_LN and WHAFIS.csv to Mapping_Method polygons based on HYDROID         #
#                                                                                  #
# UPDATE 'Id' field (we will use this to join the data back at the end)            #
# 'Id' = ('FID' + 1) * 1000                                                        #
#                                                                                  #
# EXPORT                                                                           #
# joined shapefile to new shapefile '...Mapping_Method_JOIN.shp'                   #
#                                                                                  #
# IMPORT .dbf file from new shapefile, this is what we'll be manipulating          #
####################################################################################
INPUT_FEATURES = "Cayuga_NY_Mapping_Method_JOIN"
INPUT_FILE = os.path.join(WORKING_DIR, INPUT_FEATURES)

mdf = dbf2df(INPUT_FILE+".dbf")

# Update 'Highest_WH'
mdf.loc[:, 'Highest_WH'] = mdf.loc[:, 'WHAFIS_EL'].round(1)

# Round 'GF_2PERCEN' values to tenths of a foot
mdf.loc[:, 'GF_2PERCEN'] = mdf.loc[:, 'GF_2PERCEN'].round(1)

# Update 'MAP_1stBFE' and 'MAP_1stSOU'
for i in range(len(mdf['MAP_1stBFE'])):
    water_levels = {mdf.loc[i, 'GF_2PERCEN']:'RUNUP',
                    mdf.loc[i, 'Highest_WH']:'WHAFIS'}
    if max(water_levels) == 0:
        mdf.loc[i, 'MAP_1stBFE'] = 0
        mdf.loc[i, 'MAP_1stSOU'] = ""
    elif min(water_levels) == max(water_levels):
        mdf.loc[i, 'MAP_1stBFE'] = min(water_levels)
        mdf.loc[i, 'MAP_1stSOU'] = 'WHAFIS'
    else:
        mdf.loc[i, 'MAP_1stBFE'] = max(water_levels)
        mdf.loc[i, 'MAP_1stSOU'] = water_levels[mdf.loc[i, 'MAP_1stBFE']]

# Update 'MAP_1stZON'
for i in range(len(mdf['MAP_1stZON'])):
    if mdf['WHAFIS_ZN'][i].strip() == 'VE':
        mdf.loc[i, 'MAP_1stZON'] = 'VE'
    elif mdf['WHAFIS_ZN'][i].strip() == 'AE':
        if mdf['MAP_1stSOU'][i] == 'WHAFIS':
            mdf.loc[i, 'MAP_1stZON'] = 'AE'
        elif mdf['MAP_1stSOU'][i] == 'RUNUP':
            if mdf['WHAFIS_WH'][i] > 3:
                mdf.loc[i, 'MAP_1stZON'] = 'VE'
            elif mdf['WHAFIS_WH'][i] <= 3:
                mdf.loc[i, 'MAP_1stZON'] = 'AE'
    else:
        mdf.loc[i, 'MAP_1stZON'] = ''

# Update 'LIMWA_ele' and 'LIMWA_Def'
for i in range(len(mdf['LIMWA_ele'])):
    if mdf['MAP_1stZON'][i] == 'VE' and mdf['MAP_1stSOU'][i] == 'WHAFIS':
        mdf.loc[i, 'LIMWA_ele'] = mdf['LIMWA_EL'][i]
        mdf.loc[i, 'LIMWA_Def'] = 'LiMWA needs to be mapped, VE and runup dominated'
    elif mdf['MAP_1stZON'][i] == 'AE' and mdf['WHAFIS_WH'][i] >= 3:
        mdf.loc[i, 'LIMWA_ele'] = mdf.loc[i, 'LIMWA_EL']
        mdf.loc[i, 'LIMWA_Def'] = 'LiMWA may be mapped, zone AE but WHAFIS_WH >= 3ft'
    else:
        mdf.loc[i, 'LIMWA_ele'] = -999
        mdf.loc[i, 'LIMWA_Def'] = 'Do not map LiMWA'

#### Pick up here ###
#### For this step need to have completed plateau method and 3ft capping rule

# Calculate Q (overtopping) based on controlling wave height
# terrain elevation at the first AE station of WHAFIS extract with script assign to variable
# firstAE_ele
mdf['Q'] = 'numbers'

# Update 'VAGut_ele' and 'VAGut_Def'
for i in range(len(mdf['VAGut_ele'])):
    if mdf['MAP_1stZON'][i] == 'VE':
        if mdf['MAP_1stSOU'][i] == 'WHAFIS':
            mdf.loc[i, 'VAGUT_ele'] = mdf['firstAE_ele'][i]
        elif mdf['MAP_1stSOU'][i] == 'RUNUP':
            mdf.loc[i, 'VAGUT_ele'] = mdf['runup_val'][i]-3
        if mdf['GF_EROSION_LID'][i] == 'YES':
            if mdf['MAP_1stSOU'][i] == 'RUNUP':
                mdf.loc[i, 'VAGut_ele'] = 0
                mdf.loc[i, 'VAGut_Def'] = ""    # STATIONID of VA gutter

    if mdf['Q'][i] > 1:
        mdf.loc[i, 'VAGut_ele'] = 0
        mdf.loc[i, 'VAGut_Def'] = "30ft behind crest"
        mdf.loc[i, '100Bry_Def'] = "AO zone extent station" #(extract from .OUT file with script)
    elif mdf['Q'][i] <= 1 and mdf['Q'][i] >= 0:
        mdf.loc[i, 'VAGut_ele'] = mdf['runup_val'][i]-3
        mdf.loc[i, 'VAGut_Def'] = '"Runup" – 3'

    mdf.loc[i, '100Bry_Def'] = ""   # describe AO zone extent station

# Update '100Bry_ele' and '100Bry_Def'
for i in range(len(mdf['100Bry_ele'])):
    if mdf['GF_EROSION'][i] == 'NO':
        if mdf['MAP_1stSOU'] == 'RUNUP':
            mdf.loc[i, '100Bry_ele'] = 'Numbers'
            mdf.loc[i, '100Bry_Def'] = 'value is the final runup (after plateau method and 3ft above crest capping rule'
    else:
        mdf.loc[i, '100Bry_ele'] = '0'


# Write updated df to shapefile's dbf
df2dbf(mdf, JOINED_FILE+"_updated.dbf")
