# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 10:04:02 2021

# This Python code:
#  1. imports master list excel table
#  2. Convert coordinate notation from DMS2 to DD2 (generate a point feature layer)
#  3. truncates the main feature layer
#  4. appends the point FL to the main FL
#  5. Copy the main FL in PRS92
#  6. truncates the SDE
#  7. appends the copied main FL to the SDE in PRS92

@author: oc3512
"""
# 0. Environment Setting
import arcpy
import re

## To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True

## Script parameters
# "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexn2/During-Construction_nscrexn2.gdb"
workSpace = arcpy.GetParameterAsText(0)
source_fgdb = arcpy.GetParameterAsText(1)
target_sde = arcpy.GetParameterAsText(2)
envTable = arcpy.GetParameterAsText(3) # Excel master list table

# 1. Import the Envi monitoring master list table
out_name = "monitor_table"
tableGDB = arcpy.TableToTable_conversion(envTable, workSpace, out_name)

# 2. Convert coordinate notation from DMS2 to DD2 (generate a point feature layer)
# set parameter values
output_points = 'env_monitor_point'
x_field = 'Longitude'
y_field = 'Latitude'
input_format = 'DMS_2'
output_format = 'DD_2'
spatial_ref = arcpy.SpatialReference('WGS 1984')

xyP = arcpy.ConvertCoordinateNotation_management(tableGDB, output_points, x_field, y_field, input_format, output_format, "", spatial_ref)

# create a spatial reference object for the output coordinate system
out_coordinate_system = arcpy.SpatialReference(3857) # WGS84 Auxiliary

# run the tool
output_feature_class = "env_monitor_point_prj3857"
xyP_prj = arcpy.Project_management(xyP, output_feature_class, out_coordinate_system)


# 3. Truncate the main feature layer
arcpy.TruncateTable_management(source_fgdb)

# 4. Append the point FL to the main FL
arcpy.Append_management(xyP_prj, source_fgdb, schema_type = 'NO_TEST')

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
deleteL = [tableGDB, xyP, xyP_prj, copyL]
arcpy.Delete_management(deleteL)

