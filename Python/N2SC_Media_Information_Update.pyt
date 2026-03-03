from pandas.plotting import table

import arcpy
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl
from collections import Counter

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [JustMessage1, DroneImagePoints]

class JustMessage1(object):
    def __init__(self):
        self.label = "1.0. ----- Get Dropbox Link (Run a separate Python code) -----"
        self.description = "Output is Excel file"

class DroneImagePoints(object):
    def __init__(self):
        self.label = "1.1. Add Dropbox Link to Drone Images"
        self.description = "Add Dropbox Link to Drone Images"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']

        image_folder = arcpy.Parameter(
            displayName = "Directory of Drone Images",
            name = "Directory of Drone Images",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        dbx_linke_file = arcpy.Parameter(
            displayName = "Dropbox Link Table (Excel)",
            name = "Dropbox Link Table for Images (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        target_point_layer = arcpy.Parameter(
            displayName = "Target Geotagged Point Feature Layer (To be updated)",
            name = "Target Geotagged Feature Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, image_folder, dbx_linke_file, target_point_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        image_folder = params[1].valueAsText
        dbx_link_table = params[2].valueAsText
        target_layer = params[3].valueAsText

        def Medeia_tables():
            arcpy.env.overwriteOutput = True

            # Generate geotagged points
            outFeatures = "photo_points"
            badPhotoist = "photos_noGPS"
            photoOption = "ALL_PHOTOS" # "ONLY_GEOTAGGED"
            attachmentsOption = "NO_ATTACHMENTS"

            photoLayer = arcpy.management.GeoTaggedPhotosToPoints(image_folder, outFeatures, badPhotoist, photoOption, attachmentsOption)

            # Add fields
            fields = ['Name', 'Type', 'TimeStamp', 'temp', 'Project']
            for field in fields:
                if field == 'temp':
                    arcpy.management.AddField(photoLayer, field, "SHORT", "", "", "", field, "NULLABLE", "REQUIRED")
                else:
                    arcpy.management.AddField(photoLayer, field, "TEXT", "", "", "", field, "NULLABLE", "REQUIRED")

            # For non-geotagged images:
            ## 1. Delete rows with empty x, y
            ## 2. Copy the feature
            ## 3. Join this table with fixed points created in advance using names?

            imageName_field= "Name"
            type_field = "Type"
            timestamp_field = "TimeStamp"
            temp_field = "temp"
            path_field = "Path"
            project_field = "Project"


            # Edit field
            with arcpy.da.UpdateCursor(photoLayer, [project_field]) as cursor:
                for row in cursor:
                    row[0] = proj
                    cursor.updateRow(row)

            with arcpy.da.UpdateCursor(photoLayer, [imageName_field, type_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[1] = 'image'
                    cursor.updateRow(row)

            with arcpy.da.UpdateCursor(photoLayer, [imageName_field, timestamp_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        timeStamp = row[0].split('_')[-1].split('.')[0]
                        row[1] = timeStamp
                        cursor.updateRow(row)

            # Sequantial numbers for 'temp' field
            global rec
            with arcpy.da.UpdateCursor(photoLayer, [temp_field]) as cursor:
                rec=0
                pStart = 1
                pInterval = 1
                for row in cursor:
                    if rec == 0:
                        rec = pStart
                        row[0] = rec
                    else:
                        rec = rec + pInterval
                        row[0] = rec
                    cursor.updateRow(row)

            # Generate Near Table
            out_table = 'near_table'
            id_field = 'id'
            arcpy.analysis.GenerateNearTable(photoLayer, photoLayer, out_table, "", "", "", False, 1, "PLANAR", "", "")

            # Add field 'id'
            arcpy.management.AddField(out_table, id_field, "SHORT", "", "", "", id_field, "NULLABLE", "REQUIRED")

            # Assign group id
            id_field = 'id'
            fid_list = []
            prev_row_id = 0
            prev_id = 1

            with arcpy.da.UpdateCursor(out_table, ['IN_FID', 'NEAR_FID', id_field]) as cursor:
                for i, row in enumerate(cursor):
                    if i == 0:
                        row[2] = 1            
                        fid_list = [row[0], row[1]]       
                    else:
                        new_fid = [row[0], row[1]]            
                        if Counter(fid_list) == Counter(new_fid):
                            row[2] = prev_id
                            prev_id = row[2]       
                        else:
                            row[2] = prev_id + 1
                            prev_id = row[2]
                        fid_list = [row[0], row[1]]
                    cursor.updateRow(row)

            # Join field
            arcpy.management.JoinField(in_data=photoLayer,
                                    in_field=temp_field, 
                                    join_table=out_table,
                                    join_field="IN_FID",
                                    fields=id_field)

            # Update Path using dropbox usercontent link
            table = pd.read_excel(dbx_link_table)
            todict = table.to_dict()
            dbx_link_dict = {name[1]: link[1] for name, link in zip(todict[imageName_field].items(), todict['dbx_link'].items())}

            with arcpy.da.UpdateCursor(photoLayer, [path_field, imageName_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[0] = dbx_link_dict[row[1]]
                    cursor.updateRow(row)

            # Truncate target layer
            arcpy.TruncateTable_management(target_layer)

            # Append new point layer to target layer
            arcpy.management.Append(photoLayer, target_layer, schema_type = 'NO_TEST')


        Medeia_tables()
