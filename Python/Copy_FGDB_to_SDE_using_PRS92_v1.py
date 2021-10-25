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
workSpace = arcpy.GetParameterAsText(0)
source_fgdb = arcpy.GetParameterAsText(1)
target_sde = arcpy.GetParameterAsText(2)

copied = "copied_layer"
copyL = arcpy.CopyFeatures_management(source_fgdb, copied)
arcpy.TruncateTable_management(target_sde)
arcpy.Append_management(copyL, target_sde, schema_type = 'NO_TEST')

# Delete
arcpy.Delete_management(copyL)
arcpy.AddMessage("Delete copied layer is Success")
