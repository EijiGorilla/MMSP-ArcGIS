# -*- coding: utf-8 -*-
"""
Created on Mon Mar  7 12:46:10 2022

@author: oc3512
"""
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 08:41:44 2021

@author: emasu
"""

# This python script is to copy and convert source feature layer to PRS92 and truncate the target feature layer,
# and finally append the source to the target.
# This script is intendted to work with only one source (FGDB) and one taget feature layer (SDE).
# Make sure that SDE is PRS92 and FGDB is 32652 or 3857

#
import arcpy
import re

# To alimplow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"


# Script parameters
workSpace = arcpy.GetParameterAsText(0)
source_sde = arcpy.GetParameterAsText(1)
target_fgdb = arcpy.GetParameterAsText(2)

copied = "copied_layer"

# Check if target_fgdb is 32651 (32651) or 3857 (WGS 1984 Web Mercator (auxiliary sphere))
sp_target = arcpy.Describe(target_fgdb).spatialReference.factoryCode # WKID
if sp_target == 3857:
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 Web Mercator (auxiliary sphere)")
elif sp_target == 32651:
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 UTM Zone 51N")
elif sp_target == 3123:
    arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
    
copyL = arcpy.CopyFeatures_management(source_sde, copied)
arcpy.TruncateTable_management(target_fgdb)
arcpy.Append_management(copyL, target_fgdb, schema_type = 'NO_TEST')

# Delete
arcpy.Delete_management(copyL)
arcpy.AddMessage("Delete copied layer is Success")
