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
workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)

# 0. Create emtpy dictionary for each year, month, and type
## Year 2021
pile_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
pileC_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
pier_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
pierH_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
precast_2021 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}

## Year 2022
pile_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
pileC_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
pier_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
pierH_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}
precast_2022 = {1:[],2:[],3:[],4:[],5:[],6:[],7:[],8:[],9:[],10:[],11:[],12:[]}

# 1. Update Year and Month field of inputLayer
with arcpy.da.UpdateCursor(inpuLayer, ["end_date","Year","Month"]) as cursor:
    for row in cursor:
        if row[0]:
            dmY = datetime.strptime(row[0], '%B %Y').date()
            row[1] = dmY.year
            row[2] = dmY.month
        cursor.updateRow(row)


# 2. Run 'Summary Statistics'
outStatsTable = "outStatsTable"
statsFields = [["Type"]]
caseFields = ["Type","Year","Month"]
stats = "COUNT"
summaryT = arcpy.Statistics_analysis(inputLayer, outStatsTable, stats, caseFields)

# 3. Append count to an empty dictionary by Type, Year, and Month
inFields = ["Type","Year","Month","FREQUENCY"]
with arcpy.da.SearchCursor(summaryT, inFields) as cursor:
    for row in cursor:            
        # Year 2021
        if row[0] == 1 and row[1] == 2021:
            pile_2021(row[2]).append(row[3])
        elif row[0] == 2 and row[1] == 2021:
            pileC_2021(row[2]).append(row[3])
        elif row[0] == 3 and row[1] == 2021:
            pier_2021(row[2]).append(row[3])
        elif row[0] == 4 and row[1] == 2021:
            pierH_2021(row[2]).append(row[3])
        elif row[0] == 5 and row[1] == 2021:
            precast_2021(row[2]).append(row[2])
            
        # Year 2022
        elif row[0] == 1 and row[1] == 2022:
            pile_2022(row[2]).append(row[3])
        elif row[0] == 2 and row[1] == 2022:
            pileC_2022(row[2]).append(row[3])
        elif row[0] == 3 and row[1] == 2022:
            pier_2022(row[2]).append(row[3])
        elif row[0] == 4 and row[1] == 2022:
            pierH_2022(row[2]).append(row[3])
        elif row[0] == 5 and row[1] == 2022:
            precast_2022(row[2]).append(row[3])

# Print all
print("const pile=2021" + str(pile_2021) + ";","\n",
      "const pile=2021" + str(pileC_2021) + ";","\n",
      "const pile=2021" + str(pier_2021) + ";","\n",
      "const pile=2021" + str(pierH_2021) + ";","\n",
      "const pile=2021" + str(precast_2021) + ";","\n")

print("const pile=2021" + str(pile_2022) + ";","\n",
      "const pile=2021" + str(pileC_2022) + ";","\n",
      "const pile=2021" + str(pier_2022) + ";","\n",
      "const pile=2021" + str(pierH_2022) + ";","\n",
      "const pile=2021" + str(precast_2022) + ";","\n")

# Delete
arcpy.Delete_management(summaryT)