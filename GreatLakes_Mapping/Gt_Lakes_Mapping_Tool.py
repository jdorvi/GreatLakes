""" Automate coastal hazard zone mapping steps post-modeling. Scripty relies
on python 2 and an extra module 'archook'. """
# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Gt_Lakes_Mapping_Tool.py
# Created on: 2016-12-12
# Usage: python Gt_Lakes_Mapping_Tool.py <inputfile>
# Description:
# Author: J. Dorvinen, F. Knight
# Email: jdorvinen@dewberry.com, fknight@dewberry.com
# ---------------------------------------------------------------------------

# Import modules
import sys
import archook
archook.get_arcpy()
import arcpy
import os
import imp

# Get input file location from commandline args, or user input
try:
    INPUTFILE = sys.argv[1]
except IndexError:
    INPUTFILE = input("Name of input file(with quotes)? ")

try:
    with open(INPUTFILE) as f:
        INPUTDATA = imp.load_source('INPUTDATA', '', f)
except ImportError:
    print("Could not find properly formatted input file.")

# Check out 3D analyst extension
class LicenseError(Exception):
    """ DOC STRING """
    pass

try:
    if arcpy.CheckExtension("3D") == "Available":
        arcpy.CheckOutExtension("3D")
    else:
        # raise a custom exception
        raise LicenseError
except LicenseError:
    print("3D Analyst license is unavailable")
except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))

# Allow overwrite output
arcpy.env.overwriteOutput = True

# Generated folders
OUTPUTPATH = os.path.join(INPUTDATA.MAPPING_FOLDER, "OUTPUT/")
RASTER_FOLDER = os.path.join(OUTPUTPATH, "raster/")

# Create folders
if os.path.exists(OUTPUTPATH) != True:
    os.mkdir(OUTPUTPATH)
if os.path.exists(RASTER_FOLDER) != True:
    os.mkdir(RASTER_FOLDER)

# Set Geoprocessing environments
arcpy.env.scratchWorkspace = OUTPUTPATH
arcpy.env.workspace = OUTPUTPATH

# Local variables:
MAPPING_METHOD_LAYER_1 = "Mapping_Method_Layer_1"
MAPPING_METHOD_LAYER_2 = "Mapping_Method_Layer_2"
MAPPING_METHOD_LAYER_3 = "Mapping_Method_Layer_3"

V100_YR_RAS = os.path.join(OUTPUTPATH, "100_yr_ras")
V100_YR_TIN = os.path.join(OUTPUTPATH, "100_yr_Tin")

VA_RAS = os.path.join(OUTPUTPATH, "VA_bdy_ras")
VA_TIN = os.path.join(OUTPUTPATH, "VA_Tin")

LIMWA_RAS = os.path.join(OUTPUTPATH, "LiMWA_ras")
LIMWA_TIN = os.path.join(OUTPUTPATH, "LiMWA_Tin")

OUTPUT_RASTER_1 = os.path.join(OUTPUTPATH, "raster/outras1")
OUTPUT_RASTER_2 = os.path.join(OUTPUTPATH, "raster/outras2")
OUTPUT_RASTER_3 = os.path.join(OUTPUTPATH, "raster/outras3")

V100_YR_SURF_DIFF_SHP = os.path.join(OUTPUTPATH, "100_yr_Surf_Diff.shp")
V100_YR_RUNUP_BDY_SHP = os.path.join(OUTPUTPATH, "100yr_Runup_bdy.shp")
VA_SURF_DIFF_SHP = os.path.join(OUTPUTPATH, "VA_Surf_Diff.shp")
VA_BDY_SHP = os.path.join(OUTPUTPATH, "VA_bdy.shp")
LIMWA_SURF_DIFF_SHP = os.path.join(OUTPUTPATH, "LiMWA_Surf_Diff.shp")
LIMWA_BDY_SHP = os.path.join(OUTPUTPATH, "LiMWA_bdy.shp")

