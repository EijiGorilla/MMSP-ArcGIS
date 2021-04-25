# -*- coding: utf-8 -*-
"""
Created on Mon Apr 19 15:32:50 2021

***********Always Run One Contract Package at a time*********
Do Not use Viaduct multipatch layer with multiple CP
@author: oc3512
"""
import arcpy
import re
from collections import Counter
import numpy as np

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 Web Mercator (auxiliary sphere)")
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"
#arcpy.env.workspace= "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexn2/During-Construction_nscrexn2.gdb"
# Script parameters
workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)
layerName = arcpy.GetParameterAsText(2) # Do not use '-"
pierNoPtLayer = arcpy.GetParameterAsText(3)
CPno = arcpy.GetParameterAsText(4)

arcpy.env.workspace = workSpace


# 1. Copy Feature Layer

copyFeatureName = layerName
copyStatus = arcpy.CopyFeatures_management(inputLayer, copyFeatureName)

# 2. Delete Fields
## Keep 'Entity' and 'Layer' Field
listFields = [f.name for f in arcpy.ListFields(copyStatus)]

reg=re.compile(r"shape|SHAPE|Shape|OBJECTID|object|Object|OBJECT|Global|global|GLOBAL")
requiredField = list(filter(reg.match, listFields))
requiredFieldPlus = requiredField + ['Entity', 'Layer']

dropField = [e for e in listFields if e not in requiredFieldPlus]

arcpy.DeleteField_management(copyStatus,dropField)

# 2. Add Fields
# PierNumber (text), Type (short), Status1 (short), TargetDate (Date), CP (text), Id (text)
addFields = ['PierNumber', 'Type', 'Status1', 'TargetDate', 'CP', 'ID']

for field in addFields:
    if field in ('PierNumber', 'CP', 'ID'):
        arcpy.AddField_management(copyStatus, field, "TEXT", field_alias = field, field_is_nullable="NULLABLE")
    elif field in ('Type', 'Status1'):
        arcpy.AddField_management(copyStatus, field, "SHORT", field_alias = field, field_is_nullable="NULLABLE")
    else:
        arcpy.AddField_management(copyStatus, field, "DATE", field_alias = field, field_is_nullable="NULLABLE")

# 3. Calculate Field
## Assign values to 'Type' field based on 'Layer' field
## 1. Bored Pile, 2. Pile Cap, 3. Pier, 4. Pier Head, 5. Pre-cast
listLayer = []
with arcpy.da.SearchCursor(copyStatus, ['Layer']) as cursor:
    for row in cursor:
        if row[0] is not None:
            listLayer.append(str(row[0]))
            
uniqueList = list(Counter(listLayer))
    
## Rmove unnecessary letters
reg = re.compile('.*PreCast*|.*PRECAST*|.*precast*|.*preCast*|.*Pile*|.*PILE*|.*COLUMN*|.*Column*|.*PILECAP*|.*pileCap*|.*pilecap*|.*PIER_Head*|.*PIER_head*|.*pier_head*|.*Pier_head*|.*Pier_Head*')

finalList = list(filter(reg.match, uniqueList))

codeblock = """
def reclass(layer):
    if layer == finalList[0]:
        return 5
    elif layer == finalList[1]:
        return 3
    elif layer == finalList[2]:
        return 2
    elif layer == finalList[3]:
        return 4
    elif layer == finalList[4]:
        return 1
    else:
        return None"""

arcpy.AddMessage(field)
    # Set local variables
expression = "reclass(!{}!)".format("Layer")
    
    # Execute CalculateField 
arcpy.CalculateField_management(copyStatus, "Type", expression, "PYTHON3", codeblock)

## Assign 1 (To be Constructed) to all layers for 'Status1' field
CP = CPno

with arcpy.da.UpdateCursor(copyStatus, ['Status1', 'CP']) as cursor:
    for row in cursor:
        row[0] = 1
        row[1] = CP
        cursor.updateRow(row)

## Sort by Shape (from south to north)
out_dataset = layerName + "_" + "sort"
sortedCopyStatus = arcpy.Sort_management(copyStatus, out_dataset, [["Shape", "ASCENDING"]], "LR")


