# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 21:37:09 2019
This python code updated status of land acquisition

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
inputLayerLotOrigin = arcpy.GetParameterAsText(1)
inputLayerStrucOrigin = arcpy.GetParameter(2)
inputLayerOccupOrigin = arcpy.GetParameterAsText(3)
inputLayerISFOrigin = arcpy.GetParameterAsText(4)
inputLayerN2PierOrigin = arcpy.GetParameterAsText(5)
#inputLayerBarangOrigin = arcpy.GetParameter(5)

inputListLot = arcpy.GetParameterAsText(6)
inputListStruc = arcpy.GetParameterAsText(7)
inputListISF = arcpy.GetParameterAsText(8)
inputListN2Pier = arcpy.GetParameterAsText(9)
#inputListBarangay = arcpy.GetParameterAsText(9)


#workSpace=r"C:/Users/emasu/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
#Status1011_Merge = r"gisdata.GISOWNER.Parcellary_Status_4"
#MasterList_xlsx = r"C:/Users/oc3512/OneDrive/Masterlist/Land_Acquisition/MasterList.xlsx/MasterList$"

arcpy.env.workspace = workSpace

###################### DEFINE COMMON ID

###########################################################################
##### STAGE 1: Update Existing Parcellary & Structure Feature Layers ######
###########################################################################
   

"""
# For Barangay, we will create separate package, as this may be used for contractors submission for only SC
copyNameBarang = 'Brang_Temp'
copyBarang = arcpy.CopyFeatures_management(inputLayerBarangOrigin, copyNameBarang)
  
# 2. Delete Field
fieldNameBarang = [f.name for f in arcpy.ListFields(copyBarang)]
    
## 2.1. Identify fields to be dropped
dropFieldBarang = [e for e in fieldNameBarang if e not in ('Barangay', 'barangay','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
    
## 2.2. Extract existing fields
inFieldBarang = [f.name for f in arcpy.ListFields(copyBarang)]
    
arcpy.AddMessage("Stage 1: Extract existing fields was success")
    
## 2.3. Check if there are fields to be dropped
finalDropFieldBarang = [f for f in inFieldBarang if f in tuple(dropFieldBarang)]
    
arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")
    
## 2.4 Drop
if len(finalDropFieldBarang) == 0:
   arcpy.AddMessage("There is no field that can be dropped from the feature layer")
else:
   arcpy.DeleteField_management(copyBarang, finalDropFieldBarang)
   
arcpy.AddMessage("Stage 1: Dropping Fields was success")
arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")
   
# 3. Join Field
## 3.1. Convert Excel tables to feature table
MasterListBarang = arcpy.TableToTable_conversion(inputListBarangay, workSpace, 'MasterListBarang')
    
## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
inputFieldBarang = [f.name for f in arcpy.ListFields(MasterListBarang)]
    
joinFieldBarang = [e for e in inputFieldBarang if e not in ('Barangay', 'strucID','OBJECTID')]
    
## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tBarang = [f.name for f in arcpy.ListFields(copyBarang)]
    
in_fieldBarang = ' '.join(map(str, [f for f in tBarang if f in ('Barangay','barangay')]))
  
uBarang = [f.name for f in arcpy.ListFields(MasterListBarang)]
    
join_fieldBarang = ' '.join(map(str, [f for f in uBarang if f in ('Barangay', 'barangay')]))
    
## 3.4 Join
arcpy.JoinField_management(in_data=copyBarang, in_field=in_fieldBarang, join_table=MasterListBarang, join_field=join_fieldBarang, fields=joinFieldBarang)
    
# 4. Trucnate
arcpy.TruncateTable_management(inputLayerBarangOrigin)

# 5. Append
arcpy.Append_management(copyBarang, inputLayerBarangOrigin, schema_type = 'NO_TEST')
"""


