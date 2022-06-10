# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 10:08:44 2022

@author: emasu
"""

"""
This Python code updates feature layer using an excel master list
The main steps are:
    1. Copy featurey layer
    2. Delete field names EXCEPT an unique ID from the copied feature layer
    3. Join the excel master list to the copied feature layer
    4. Truncate the original feature layer
    5. Append the copied to the original feature layer
"""

import arcpy
import re

# Define Parameters
 ## To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True


# Script parameters
#C:/Users/emasu/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb
workSpace = arcpy.GetParameterAsText(0)
inputLayerOrigin = arcpy.GetParameterAsText(1)
inputML = arcpy.GetParameterAsText(2)
joinField = arcpy.GetParameterAsText(3)

# 1. Copy feature layer
copyLayer = 'copiedLayer'

copiedL = arcpy.CopyFeatures_management(inputLayerOrigin, copyLayer)

# 2. Delete Field
fieldNames= [f.name for f in arcpy.ListFields(copiedL)]

## 2.1. Identify fields to be droppeds
baseField = ['Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','OBJECTID_1','GlobalID']
fieldsKeep = tuple([joinField]) + tuple(baseField)

dropField = [e for e in fieldNames if e not in fieldsKeep]

## 2.2. Extract existing fields
inField = [f.name for f in arcpy.ListFields(copiedL)]

arcpy.AddMessage("Stage 1: Extract existing fields was success")

## 2.3. Check if there are fields to be dropped
finalDropField = [f for f in inField if f in tuple(dropField)]

arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")

## 2.4 Drop
if len(finalDropField) == 0:
    arcpy.AddMessage("There is no field that can be dropped from the feature layer")
else:
    arcpy.DeleteField_management(copiedL, finalDropField)
    
arcpy.AddMessage("Stage 1: Dropping Fields was success")
arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

# 3. Join Field
## 3.1. Convert Excel tables to feature table
MasterList = arcpy.TableToTable_conversion(inputML, workSpace, 'MasterList')

## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
inputField = [f.name for f in arcpy.ListFields(MasterList)]

toBeJoinedField = tuple([joinField]) + tuple(['OBJECTID'])
joiningField = [e for e in inputField if e not in toBeJoinedField]

## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tLot = [f.name for f in arcpy.ListFields(copiedL)]

in_field = ' '.join(map(str, [f for f in tLot if f in tuple([joinField])]))
uLot = [f.name for f in arcpy.ListFields(MasterList)]

join_field=' '.join(map(str, [f for f in uLot if f in tuple([joinField])]))

## 3.4 Join
arcpy.JoinField_management(in_data=copiedL, in_field=in_field, join_table=MasterList, join_field=join_field, fields=joiningField)

# 4. Trucnate
arcpy.TruncateTable_management(inputLayerOrigin)

# 5. Append
arcpy.Append_management(copiedL, inputLayerOrigin, schema_type = 'NO_TEST')

# Delete the copied feature layer
deleteTempLayers = [copiedL, MasterList]
arcpy.Delete_management(deleteTempLayers)

