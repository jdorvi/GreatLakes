""" Gt_Lakes_Mapping_Tool.py input file"""
# Set input paths for county being mapped
import os

# Study directory
SOURCE_DIRECTORY = "P:/02/NY/Chautauqua_Co_36013C/STUDY__TO90"

# Location of mapping method polygon shapefile
MAPPING_METHOD_POLYGON = os.path.join(SOURCE_DIRECTORY,
                                      "TECHNICAL/ENG_FLOOD_HAZ_DEV/COASTAL/MAPPING/Chautauqua_NY_Mapping_Method.shp")

# Location of terrain
TERRAIN = os.path.join(SOURCE_DIRECTORY,
                       "GIS/DATA/TOPO/Terrain/Chautauqua_Terrain.gdb/NAVD88_Terrain")