FIELD_ARGS = "FID FID VISIBLE NONE;Shape Shape VISIBLE NONE;Id Id VISIBLE NONE;\
              100Bry_ele 100Bry_ele VISIBLE NONE;VAGut_ele VAGut_ele VISIBLE NONE;\
              LIMWA_ele LIMWA_ele VISIBLE NONE;100Bry_Def 100Bry_Def VISIBLE NONE;\
              VAGut_Def VAGut_Def VISIBLE NONE;HYDROID HYDROID VISIBLE NONE;\
              Notes Notes VISIBLE NONE;Highest_WH Highest_WH VISIBLE NONE;\
              MAP_1stBFE MAP_1stBFE VISIBLE NONE;MAP_1stZON MAP_1stZON VISIBLE NONE;\
              Map_1stSOU Map_1stSOU VISIBLE NONE;LIMWA_Def LIMWA_Def VISIBLE NONE"

def main():
    """ DOC STRING """
    # Make Feature Layers
    arcpy.MakeFeatureLayer_management(INPUTDATA.MAPPING_METHOD_POLYGON, # in_features
                                      MAPPING_METHOD_LAYER_1, # out_layer
                                      "\"100Bry_ele\" <> 0", # where_clause
                                      "", # workspace
                                      FIELD_ARGS)
    arcpy.MakeFeatureLayer_management(INPUTDATA.MAPPING_METHOD_POLYGON,
                                      MAPPING_METHOD_LAYER_2,
                                      "\"VAGut_ele\" <> 0",
                                      "",
                                      FIELD_ARGS)
    arcpy.MakeFeatureLayer_management(INPUTDATA.MAPPING_METHOD_POLYGON,
                                      MAPPING_METHOD_LAYER_3,
                                      "\"LIMWA_ele\" <> 0",
                                      "",
                                      FIELD_ARGS)

    # Convert Polygons to Rasters
    arcpy.PolygonToRaster_conversion(MAPPING_METHOD_LAYER_1,
                                     "100Bry_ele",
                                     V100_YR_RAS,
                                     "CELL_CENTER",
                                     "NONE",
                                     "25")
    arcpy.PolygonToRaster_conversion(MAPPING_METHOD_LAYER_2,
                                     "VAGut_ele",
                                     VA_RAS,
                                     "CELL_CENTER",
                                     "NONE",
                                     "25")
    arcpy.PolygonToRaster_conversion(MAPPING_METHOD_LAYER_3,
                                     "LIMWA_ele",
                                     LIMWA_RAS,
                                     "CELL_CENTER",
                                     "NONE",
                                     "25")

    # Convert Rasters to TINs
    arcpy.RasterTin_3d(V100_YR_RAS,
                       V100_YR_TIN,
                       "0.01",
                       "1500000",
                       "1")
    arcpy.RasterTin_3d(VA_RAS,
                       VA_TIN,
                       "0.01",
                       "1500000",
                       "1")
    arcpy.RasterTin_3d(LIMWA_RAS,
                       LIMWA_TIN,
                       "0.01",
                       "1500000",
                       "1")

    # Calculate Surface Difference new TINs vs. TERRAIN
    arcpy.SurfaceDifference_3d(V100_YR_TIN,
                               INPUTDATA.TERRAIN,
                               V100_YR_SURF_DIFF_SHP,
                               "0", "0",
                               OUTPUT_RASTER_1,
                               "10", "", "")
    arcpy.SurfaceDifference_3d(VA_TIN,
                               INPUTDATA.TERRAIN,
                               VA_SURF_DIFF_SHP,
                               "0", "0",
                               OUTPUT_RASTER_2,
                               "10", "", "")
    arcpy.SurfaceDifference_3d(LIMWA_TIN,
                               INPUTDATA.TERRAIN,
                               LIMWA_SURF_DIFF_SHP,
                               "0", "0",
                               OUTPUT_RASTER_3,
                               "10", "", "")

    # Process: Polygon To Line
    arcpy.PolygonToLine_management(V100_YR_SURF_DIFF_SHP,
                                   V100_YR_RUNUP_BDY_SHP,
                                   "IDENTIFY_NEIGHBORS")
    arcpy.PolygonToLine_management(VA_SURF_DIFF_SHP,
                                   VA_BDY_SHP,
                                   "IDENTIFY_NEIGHBORS")
    arcpy.PolygonToLine_management(LIMWA_SURF_DIFF_SHP,
                                   LIMWA_BDY_SHP,
                                   "IDENTIFY_NEIGHBORS")

if __name__ == '__main__':
    main()