#################
## Join PierNo point feature layer to the sorted multipatch
# Make sure that this point feature layer is also sorted by shape (lower right)
# 1. DefinitionExpression: only pier head
out_layer = out_dataset + "_PierHead"
tempCopy = arcpy.MakeFeatureLayer_management(sortedCopyStatus, "deleteLater", "Type = 4")
sortedCopyStatusPierHead = arcpy.CopyFeatures_management(tempCopy, out_layer)


addField = "tempID"
arcpy.AddField_management(sortedCopyStatusPierHead, addField, "SHORT", field_alias = addField, field_is_nullable="NULLABLE")

# sequential number
with arcpy.da.UpdateCursor(sortedCopyStatusPierHead, addField) as cursor:
    n = 0
    for row in cursor:
        n = n + 1
        row[0] = n
        cursor.updateRow(row)
        
        
# 2. Only extract target CP of the PierNo point feature layer
listCP = []
with arcpy.da.SearchCursor(sortedCopyStatusPierHead, ['CP']) as cursor:
    for row in cursor:
        if row[0] is not None:
            listCP.append(str(row[0]))
            
uniqueListCP = list(Counter(listCP))

# 3. Copy PierNo Feature Layer
#Join the pier No point feature layer to the sorted viaduct
outLayer = out_dataset + "_CPno"
sqlExpression = "CP = '{}'".format(CPno)
sortedPierNoPt_CP = arcpy.MakeFeatureLayer_management(pierNoPtLayer, outLayer, sqlExpression)

out_dataset_p = outLayer + "_sort"
sortedPierNoPt_CP_sort = arcpy.Sort_management(sortedPierNoPt_CP, out_dataset_p, [["Shape", "ASCENDING"]], "LR")

# Add Field for join
arcpy.AddField_management(sortedPierNoPt_CP_sort, addField, "SHORT", field_alias = addField, field_is_nullable="NULLABLE")

# sequential number
with arcpy.da.UpdateCursor(sortedPierNoPt_CP_sort, addField) as cursor:
    n = 0
    for row in cursor:
        n = n + 1
        row[0] = n
        cursor.updateRow(row)

fieldAdd = "PIER"
arcpy.JoinField_management(in_data=sortedCopyStatusPierHead, in_field=addField, join_table=sortedPierNoPt_CP_sort, join_field=addField, fields=fieldAdd)

# 4.  Merge this multipatch of pier head with pierNo with before-definitionQuery multipatch
## Delete all pier head layers from 'Viaduct_N04_test_sort'


## Select rows of pier head
with arcpy.da.UpdateCursor(sortedCopyStatus, "Type") as cursor:
    for row in cursor:
        if row[0] == 4:
            cursor.deleteRow()
            
## Append 'sortedCopyStatusPierHead' to this layer
testMerge = arcpy.Merge_management([sortedCopyStatusPierHead, sortedCopyStatus], "testMerge")

## Sort again for assigning Pier ID No. manually to all the other components (precast, pile, pilecap..)
out_layer_final = layerName + "_before_PierNo_Assignment"
finalSortedLayer = arcpy.Sort_management(testMerge, out_layer_final, [["Shape", "ASCENDING"]], "LR")


# Finally, copy joined PIER information to 'PierNumber' field
with arcpy.da.UpdateCursor(finalSortedLayer, ['PierNumber', fieldAdd]) as cursor:
    for row in cursor:
        row[0] = row[1]
        cursor.updateRow(row)

# Delete 'PIER' Field
arcpy.DeleteField_management(finalSortedLayer, [fieldAdd, addField])

# Add Field
arcpy.AddField_management(finalSortedLayer, "PileNo", "TEXT", field_alias = "PileNo", field_is_nullable="NULLABLE")

##########################################################
# 9. Delete Copied feature layer
##########################################################
# List of Copied Feature Layer
deleteList = [copyFeatureName, out_dataset, out_layer, out_dataset_p, sortedPierNoPt_CP_sort, "testMerge", "deleteLater"]

# Delete the copied feature layer
arcpy.Delete_management(deleteList)

# Delete All
del copyStatus
