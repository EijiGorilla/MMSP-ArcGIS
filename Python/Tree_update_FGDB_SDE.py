# -*- coding: utf-8 -*-
"""
Created on Tue Oct 12 17:31:16 2021

# This Python code:
#  1. imports master list excel table
#  2. converts the table to a point feature layer
#  3. truncates the main feature layer
#  4. appends the point FL to the main FL
#  5. Copy the main FL in PRS92
#  6. truncates the SDE
#  7. appends the copied main FL to the SDE in PRS92
# 
@author: oc3512
"""
# 0. Environment Setting
import arcpy
import re

## To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True

## Script parameters
# "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
workSpace = arcpy.GetParameterAsText(0)
source_fgdb = arcpy.GetParameterAsText(1)
target_sde = arcpy.GetParameterAsText(2)
treeTable = arcpy.GetParameterAsText(3) # Excel master list table

# 1. Import the tree master list table
out_name = "Trees_table"
treeTableGDB = arcpy.TableToTable_conversion(treeTable, workSpace, out_name)

# 2. Convert the table to a point feature layer
fNames = [f.name for f in arcpy.ListFields(treeTableGDB)]

## Obtain field name for latitude and longitude
reg_long = re.compile(r"Long*|long*")
reg_lat = re.compile(r"Lati*|lati*")

long = list(filter(reg_long.match, fNames))
lat = list(filter(reg_lat.match, fNames))

out_feature_class = "Tree_points"
xyP = arcpy.management.XYTableToPoint(treeTableGDB, out_feature_class, long[0], lat[0], "", arcpy.SpatialReference(4326))

# 3. Truncate the main feature layer
arcpy.TruncateTable_management(source_fgdb)

# 4. Append the point FL to the main FL
arcpy.Append_management(xyP, source_fgdb, schema_type = 'NO_TEST')

# 5. Copy the main FL in PRS92
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

copied = "copied_layer"
copyL = arcpy.CopyFeatures_management(source_fgdb, copied)

# 6. truncates the SDE
arcpy.TruncateTable_management(target_sde)

# 7, Append the copied FGDB to the SDE
arcpy.Append_management(copyL, target_sde, schema_type = 'NO_TEST')

# Delete
deleteL = [treeTableGDB, xyP, copyL]
arcpy.Delete_management(deleteL)

