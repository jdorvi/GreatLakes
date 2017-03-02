# -*- coding: utf-8 -*-
""" Automate attribution of coastal Mapping_Method polygons during coastal modeling
mapping process """
# ---------------------------------------------------------------------------
# mapping_method.py
# Created on: 2016-12-19
# Usage:
# Description:
# Author: J. Dorvinen
# Email: jdorvinen@dewberry.com
# ---------------------------------------------------------------------------

# Import modules
import archook
archook.get_arcpy()
import arcpy
import os
from dataIO import dbf2df, df2dbf
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Set working environment
WORKING_DIR = "P:/02/NY/Cayuga_Co_36011C/STUDY__TO90/TECHNICAL/ENG_FLOOD_HAZ_DEV/COASTAL/MAPPING"
arcpy.env.workspace = WORKING_DIR

####################################################################################
# PREPAIRING THE DATA ##############################################################
####################################################################################
# ASSIGN                                                                           #
# HYDROID                                                                          #
# Input this field with the number of the transect that it’s runup/WHAFIS result is#
# used to map one mapping polygon. If that transect is not directly overlapping    #
# with this mapping method polygon, please write “transect# borrowed”.  For area   #
# between transects, leave this field blank.                                       #
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
# CALCULATE Q                                                                      #
# If overtopping is occuring assign 'YES' to 'OVERTOPPED' field, else assign 'NO'  #
# Calculate overtopping based on controlling wave height and assign to field 'Q'   #
# (use the starting wave condition of each transect as the wave condition at toe of#
#  each transect for overtopping calculation)                                      #
#                                                                                  #
# NOTES                                                                            #
# Input any other description about mapping method within this mapping method      #
# polygon. Suggest to write down final runup value and runup method in this field. #
#                                                                                  #
# EXPORT                                                                           #
# joined shapefile to new shapefile '...Mapping_Method_JOIN.shp'                   #
#                                                                                  #
# IMPORT .dbf file from new shapefile, this is what we'll be manipulating          #
####################################################################################
INPUT_FEATURES = "Cayuga_NY_Mapping_Method_JOINv2"
INPUT_FILE = os.path.join(WORKING_DIR, INPUT_FEATURES)

mdf = dbf2df(INPUT_FILE+".dbf")

# Make sure 'WHAFIS_ZON' is all CAPS
mdf['WHAFIS_ZON'] = mdf['WHAFIS_ZON'].str.strip().str.upper()

# Update 'Highest_WH'
# Input this field with the highest wave crest in Scenario4’s WHAFIS output
mdf.loc[:, 'Highest_WH'] = mdf.loc[:, 'WHAFIS_SWE'].round(1)

# Round 'GF_2PERCEN' values to tenths of a foot
mdf.loc[:, 'GF_2PERCEN'] = mdf.loc[:, 'GF_2PERCEN'].round(1)

# Update 'MAP_1stBFE' and 'MAP_1stSOU'
# Compare the final runup and Highest_WH, input the higher value.
# Input the source of MAP_1stBFE (WHAFIS or RUNUP)
for i in range(len(mdf['MAP_1stBFE'])):
    water_levels = {mdf.loc[i, 'GF_2PERCEN']:'RUNUP',
                    mdf.loc[i, 'Highest_WH']:'WHAFIS'}
    if max(water_levels) == 0:
        mdf.loc[i, 'MAP_1stBFE'] = 0
        mdf.loc[i, 'Map_1stSOU'] = ''
    elif min(water_levels) == max(water_levels):
        mdf.loc[i, 'MAP_1stBFE'] = min(water_levels)
        mdf.loc[i, 'Map_1stSOU'] = 'WHAFIS'
    else:
        mdf.loc[i, 'MAP_1stBFE'] = max(water_levels)
        mdf.loc[i, 'Map_1stSOU'] = water_levels[mdf.loc[i, 'MAP_1stBFE']]

# Update 'MAP_1stZON'
for i in range(len(mdf['MAP_1stZON'])):
    if mdf['WHAFIS_ZON'][i] == 'VE': #If WHAFIS’s first zone is VE, 
        mdf.loc[i, 'MAP_1stZON'] = 'VE' #input “VE”. 
    elif mdf['WHAFIS_ZON'][i] == 'AE': # If WHAFIS’s first zone is AE
        if mdf['Map_1stSOU'][i] == 'WHAFIS': # and WHAFIS dominates
            mdf.loc[i, 'MAP_1stZON'] = 'AE' # input “AE”.  
        elif mdf['Map_1stSOU'][i] == 'RUNUP': # If WHAFIS’s first zone is AE but runup dominates, 
            if mdf['WHAFIS_WAV'][i] > 3: #check if the controlling wave height is more than 3ft,
                mdf.loc[i, 'MAP_1stZON'] = 'VE' # input 'VE'
            elif mdf['WHAFIS_WAV'][i] <= 3: # if not, 
                mdf.loc[i, 'MAP_1stZON'] = 'AE' # input “AE”.  
    else:
        mdf.loc[i, 'MAP_1stZON'] = ''

