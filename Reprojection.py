# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 08:49:47 2019

How to Reproject vectors
@author: oc3512
"""

import arcpy
import ListNamesFeatureClass

# Set the environment
arcpy.env.workspace="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/Lesson2"
inFolder="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/Lesson2"
arcpy.env.overwriteOutput=True

# Read feature class
featureList=arcpy.ListFeatureClasses()
for feature in featureList:
    print("{0}".format(feature))

# Define the target CRS
targetCS=arcpy.Describe(featureList[1]).spatialReference


for feature in featureList:
    nowCS=arcpy.Describe(feature).spatialReference
    if nowCS.Name != targetCS.Name:
        newName=feature.replace(".shp","_Projected.shp")
        arcpy.Project_management(feature,newName,targetCS)


##########
import arcpy
import ListNamesFeatureClass
import os

arcpy.env.overwriteOutput=True

out_Location="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice"
inFile="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/Stations.kmz"

baseName=os.path.splitext(os.path.basename(inFile))[0] # returns
arcpy.KMLToLayer_conversion(inFile,out_Location) # conver to a file geodatabase

fcDataSets=ListNamesFeatureClass.listFeatureClassDatasetNames('C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/Stations.gdb')
fcFeatureList=ListNamesFeatureClass.listFeatureClassNames(fcDataSets)

currentCRS=arcpy.Describe(fcFeatureList).spatialReference.Name

targetCRS1=arcpy.SpatialReference("WGS 1984 UTM Zone 51N")
targetCRS2=arcpy.SpatialReference("PRS 1992 Philippines Zone III")

arcpy.CopyFeatures_management(fcFeatureList,"TEST123.shp")

fc_targetCRS1=arcpy.Project_management("TEST123.shp","TEST123_32651.shp",targetCRS1)
fc_targetCRS2=arcpy.Project_management("TEST123_32651.shp","TEST123_3123.shp",targetCRS2)

