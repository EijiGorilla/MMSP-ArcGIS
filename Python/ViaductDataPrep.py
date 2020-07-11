# -*- coding: utf-8 -*-
"""
Created on Sat Jul 11 10:13:47 2020

@author: oc3512

This python script add field names to individually separated viaduct structures, and
add the structure types, PierNo, and CP. It finally merges the individual layers into a single multipatch.
"""

import arcpy
import os

# Define Parameters
Workspace = arcpy.GetParameterAsText(0)
inputFeatures = arcpy.GetParameterAsText(1) # multiple, Table View
outputFeature = arcpy.GetParameterAsText(2) # Output: Fature Class

#
layerList = list(inputFeatures.split(";"))
arcpy.AddMessage(layerList)

# 
inputFeatureList = ["PILECAP_surface", "C_PIER_CONC_surface", "PILE_surface"]
fieldNamesAdd = ["Type", "PierNo", "CP"]
cpID = "N04"

# Delete Field Names if a feature layer already has above field names.
for layerl in layerList:
    fieldNames=[f.name for f in arcpy.ListFields(layerl)]
    dropField = [e for e in fieldNames if e in fieldNamesAdd]
    if len(dropField) == 0:
        arcpy.AddMessage("{}: No Field to be Dropped".format(layerl))
    else:
        arcpy.DeleteField_management(layerl,dropField)

   
# Add Field Names
for layer in layerList:
    for field in fieldNamesAdd:
        if field == "Type":
            arcpy.AddField_management(layer, field, "DOUBLE")
        else:
            arcpy.AddField_management(layer, field, "TEXT")


# Update Field Names
# with arcpy.da.UpdateCursor(layer, '"OBJECTID" IN {}'.format(strlinst)) as cursor: # you can define query expression  
            
for layer in layerList:
    with arcpy.da.UpdateCursor(layer, fieldNamesAdd) as cursor:
        # row[0]: "Type", row[1]: "PierNo", row[2]: "CP"
        # 1: "Bored Pile", 2: "Pile Cap", 3: "Pier", 4: "Pier Head", 5: "Pre-Cast"
        for row in cursor:
            if layer == inputFeatureList[1]:
                row[0] = 3
                row[2] = cpID
            elif layer == inputFeatureList[2]:
                row[0] = 1
                row[2] = cpID
            elif layer == inputFeatureList[0]:
                row[0] = 2
                row[2] = cpID
            else:
                row[0] = None
                row[2] = cpID
            cursor.updateRow(row)


# Merge
arcpy.Merge_management(layerList, outputFeature)

# Output

