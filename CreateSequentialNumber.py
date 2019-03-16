# -*- coding: utf-8 -*-
"""
Created on Sat Mar 16 10:22:31 2019
"Creating sequential numbers in the Field"

@author: oc3512
"""
       
import arcpy
workSpace=arcpy.GetParameterAsText(0) # if other than feature datasets
workSpace=arcpy.GetParameterAsText(1) # if feature datasets will be selected

#arcpy.env.workspace="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_utm.gdb"

featureClass=arcpy.GetParameterAsText(2)
fieldName=arcpy.GetParameterAsText(3)

#datasets=arcpy.ListDatasets(feature_type="feature")

#datasets = arcpy.ListDatasets(feature_type='feature')
#datasets = [''] + datasets if datasets is not None else []

#for ds in datasets:
#    for fc in arcpy.ListFeatureClasses(feature_dataset=ds):

#fieldNames=[f.name for f in arcpy.ListFields(fc)]

startNo=1
with arcpy.da.UpdateCursor(featureClass,fieldName) as cursor:
    for row in cursor:
        row[0]=startNo
        startNo +=1
        cursor.updateRow(row)
        




