# -*- coding: utf-8 -*-
"""
Created on Mon May 17 14:00:14 2021

This python code is intended to import alignment KMZ files created by Sekiguchi san?.
The KMZ files are stored in the GCR NAS device.

@author: oc3512
"""
from pathlib import Path
import sys

from arcgis.gis import GIS, Item
from arcgis.features import FeatureLayerCollection
from arcgis.mapping import WebMap

import arcpy
import os
import re
from collections import Counter

workSpace = arcpy.GetParameterAsText(0) #workSpace = "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2"
fgdbDir = arcpy.GetParameterAsText(1) #"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
kmzDir = arcpy.GetParameterAsText(2) # "C:/Users/oc3512/Dropbox/01-Railway"

arcpy.env.workspace = workSpace
arcpy.env.overwriteOutput = True

# 1. Download all KMZ files from the above link. KMZ files are saved by CP.
# Change the file name like "MCRP_CP_N01"

# 2. Specify a directory of the downloaded KMZ files
allFilesList = os.listdir(kmzDir)
reg = re.compile(r".*kmz")
kmzList = list(filter(reg.match, allFilesList))

# 3. Loop for each kmz files
for kmz in kmzList:
    in_kmz_file = os.path.join(kmzDir, kmz)
    arcpy.conversion.KMLToLayer(in_kmz_file, workSpace)
    
    # Obtain geodatabase name and directory
    gdbName = os.path.splitext(kmz)[0]
    gdbDir = gdbName + ".gdb"
    
    
    # # # # # # Columnation, Centerline, Station Platform, ROW # # # # # # 
    Polylines = os.path.join(workSpace, gdbDir, "Placemarks/Polylines")
    
    # Extract CP number
    regN = re.compile(r"N-01|N01|N-02|N02|N-03|N03|N-04|N04|N-05|N05|S-01|S01|S-02|S02|S-03|S03|S-04|S04|S-05|S05")
    cp = re.findall(regN, gdbName)[0]
    
    # 3.1. Add Field
    addField = "type"
    addField2 = "CP"
    
    arcpy.AddField_management(Polylines, addField, "Text", field_alias = addField, field_is_nullable="NULLABLE")
    arcpy.AddField_management(Polylines, addField2, "Text", field_alias = addField2, field_is_nullable="NULLABLE")
    
    ## Fill in
    regT = re.compile(r"COLUMNATION|Columnation|columnation|Main_Alignment|MAIN_ALIGNMENT|Station_Platform|STATION_PLATFORM|MCRP_ROW|CenterLine|CENTERLINE|Centerline")
    
    with arcpy.da.UpdateCursor(Polylines, ["FolderPath", addField, addField2]) as cursor:
        for row in cursor:
            tex = re.findall(regT, row[0])
            if len(tex) == 0:
                row[1] = None
                row[2] = cp
            else:
                row[1] = tex[0].lower() # lowercase
                row[2] = cp
            cursor.updateRow(row)
            
    # Get a unique name
    listLayer = []
    with arcpy.da.SearchCursor(Polylines, addField) as cursor:
        for row in cursor:
            if row[0] is not None:
                listLayer.append(str(row[0])) 
        
    uniqueList = list(Counter(listLayer))
    
    # Drop Field
    fieldNames=[f.name for f in arcpy.ListFields(Polylines)]
    dropField = [e for e in fieldNames if e not in (addField, addField2, 'SymbolID', 'Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID', 'OID')]
    arcpy.DeleteField_management(Polylines, dropField)
 
    appendListPolylie = []
    appendListPoint = []
    
    for types in uniqueList: 
        # 3.1. Filter each type and copy to the file geodatabase
        if cp == 'N01' and types == 'columnation':
            sqlExpression = "SymbolID = 0" + " AND " + "type = '{}'".format(types)
        elif cp == 'N01' and types == 'station_platform': # symbolID = 9 and 10
            sqlExpression = "SymbolID = 0" + " AND " + "type = '{}'".format(types)             
        elif cp == 'N01' and types == 'main_alignment': # symbolID = 9 and 10
            sqlExpression = "SymbolID IN (0, 11)" + " AND " + "type = '{}'".format(types) 
        elif cp == 'N01' and types == 'mcrp_row': # symbolID = 9 and 10
            sqlExpression = "SymbolID IN (9, 10)" + " AND " + "type = '{}'".format(types)
        elif cp == 'N01' and types == 'centerline':   
            sqlExpression = "SymbolID = 15" + " AND " + "type = '{}'".format(types)
            
        elif cp == 'N03' and types == 'columnation':
            sqlExpression = "SymbolID = 0" + " AND " + "type = '{}'".format(types)
        elif cp == 'N03' and types == 'station_platform':
            sqlExpression = "SymbolID = 0" + " AND " + "type = '{}'".format(types)            
        elif cp == 'N03' and types == 'main_alignment':
            sqlExpression = "SymbolID IN (0, 3)" + " AND " + "type = '{}'".format(types)
        elif cp == 'N03' and types == 'mcrp_row':
            sqlExpression = "SymbolID = 6" + " AND " + "type = '{}'".format(types)
        elif cp == 'N03' and types == 'centerline':
            sqlExpression = "SymbolID = 3" + " AND " + "type = '{}'".format(types)
            
        elif cp == 'N02' and types == 'mcrp_row':
            sqlExpression = "SymbolID = 0" + " AND " + "type = '{}'".format(types)
        elif cp == 'N02' and types == 'centerline':
            sqlExpression = "SymbolID = 6" + " AND " + "type = '{}'".format(types)
        elif cp == 'N02' and types == 'station_platform':
            sqlExpression = "SymbolID = 2" + " AND " + "type = '{}'".format(types)
        elif cp == 'N02' and types == 'columnation':
            sqlExpression = "SymbolID = 2" + " AND " + "type = '{}'".format(types)
        elif cp == 'N02' and types == 'main_alignment':
            sqlExpression = "SymbolID IN (2, 3)" + " AND " + "type = '{}'".format(types)
            
        elif cp == 'N04' and types == 'columnation':
            sqlExpression = "SymbolID IN (1, 13)" + " AND " + "type = '{}'".format(types)
        elif cp == 'N04' and types == 'centerline':
            sqlExpression = "SymbolID = 7" + " AND " + "type = '{}'".format(types)
        elif cp == 'N02' and types == 'main_alignment':
            sqlExpression = "SymbolID IN (0, 1)" + " AND " + "type = '{}'".format(types)
        elif cp == 'N02' and types == 'main_alignment':
            sqlExpression = "SymbolID = 11" + " AND " + "type = '{}'".format(types)
            
        
        makeLayer = arcpy.MakeFeatureLayer_management(Polylines, types, sqlExpression)
        
        ExportDir = os.path.join(fgdbDir, types + "_" + cp)
        arcpy.CopyFeatures_management(makeLayer, ExportDir)
        
        appendListPolylie.append(ExportDir)
    
        # Delete
        arcpy.Delete_management(makeLayer)

        
    # # # # # # PierID (in columnation), star/end point labels and chainage (in centerline) # # # # # # 
    Points = os.path.join(workSpace, gdbDir, "Placemarks/Points")
    
    # 3.1. Add Field 
    arcpy.AddField_management(Points, addField, "Text", field_alias = addField, field_is_nullable="NULLABLE")
    arcpy.AddField_management(Points, addField2, "Text", field_alias = addField2, field_is_nullable="NULLABLE")
    
    with arcpy.da.UpdateCursor(Points, ["FolderPath", addField, addField2]) as cursor:
        for row in cursor:
            tex = re.findall(regT, row[0])
            if len(tex) == 0:
                row[1] = None
                row[2] = cp
            else:
                row[1] = tex[0].lower() # lowercase
                row[2] = cp
            cursor.updateRow(row)
            
    # Get a unique name
    listLayerP = []
    with arcpy.da.SearchCursor(Points, addField) as cursor:
        for row in cursor:
            if row[0] is not None:
                listLayerP.append(str(row[0])) 
        
    uniqueListP = list(Counter(listLayerP))
    
    # Drop Field
    fieldNamesP = [f.name for f in arcpy.ListFields(Points)]
    dropFieldP = [e for e in fieldNamesP if e not in (addField, addField2, 'Name', 'Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID', 'OID')]
    arcpy.DeleteField_management(Points, dropFieldP)
    
    for types in uniqueListP: 
        # 3.1. Filter each type and copy to the file geodatabase
        if types == 'columnation':
            sqlExpression = "type = '{}'".format(types) 
        elif types == 'centerline': # symbolID = 9 and 10
            sqlExpression = "type = '{}'".format(types) 
        
        makeLayerP = arcpy.MakeFeatureLayer_management(Points, types, sqlExpression)
        
        ExportDirP = os.path.join(fgdbDir, types + "_" + cp + "_point")
        arcpy.CopyFeatures_management(makeLayerP, ExportDirP)
        
        appendListPoint.append(ExportDirP)
    
        # Delete
        arcpy.Delete_management(makeLayerP)
    
   # arcpy.Delete_management(os.path.join(workSpace, gdbDir))
   
