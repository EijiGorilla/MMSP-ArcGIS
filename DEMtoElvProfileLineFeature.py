# -*- coding: utf-8 -*-
"""
Created on Sat Mar  9 08:47:17 2019f

@author: oc3512
"""

import arcpy
import os

class LicenseError(Exception):
    pass

try:
    if arcpy.CheckExtension("3D") == "Available":
        arcpy.CheckOutExtension("3D")
    else:
        raise LicenseError
    
    # Set environment setting
#    arcpy.env.workspace=arcpy.GetParameterAsText(0)
#    arcpy.env.workspace="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP"
    arcpy.env.overwriteOutput=True
    
    
    # Set output workspace
    outFolder=arcpy.GetParameterAsText(0) #choose .gdb
    # eg., outFolder="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_utm.gdb"
    
    # Choose a DEM raster
    RasterFile=arcpy.GetParameterAsText(1) # choose only raster layer, mosaic layer for parameter
    # eg., RasterFile="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_utm.gdb/PO_SURF_2m1_reproject"
    
    arcpy.CheckInExtension("3D")
    
    outTin=os.path.splitext(os.path.basename(RasterFile))[0] + "_TIN"
        
    print("Creating TIN from " + RasterFile + ".") 
        
    # Set local variables
    maxPts=1500000
    zFactor=1
    
    # Excecute RasterTin
    in_surface=arcpy.RasterTin_3d(RasterFile,outTin,"",maxPts,zFactor)
    print("Finished.")

    # Create a line feature:
    in_feature_class=arcpy.GetParameterAsText(2) # Set data parameter as "Feature Set"
    # eg., in_feature_class="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_utm.gdb/Elevation_profile"
    
    # Name the Output (elevation profile) line to be used for creating Elevation profile
    out_feature_class=arcpy.GetParameterAsText(3)
    outFC=os.path.join(outFolder,out_feature_class)
    
    # Interpolate shape
    arcpy.InterpolateShape_3d(in_surface,in_feature_class,outFC)
     
except LicenseError:
    print("3D Analyst license is unavailable")
except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))
       
        
        
