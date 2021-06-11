# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 21:37:09 2019
This python code updated status of land and structure acquisition and relocation status of NLO/LO for N2

@author: oc3512
"""
## CAUTION
# 1. Make sure that data type matches between master list excel table and existing feature layers for all field names
import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True

#arcpy.env.workspace="C:/Users/matsuzaki_a48/Documents/ArcGIS/Packages/Environmental_Team_88be65/Land_Acquisition.sde"

# Script parameters
workSpace = arcpy.GetParameterAsText(0)
inputLayerLot = arcpy.GetParameterAsText(1)
inputLayerStruc = arcpy.GetParameterAsText(2)
inputLayerOccup = arcpy.GetParameterAsText(3)
inputLayerISF = arcpy.GetParameterAsText(4)
inputListLot = arcpy.GetParameterAsText(5)
inputListStruc = arcpy.GetParameterAsText(6)
inputListISF = arcpy.GetParameterAsText(7)

#workSpace=r"C:/Users/oc3512/Documents/ArcGIS/Projects/Environmental_Team/Land_Acquisition.sde"
#Status1011_Merge = r"gisdata.GISOWNER.Parcellary_Status_4"
#MasterList_xlsx = r"C:/Users/oc3512/OneDrive/Masterlist/Land_Acquisition/MasterList.xlsx/MasterList$"

arcpy.env.workspace = workSpace

###########################################################################
##### STAGE 1: Update Existing Parcellary & Structure Feature Layers ######
###########################################################################

# 1. Copy Feature Layer
copyNameLot = 'LA_Temp'
copyNameStruc = 'Struc_Temp'

copyLot = arcpy.CopyFeatures_management(inputLayerLot, copyNameLot)
copyStric = arcpy.CopyFeatures_management(inputLayerStruc, copyNameStruc)

arcpy.AddMessage("Stage 1: Copy feature layer was success")

# 2. Delete Field
fieldNameLot = [f.name for f in arcpy.ListFields(copyLot)]
fieldNameStruc = [f.name for f in arcpy.ListFields(copyStruc)]

arcpy.AddMessage("Stage 1: Delete Field was success")

## 2.1. Identify fields to be dropped
dropFieldLot = [e for e in fieldNameLot if e not in ('Id', 'ID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
dropFieldStruc = [e for e in fieldNameStruc if e not in ('StrucID', 'ID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]

## 2.2. Extract existing fields
inFieldLot = [f.name for f in arcpy.ListFields(copyLot)]
inFieldStruc = [f.name for f in arcpy.ListFields(copyStruc)]

arcpy.AddMessage("Stage 1: Extract existing fields was success")

## 2.3. Check if there are fields to be dropped
finalDropFieldLot = [f for f in inFieldLot if f in tuple(dropFieldLot)]
finalDropFieldStruc = [f for f in inFieldStruc if f in tuple(dropFieldStruc)]

arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")

## 2.4 Drop
if len(finalDropFieldLot) == 0:
    arcpy.AddMessage("There is no field that can be dropped from the feature layer")
else:
    arcpy.DeleteField_management(copyLot, finalDropFieldLot)
    
if len(finalDropFieldStruc) == 0:
    arcpy.AddMessage("There is no field that can be dropped from the feature layer")
else:
    arcpy.DeleteField_management(copyStruc, finalDropFieldStruc)

arcpy.AddMessage("Stage 1: Dropping Fields was success")
arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

# 3. Join Field
## 3.1. Convert Excel tables to feature table
MasterListLot = arcpy.TableToTable_conversion(inputListLot, workSpace, 'MasterListLot')
MasterListStruc = arcpy.TableToTable_conversion(inputListStruc, workSpace, 'MasterListStruc')

## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
inputFieldLot = [f.name for f in arcpy.ListFields(MasterListLot)]
inputFieldStruc = [f.name for f in arcpy.ListFields(MasterListStruc)]

joinFieldLot = [e for e in inputFieldLot if e not in ('Id', 'ID','OBJECTID')]
joinFieldStruc = [e for e in inputFieldStruc if e not in ('Id', 'ID','OBJECTID')]

## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tLot = [f.name for f in arcpy.ListFields(copyLot)]
tStruc = [f.name for f in arcpy.ListFields(copyStruc)]

in_fieldLot = ' '.join(map(str, [f for f in tLot if f in ('Id','ID')]))
in_fieldStruc = ' '.join(map(str, [f for f in tStruc if f in ('StrucID', 'strucID')]))
 
uLot = [f.name for f in arcpy.ListFields(MasterListLot)]
uStruc = [f.name for f in arcpy.ListFields(MasterListStruc)]

join_fieldLot=' '.join(map(str, [f for f in uLot if f in ('Id','ID')]))
join_fieldStruc = ' '.join(map(str, [f for f in uStruc if f in ('StrucID', 'strucID')]))

## 3.4 Join
arcpy.JoinField_management(in_data=copyLot, in_field=in_fieldLot, join_table=MasterListLot, join_field=join_fieldLot, fields=joinFieldLot)
arcpy.JoinField_management(in_data=copyStruc, in_field=in_fieldStruc, join_table=MasterListStruc, join_field=join_fieldStruc, fields=joinFieldStruc)

# 4. Trucnate
arcpy.TruncateTable_management(inputLayerLot)
arcpy.TruncateTable_management(inputLayerStruc)

# 5. Append
arcpy.Append_management(copyLot, inputLayerLot,schema_type = 'NO_TEST')
arcpy.Append_management(copyStruc, inputLayerStruc, schema_type = 'NO_TEST')

###########################################################################
##### STAGE 2: Update Existing Structure (Occupancy) & Structure (ISF) ######
###########################################################################

# STAGE: 2-1. Create Structure (point) for Occupany
## 2-1.1. Feature to Point for Occupany
outFeatureClassPointStruc = 'Structure_point_occupancy_temp'
pointStruc = arcpy.FeatureToPoint_management(inputLayerStruc, outFeatureClassPointStruc, "CENTROID")

## 2-1.2. Add XY Coordinates
arcpy.AddXY_management(pointStruc)

## 2-1.3. Truncate original point structure layer (Occupancy)
arcpy.TruncateTable_management(inputLayerOccup)

## 2-1.4. Append to the original FL
arcpy.Append_management(pointStruc, inputLayerStruc, schema_type = 'NO_TEST')


# STAGE: 2-2. Create and Update ISF Feture Layer
## 2-2.1. Convert ISF (Relocation excel) to Feature table
MasterListISF = arcpy.TableToTable_conversion(inputListISF workSpace, 'MasterListISF')

## 2-2.2. Get Join Field from MasterList gdb table: Gain all fields except 'StrucId'
inputFieldISF = [f.name for f in arcpy.ListFields(MasterListISF)]
joinFieldISF = [e for e in inputFieldISF if e not in ('StrucId', 'strucID','OBJECTID')]

## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tISF = [f.name for f in arcpy.ListFields(inputLayerOccup)]
in_fieldISF= ' '.join(map(str, [f for f in tISF if f in ('StrucId','strucID')]))
 
uISF = [f.name for f in arcpy.ListFields(MasterListISF)]
join_fieldISF = ' '.join(map(str, [f for f in uISF if f in ('StrucID', 'strucID')]))

## Join
xCoords = "POINT_X"
yCoords = "POINT_Y"

arcpy.JoinField_management(in_data=MasterListISF, in_field=join_fieldISF, join_table=inputLayerOccup, join_field=in_fieldISF, fields=[xCoords, yCoords])

## 2-2.3. XY Table to Points (FL)
out_feature_class = "Status_for_Relocation_ISF_temp"
outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords)

## 2-2.4. Add Domain

## 2-2.5. Truncate original ISF point FL
arcpy.TruncateTable_management(inputLayerISF)

## 2-2.6. Append to the Original ISF
arcpy.Append_management(outLayerISF, inputLayerISF, schema_type = 'NO_TEST')


# Delete the copied feature layer
#arcpy.Delete_management(deleteCopy)

