import arcpy
import os

# Set environment settings
workSpace = arcpy.GetParameterAsText(0)
#workSpace = "C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/ORG"


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
        outCS0 = arcpy.SpatialReference(3857) # 'WGS_1984_Web_Mercator_Auxiliary_Sphere'
        outCS1 = arcpy.SpatialReference(32651) #"WGS 1984 UTM Zone 51N"
        outCS2 = arcpy.SpatialReference(3123) #"PRS 1992 Philippines Zone III"
        outCS3 = arcpy.SpatialReference(25393) # "Philippines_Zone_III"
        outCS4 = arcpy.SpatialReference(4326) # 'GCS_WGS_1984'
      
        if dsc.spatialReference.name == "Unknown":
            print('skipped this fc due to undefined coordinate system: ' + infc) 
            
        elif dsc.spatialReference.name == outCS2.name:
            # just copy the existing file to the PRS92 file geodatabase
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            
            if outfc_prs.find('.shp') != -1: # when file is .shp format
                # PRS 92
                newName=str(infc.replace(".shp","")+"_PRS92")
                newName=newName.replace("-","_")
                outfc_prs = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_prs,newName)
                
                # To UTM
                newName=str(infc.replace(".shp","")+"_utm")
                newName=newName.replace("-","_")                
                outfc_utm = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_utm,newName)
                arcpy.Project_management(infc,outfc_utm,outCS1)
            else:
                # Just copy for PRS92
                arcpy.CopyFeatures_management(infc, outfc_prs+"_PRS92")
                
                # Conver PRS92 to UTM
                arcpy.Project_management(infc, outfc_utm+"_utm",outCS1)
                
            # check messages
            print(arcpy.GetMessages())           
                
        elif dsc.spatialReference.name == outCS1.name:
            # just copy the existing file to the PRS92 file geodatabase
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            
            if outfc_prs.find('.shp') != -1: # when file is .shp format
                # PRS 92
                newName=str(infc.replace(".shp","")+"_PRS92")
                newName=newName.replace("-","_")
                outfc_prs = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_prs,newName)
                arcpy.Project_management(infc,outfc_prs,outCS2)
                
                # To UTM
                newName=str(infc.replace(".shp","")+"_utm")
                newName=newName.replace("-","_")                
                outfc_utm = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_utm,newName)

            else:
                # Convert UTM to PRS92
                arcpy.Project_management(infc, outfc_prs+"_PRS92",outCS2)
                # Just copy for UTM
                arcpy.CopyFeatures_management(infc, outfc_utm+"_utm") 

            # check messages
            print(arcpy.GetMessages())  
            
        elif dsc.spatialReference.name == outCS3.name:
            # Determine the newoutput feature class path and name
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            
            if outfc_prs.find('.shp') != -1: # when file is .shp format
                # To PRS 92
                newName=str(infc.replace(".shp","")+"_PRS92")
                newName=newName.replace("-","_")
                outfc_prs = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_prs,newName)               
                
                # run project tool
                arcpy.Project_management(infc, outfc_prs, outCS2)
                
                # TO UTM
                newName=str(infc.replace(".shp","")+"_utm")
                newName=newName.replace("-","_")
                outfc_utm = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_utm,newName)
                # run project tool
                arcpy.Project_management(infc, outfc_utm, outCS1)
                
            else: # when file is just feature class of file geodatabase
                arcpy.Project_management(infc, outfc_prs+"_PRS92",outCS2)
                arcpy.Project_management(infc, outfc_utm+"_utm",outCS1)
             
            # check messages
            print(arcpy.GetMessages())
            
        elif dsc.spatialReference.name == outCS0.name or dsc.spatialReference.name == outCS4.name:
            # Determine the newoutput feature class path and name
            outfc_prs = os.path.join(outWorkspace_prs,infc)
            outfc_utm = os.path.join(outWorkspace_utm,infc)
            
            if outfc_prs.find('.shp') != -1: # when file is .shp format
                # To PRS 92
                newName=str(infc.replace(".shp","")+"_utm")
                newName=newName.replace("-","_")
                outfc_utm = arcpy.FeatureClassToFeatureClass_conversion(infc, outWorkspace_utm,newName)               
                
                # run project tool
                ttt = arcpy.Project_management(infc,outfc_utm + "_utm",outCS1)
                arcpy.Project_management(ttt, outfc_prs + "_PRS92", outCS2)
                               
            else: # when file is just feature class of file geodatabase
                ttt = arcpy.Project_management(infc,outfc_utm + "_utm",outCS1)
                arcpy.Project_management(ttt, outfc_prs + "_PRS92", outCS2)

            # check messages
            print(arcpy.GetMessages())

except arcpy.ExecuteError:
    print(arcpy.GetMessages(2))
    
except Exception as ex:
    print(ex.args[0])