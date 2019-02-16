# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 08:49:47 2019

How to Reproject vectors
@author: oc3512
"""

import arcpy
import ListNamesFeatureClass
import os

arcpy.env.workspace="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/Lesson2"
inFolder="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/Lesson2"
arcpy.env.overwriteOutput=True


featureList=arcpy.ListFeatureClasses()

for feature in featureList:
    print("{0}".format(feature))

targetCS=arcpy.Describe(featureList[1]).spatialReference



for feature in featureList:
    nowCS=arcpy.Describe(feature).spatialReference
    if nowCS.Name != targetCS.Name:
        newName=feature.replace(".shp","_Projected.shp")
        arcpy.Project_management(feature,newName,targetCS)


