# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 17:26:51 2021

@author: oc3512
"""
import arcpy
import re
from collections import Counter
import numpy as np
import os

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True

workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)
outputLocation = arcpy.GetParameterAsText(2)
#"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/tempCheck"
arcpy.env.workspace = workSpace

# Copy Feature for 'L' (left) Piles
sqlExpression = "PileNo = '{}'".format('L')
tempCopyLeft = arcpy.MakeFeatureLayer_management(inputLayer, "deleteLater", sqlExpression)
pilesLeft = arcpy.CopyFeatures_management(tempCopyLeft, "Piles_Left")

sqlExpression = "PileNo = '{}'".format('M')
tempCopyMid = arcpy.MakeFeatureLayer_management(inputLayer, "deleteLater", "PileNo = 'M'")
pilesMid = arcpy.CopyFeatures_management(tempCopyMid, "Piles_Mid")

sqlExpression = "PileNo = '{}'".format('R')
tempCopyRight = arcpy.MakeFeatureLayer_management(inputLayer, "deleteLater", "PileNo = 'R'")
pilesRight = arcpy.CopyFeatures_management(tempCopyRight, "Piles_Right")

# Sort each
sortedPilesLeft = arcpy.Sort_management(pilesLeft, "sortedPilesLeft", [["Shape", "ASCENDING"]], "LR")
sortedPilesMid = arcpy.Sort_management(pilesMid, "sortedPilesMid", [["Shape", "ASCENDING"]], "LR")
sortedPilesRight = arcpy.Sort_management(pilesRight, "sortedPilesRight", [["Shape", "ASCENDING"]], "LR")

# Assign 'temp' Field Name
tempField = "temp"
arcpy.AddField_management(sortedPilesLeft, tempField, "SHORT", field_alias = tempField, field_is_nullable="NULLABLE")
arcpy.AddField_management(sortedPilesMid, tempField, "SHORT", field_alias = tempField, field_is_nullable="NULLABLE")
arcpy.AddField_management(sortedPilesRight, tempField, "SHORT", field_alias = tempField, field_is_nullable="NULLABLE")

# Delete Field 'ID'
deleteField = "ID"
arcpy.DeleteField_management(sortedPilesLeft, deleteField)
arcpy.DeleteField_management(sortedPilesMid, deleteField)
arcpy.DeleteField_management(sortedPilesRight, deleteField)

# Add Sequential numbers
def addSequentialValueToTable(inLayer):
    with arcpy.da.UpdateCursor(inLayer, tempField) as cursor:
        n = 0
        for row in cursor:
            n = n + 1
            row[0] = n
            cursor.updateRow(row)
    
    # Table to table conversion
    fileName = arcpy.Describe(inLayer).name
    exportFile = fileName + ".csv"
    arcpy.TableToTable_conversion(inLayer, outputLocation, exportFile)

addSequentialValueToTable(sortedPilesLeft)
addSequentialValueToTable(sortedPilesMid)
addSequentialValueToTable(sortedPilesRight)

# Delete
deleteList = ["Piles_Left", "Piles_Mid", "Piles_Right", "deleteLater"]

# Delete the copied feature layer
arcpy.Delete_management(deleteList)

