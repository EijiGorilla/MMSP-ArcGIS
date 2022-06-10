# -*- coding: utf-8 -*-
"""
Created on Sat May 22 08:04:32 2021
This python code updates Site Photo point feature layer to display site images in the popupTemplate
The code does the follows:
    1. convert geotagged photos to points
    2. Add field to the poin feature layer (i.e., Description, Date, ImageURL, and Title)
    3. Enter information in the added fields
    4. Trucnate original point feature layer
    5. Append the new point feature layer to the original
@author: oc3512
"""

import arcpy
import re
import os

arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

# 0. Define parameters
workSpace = arcpy.GetParameterAsText(0)
inFolder = arcpy.GetParameterAsText(1) # Choose a directory where the excel master list is saved.
originalFeature = arcpy.GetParameterAsText(2)

# 1. convert geotagged photos to points
outFeatures = "photo_points"
badPhotoist = "photos_noGPS"
photoOption = "ONLY_GEOTAGGED"
attachmentsOption = "NO_ATTACHMENTS"
photoLayer = arcpy.GeoTaggedPhotosToPoints_management(inFolder, outFeatures, badPhotoist, photoOption, attachmentsOption)

# 2. Add field to the poin feature layer (i.e., Description, Date, ImageURL, and Title)
addFields = ["Description", "ImageURL", "Title"]
for field in addFields:
    arcpy.AddField_management(photoLayer, field, "TEXT", "", "", "", field, "NULLABLE", "")

# 3. Enter information in the added fields
## When a point layer is created, it automatically adds Name and DateTime
## so we can obtain photo names uing 'Name'

### Use Calculate Field
#### Add information to 'Title'
field_Title = "Title"
field_Name = "Name"

codeblock = """
import re
def reclass(name):
    reg = re.sub('.jpg|.png',"",name)
    return reg"""

expression = "reclass(!{}!)".format(field_Name)
arcpy.CalculateField_management(photoLayer, field_Title, expression, "PYTHON3",codeblock)

#### Add information to 'ImageURL'
field_url = "ImageURL"

codeblock = """
import os
imageURL = "https://EijiGorilla.github.io/Site_Photo/MMSP"
def reclass(name):
    path = os.path.join(imageURL, name)
    return path """

expression = "reclass(!{}!)".format(field_Name)
arcpy.CalculateField_management(photoLayer, field_url, expression, "PYTHON3",codeblock)

#### Add information to 'Description'
field_Description = "Description"

codeblock = """
def reclass(name):
    if name:
        desc = "PHOTO"
        return desc
    else:
        return None """

expression = "reclass(!{}!)".format(field_Name)
arcpy.CalculateField_management(photoLayer, field_Description, expression, "PYTHON3",codeblock)


## 4. Trucnate original point feature layer
arcpy.DeleteRows_management(originalFeature)

## Convert to PRS92
copied = "copied_layer"
copyL = arcpy.CopyFeatures_management(photoLayer, copied)

## 5. Append the new point feature layer to the original
arcpy.Append_management(copyL, originalFeature, schema_type = 'NO_TEST')

## 99. Delete
deleteLayer = [photoLayer, copyL]
arcpy.Delete_management(deleteLayer)


