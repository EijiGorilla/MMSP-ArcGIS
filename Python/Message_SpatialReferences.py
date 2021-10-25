# -*- coding: utf-8 -*-
"""
Created on Fri Jul  9 10:37:46 2021

@author: oc3512
"""
import arcpy

inputLayers = arcpy.GetParameterAsText(0)

spatial_ref = arcpy.Describe(inputLayers).spatialReference.Name
arcpy.AddMessage(spatial_ref)
