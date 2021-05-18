# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 14:55:58 2020

@author: oc3512

This script only works in Python console within ArcGIS Pro. If you create a script and define parameters, this does not work.

---How to run this script---
1. Open Python console from Analysis tab of ArcGIS Pro
2. Drag and drop inputFeature from the Content panel
3. Copy and paste directories for layerFileDir (.lyrx) and OutputDir
4. Copy and paste the remaining code
"""

import arcpy
import os
import re

aprx = arcpy.mp.ArcGISProject('current')


#inputFeature = arcpy.GetParameterAsText(0) # Feature Layer
inputFeature = "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Environmental_Team/Environmental_Team.gdb/Parcellary_Status_20200616"

#layerFileDir = arcpy.GetParameterAsText(1)
layerFileDir = "C:/Users/oc3512/Dropbox/01-Railway/01-MMSP/10-ArcGIS/01-Reference/01-Layer File-lyrx/01-Land Acquisition/02-Time Slice/from mid January 2021"

#outputDir = arcpy.GetParameterAsText(2)
outputDir = 'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Time slice/20210121'



# Reference variables in the ArcGIS Project
#aprx = arcpy.mp.ArcGISProject(r'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Environmental_Team/Environmental_Team.aprx')

# Define Parameters
demolitionM = "demolition_Ready_MTH" # Field name of demolition plan months
Pages = "Depot;Quirino Highway;Tandang Sora" # Define Map Series names
# As of Date
asofDate = "20210121"

layout = aprx.listLayouts('DemolitionPlan')[0]
ms = layout.mapSeries
mf = layout.listElements("MAPFRAME_ELEMENT", "Map Frame 1")[0]
mapSeriesLyr = mf.map.listLayers("Construction Boundary")[0]

# Add a temporary Field to the layer
inputLyr = inputFeature
arcpy.AddField_management(inputLyr, "temp", "TEXT")

# Define a Field of demolition ready month


# Add demolition month string labels
codeblock = """
def reclass(demo):
    if demo == 99 or demo == 1.5:
        return "202101Mid"   
    elif demo == 1.75:
        return "202101End"
    elif demo == 2.5:
        return "202102Mid"
    elif demo == 2.75:
        return "202102End"
    elif demo == 3.5:
        return "202103Mid"
    elif demo == 3.75:
        return "202103End"
    elif demo == 4.5:
        return "202104Mid"
    elif demo == 4.75:
        return "202104End"
    elif demo == 5.5:
        return "202105Mid"
    elif demo == 5.75:
        return "202105End"
    elif demo == 6.5:
        return "202106Mid"
    elif demo == 6.75:
        return "202106End"
    elif demo == 7.5:
        return "202107Mid"
    elif demo == 7.75:
        return "202107End"
    elif demo == 8.5:
        return "202108Mid"
    elif demo == 8.75:
        return "202108End"
    elif demo == 9.5:
        return "202109Mid"
    elif demo == 9.75:
        return "202109End"
    elif demo == 10.5:
        return "202110Mid"
    elif demo == 10.75:
        return "202110End"
    elif demo == 11.5:
        return "202111Mid"
    elif demo == 11.75:
        return "202111End"
    else:
        return None"""

expression = "reclass(!{}!)".format(demolitionM)
arcpy.CalculateField_management(inputLyr, "temp", expression, "PYTHON3", codeblock)

# Apply Symbology from layer for each demolition Plan month
## Get month list from the layerFileDir being defined
monthList = [re.sub('.lyrx', '', _) for _ in os.listdir(layerFileDir)]

#monthList= ["202101Mid", "202101End", "202102Mid", "202102End", "202103Mid", "202103End"]

for m in monthList:
    symbolLyrx = os.path.join(layerFileDir, m + ".lyrx")
    arcpy.ApplySymbologyFromLayer_management(inputLyr, symbolLyrx, [["VALUE_FIELD", demolitionM, demolitionM]], update_symbology="MAINTAIN")[0]
    
    # Get the corresponding map series page numbers
    pages_list = Pages.split(";") # Construction boundary names
    pages_str = ",".join("'" + p + "'" for p in pages_list)
    sql = 'Station IN ({})'.format(pages_str)
    arcpy.SelectLayerByAttribute_management(mapSeriesLyr, "NEW_SELECTION", sql)    
    
    # Get the corresponding map series page numbers
    msPDF = os.path.join(outputDir, asofDate + "_" + "TimeSlice_" + m + ".pdf")
    #ms.exportToPDF(msPDF, 'SELECTED')
    ms.exportToPDF(msPDF, 'SELECTED', multiple_files = "PDF_MULTIPLE_FILES_PAGE_NAME")
    
arcpy.DeleteField_management(inputLyr, "temp")