########################### Process for updating N2 Pier ##############################
# 1. Copy
try:
    copyNameN2Pier = 'N2_Pier_test'
    copyN2Pier = arcpy.CopyFeatures_management(inputLayerN2PierOrigin, copyNameN2Pier)
    
    # 2. Delete fields: 'Municipality' and 'AccessDate'
    fieldNameN2Pier = [f.name for f in arcpy.ListFields(copyN2Pier)]
    
    ## 2.1. Fields to be dropped
    dropFieldN2Pier = [e for e in fieldNameN2Pier if e not in ('PIER','CP','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
    
    ## 2.2 Extract existing fields
    inFieldN2Pier = [f.name for f in arcpy.ListFields(copyN2Pier)]
    
    ## 2.3. Check if there are fields to be dropped
    finalDropFieldN2Pier = [f for f in inFieldN2Pier if f in tuple(dropFieldN2Pier)]
    
    ## 2.4 Drop
    if len(finalDropFieldN2Pier) == 0:
        arcpy.AddMessage("There is no field that can be dropped from the feature layer")
    else:
        arcpy.DeleteField_management(copyN2Pier, finalDropFieldN2Pier)
        
    # 3. Join Field
    ## 3.1. Convert Excel tables to feature table
    MasterListN2Pier = arcpy.TableToTable_conversion(inputListN2Pier, workSpace, 'MasterListN2Pier')
    
    ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
    inputFieldN2Pier = [f.name for f in arcpy.ListFields(MasterListN2Pier)]
    joinFieldN2Pier = [e for e in inputFieldN2Pier if e not in ('PIER', 'Pier','OBJECTID')]
    
    ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
    tN2Pier = [f.name for f in arcpy.ListFields(copyN2Pier)]
    in_fieldN2Pier = ' '.join(map(str, [f for f in tN2Pier if f in ('PIER', 'Pier')]))
    
    uN2Pier = [f.name for f in arcpy.ListFields(MasterListN2Pier)]
    join_fieldN2Pier=' '.join(map(str, [f for f in uN2Pier if f in ('PIER', 'Pier')]))
    
    ## 3.4 Join
    arcpy.JoinField_management(in_data=copyN2Pier, in_field=in_fieldN2Pier, join_table=MasterListN2Pier, join_field=join_fieldN2Pier, fields=joinFieldN2Pier)
    
    # 4. Trucnate
    arcpy.TruncateTable_management(inputLayerN2PierOrigin)
    
    # 5. Append
    arcpy.Append_management(copyN2Pier, inputLayerN2PierOrigin, schema_type = 'NO_TEST')
    
except:
    pass

#######################################################################################
#######################################################################################
    
# 1. Copy Original Feature Layers
    
copyNameLot = 'LA_Temp'
copyNameStruc = 'Struc_Temp'
    
copyLot = arcpy.CopyFeatures_management(inputLayerLotOrigin, copyNameLot)
copyStruc = arcpy.CopyFeatures_management(inputLayerStrucOrigin, copyNameStruc)
    
#copyLot = arcpy.CopyFeatures_management(inputLayerLot, copyNameLot)
#copyStruc = arcpy.CopyFeatures_management(inputLayerStruc, copyNameStruc)
    
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
arcpy.TruncateTable_management(inputLayerLotOrigin)
arcpy.TruncateTable_management(inputLayerStrucOrigin)

# 5. Append
arcpy.Append_management(copyLot, inputLayerLotOrigin, schema_type = 'NO_TEST')
arcpy.Append_management(copyStruc, inputLayerStrucOrigin, schema_type = 'NO_TEST')

 ##########################################################################
 ##### STAGE 2: Update Existing Structure (Occupancy) & Structure (ISF) ######
 ###########################################################################
 ## Copy original feature layer
 
 
 # STAGE: 2-1. Create Structure (point) for Occupany
 ## 2-1.1. Feature to Point for Occupany
outFeatureClassPointStruc = 'Structure_point_occupancy_temp'
pointStruc = arcpy.FeatureToPoint_management(inputLayerStrucOrigin, outFeatureClassPointStruc, "CENTROID")
 
## 2-1.2. Add XY Coordinates
arcpy.AddXY_management(pointStruc)
 
## 2-1.3. Truncate original point structure layer (Occupancy)
arcpy.TruncateTable_management(inputLayerOccupOrigin)

## 2-1.4. Append to the original FL
arcpy.Append_management(pointStruc, inputLayerOccupOrigin, schema_type = 'NO_TEST')


# STAGE: 2-2. Create and Update ISF Feture Layer
## 2-2.1. Convert ISF (Relocation excel) to Feature table
MasterListISF = arcpy.TableToTable_conversion(inputListISF, workSpace, 'MasterListISF')

## 2-2.2. Get Join Field from MasterList gdb table: Gain all fields except 'StrucId'
inputFieldISF = [f.name for f in arcpy.ListFields(MasterListISF)]
joinFieldISF = [e for e in inputFieldISF if e not in ('StrucId', 'strucID','OBJECTID')]

## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
tISF = [f.name for f in arcpy.ListFields(inputLayerOccupOrigin)] # Note 'inputLayerOccupOrigin' must be used, not ISF
in_fieldISF= ' '.join(map(str, [f for f in tISF if f in ('StrucID','strucID')]))

uISF = [f.name for f in arcpy.ListFields(MasterListISF)]
join_fieldISF = ' '.join(map(str, [f for f in uISF if f in ('StrucID', 'strucID')]))

## Join
xCoords = "POINT_X"
yCoords = "POINT_Y"
zCoords = "POINT_Z"

# Join only 'POINT_X' and 'POINT_Y' in the 'inputLayerOccupOrigin' to 'MasterListISF'
arcpy.JoinField_management(in_data=MasterListISF, in_field=join_fieldISF, join_table=inputLayerOccupOrigin, join_field=in_fieldISF, fields=[xCoords, yCoords, zCoords])

## 2-2.3. XY Table to Points (FL)
out_feature_class = "Status_for_Relocation_ISF_temp"
sr = arcpy.SpatialReference(32651)
outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords, zCoords, sr)


### Delete 'POINT_X', 'POINT_Y', 'POINT_Z'; otherwise, it gives error for the next batch
dropXYZ = [xCoords, yCoords, zCoords]
arcpy.DeleteField_management(outLayerISF, dropXYZ)

## 2-2.4. Add Domain
 
## 2-2.5. Truncate original ISF point FL
arcpy.TruncateTable_management(inputLayerISFOrigin)

## 2-2.6. Append to the Original ISF
arcpy.Append_management(outLayerISF, inputLayerISFOrigin, schema_type = 'NO_TEST')

###########################################################################
##### STAGE 3: Convert 0 to Null ######
###########################################################################
paid = "Paid"
handOver = "HandOver"
moa = "MoA"
relocated = "Relocated"
status = "Status"
pte = "PTE"
#barang = "Barangay"

varFieldLA = [paid, handOver, moa, pte]
varFieldStruc = [paid, handOver, moa, status, pte]
varFieldOccup= [paid, moa, status]
varFieldISF = [paid, relocated]
#varFieldBarang = [barang]
 
codeblock = """
def reclass(status):
    if status == None:
        return None
    elif status == 0:
        return None
    else:
        return status"""
    
#Apply to four layers: 'Status for LA', 'Status of Structure', 'Status of Relocation (occupany)', and
# 'Status for Relocation (ISF)'

## 1. Status for LA
for field in varFieldLA:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerLotOrigin, field, expression, "PYTHON3", codeblock)
    
    ## 2. Status for Structure
for field in varFieldStruc:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerStrucOrigin, field, expression, "PYTHON3", codeblock)
 ## 2. Status for Relocation (Occupancy)
for field in varFieldOccup: 
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerOccupOrigin, field, expression, "PYTHON3", codeblock)
    
    ## 3. Status for Relocation (ISF)
for field in varFieldISF:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
    
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerISFOrigin, field, expression, "PYTHON3", codeblock)    

"""
    ## 4. Status for Barangay
for field in varFieldBarang:
    arcpy.AddMessage(field)
    expression = "reclass(!{}!)".format(field)
        
    # Execute CalculateField
    arcpy.CalculateField_management(inputLayerBarangOrigin, field, expression, "PYTHON3", codeblock)  
"""

 # Delete the copied feature layer
deleteTempLayers = [copyLot, copyStruc, pointStruc, outLayerISF, MasterListLot, MasterListStruc, MasterListISF]
arcpy.Delete_management(deleteTempLayers)

