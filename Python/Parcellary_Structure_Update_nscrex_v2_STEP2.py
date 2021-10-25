# -*- coding: utf-8 -*-
"""
Created on Thu Sep  9 08:41:44 2021

@author: emasu
"""

# This python script is run after "Parcellary_Structure_Update_nscrex_v2" to
# convert WGS84 to PRS92, truncate feature layers in FGDB, and append them to ones in SDE
# This code will be more useful in case you need to repeat this on multiple layers

#
import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"


# Script parameters
workSpace = arcpy.GetParameterAsText(0)
land_fgdb = arcpy.GetParameterAsText(1)
struc_fgdb = arcpy.GetParameter(2)
strucOccup_fgdb = arcpy.GetParameterAsText(3)
strucISF_fgdb = arcpy.GetParameterAsText(4)

land_sde = arcpy.GetParameterAsText(5)
struc_sde = arcpy.GetParameter(6)
strucOccup_sde = arcpy.GetParameterAsText(7)
strucISF_sde = arcpy.GetParameterAsText(8)

# Copy each layer in PRS92, Truncate, and append
layerList_fgdb = list()
layerList_sde = list()

layerList_fgdb.append(land_fgdb)
layerList_fgdb.append(struc_fgdb)
layerList_fgdb.append(strucOccup_fgdb)
layerList_fgdb.append(strucISF_fgdb)

layerList_sde.append(land_sde)
layerList_sde.append(struc_sde)
layerList_sde.append(strucOccup_sde)
layerList_sde.append(strucISF_sde)

# Delete empty elements (i.e., if some layers are not selected, we need to vacate this element)
layerList_fgdb = [s for s in layerList_fgdb if s != '']
layerList_sde = [s for s in layerList_sde if s != '']

arcpy.AddMessage("Layer List of FGDB: " + str(layerList_fgdb))
arcpy.AddMessage("Layer List of SDE: " + str(layerList_sde))

for layer in layerList_fgdb:
    #arcpy.AddMessage("Layer to be added: " + str(layer))
    
    try:
        # Copy to transform WGS84 to PRS92
        copied = "copied_layer"
        copyL = arcpy.CopyFeatures_management(layer, copied)
        
        arcpy.AddMessage("Copy to CS tranformation for PRS92: Success")
        
        # Truncate and append
        if layer == layerList_fgdb[0]:
            arcpy.TruncateTable_management(land_sde)
            arcpy.Append_management(copyL, land_sde, schema_type = 'NO_TEST')
            
        elif layer == layerList_fgdb[1]:
            arcpy.TruncateTable_management(struc_sde)
            arcpy.Append_management(copyL, struc_sde, schema_type = 'NO_TEST')
            
        elif layer == layerList_fgdb[2]:
            arcpy.TruncateTable_management(strucOccup_sde)
            arcpy.Append_management(copyL, strucOccup_sde, schema_type = 'NO_TEST')
            
        elif layer == layerList_fgdb[3]:
            arcpy.TruncateTable_management(strucISF_sde)
            arcpy.Append_management(copyL, strucISF_sde, schema_type = 'NO_TEST')
            
            arcpy.AddMessage("Truncate and Append is Success")
            
    except:
        pass
    
# Delete
arcpy.Delete_management(copyL)
arcpy.AddMessage("Delete copied layer is Success")
