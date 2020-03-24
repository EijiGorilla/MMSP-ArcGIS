# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 16:22:14 2020

@author: oc3512
"""
import arcpy

arcpy.env.overwriteOutput = True

# Script parameters
inFeature = arcpy.GetParameterAsText(0)
inField = arcpy.GetParameterAsText(1)

listField = list(inField.split(";"))

codeblock = """
def reclass(status):
    if status == 0:
        return None
    else:
        return status"""

for field in listField:
    arcpy.AddMessage(field)
    # Set local variables
    expression = "reclass(!{}!)".format(field)
    
    # Execute CalculateField 
    arcpy.CalculateField_management(inFeature, field, expression, "PYTHON3", codeblock)