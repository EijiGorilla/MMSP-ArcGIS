# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 12:17:21 2022

@author: oc3512
"""
# -*- coding: utf-8 -*-
"""
Created on Sat May 22 08:04:32 2021

@author: oc3512
"""

# Facility
"""
## 1. Overhead
## 2. Underground
## 3. At-Grade
"""

## UtilType2 for Points
""" 
1.	Telecom (BTS)
2.	Telecom Cable TV Pole
3.	Telecom Pole
4.	Sluice Gate
5.	Air Valve
6.	District Meter
7.	Water Meter
8.	Gate Valve
9.	Valve
10.	STC
11.	Drain Box
12.	Manhole
13.	Electric Pole
14.	Street Light
15.	Traffic Light
16.	Road Safety Signs
17.	Junction Box
18.	Pedestal
19.	Transvault
20.	Fire Hydrant
21.	Handhole

"""

## UtilType2 for Line
"""
1.	Telecom Line
2.	Internet Cable TV Line
3.	Duct Bank
4.	Water Distribution Pipe
5.	Main Line
6.	Sub-main line
7.	Canal
8.	Sewer Pipeline
9.	Sewer Drainage
10.	Creek
11.	Electric Line
12.	Storm Drainage
13.	Drainage
14.	Gas line

"""


import arcpy
import re

workSpace = arcpy.GetParameterAsText(0)
# "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
inputLayer = arcpy.GetParameterAsText(1)

geometryType = arcpy.Describe(inputLayer).ShapeType

if geometryType == 'Point':
    with arcpy.da.UpdateCursor(inputLayer, ['Facility', 'UtilType2', 'Height', 'Type']) as cursor:
        for row in cursor:
            row[3] == "Point"
            
            # Define height
            if row[0] == 3:
                row[2] = 0
            elif row[0] == 2:
                row[2] = -3
            elif row[0] == 1:
                row[2] = 8
            
            # if UtilType2 is 'Manhole', Facility must be 'At-Grade'
            elif row[1] == 12:
                row[0] = 3
            cursor.updateRow(row)
    
    with arcpy.da.UpdateCursor(inputLayer, ['Facility', 'UtilType2', 'SIZE']) as cursor:
        # Define size by UtilType2
        for row in cursor:
            if row[1] in [1,2,3,13,14,15,16]:
                row[2] = 8
            elif row[1] in [4,5,6,7,8,9,10,11,17,19,20,21]:
                row[2] = 0.5
            elif row[1] == 12:
                row[2] = 0.2
            elif row[1] in [18]:
                row[2] = 3
            cursor.updateRow(row)

    # Add field name 'Checks' if not added
    newField = "Checks"
    listFields = [f.name for f in arcpy.ListFields(inputLayer)]
    listChecks = [f for f in listFields if f in newField]
    if listChecks:
        print("There is already a field name {}".format(newField))
    else:
        arcpy.AddField_management(inputLayer, newField, "SHORT", field_alias=newField, field_is_nullable="NULLABLE")

    # Enter 1 in 'Checks' field if utilType and/or utilType2 is null
    with arcpy.da.UpdateCursor(inputLayer,['UtilType','UtilType2',newField]) as cursor:
        for row in cursor:
            if row[0] is None or row[0] == "":
                row[2] = 1
            elif row[0] is None or row[0] == "":
                row[2] = 1
            else:
                row[2] is None
            cursor.updateRow(row)
                
        
else:
    with arcpy.da.UpdateCursor(inputLayer, ['Facility', 'UtilType2', 'Height', 'Type']) as cursor:
        for row in cursor:
            row[3] = "Line"
            
            # Define height by Facility
            if row[0] == 1:
                row[2] = 8
            elif row[0] == 2:
                row[2] = -3
            elif row[0] == 3:
                row[2] = 0
            cursor.updateRow(row)
            
        # Add field name 'Checks' if not added
        newField = "Checks"
        listFields = [f.name for f in arcpy.ListFields(inputLayer)]
        listChecks = [f for f in listFields if f in newField]

        if listChecks:
            print("There is already a field name {}".format(newField))
        else:
            arcpy.AddField_management(inputLayer, newField, "SHORT", field_alias=newField, field_is_nullable="NULLABLE")

        # Enter 1 in 'Checks' field if utilType and/or utilType2 is null
        with arcpy.da.UpdateCursor(inputLayer,['UtilType','UtilType2',newField]) as cursor:
            for row in cursor:
                if row[0] is None or row[0] == "":
                    row[2] = 1
                elif row[0] is None or row[0] == "":
                    row[2] = 1
                else:
                    row[2] is None
                cursor.updateRow(row)
"""        
    with arcpy.da.UpdateCursor(layer, ['Facility', 'UtilType2', 'Height']) as cursor:
        for row in cursor:
            if row[1] == 3:
                row[2] = -1
            elif row[0] == 2 and row[1] in [1,2]:
                row[2] = -2
            elif row[0] == 1 and row[1] in [1,8]:
                row[2] = 8
            elif row[0] == 2 and row[1] in [8]:
                row[2] = -2.5
            elif row[0] == 2 and row[1] in [4]:
                row[2] = -3
            cursor.updateRow(row)
"""
