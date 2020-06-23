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

aprx = arcpy.mp.ArcGISProject('current')

# Define Parameters
demolitionM = "demolition_Ready_MTH" # Field name of demolition plan months
Pages = "Depot;Quirino Highway;Tandang Sora" # Define Map Series names



#inputFeature = arcpy.GetParameterAsText(0) # Feature Layer
inputFeature = "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Environmental_Team/Environmental_Team.gdb/Parcellary_Status_20200616"

#layerFileDir = arcpy.GetParameterAsText(1)
layerFileDir = "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/MMSP/99-Layer File-lyrx/Land Acquisition/TimeSliced/from mid July 2020"

#outputDir = arcpy.GetParameterAsText(2)
outputDir = 'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Time slice/v6'

# As of Date
asofDate = "20200610"

# Reference variables in the ArcGIS Project
#aprx = arcpy.mp.ArcGISProject(r'C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/Environmental_Team/Environmental_Team.aprx')


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
    if demo == 7.25 or demo == 7.5:
        return "202007Mid"
    elif demo == 7.75 or demo == 7:
        return "202007End"      
    elif demo == 8.25 or demo == 8.5:
        return "202008Mid"
    elif demo == 8.75 or demo == 8:
        return "202008End"
    elif demo == 9.25 or demo == 9.5:
        return "202009Mid"
    elif demo == 9.75 or demo == 9:
        return "202009End"
    elif demo == 10.25 or demo == 10.5:
        return "202010Mid"
    elif demo == 10.75 or demo == 10:
        return "202010End"
    elif demo == 11.25 or demo == 11.5:
        return "202011Mid"
    elif demo == 11.75 or demo == 11:
        return "202011End"
    elif demo == 12.25 or demo == 12.5:
        return "202012Mid"
    elif demo == 12.75 or demo == 12:
        return "202012End"
    elif demo == 13.25 or demo == 13.5:
        return "202101Mid"
    elif demo == 13.75 or demo == 13:
        return "202101End"
    elif demo == 14.25 or demo == 14.5:
        return "202102Mid"
    elif demo == 14.75 or demo == 14:
        return "202102End"
    elif demo == 15.25 or demo == 15.5:
        return "202103Mid"
    elif demo == 15.75 or demo == 15:
        return "202103End"
    elif demo == 16.25 or demo == 16.5:
        return "202104Mid"
    elif demo == 16.75 or demo == 16:
        return "202104End"
    elif demo == 17.25 or demo == 17.5:
        return "202105Mid"
    elif demo == 17.75 or demo == 17:
        return "202105End"
    elif demo == 18.25 or demo == 18.5:
        return "202106Mid"
    elif demo == 18.75 or demo == 18:
        return "202106End"
    else:
        return None"""

expression = "reclass(!{}!)".format(demolitionM)
arcpy.CalculateField_management(inputLyr, "temp", expression, "PYTHON3", codeblock)

# Apply Symbology from layer for each demolition Plan month
monthList= ["202007Mid", "202007End", "202008Mid", "202008End", "202009Mid", "202009End", "202010Mid", "202010End",
            "202011Mid", "202011End", "202012Mid", "202012End", "202101Mid", "202101End", "202102Mid",
           "202102End", "202103Mid", "202103End", "202104Mid", "202104End", "202105Mid", "202105End",
            "202106Mid", "202106End"]

#monthList= ["202007Mid", "202007End", "202008Mid", "202008End"]
#Pages = "Depot;Quirino Highway;Tandang Sora"
#m = "202007Mid"

for m in monthList:
    symbolLyrx = os.path.join(layerFileDir, m + ".lyrx")
    arcpy.ApplySymbologyFromLayer_management(inputLyr, symbolLyrx, [["VALUE_FIELD", demolitionM, demolitionM]], update_symbology="MAINTAIN")[0]
    
    # Get the corresponding map series page numbers
    pages_list = Pages.split(";")
    pages_str = ",".join("'" + p + "'" for p in pages_list)
    sql = 'Station IN ({})'.format(pages_str)
    arcpy.SelectLayerByAttribute_management(mapSeriesLyr, "NEW_SELECTION", sql)    
    
    # Get the corresponding map series page numbers
    msPDF = os.path.join(outputDir, asofDate + "_" + "TimeSlice_" + m + ".pdf")
    #ms.exportToPDF(msPDF, 'SELECTED')
    ms.exportToPDF(msPDF, 'SELECTED', multiple_files = "PDF_MULTIPLE_FILES_PAGE_NAME")
    
arcpy.DeleteField_management(inputLyr, "temp")