# Update 'LIMWA_ele' and 'LIMWA_Def'
# field is input with the water elevation at the 1st 1.5 wave point.
for i in range(len(mdf['LIMWA_ele'])):
    if mdf['MAP_1stZON'][i] == 'VE' and mdf['Map_1stSOU'][i] == 'WHAFIS': # If WHAFIS’s first zone is VE and no runup is mapped.
        mdf.loc[i, 'LIMWA_ele'] = mdf['LIMWA_SWEL'][i] #input with the water elevation at the 1st 1.5 wave point
        mdf.loc[i, 'LIMWA_Def'] = 'LiMWA needs to be mapped, VE and runup dominated'
    elif mdf['MAP_1stZON'][i] == 'AE' and mdf['WHAFIS_WAV'][i] >= 3: #If WHAFIS’s first zone is AE, but controlling wave height is more than 3ft,
        mdf.loc[i, 'LIMWA_ele'] = mdf.loc[i, 'LIMWA_SWEL'] #it might be ok to map LiMWA
        mdf.loc[i, 'LIMWA_Def'] = 'LiMWA may be mapped, zone AE but WHAFIS_WAV >= 3ft' #based on engineering judgment.
    else: # . If transect is eroded or VA gutter station is based on overtopping result or WHAFIS’s first zone is AE, 
        mdf.loc[i, 'LIMWA_ele'] = -999 # leave this field 0. 
        mdf.loc[i, 'LIMWA_Def'] = 'Do not map LiMWA'

#### Pick up here ###

# Update 'VAGut_ele' and 'VAGut_Def'
for i in range(len(mdf['VAGut_ele'])):
    if mdf['MAP_1stZON'][i] == 'VE': # Input this value when MAP_1stZON is VE. 
        if mdf['Map_1stSOU'][i] == 'WHAFIS': #When WHAFIS dominates,
            mdf.loc[i, 'VAGut_ele'] = mdf['VA_ELEV'][i] # put the terrain elevation at the first AE station of WHAFIS output. 
        elif mdf['Map_1stSOU'][i] == 'RUNUP': #When runup dominates, 
            mdf.loc[i, 'VAGut_ele'] = mdf['GF_2PERCEN'][i]-3 #put (final runup-3ft). 
        if mdf['GF_EROSION'][i] == 'YES': #When a transect is eroded
            if mdf['Map_1stSOU'][i] == 'RUNUP': # and runup dominates
                mdf.loc[i, 'VAGut_ele'] = 0 #leave this field 0
                mdf.loc[i, 'VAGut_Def'] = 'Do not map VA gutter' # and note the station of VA gutter in VAGut_Def.

    if mdf['Q'][i] > 1: # When overtopping rate Q>1
        mdf.loc[i, 'VAGut_ele'] = 0 #leave this field 0 
        mdf.loc[i, 'VAGut_Def'] = '30ft behind crest' #VA gutter should be mapped at 30ft behind crest 
        mdf.loc[i, '100Bry_Def'] = "AO zone extent station" #and describe AO zone extent station in 100Bry_Def
    elif mdf['Q'][i] <= 1 and mdf['Q'][i] >= 0: #When overtopping rates Q is between 0-1
        mdf.loc[i, 'VAGut_ele'] = mdf['GF_2PERCEN'][i]-3 #put VA gutter at (final runup-3ft) 
        mdf.loc[i, 'VAGut_Def'] = '"Runup" – 3' #
        mdf.loc[i, '100Bry_Def'] = "AO zone extent station" #and describe AO zone extent station in 100Bry_Def.
    else:
        mdf.loc[i, 'Q'] = -999

# Update '100Bry_ele' and '100Bry_Def'
# Input this field with the water elevation at 100yr boundary
for i in range(len(mdf['100Bry_ele'])):
    if mdf['GF_EROSION'][i] == 'NO': # at non-eroded transects. 
        if mdf['Map_1stSOU'][i] == 'RUNUP': #If runup dominates at 100yr boundary,
            if mdf['OVERTOPPED'][i] == 'NO':
                mdf.loc[i, '100Bry_ele'] = mdf['GF_2PERCEN'][i] #this value is the final runup (after plateau method and 3ft above crest capping rule).
                mdf.loc[i, '100Bry_Def'] = 'value is the final runup'
            elif mdf['OVERTOPPED'][i] == 'YES':
                mdf.loc[i, '100Bry_ele'] = -999 #this value is the final runup (after plateau method and 3ft above crest capping rule).
                mdf.loc[i, '100Bry_Def'] = 'value is the final runup (after plateau method and 3ft above crest capping rule)'
    else: #If 100yr boundary is mapped to 100yr SWEL or transect is eroded or if there is no 100yr boundary needed, leave this field 0.
        mdf.loc[i, '100Bry_ele'] = 0

# Drop unneeded indices
mdf.drop(mdf.columns[[4, 5]], axis=1, inplace=True)

# Write updated df to shapefile's dbf
OUTSPECS = [('C', 200, 0), ('N', 8, 2), ('N', 8, 2),
            ('C', 9, 0), ('N', 8, 0), ('C', 9, 0),
            ('N', 8, 2), ('N', 8, 0), ('C', 200, 0),
            ('N', 8, 2), ('N', 8, 2), ('N', 8, 2),
            ('N', 8, 2), ('N', 8, 2), ('C', 9, 0),
            ('C', 9, 0), ('C', 200, 0), ('C', 9, 0),
            ('N', 20, 15), ('N', 8, 0), ('C', 200, 0),
            ('N', 8, 2), ('N', 8, 2), ('N', 8, 2),
            ('N', 8, 2), ('N', 8, 2), ('N', 8, 2),
            ('C', 9, 0)]

df2dbf(mdf, INPUT_FILE+"_updated.dbf", my_specs=OUTSPECS)
