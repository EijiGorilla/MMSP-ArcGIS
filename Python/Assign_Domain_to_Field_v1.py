# -*- coding: utf-8 -*-
"""
Created on Sat May 22 08:04:32 2021

@author: oc3512
"""
import arcpy
import re

workSpace = GetParameterAsText(0)
# "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
inputLayers = GetParameterAsText(1)

for layer in inputLayers:
    # Assign Domains to Field
    arcpy.AssignDomainToField_management(layer, "Status", 'Utility Relocation Status')
    arcpy.AssignDomainToField_management(layer, "UtilType", 'Utility Type')
    arcpy.AssignDomainToField_management(layer, "Comp_Agency", 'Utility Company')
    arcpy.AssignDomainToField_management(layer, "LAYER", 'Utility LAYER type')
    arcpy.AssignDomainToField_management(layer, "Facility", 'Utility Relocation Facility')
    
    geometryType = arcpy.Describe(layer).ShapeType

    if geometryType == 'Point':
        arcpy.AssignDomainToField_management(layer, "UtilType2", 'Utility Point Type 2')
        
        # Enter 'Height' and 'SIZE'
        with arcpy.da.UpdateCursor(layer, ['Facility', 'UtilType2', 'Height']) as cursor:
            for row in cursor:
                 # At-Grade means that height = 0
                if row[0] == 3:
                    row[2] = 0
                cursor.updateRow(row)
                
         with arcpy.da.UpdateCursor(layer, ['Facility', 'UtilType2', 'SIZE']) as cursor:
            for row in cursor:
                 # At-Grade means that height = 0
                if row[1] in [3, 4, 5, 6, 9, 10]:# UtiltyType2 water meter, water valve, manole, drainbox, junction box, coupling
                    row[2] = 0.5
                elif row[1] in [1, 2, 7, 8]: # electric pole, telcom pole, street light
                    row[2] = 8
                cursor.updateRow(row)
                   
    else: # Polyline
        arcpy.AssignDomainToField_management(layer, "UtilType2", 'Utility Line Type 2')
        
        # Enter 'Height' and 'SIZE'
        with arcpy.da.UpdateCursor(layer, ['Facility', 'UtilType2', 'Height']) as cursor:
            for row in cursor:
                 # Overhead line means that height = 8m
                if row[0] == 1:
                    row[2] = 8
                # At-Grade
                elif row[0] == 3:
                    row[2] = 0
                cursor.updateRow(row)
            
