# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 18:52:18 2019

@author: oc3512
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Feb 23 16:36:27 2019

@author: oc3512
"""
import arcpy
import os

# Set environment settings
workSpace = arcpy.GetParameterAsText(0)
#workSpace = "C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP.gdb"

def listFeatureClassNames(location):
    import arcpy
    arcpy.env.workspace=location
    fcList=arcpy.ListFeatureClasses()
    return fcList

arcpy.env.overwriteOutput=True
    
# Set local variables
outWorkspace_prs = arcpy.GetParameterAsText(1)
outWorkspace_utm = arcpy.GetParameterAsText(2)

#outWorkspace_prs = "C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_PRS92.gdb"
#outWorkspace_utm = "C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_utm.gdb"

try:
    fcList=listFeatureClassNames(workSpace)
    for infc in fcList:
        dsc = arcpy.Describe(infc)

        # Set output coordinate system
        outCS1 = arcpy.SpatialReference("WGS 1984 UTM Zone 51N")
        outCS2 = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
        
        if dsc.spatialReference.name == "Unknown":
            print('skipped this fc due to undefined coordinate system: ' + infc)
        
        elif dsc.spatialReference.name == outCS2.name:
            # just copy the existing file to the PRS92 file geodatabase
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            arcpy.CopyFeatures_management(infc,outfc_prs)
            
            # Also reproject to UTM 51N then save it in the utm file geodatabase
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            arcpy.Project_management(infc,outfc_utm + "_utm",outCS1)
        elif dsc.spatialReference.name == outCS1.name:
            # just copy the existing file to the utm file geodatabase
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            arcpy.CopyFeatures_management(infc,outfc_utm)
            
            # Also reproject to PRS then save it in the prs file geodatabase
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            arcpy.Project_management(infc,outfc_prs + "_PRS92",outCS2)        
            #print("skipped this fc because it has " + outCS2.name)
        elif dsc.spatialReference.name == "Philippines_Zone_III":
            # Determine the newoutput feature class path and name
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            
            # run project tool
            arcpy.Project_management(infc, outfc_prs, outCS2)
            
            # check messages
            print(arcpy.GetMessages())
        elif dsc.spatialReference.name == "WGS_1984_Web_Mercator_Auxiliary_Sphere":
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            
            ttt = arcpy.Project_management(infc,outfc_utm + "_utm",outCS1)
            arcpy.Project_management(ttt, outfc_prs + "_PRS92", outCS2)
            
            print(arcpy.GetMessages())

except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))
    
except Exception as ex:
    print(ex.args[0])