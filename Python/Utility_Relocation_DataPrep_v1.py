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
1.	Telecom BTS
2.	Telecom Pole
3.	Water Meter
4.	Water Valve
5.	Manhole
6.	Drain Box
7.	Electric Pole
8.	Street Light
9.	Junction Box
10.	Coupling
11.	Fitting
12.	Transformer
13.	Truss Guy
14.	Concrete Pedestal
15.	Ground
16.	Down Guy
"""

## UtilType2 for Line
"""
1.	Telecom Line
2.	Internet Cable Line
3.	Water Distribution Pipe
4.	Sewerage
5.	Drainage
6.	Canal
7.	Creek
8.	Electric Line
9.	Duct Bank
10.	Water Line

"""


import arcpy
import re
from datetime import datetime

workSpace = arcpy.GetParameterAsText(0)
# "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Pre-Construction_nscrexn2/Pre-Construction_nscrexn2.gdb"
inputLayers = arcpy.GetParameterAsText(1)

testL = inputLayers.replace("'","")
listLayers = testL.split(';')

#Calendar = {1:"January", 2:"February", 3:"March", 4:"April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"December"}


for layer in listLayers:
    # First Add 'TargetDate1' if layer does not have this field name
    #addField = "TargetDate1"
    #temp = [f.name for f in arcpy.ListFields(layer)]
    #listF = [f for f in temp if f in addField]

    #try:
    #    arcpy.AddField_management(layer, addField, "DATE", field_alias = addField, field_is_nullable="NULLABLE")
    #except:
    #    pass
    
    # Assign Domains to Field
    arcpy.AssignDomainToField_management(layer, "Status", 'Utility Relocation Status')
    arcpy.AssignDomainToField_management(layer, "UtilType", 'Utility Type')
    arcpy.AssignDomainToField_management(layer, "Comp_Agency", 'Utility Company')
    arcpy.AssignDomainToField_management(layer, "LAYER", 'Utility LAYER type')
    arcpy.AssignDomainToField_management(layer, "Facility", 'Utility Relocation Facility')
    
    geometryType = arcpy.Describe(layer).ShapeType

    if geometryType == 'Point':
        arcpy.AssignDomainToField_management(layer, "UtilType2", 'Utility Point Type 2')
        
        ##cp = arcpy.Describe(layer).basename
        ##cpName = re.search(r'N-0.*|S-0.*',cp).group()

        ## 1. Enter Facitlity (1. Overhead, 2. Underground, 3. At-Grade) using UtilType2
        with arcpy.da.UpdateCursor(layer, ['Facility','UtilType2']) as cursor:
            for row in cursor:
                # Enter Facility
                if row[1] in [1, 2, 5, 18, 7, 8, 19, 14]:
                    row[0] = 3
                elif row[1] in [3, 4, 10, 11, 17, 6]:
                    row[0] = 2
                cursor.updateRow(row)
        
        ## 2. Enter Height
        ### At-Grade: Height = 0
        with arcpy.da.UpdateCursor(layer, ['Facility', 'Height', 'UtilType2']) as cursor:
            for row in cursor:
                if row[0] == 3:
                    row[1] = 0
                elif row[2] in (3, 4, 10, 11, 17):
                    row[1] = -1
                elif row[2] == 6:
                    row[1] = -3
                cursor.updateRow(row)

        ## 3. Enter Size
        with arcpy.da.UpdateCursor(layer, ['SIZE', 'UtilType2']) as cursor:
            for row in cursor:
                if row[1] in (1, 2, 7, 8, 19):
                    row[0] = 8
                elif row[1] in (3, 4, 5, 10, 11, 17, 18, 6):
                    row[0] = 0.5
                elif row[1] == 14:
                    row[0] = 3
                cursor.updateRow(row)
        
        # Convert date text format
        #with arcpy.da.UpdateCursor(layer, ['TargetDate', 'TargetDate1']) as cursor:
        #    for row in cursor:
        #        if row[0]:
        #            dmY = datetime.strptime(row[0], '%B %Y').date() # date format "December 2022"
        #            row[1] = dmY
        #            mm = dmY.month
        #            years = dmY.year
        #            row[0] = str(Calendar[mm]) + " " + str(years) # string format
        #        else:
        #            row[0] = None
        #            row[1] = None
        #        cursor.updateRow(row)
            
    else:
                
        arcpy.AssignDomainToField_management(layer, "UtilType2", 'Utility Line Type 2')
        
        ##cp = arcpy.Describe(layer).basename
        ##cpName = re.search(r'N-0.*|S-0.*',cp).group()
        """ When CP is entered for individual attribute tables
                with arcpy.da.UpdateCursor(layer, ['Facility', 'UtilType2', 'Height', 'CP', 'Type']) as cursor:
            for row in cursor:
                ##row[3] = cpName
                row[4] = "Line"
                
                # Enter Height by Facility
                if row[0] == 1:
                    row[2] = 8
                elif row[0] == 3:
                    row[2] = 0
                cursor.updateRow(row)
        """

        ## 1. Enter Height
        with arcpy.da.UpdateCursor(layer, ['UtilType2', 'Facility', 'Height']) as cursor:
            for row in cursor:
                # Telecom Line and Underground, Height = -2.0
                if row[0] == 1 and row[1] == 2: 
                    row[2] = -2
                
                # Telecome Line/Internet Cable Line/Electric Line and Aboveground, height = 8.0
                elif row[0] in (1, 2, 8) and row[1] == 1:
                    row[2] = 8

                # Internet Cable Line for Underground
                elif row[0] == 2 and row[1] == 2:
                    row[2] = -3

                # Sewerage/Drainage/Canal/Creek and Underground, Height = -3.0
                elif row[0] in (4, 5, 6, 7, 11):
                    row[1] == 2
                    row[2] = -3

                # Water Distribution Pipe and Underground, Height = -3.5
                elif row[0] == 3:
                    row[1] == 2
                    row[2] = -3.5

                # Electric Line and Underground, Height = -2.5
                elif row[0] == 8 and row[1] == 2:
                    row[2] = -2.5
                cursor.updateRow(row)

               # Convert date text format
        #with arcpy.da.UpdateCursor(layer, ['TargetDate','TargetDate1']) as cursor:
        #    for row in cursor:
        #        if row[0]:
        #            dmY = datetime.strptime(row[0], '%B %Y').date() # date format '%d/%m/%Y'
        #            row[1] = dmY
        #            mm = dmY.month
        #            years = dmY.year
        #            row[0] = str(Calendar[mm]) + " " + str(years) # string format
        #        else:
        #            row[0] = None
        #            row[1] = None
        #        cursor.updateRow(row)

"""
Calendar = {1:"January", 2:"February", 3:"March", 4:"April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"December"}
y[1]
test = "23/08/2022"
from datetime import datetime
ttt = datetime.strptime(test,'%d/%m/%Y').date()
mm = ttt.month
years = ttt.year

str(y[mm]) + " " + str(years)
"""
