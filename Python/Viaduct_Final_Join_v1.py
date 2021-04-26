# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 14:46:35 2021

@author: oc3512
"""
import arcpy
import re
from collections import Counter
import numpy as np
import os

arcpy.env.overwriteOutput = True

workSpace = arcpy.GetParameterAsText(0)
inputFeature = arcpy.GetParameterAsText(1)
joinField = arcpy.GetParameterAsText(2)
joinTable = arcpy.GetParameterAsText(3)
transferField = arcpy.GetParameterAsText(4)

arcpy.env.workspace = workSpace

# Join Field
arcpy.JoinField_management(in_data=inputFeature, in_field=joinField, join_table=joinTable, join_field=joinField, fields=transferField)

# create tempid
addField = "tempid"
arcpy.AddField_management(mergedLayer, addField, "Short", field_alias = addField, field_is_nullable="NULLABLE")

# Sort field (idd) tranferField
outName = arcpy.Describe(inputFeature).name
finalLayer = outName + "_FINAL"
sortedFinalLayer = arcpy.Sort_management(inputFeature, finalLayer, [[transferField, "ASCENDING"]])

# Define Domain
# list of domain names
domains = arcpy.da.ListDomains(workSpace)
domainList = []
for domain in domains:
    domainList.append(domain.name)
    
regType = re.compile(r'.*ViaductType|.*viaducttype|.*viaductType|.*Viaduct Type|.*viadcut Type')
regStatus = re.compile(r'.*ViaductStatus|.*viaductStatus|.*viaductstatus|.*Viaduct Status')

domainType = list(filter(regType.match, domainList))
domainStatus = list(filter(regStatus.match, domainList))

arcpy.AssignDomainToField_management(sortedFinalLayer, "Type", domainType[0])
arcpy.AssignDomainToField_management(sortedFinalLayer, "Status1", domainStatus[0])

# Delete 'tempid' Field
arcpy.DeleteField_management(sortedFinalLayer, addField)