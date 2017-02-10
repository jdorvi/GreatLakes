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

# Get input file location from commandline args
try:
    INPUTFILE = sys.argv[1]
except IndexError:
    INPUTFILE = input("Name of input file(with quotes)? ")

try:
    with open(INPUTFILE) as f:
        INPUTDATA = imp.load_source('INPUTDATA', '', f)
except ImportError:
    print("Could not find properly formatted input file.")

print(INPUTDATA.TERRAIN)