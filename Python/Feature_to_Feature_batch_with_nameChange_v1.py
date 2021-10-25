# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 09:44:28 2021

@author: oc3512
"""
# Note that you need to add featuer layers to be copied in the Contents panel of ArcGIS Pro with no Grouping.
# If the layers are added to some group, it will fail. WHY?
import time, os, datetime, sys, logging, logging.handlers, shutil, traceback, re
import arcpy

arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

#workspace = r'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/MMSP/001-CIVIL.gdb'

# choose feature layers
workSpace = arcpy.GetParameterAsText(0)
inFeatures = arcpy.GetParameterAsText(1) # multiple Table View
projectName = arcpy.GetParameterAsText(2)

#
FeatureList = list(inFeatures.split(";"))
arcpy.AddMessage(FeatureList)

#
for layers in FeatureList:
    outLocation = workSpace
   #baseN = os.path.basename(layers)
    outFeatureClass = projectName + "_" + layers
    
    # Execute FeatureClassToFeatureClass
    arcpy.FeatureClassToFeatureClass_conversion(layers, outLocation, outFeatureClass)
    