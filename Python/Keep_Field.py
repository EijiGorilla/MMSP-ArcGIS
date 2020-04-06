# -*- coding: utf-8 -*-
"""
Created on Fri Jan 24 14:13:24 2020

This script keeps only field names of your choice and removes all the other fields in batch (multiple feature layers)

@author: Eiji Matsuzaki
"""

import arcpy
import re
import os

arcpy.env.overwriteOutput = True
#arcpy.env.workspace = r"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/NSCR-Backup.gdb"

# Set parameter
workSpace = arcpy.GetParameterAsText(0) # Workspace (gdb)
inFeature = arcpy.GetParameterAsText(1) # The batch only works when input feature layer is added to the Contents (just rule)
KeepField = arcpy.GetParameterAsText(2) # Field

#workSpace = r"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/NSCR-Backup.gdb"
#inFeature = 'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/NSCR-Backup.gdb/Parcellary_AsBuilt/ANGELES_ASBUILT_version1'
#KeepField = "StrucID;Struc_ID"

arcpy.env.workspace = workSpace

# Define keep field in a list
KeepFieldList = list(KeepField.split(";"))
NonDeletable = ['Shape','Shape_Length','Shape_Area','OBJECTID','GlobalID']
KeepFieldList = KeepFieldList + NonDeletable

FeatureList = list(inFeature.split(";"))


#arcpy.AddMessage(FeatureList)
#fieldNames = [f.name for f in arcpy.ListFields(inFeature)]
#dropField = [e for e in fieldNames if e not in KeepFieldList]
#if len(dropField ) == 0:
#    arcpy.AddMessage("{}: No Dropped Field".format(inFeature))
#else:
#    arcpy.DeleteField_management(inFeature,dropField)

###
    
#arcpy.AddMessage(inFeature)
for nn in FeatureList:
    fieldNames = [f.name for f in arcpy.ListFields(nn)]
    arcpy.AddMessage(fieldNames)
    dropField = [e for e in fieldNames if e not in KeepFieldList]
    if len(dropField) == 0:
        arcpy.AddMessage("{}: No Dropped Field".format(inFeature))
    else:
        arcpy.DeleteField_management(nn,dropField)
