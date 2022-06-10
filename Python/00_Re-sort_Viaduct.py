# -*- coding: utf-8 -*-
"""
Created on Sat May 22 08:04:32 2021
This python code re-sorts viaduct multipatch layer. The resorting needs to be done after adding or deleting layers.

    1. Create 'temp' field (type: short)
    2. Extract numbers using PierNumber
    3. Sort and export
    4. Delete the 'temp' field from original and sorted layers
    5. Truncate the original Viaduct layer
    6. Append the sorted layer to the original layer.
    7. Delete sorted layer

If you wish to update Excel masterlist based on the updated viadcut layer, 
pleaser run another python code "00-Update_Excel_ML_using_FeatureLayer"
@author: oc3512
"""

import arcpy
import re
import os

# 0. Define parameters
workSpace = arcpy.GetParameterAsText(0) # Choose a folder where the excel master list is saved.
inputFeature = arcpy.GetParameterAsText(1)

# 1. Create 'temp' field (type: short)
addField = 'temp'
arcpy.AddField_management(inputFeature, addField, "SHORT", "", "", "", addField, "NULLABLE", "")

# 2. Extract numbers using PierNumber
field_pier = "PierNumber"
field_temp = "temp"
codeblock = """
import re
def reclass(pier):
    try:
        reg = re.search('\\d+',pier).group()
        return reg
    except AttributeError:
        reg = re.search('\\d+',pier)
        return reg
"""
expression = "reclass(!{}!)".format(field_pier)
arcpy.CalculateField_management(inputFeature, field_temp, expression, "PYTHON3", codeblock)

# 3. Sort and export
out_dataset = "viaduct_Sort"
sort_fields = [["CP","ASCENDING"],["temp","ASCENDING"],["PierNumber","ASCENDING"],["Type","ASCENDING"],["pp","ASCENDING"]]
sortedLayer = arcpy.Sort_management(inputFeature, out_dataset, sort_fields, "")

# 4. Delete the 'temp' field from original and sorted layers
arcpy.DeleteField_management(inputFeature, field_temp, "DELETE_FIELDS")
arcpy.DeleteField_management(sortedLayer, field_temp, "DELETE_FIELDS")

# 5. Truncate the original Viaduct layer
arcpy.TruncateTable_management(inputFeature)

# 6. Append the sorted layer to the original layer.
arcpy.Append_management(sortedLayer, inputFeature, schema_type = 'NO_TEST')

# 7. Delete sorted layer
arcpy.Delete_management(sortedLayer)
