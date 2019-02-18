# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 14:08:40 2019

@author: oc3512
"""

import arcpy
import ListNamesFeatureClass
import os

arcpy.env.overwriteOutput=True
    
try: 
    
    inFile="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice/MMSP.kml"
    out_Location="C:/Users/oc3512/Documents/ArcGIS/Projects/Python_practice"
   
    baseName=os.path.splitext(os.path.basename(inFile))[0] # returns
    arcpy.conversion.KMLToLayer(inFile,out_Location)
    
    fcDataSetFile=out_Location + "/" + baseName + ".gdb"
    fcDataSets=ListNamesFeatureClass.listFeatureClassDatasetNames(fcDataSetFile)
    fcFeatureList=ListNamesFeatureClass.listFeatureClassNames(fcDataSets)
    
    currentCRS=arcpy.Describe(fcFeatureList).spatialReference.Name
    CRS1=arcpy.SpatialReference("WGS 1984 UTM Zone 51N")
    CRS2=arcpy.SpatialReference("PRS 1992 Philippines Zone III")
    
    outFiles=str(baseName + ".shp")
    TT=arcpy.CopyFeatures_management(fcFeatureList,outFiles)
    
    firstCRS=arcpy.Project_management(TT,baseName+"_reproject.shp",CRS1)
    arcpy.Project_management(firstCRS,baseName+"_reproject_PRS.shp",CRS2)
    
except:
    arcpy.GetMessage()