## Lastly, merge by types
## Polylines
# ['C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N05']
appendListPolylie = ['C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N01',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N02',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N03',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N04',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N05',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N01',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N02',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N03',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N04',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N05',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N01',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N02',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N03',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N04',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\mcrp_row_N01',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\mcrp_row_N02',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\mcrp_row_N03',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\mcrp_row_N04',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\mcrp_row_N05',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\station_platform_N01',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\station_platform_N02',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\station_platform_N03']

appendListPoint = ['C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\main_alignment_N05_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N01_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N02_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N03_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N04_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\centerline_N05_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N01_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N02_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N03_point',
                     'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb\\columnation_N04_point']


uniqueList = ['centerline', 'main_alignment', 'mcrp_row', 'station_platform', 'columnation']
for types in uniqueList:
    regA = re.compile(r".*{}".format(types))
    mergeList = list(filter(regA.match, appendListPolylie))
    OutName = types.title() + "_N2"
    arcpy.Merge_management(mergeList, os.path.join(fgdbDir, OutName))

## Points
for types in uniqueListP:
    regP = re.compile(r".*{}".format(types))
    mergeListP = list(filter(regP.match, appendListPoint))
    OutNameP = types.title() + "_N2"
    arcpy.Merge_management(mergeListP, os.path.join(fgdbDir, OutNameP))
    
# Delete
arcpy.Delete_management(appendListPolylie)
arcpy.Delete_management(appendListPoint)