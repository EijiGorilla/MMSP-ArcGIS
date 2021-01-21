# -*- coding: utf-8 -*-
"""
Created on Thu Dec 31 08:46:17 2020

This python code remove the following punctuations and others from chosen fields:
    1. Asterisk mark (i.e., '*')
    2. Period (i.e., '.')
    2. Space (before, after, and inside text)
    
@author: oc3512
"""
import re
import arcpy

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
#arcpy.env.workspace="C:/Users/matsuzaki_a48/Documents/ArcGIS/Packages/Environmental_Team_88be65/Land_Acquisition.sde"

# Script parameters
workSpace = arcpy.GetParameterAsText(0)
inputTable = arcpy.GetParameterAsText(1)
inputField = arcpy.GetParameterAsText(2)

arcpy.env.workspace = workSpace


# List fields being chosen
#fieldList = inputField
#fieldList = list(inputField)
#arcpy.AddMessage(fieldList)

codeblock = """
import re
def reclass(status):
    if len(status) > 0:
        regex = re.compile(r'(\s+)?([*.]+)?')
        return regex.sub(r'',status)
    else:
        return None"""

#for field in fieldList:
#    arcpy.AddMessage(field)
    # Set local variables
expression = "reclass(!{}!)".format(inputField)
    
# Execute CalculateField 
arcpy.CalculateField_management(inputTable, inputField, expression, "PYTHON3", codeblock)
