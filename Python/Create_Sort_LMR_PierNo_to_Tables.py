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

# C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexn2/During-Construction_nscrexn2.gdb
workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)
outputLocation = arcpy.GetParameterAsText(2)

#"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/tempCheck"
arcpy.env.workspace = workSpace

# OLD CODE: keep this just in case
#sqlExpression = "PileNo = '{}'".format('L')
#tempCopyLeft = arcpy.MakeFeatureLayer_management(inputLayer, "deleteLater", sqlExpression)
#pilesLeft = arcpy.CopyFeatures_management(tempCopyLeft, "Piles_Left")

#sqlExpression = "PileNo = '{}'".format('M')
#tempCopyMid = arcpy.MakeFeatureLayer_management(inputLayer, "deleteLater", "PileNo = 'M'")
#pilesMid = arcpy.CopyFeatures_management(tempCopyMid, "Piles_Mid")

#sqlExpression = "PileNo = '{}'".format('R')
#tempCopyRight = arcpy.MakeFeatureLayer_management(inputLayer, "deleteLater", "PileNo = 'R'")
#pilesRight = arcpy.CopyFeatures_management(tempCopyRight, "Piles_Right")

##
# Create individual Bored Pile multipatch layers: L, M, and R
sqlExpression = "PileNo = '{}'".format('L')
pilesLeft = arcpy.MakeFeatureLayer_management(inputLayer, "Piles_Left", sqlExpression)

sqlExpression = "PileNo = '{}'".format('M')
pilesMid = arcpy.MakeFeatureLayer_management(inputLayer, "Piles_Mid", "PileNo = 'M'")

sqlExpression = "PileNo = '{}'".format('R')
pilesRight = arcpy.MakeFeatureLayer_management(inputLayer, "Piles_Right", "PileNo = 'R'")


# Sort each
## Get Contract Package
jj = arcpy.Describe(inputLayer).name
cp = re.findall("N0+[0-9]|N-0[0-9]|N_0[0-9]|S0+[0-9]|S-0[0-9]|S_0[0-9]",jj)
cp = ' '.join(cp)
cpL = [f for f in cp if f in "N"]

# SC
if len(cpL) > 0:
    arcpy.AddMessage("You sorted by Upper Left for N2 extension")
    sortedPilesLeft = arcpy.Sort_management(pilesLeft, "sortedPilesLeft", [["Shape", "ASCENDING"]], "LR")
    sortedPilesMid = arcpy.Sort_management(pilesMid, "sortedPilesMid", [["Shape", "ASCENDING"]], "LR")
    sortedPilesRight = arcpy.Sort_management(pilesRight, "sortedPilesRight", [["Shape", "ASCENDING"]], "LR")
else:
    arcpy.AddMessage("You sorted by Upper Left for SC extension")
    sortedPilesLeft = arcpy.Sort_management(pilesLeft, "sortedPilesLeft", [["Shape", "ASCENDING"]], "UL")
    sortedPilesMid = arcpy.Sort_management(pilesMid, "sortedPilesMid", [["Shape", "ASCENDING"]], "UL")
    sortedPilesRight = arcpy.Sort_management(pilesRight, "sortedPilesRight", [["Shape", "ASCENDING"]], "UL")

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
    fileName = arcpy.Describe(inLayer).name + "_T.csv"
    #exportFile = os.path.join(outputLocation, fileName)
    arcpy.TableToTable_conversion(inLayer, outputLocation, fileName)

addSequentialValueToTable(sortedPilesLeft)
addSequentialValueToTable(sortedPilesMid)
addSequentialValueToTable(sortedPilesRight)

# Delete
deleteList = ["Piles_Left", "Piles_Mid", "Piles_Right", "deleteLater"]

# Delete the copied feature layer
arcpy.Delete_management(deleteList)

