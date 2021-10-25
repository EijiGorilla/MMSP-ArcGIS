# -*- coding: utf-8 -*-
"""
Created on Thu Apr 22 10:12:08 2021

@author: oc3512
"""
import arcpy
import re
from collections import Counter
import numpy as np
import os

arcpy.env.overwriteOutput = True

workSpace = arcpy.GetParameterAsText(0)
#C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexsc/During-Construction_nscrexsc.gdb
#C:/Users/emasu/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexsc/During-Construction_nscrexsc.gdb

joinTableL = arcpy.GetParameterAsText(1)
joinTableM = arcpy.GetParameterAsText(2)
joinTableR = arcpy.GetParameterAsText(3)
inputLayerL = arcpy.GetParameterAsText(4)
inputLayerM = arcpy.GetParameterAsText(5)
inputLayerR = arcpy.GetParameterAsText(6)
sourceLayer = arcpy.GetParameterAsText(7) # Viaduct_N04_before_PierNo_Assignment
outputDir = arcpy.GetParameterAsText(8) #C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/tempCheck

arcpy.env.workspace = workSpace

# Make sure to copy the source layer in case the source layer is corrupted
copiedSourceLayer = arcpy.Describe(sourceLayer).name + "_COPY1"
arcpy.CopyFeatures_management(sourceLayer, copiedSourceLayer)

# Join excel table (PierID No created) to sortedPiles (L, M, R)
joinField = "temp"
transferField = "ID"
def joinDeleteFieldTable(inputLayer, joinField, joinTable, transferField):
    arcpy.JoinField_management(in_data = inputLayer, in_field=joinField, join_table = joinTable, join_field=joinField, fields=transferField)
    arcpy.DeleteField_management(inputLayer, joinField)


joinDeleteFieldTable(inputLayerL, joinField, joinTableL, transferField)
joinDeleteFieldTable(inputLayerM, joinField, joinTableM, transferField)
joinDeleteFieldTable(inputLayerR, joinField, joinTableR, transferField)


# Delete all the Piles from the source multipatch
with arcpy.da.UpdateCursor(sourceLayer, "Type") as cursor:
    for row in cursor:
        if row[0] == 1:
            cursor.deleteRow()

# Merge all for a final multipatch layer
listLayer = []
with arcpy.da.SearchCursor(sourceLayer, ['Layer']) as cursor:
    for row in cursor:
        if row[0] is not None:
            listLayer.append(str(row[0]))
            
uniqueList = list(Counter(listLayer))
cp = uniqueList[0].replace('-', '')

finalLayer = "Viaduct" + "_" + cp + "_Final"
mergedLayer = arcpy.Merge_management([sourceLayer, inputLayerL, inputLayerM, inputLayerR], finalLayer)

    

# Finally sort the merged layer from south to north
cpL = [f for f in cp if f in "N"]

if len(cpL) > 0:
    mergedLayerSorted = arcpy.Sort_management(mergedLayer, finalLayer + "_sorted", [["Shape", "ASCENDING"]], "LR")
else:
    arcpy.AddMessage("You sorted by Upper Left for SC extension")
    mergedLayerSorted = arcpy.Sort_management(mergedLayer, finalLayer + "_sorted", [["Shape", "ASCENDING"]], "UL")

# Delete PileNo Field
deleteField = "PileNo"
arcpy.DeleteField_management(mergedLayerSorted, deleteField)


# Define Domain
# list of domain names
domains = arcpy.da.ListDomains(workSpace)
domainList = []
for domain in domains:
    domainList.append(domain.name)
    
regType = re.compile(r'.*ViaductType|.*viaducttype|.*viaductType|.*Viaduct Type|.*viadcut Type')
regStatus = re.compile(r'.*ViaductStatus|.*viaductStatus|.*viaductstatus|.*Viaduct Status')

domainType = list(filter(regType.match, domainList))
domainStatus = list(filter(regStatus.match, domainList))

arcpy.AssignDomainToField_management(mergedLayerSorted, "Type", domainType[0])
arcpy.AssignDomainToField_management(mergedLayerSorted, "Status1", domainStatus[0])

# create tempid
addField = "tempid"
arcpy.AddField_management(mergedLayerSorted, addField, "Short", field_alias = addField, field_is_nullable="NULLABLE")

with arcpy.da.UpdateCursor(mergedLayerSorted, ['tempid']) as cursor:
    n= 0
    for row in cursor:
        n = n + 1
        row[0] = n
        cursor.updateRow(row)

# Export to excel csv
fileName = arcpy.Describe(mergedLayer).name
exportFile = fileName + "_fineSort" + ".csv"
arcpy.TableToTable_conversion(mergedLayerSorted, outputDir, exportFile)


del joinField
del transferField
del joinDeleteFieldTable
del finalLayer