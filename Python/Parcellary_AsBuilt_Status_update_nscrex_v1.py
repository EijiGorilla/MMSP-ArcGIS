# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 21:37:09 2019

@author: oc3512
"""
## CAUTION
# 1. Make sure that data type matches between master list excel table and existing feature layers for all field names
# 2. This script does not work on hosted feature layers.



import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
#arcpy.env.workspace="C:/Users/matsuzaki_a48/Documents/ArcGIS/Packages/Environmental_Team_88be65/Land_Acquisition.sde"

# Script parameters
workSpace = arcpy.GetParameterAsText(0)
featureLayer = arcpy.GetParameterAsText(1)
MasterList_xlsx = arcpy.GetParameterAsText(2)
joinFieldID = arcpy.GetParameterAsText(3)

#workSpace=r"C:/Users/oc3512/Documents/ArcGIS/Projects/Environmental_Team/Land_Acquisition.sde"
#featureLayer = r"gisdata.GISOWNER.Parcellary_Status_4"
#MasterList_xlsx = r"C:/Users/oc3512/OneDrive/Masterlist/Land_Acquisition/MasterList.xlsx/MasterList$"

arcpy.env.workspace = workSpace

###################################
# 1. Copy Feature Layer
###################################
copyFeatureName = 'LAR_Status_Temp'
copyStatus = arcpy.CopyFeatures_management(featureLayer, copyFeatureName)

#######################################################
# 2. Delete Field from Copyied Feature Layer
#######################################################
# Get drop fields: exclude arcgis default fields: id, shape,...
fieldNames=[f.name for f in arcpy.ListFields(copyStatus)]

reg=re.compile(r"shape|SHAPE|Shape|OBJECTID|object|Object|OBJECT|Global|global|GLOBAL")
requiredField = list(filter(reg.match, fieldNames))
requiredFieldPlus = requiredField + [joinFieldID, joinFieldID.upper(), joinFieldID.lower(), joinFieldID.title(), "FID"]

dropField = [e for e in fieldNames if e not in requiredFieldPlus]

arcpy.DeleteField_management(copyStatus,dropField)

#######################################################
# 3. Convert MasterList.xlsx to Enterprise geodatabase table
#######################################################
# 3. Convert MasterList.xlsx to gdb table (use 'Table to Table' geoprocessing tool)
arcpy.TableToTable_conversion(MasterList_xlsx, workSpace, 'MasterList')

#######################################################
# 4. Join Master List to Copied Feature Layer
#######################################################
## Extract a list of geodatabase tables
tableList=arcpy.ListTables("*")

## Extract only MasterList geodatabase table
r=re.compile(".*Master")
rList = list(filter(r.match, tableList))
MasterList=''.join(rList)

# 4. Join Field
## Get Join Field from MasterList gdb table: Gain all fields except 'Id'
inputField=[f.name for f in arcpy.ListFields(MasterList)]
joinFields = [e for e in inputField if e not in (joinFieldID, joinFieldID.upper(),'OBJECTID')]

## Extract a Field from MasterList and Feature Layer to be used to join two tables
t=[f.name for f in arcpy.ListFields(copyStatus)]
in_field=' '.join(map(str, [f for f in t if f in (joinFieldID, joinFieldID.upper())]))
 
u=[f.name for f in arcpy.ListFields(MasterList)]
join_field=' '.join(map(str, [f for f in u if f in (joinFieldID, joinFieldID.upper())]))

## Execute Join
arcpy.JoinField_management(in_data=copyStatus, in_field=in_field, join_table=MasterList, join_field=join_field, fields=joinFields)

#######################################################
# 5. Truncate or Delete Original Feature Layer
#######################################################
#featureLayer=r"gisdata.GISOWNER.Parcellary_Status"
#Note that if the feature layer is 'hosted' and 'Related', you must use 'Delete all' instead of Truncate

## Check if the feature Layer is 'hosted' or not
desc = arcpy.Describe(featureLayer)
pathFL = desc.path
reg = re.compile(r'https://services')
m  = reg.findall(pathFL)

## note that 'Status for relocation' (points) is related to the relocation table
## this ponint FL cannot be used with 'Truncate'
reg1 = re.compile(r'points|Points|point|Point')
m1 = reg1.findall(featureLayer)


if len(m) > 0 and len(m1) > 0:
    arcpy.management.DeleteRows(featureLayer)
else:
    arcpy.TruncateTable_management(featureLayer)

##########################################################
# 6. Append copied feature layer to original feature layer
##########################################################
arcpy.Append_management(copyStatus, featureLayer,schema_type = 'NO_TEST')

##########################################################
# 9. Delete Copied feature layer
##########################################################
# List of Copied Feature Layer
fcList=arcpy.ListFeatureClasses()

# Extract copied feature layer name
rr=re.compile('.*' + format(copyFeatureName))
rList = list(filter(rr.match, fcList))
deleteCopy = ''.join(rList)

# Delete the copied feature layer
arcpy.Delete_management(deleteCopy)

del copyStatus
del tableList
del MasterList
del deleteCopy