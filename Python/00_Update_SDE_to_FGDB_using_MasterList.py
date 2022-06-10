# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 08:41:44 2021

@author: emasu
"""

# This python script is to copy and convert source feature layer to PRS92 and truncate the target feature layer,
# and finally append the source to the target.fgdb
# This script is intendted to work with only one source (FGDB) and one taget feature layer (SDE).

#
import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"


# Script parameters
# workSpace = r"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexn2/During-Construction_nscrexn2.gdb"
workSpace = arcpy.GetParameterAsText(0)
source_sde = arcpy.GetParameterAsText(1)
target_fgdb = arcpy.GetParameterAsText(2)
MLTable = arcpy.GetParameterAsText(3)
join_Field = arcpy.GetParameterAsText(4)

# 1. Copy the source SDE
copied = "copied_layer"

## 1.1 Check if target_fgdb is 32651 or 3857
sp_target = arcpy.Describe(target_fgdb).spatialReference.factoryCode # WKID
if sp_target == 3857:
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 Web Mercator (auxiliary sphere)")
elif sp_target == 32651:
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 51N")
elif sp_target == 3123:
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")

copyL = arcpy.CopyFeatures_management(source_sde, copied)

# 2. Delete Field the copied SDE
fieldList = [f.name for f in arcpy.ListFields(copyL)]           
dropFieldLot = [e for e in fieldList if e not in (join_Field,'Shape','created_user','created_date','last_edited_user','last_edited_date','OBJECTID','GlobalID')]

arcpy.DeleteField_management(copyL, dropFieldLot)

# 3. Join masterlist table to the copied SDE
## 3.1. Convert Excel tables to feature table
MLTable_sde = arcpy.TableToTable_conversion(MLTable, workSpace, 'MasterListLot')

## 3.1. Identify joined fields from masterlist table
joinedFieldList = [f.name for f in arcpy.ListFields(MLTable_sde)]
joinedFields = [e for e in joinedFieldList if e not in (join_Field,'OBJECTID')]

joinField = join_Field
arcpy.JoinField_management(in_data=copyL, in_field=joinField, join_table=MLTable_sde, join_field=joinField, fields=joinedFields)

# 4. Truncate the source SDE
arcpy.TruncateTable_management(source_sde)

# 5. Append the copied SDE to the source SDE
arcpy.Append_management(copyL, source_sde, schema_type = 'No_TEST')

# 6. Truncate the target FGDB
arcpy.TruncateTable_management(target_fgdb)

# 6. Append the source SDE to the target FGDB 
arcpy.Append_management(source_sde, target_fgdb, schema_type = 'No_TEST')

# Delete
deleteLayer = [copyL, MLTable_sde]
arcpy.Delete_management(deleteLayer)
arcpy.AddMessage("Delete copied layer is Success")
