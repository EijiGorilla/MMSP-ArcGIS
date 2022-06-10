# -*- coding: utf-8 -*-
"""
Created on Sat May 22 08:04:32 2021
This python code updates Excel master list using feature layer.
When the feature layer is edited or updated, the corresponding excel sheet must also be updated according to the feature layer.
This code
    1. Refresh uniqueID by adding sequential number
    2. Export the feature layer to Excel sheet using 'Table_To_Table' geoprocessing tool.
    3. Delete unneeded field names (i.e., OBJECTID, GlobalID, created_user, created_date, last_edited_user, last_edited_date)
@author: oc3512
"""

import arcpy
import re
import os

# 0. Define parameters
workSpace = arcpy.GetParameterAsText(0) # Choose a folder where the excel master list is saved.
inputFeature = arcpy.GetParameterAsText(1)

# 1. Refresh uniqueID by adding sequential number
rec=0
with arcpy.da.UpdateCursor(inputFeature, ["uniqueID"]) as cursor:
    for row in cursor:
        pStart = 1
        pInterval = 1
        if (rec == 0):
            rec = pStart
            row[0] = rec
        else:
            rec = rec + pInterval
            row[0] = rec
        cursor.updateRow(row)

# 2. Export inputFeature to Excel sheet
out_xlsx = os.path.join(workSpace,inputFeature + "_NEW_ML.xlsx")

## Execute TableToExcel
arcpy.TableToExcel_conversion(inputFeature, out_xlsx)

"""
# 3. Delete field names
fieldList = [f.name for f in arcpy.ListFields(inputFeature)]
delFields = ['OBJECTID_1', 'GlobalID', 'created_user', 'created_date', 'last_edited_user', 'last_edited_date']

## Look for field names to be deleted in the feature layer
reg = re.compile(r'OBJECTID|GlobalID|created_user|created_date|last_edited_user|last_edited_date')
fieldDropped = list(filter(reg.match,fieldList))
"""



