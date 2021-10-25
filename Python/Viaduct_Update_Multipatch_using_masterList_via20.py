# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 08:41:44 2021

@author: emasu
"""

# This python script is to copy and convert source feature layer to PRS92 and truncate the target feature layer,
# and finally append the source to the target.
# This script is intendted to work with only one source (FGDB) and one taget feature layer (SDE).

#
import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"


# Script parameters
# workSpace = r"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexn2/During-Construction_nscrexn2.gdb"


workSpace = arcpy.GetParameterAsText(0)
source_fgdb = arcpy.GetParameterAsText(1)
target_sde = arcpy.GetParameterAsText(2)
MLTable = arcpy.GetParameterAsText(3)

# 1. Copy the source FGDB
copied = "copied_layer"
copyL = arcpy.CopyFeatures_management(source_fgdb, copied)

# 2. Delete Field the copied FGDB
fieldList = [f.name for f in arcpy.ListFields(copyL)]           
dropFieldLot = [e for e in fieldList if e not in ('uniqueID','Shape','created_user','created_date','last_edited_user','last_edited_date','OBJECTID','GlobalID')]

arcpy.DeleteField_management(copyL, dropFieldLot)

# 3. Join masterlist table to the copied FGDB
## 3.1. Convert Excel tables to feature table
MLTable_fgdb = arcpy.TableToTable_conversion(MLTable, workSpace, 'MasterListLot')

## 3.1. Identify joined fields from masterlist table
joinedFieldList = [f.name for f in arcpy.ListFields(MLTable_fgdb)]
joinedFields = [e for e in joinedFieldList if e not in ('uniqueID','OBJECTID')]

joinField = "uniqueID"
arcpy.JoinField_management(in_data=copyL, in_field=joinField, join_table=MLTable_fgdb, join_field=joinField, fields=joinedFields)

# 4. Truncate the source FGDB
arcpy.TruncateTable_management(source_fgdb)

# 5. Append the copied FGDB to the source FGDB
arcpy.Append_management(copyL, source_fgdb, schema_type = 'No_TEST')

# 6. Truncate the target SDE
arcpy.TruncateTable_management(target_sde)

# 6. Append the source FGDB to the target SDE 
arcpy.Append_management(source_fgdb, target_sde, schema_type = 'No_TEST')

# Delete
deleteLayer = [copyL, MLTable_fgdb]
arcpy.Delete_management(deleteLayer)
arcpy.AddMessage("Delete copied layer is Success")
