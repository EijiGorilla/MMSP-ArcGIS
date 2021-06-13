# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 21:37:09 2019
This python code updated status of land and structure acquisition and relocation status of NLO/LO for N2

Note that main difficult is 'Append' geoprocessing tool. Please run this code to only local geodatabase files
** Registered geodatabase have a few unique field names, which may give rise to geprocessing error for Append
@author: oc3512
"""
## CAUTION
# 1. Make sure that data type matches between master list excel table and existing feature layers for all field names
import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True


# Script parameters
workSpace = arcpy.GetParameterAsText(0)
inputLayerLot = arcpy.GetParameterAsText(1)
inputLayerStruc = arcpy.GetParameterAsText(2)
inputLayerOccup = arcpy.GetParameterAsText(3)
inputLayerISF = arcpy.GetParameterAsText(4)
inputListLot = arcpy.GetParameterAsText(5)
inputListStruc = arcpy.GetParameterAsText(6)
inputListISF = arcpy.GetParameterAsText(7)
inputLayerLotOrigin = arcpy.GetParameterAsText(8)
inputLayerStrucOrigin = arcpy.GetParameter(9)
inputLayerOccupOrigin = arcpy.GetParameterAsText(10)
inputLayerISFOrigin = arcpy.GetParameterAsText(11)

#workSpace=r"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
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
copyStruc = arcpy.CopyFeatures_management(inputLayerStruc, copyNameStruc)

arcpy.AddMessage("Stage 1: Copy feature layer was success")

# 2. Delete Field
fieldNameLot = [f.name for f in arcpy.ListFields(copyLot)]
fieldNameStruc = [f.name for f in arcpy.ListFields(copyStruc)]

## 2.1. Identify fields to be dropped
dropFieldLot = [e for e in fieldNameLot if e not in ('LotId', 'LotID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
dropFieldStruc = [e for e in fieldNameStruc if e not in ('StrucID', 'strucID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]

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

joinFieldLot = [e for e in inputFieldLot if e not in ('LotId', 'LotID','OBJECTID')]
joinFieldStruc = [e for e in inputFieldStruc if e not in ('StrucID', 'strucID','OBJECTID')]

## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tLot = [f.name for f in arcpy.ListFields(copyLot)]
tStruc = [f.name for f in arcpy.ListFields(copyStruc)]

in_fieldLot = ' '.join(map(str, [f for f in tLot if f in ('LotId', 'LotID')]))
in_fieldStruc = ' '.join(map(str, [f for f in tStruc if f in ('StrucID', 'strucID')]))
 
uLot = [f.name for f in arcpy.ListFields(MasterListLot)]
uStruc = [f.name for f in arcpy.ListFields(MasterListStruc)]

join_fieldLot=' '.join(map(str, [f for f in uLot if f in ('LotId', 'LotID')]))
join_fieldStruc = ' '.join(map(str, [f for f in uStruc if f in ('StrucID', 'strucID')]))

## 3.4 Join
arcpy.JoinField_management(in_data=copyLot, in_field=in_fieldLot, join_table=MasterListLot, join_field=join_fieldLot, fields=joinFieldLot)
arcpy.JoinField_management(in_data=copyStruc, in_field=in_fieldStruc, join_table=MasterListStruc, join_field=join_fieldStruc, fields=joinFieldStruc)

# 4. Trucnate
arcpy.TruncateTable_management(inputLayerLot)
arcpy.TruncateTable_management(inputLayerStruc)

# 5. Append
arcpy.Append_management(copyLot, inputLayerLot, schema_type = 'NO_TEST')
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
arcpy.Append_management(pointStruc, inputLayerOccup, schema_type = 'NO_TEST')


# STAGE: 2-2. Create and Update ISF Feture Layer
## 2-2.1. Convert ISF (Relocation excel) to Feature table
MasterListISF = arcpy.TableToTable_conversion(inputListISF, workSpace, 'MasterListISF')

## 2-2.2. Get Join Field from MasterList gdb table: Gain all fields except 'StrucId'
inputFieldISF = [f.name for f in arcpy.ListFields(MasterListISF)]
joinFieldISF = [e for e in inputFieldISF if e not in ('StrucId', 'strucID','OBJECTID')]

## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tISF = [f.name for f in arcpy.ListFields(inputLayerOccup)] # Note 'inputLayerOccup' must be used, not ISF
in_fieldISF= ' '.join(map(str, [f for f in tISF if f in ('StrucID','strucID')]))
 
uISF = [f.name for f in arcpy.ListFields(MasterListISF)]
join_fieldISF = ' '.join(map(str, [f for f in uISF if f in ('StrucID', 'strucID')]))

## Join
xCoords = "POINT_X"
yCoords = "POINT_Y"
zCoords = "POINT_Z"

# Join only 'POINT_X' and 'POINT_Y' in the 'inputLayerOccup' to 'MasterListISF'
arcpy.JoinField_management(in_data=MasterListISF, in_field=join_fieldISF, join_table=inputLayerOccup, join_field=in_fieldISF, fields=[xCoords, yCoords, zCoords])

## 2-2.3. XY Table to Points (FL)
out_feature_class = "Status_for_Relocation_ISF_temp"
sr = arcpy.SpatialReference(32651)
outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords, zCoords, sr)


### Delete 'POINT_X', 'POINT_Y', 'POINT_Z'; otherwise, it gives error for the next batch
dropXYZ = [xCoords, yCoords, zCoords]
arcpy.DeleteField_management(outLayerISF, dropXYZ)

## 2-2.4. Add Domain

## 2-2.5. Truncate original ISF point FL
arcpy.TruncateTable_management(inputLayerISF)

## 2-2.6. Append to the Original ISF
arcpy.Append_management(outLayerISF, inputLayerISF, schema_type = 'NO_TEST')



###########################################################################
##### STAGE 3: Convert 0 to Null ######
###########################################################################
paid = "Paid"
handOver = "HandOver"
moa = "MoA"
relocated = "Relocated"
status = "Status"
pte = "PTE"

varFieldLA = [paid, handOver, moa, pte]
varFieldStruc = [paid, handOver, moa, status, pte]
varFieldOccup= [paid, moa, status]
varFieldISF = [paid, relocated]

codeblock = """
def reclass(status):
    if status == None:
        return None
    elif status == 0:
        return None
    else:
        return status"""

# Apply to four layers: 'Status for LA', 'Status of Structure', 'Status of Relocation (occupany)', and
# 'Status for Relocation (ISF)'

## 1. Status for LA
for field in varFieldLA:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerLot, field, expression, "PYTHON3", codeblock)

## 2. Status for Structure
for field in varFieldStruc:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerStruc, field, expression, "PYTHON3", codeblock)

## 2. Status for Relocation (Occupancy)
for field in varFieldOccup:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerOccup, field, expression, "PYTHON3", codeblock)
    
## 3. Status for Relocation (ISF)
for field in varFieldISF:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerISF, field, expression, "PYTHON3", codeblock)    
    
    

# Delete the copied feature layer
deleteTempLayers = [copyLot, copyStruc, pointStruc, outLayerISF, MasterListLot, MasterListStruc, MasterListISF]
arcpy.Delete_management(deleteTempLayers)


###########################################################################
##### STAGE 4: Append all to Original Layers ######
###########################################################################
# 4-1. Truncate Original Feature layers
arcpy.TruncateTable_management(inputLayerLotOrigin)
arcpy.TruncateTable_management(inputLayerStrucOrigin)
arcpy.TruncateTable_management(inputLayerOccupOrigin)
arcpy.TruncateTable_management(inputLayerISFOrigin)

## 2-2.6. Append to the Original ISF
arcpy.Append_management(inputLayerLot, inputLayerLotOrigin, schema_type = 'NO_TEST')
arcpy.Append_management(inputLayerStruc, inputLayerStrucOrigin, schema_type = 'NO_TEST')
arcpy.Append_management(inputLayerOccup, inputLayerOccupOrigin, schema_type = 'NO_TEST')
arcpy.Append_management(inputLayerISF, inputLayerISFOrigin, schema_type = 'NO_TEST')
