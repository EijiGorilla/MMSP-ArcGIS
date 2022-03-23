# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 14:38:43 2022

This code assigns tbmSpot to TBM segmented line layer

@author: oc3512
"""
import arcpy

arcpy.env.overwriteOutput = True

# Script parameters
workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)

#
TBM1 = []
TBM2 = []
TBM3 = []
TBM4 = []
TBM5 = []
TBM6 = []

# First collect segment Numbers for each TBM line where status is completed
fields = ["line","segmentno","status"]
with arcpy.da.SearchCursor(inputLayer, fields) as cursor:
    for row in cursor:
        if row[0] == "TBM1" and row[2] == 4:
            TBM1.append(row[1])
        elif row[0] == "TBM2" and row[2] == 4:
            TBM2.append(row[1])
        elif row[0] == "TBM3" and row[2] == 4:
            TBM3.append(row[1])
        elif row[0] == "TBM4" and row[2] == 4:
            TBM4.append(row[1])
        elif row[0] == "TBM5" and row[2] == 4:
            TBM5.append(row[1])
        elif row[0] == "TBM6" and row[2] == 4:
            TBM6.append(row[1])

# Now fill in tbmSpot
fields1 = ["line","segmentno","tbmSpot"] 
with arcpy.da.UpdateCursor(inputLayer, fields1) as cursor:
    for row in cursor:
        if row[0] == "TBM1" and row[1] == max(TBM1):
            row[2] = 1
        elif row[0] == "TBM2" and row[1] == max(TBM2):
            row[2] = 1
        elif row[0] == "TBM3" and row[1] == max(TBM3):
            row[2] = 1
        elif row[0] == "TBM4" and row[1] == max(TBM4):
            row[2] = 1
        elif row[0] == "TBM5" and row[1] == max(TBM5):
            row[2] = 1
        elif row[0] == "TBM6" and row[1] == max(TBM6):
            row[2] = 1
        cursor.updateRow(row)