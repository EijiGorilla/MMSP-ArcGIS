# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 21:37:09 2019

@author: oc3512
"""
## CAUTION
# 1. Make sure that data type matches between master list excel table and existing feature layers for all field names



import arcpy
import re

# To allow overwriting the outputs change the overwrite option to true.
arcpy.env.overwriteOutput = True
#arcpy.env.workspace="C:/Users/matsuzaki_a48/Documents/ArcGIS/Packages/Environmental_Team_88be65/Land_Acquisition.sde"

# Script parameters
workSpace = arcpy.GetParameterAsText(0)
Status1011_Merge = arcpy.GetParameterAsText(1)
MasterList_xlsx = arcpy.GetParameterAsText(2)

#workSpace=r"C:/Users/oc3512/Documents/ArcGIS/Projects/Environmental_Team/Land_Acquisition.sde"
#Status1011_Merge = r"gisdata.GISOWNER.Parcellary_Status_4"
#MasterList_xlsx = r"C:/Users/oc3512/OneDrive/Masterlist/Land_Acquisition/MasterList.xlsx/MasterList$"

arcpy.env.workspace = workSpace

###################################
# 1. Copy Feature Layer
###################################
copyFeatureName = 'LAR_Status_Temp'
copyStatus = arcpy.CopyFeatures_management(Status1011_Merge, copyFeatureName)

#######################################################
# 2. Delete Field from Copyied Feature Layer
#######################################################
# Get drop fields: exclude arcgis default fields: id, shape,...
fieldNames=[f.name for f in arcpy.ListFields(copyStatus)]
dropField = [e for e in fieldNames if e not in ('Id', 'ID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]

# 1. Determine Drop Fields:
## List of exisiting feature layer field names
inFields=[f.name for f in arcpy.ListFields(copyStatus)]

## Check if there is any field that exists for dropping
comField=[f for f in inFields if f in tuple(dropField)]

# 2. Delete Fields
## Execute Delete field only if fields to be dropped are present in the existing feature layer
if len(comField) == 0:
    print("There is no field that can be dropped from the feature layer")
else:
    arcpy.DeleteField_management(copyStatus,dropField)

#######################################################
# 3. Convert MasterList.xlsx to Enterprise geodatabase table
#######################################################
# 3. Convert MasterList.xlsx to gdb table (use 'Table to Table' geoprocessing tool)
arcpy.TableToTable_conversion(MasterList_xlsx, workSpace, 'MasterList')

#######################################################
# 4. Join Master List to Copied Feature Layer
#######################################################
## Extract a list of geodatabase tables
tableList=arcpy.ListTables("*")

## Extract only MasterList geodatabase table
r=re.compile(".*Master")
rList = list(filter(r.match, tableList))
MasterList=''.join(rList)

# 4. Join Field
## Get Join Field from MasterList gdb table: Gain all fields except 'Id'
inputField=[f.name for f in arcpy.ListFields(MasterList)]
joinFields = [e for e in inputField if e not in ('Id', 'ID','OBJECTID')]

## Extract a Field from MasterList and Feature Layer to be used to join two tables
t=[f.name for f in arcpy.ListFields(copyStatus)]
in_field=' '.join(map(str, [f for f in t if f in ('Id','ID')]))
 
u=[f.name for f in arcpy.ListFields(MasterList)]
join_field=' '.join(map(str, [f for f in u if f in ('Id','ID')]))

## Execute Join
arcpy.JoinField_management(in_data=copyStatus, in_field=in_field, join_table=MasterList, join_field=join_field, fields=joinFields)

#######################################################
# 5. Truncate Original Feature Layer
#######################################################
#Status1011_Merge=r"gisdata.GISOWNER.Parcellary_Status"

arcpy.TruncateTable_management(Status1011_Merge)

##########################################################
# 6. Append copied feature layer to original feature layer
##########################################################
arcpy.Append_management(copyStatus, Status1011_Merge,schema_type = 'NO_TEST')

##########################################################
# 7. Convert 99 to None in Status fields
##########################################################
#-----------------------
# 5. Convert 99 to None
# 99 is used to keep the field as numeric type 
# Set local variables
Status1 = 'Status1'
Status2 = 'Status2'
exproCaseProfile = 'Expro_Case_Profile'
Scale = 'Scale'
OtB_Prep = 'OtB_Preparation'
OtB_Deliv = 'OtB_Delivered'
PayP = 'Payment_Processing'
ExproC = 'Expropriation_Case'
newPrioArea = 'NewPriorityArea'

varFieldList = [Status1, Status2, exproCaseProfile, Scale, OtB_Prep, OtB_Deliv, PayP, ExproC, newPrioArea]


# Set local variables
#expression1 = "reclass(!{}!)".format(Status1)
#expression2 = "reclass(!{}!)".format(Status2)
#expression3 = "reclass(!{}!)".format(exproCaseProfile)
#expression4 = "reclass(!{}!)".format(Scale)
#expression5 = "reclass(!{}!)".format(OtB_Prep)
#expression6 = "reclass(!{}!)".format(OtB_Deliv)
#expression7 = "reclass(!{}!)".format(PayP)
#expression8 = "reclass(!{}!)".format(ExproC)
#expression9 = "reclass(!{}!)".format(newPrioArea)

codeblock = """
def reclass(status):
    if status == None:
        return None
    elif status == 0:
        return None
    else:
        return status"""

for field in varFieldList:
    arcpy.AddMessage(field)
    # Set local variables
    expression = "reclass(!{}!)".format(field)
    
    # Execute CalculateField 
    arcpy.CalculateField_management(Status1011_Merge, field, expression, "PYTHON3", codeblock)
    
# Execute CalculateField 
#arcpy.CalculateField_management(Status1011_Merge, Status1, expression1, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, Status2, expression2, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, exproCaseProfile, expression3, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, Scale, expression4, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, OtB_Prep, expression5, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, OtB_Deliv, expression6, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, PayP, expression7, "PYTHON3", codeblock)
#arcpy.CalculateField_management(Status1011_Merge, ExproC, expression8, "PYTHON3", codeblock)

##########################################################
# 8. Assign domain to Status fields
##########################################################
# 6. Assign Domain to Field
#arcpy.AssignDomainToField_management(Status1011_Merge, Priority_Cluster, Domain_name1)
#arcpy.AssignDomainToField_management(Status1011_Merge, Status1, Domain_name2)
#arcpy.AssignDomainToField_management(Status1011_Merge, Status2, Domain_name3)

# list of domain names
#domains = arcpy.da.ListDomains(workSpace)
#for domain in domains:
#    print('Domain name: {0}'.format(domain.name))

##########################################################
# 9. Delete Copied feature layer
##########################################################
# List of Copied Feature Layer
fcList=arcpy.ListFeatureClasses()

# Extract copied feature layer name
rr=re.compile('.*' + format(copyFeatureName))
rList = list(filter(rr.match, fcList))
deleteCopy = ''.join(rList)

# Delete the copied feature layer
arcpy.Delete_management(deleteCopy)

del copyStatus
del tableList
del MasterList
del deleteCopy
del varFieldList
