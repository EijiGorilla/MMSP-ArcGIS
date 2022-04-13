# -*- coding: utf-8 -*-
"""
Created on Wed Mar 30 09:26:26 2022

@author: oc3512

This python script calculated summary statistics for displaying monthly progress in stacked bar charts
used in ArcGIS API for JavaScript

The general steps are:
    0: Create an empty dictionary for each type, year, and month
    1. Update 'Year' and 'Month' field of source layer
    2. Run 'Summary Statistics'
    3. Append count to an empty dictionary by Type, Year, and Month 

"""

import arcpy
from datetime import datetime

arcpy.env.overwriteOutput = True

# Define parameters
# "C:/Users/eiji.LAPTOP-KSD9P6CP/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/During-Construction_nscrexn2"
workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)

# 0. Create emtpy dictionary for each year, month, and type
## Year 2021
dwall_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
column_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
slab_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
kingpost_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
secantp_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}

## Year 2022
dwall_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
column_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
slab_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
kingpost_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
secantp_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}

# Check if there are field names for 'Year' and 'Month'
field1 = "Year"
field2 = "Month"

fieldNames = [f.name for f in arcpy.ListFields(inputLayer)]
targetFields = [f for f in fieldNames if f in ('Year','Month')]
if targetFields:
    print("you already have Year and Month field names.")
else:
    arcpy.AddField_management(inputLayer, field1, "SHORT", field_alias=field1, field_is_nullable="NULLABLE")
    arcpy.AddField_management(inputLayer, field2, "SHORT", field_alias=field2, field_is_nullable="NULLABLE")

# 1. Update Year and Month field of inputLayer
with arcpy.da.UpdateCursor(inputLayer, ["end_date","Year","Month"]) as cursor:
    for row in cursor:
        if row[0]:
            row[1] = row[0].year
            row[2] = row[0].month
        cursor.updateRow(row)
# 2. Run 'Summary Statistics'
outStatsTable = "outStatsTable"
statsFields = [["Type", "COUNT"]]
caseFields = ["Type","Year","Month"]
summaryT = arcpy.Statistics_analysis(inputLayer, outStatsTable, statsFields, caseFields)

# 3. Append count to an empty dictionary by Type, Year, and Month
inFields = ["Type","Year","Month","FREQUENCY"]
with arcpy.da.SearchCursor(summaryT, inFields) as cursor:
    for row in cursor:            
        # Year 2021
        if row[0] == 1 and row[1] == 2021:
            dwall_2021[row[2]].append(row[3])
        elif row[0] == 2 and row[1] == 2021:
            column_2021[row[2]].append(row[3])
        elif row[0] == 3 and row[1] == 2021:
            slab_2021[row[2]].append(row[3])
        elif row[0] == 4 and row[1] == 2021:
            kingpost_2021[row[2]].append(row[3])
        elif row[0] == 5 and row[1] == 2021:
            secantp_2021[row[2]].append(row[3])
            
        # Year 2022
        elif row[0] == 1 and row[1] == 2022:
            dwall_2022[row[2]].append(row[3])
        elif row[0] == 2 and row[1] == 2022:
            column_2022[row[2]].append(row[3])
        elif row[0] == 3 and row[1] == 2022:
            slab_2022[row[2]].append(row[3])
        elif row[0] == 4 and row[1] == 2022:
            kingpost_2022[row[2]].append(row[3])
        elif row[0] == 5 and row[1] == 2022:
            secantp_2022[row[2]].append(row[3])

# Print all
arcpy.AddMessage("const dwall_2021 = " + str(dwall_2021) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const column_2021 = " + str(column_2021) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const slab_2021 = " + str(slab_2021) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const kingpost_2021 = " + str(kingpost_2021) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const secantp_2021 = " + str(secantp_2021) + ";")
arcpy.AddMessage("\n")

arcpy.AddMessage("const dwall_2022 = " + str(dwall_2022) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const column_2022 = " + str(column_2022) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const slab_2022 = " + str(slab_2022) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const kingpost_2022 = " + str(kingpost_2022) + ";")
arcpy.AddMessage("\n")
arcpy.AddMessage("const secantp_2022 = " + str(secantp_2022) + ";")

# Delete
arcpy.Delete_management(summaryT)
