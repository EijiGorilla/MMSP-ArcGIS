# -*- coding: utf-8 -*-
"""
Created on Wed May  5 14:45:55 2021

@author: oc3512
"""
import arcpy
import re
from collections import Counter
import numpy as np
import os

arcpy.env.overwriteOutput = True

workSpace = arcpy.GetParameterAsText(0)
joinTable = arcpy.GetParameterAsText(1)
targetTable = arcpy.GetParameterAsText(2)
joinField = arcpy.GetParameterAsText(3) #tempID
transferField = arcpy.GetParameterAsText(4) #PierNumber_1

# Join Field
joinedLayer = arcpy.JoinField_management(in_data=joinTable, in_field=joinField, join_table=targetTable, join_field=joinField, fields=transferField)

# Copy to the PierNumber field
with arcpy.da.UpdateCursor(joinedLayer, ['PierNumber', transferField]) as cursor:
    for row in cursor:
        row[0] = row[1]
        cursor.updateRow(row)

# Delete 'PIER' Field
arcpy.DeleteField_management(joinedLayer, [joinField, transferField])
