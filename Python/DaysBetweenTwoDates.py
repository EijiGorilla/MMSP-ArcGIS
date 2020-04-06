# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 08:54:08 2019

Insert 3 floors for each building
@author: oc3512
"""
import arcpy
from datetime import datetime

# Set work space
workspace=arcpy.GetParameterAsText(0) # workspace
inputTable=arcpy.GetParameterAsText(1) # Table View
startDate=arcpy.GetParameterAsText(2) # Field, Dependency: inputTalbe
endDate=arcpy.GetParameterAsText(3) # Field, Dependency: inputTable
updateField=arcpy.GetParameterAsText(4) # Field, Dependency: inputTable

#arcpy.env.workspace="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP_utm.gdb"
arcpy.env.overwriteOutput=True

# Generate a list of file geodatabase tables
#dataTable=arcpy.ListTables()

# Choose a table of your interest:
#tableName="TimeRemaining_building1"
#index=dataTable.index(tableName)
#inputTable=dataTable[index]

# when field names are added
#arcpy.AddField_management(inputTable,field_name="Diff",field_type="long")
#fieldNames=[f.name for f in arcpy.ListFields(inputTable)]

date_format="%Y-%m-%d %H:%M:%S"

with arcpy.da.UpdateCursor(inputTable,(startDate,endDate,updateField)) as cursor:
    for row in cursor:
        end_date=datetime.strptime(str(row[1]), date_format)
        start_date=datetime.strptime(str(row[0]),date_format)
        row[2]=abs((end_date-start_date).days)
        cursor.updateRow(row)