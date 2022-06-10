# -*- coding: utf-8 -*-
"""
Created on Sat May 22 08:04:32 2021
This python code re-sorts Depot building multipatch layer. The resorting needs to be done after adding or deleting layers.

    1. Sort by 'Name' and export
    2. Truncate the original Depot building layer
    3. Append the sorted layer to the original layer.
    4. Delete the sorted layer

If you wish to update Excel masterlist based on the updated Depot building layer, 
pleaser run another python code "00-Update_Excel_ML_using_FeatureLayer"
@author: oc3512
"""

import arcpy
import re
import os

# 0. Define parameters
workSpace = arcpy.GetParameterAsText(0) # Choose a folder where the excel master list is saved.
inputFeature = arcpy.GetParameterAsText(1)

# 1. Sort and export
out_dataset = "depotBuilding_Sort"
sort_fields = [["Name","ASCENDING"],["ObjectId","ASCENDING"]]
sortedLayer = arcpy.Sort_management(inputFeature, out_dataset, sort_fields, "")

# Truncate the original Depot building layer
arcpy.TruncateTable_management(inputFeature)

# 3. Append the sorted layer to the original layer
arcpy.Append_management(sortedLayer, inputFeature, schema_type = 'NO_TEST')

# 4. Delete the sorted layer
arcpy.Delete_management(sortedLayer)
