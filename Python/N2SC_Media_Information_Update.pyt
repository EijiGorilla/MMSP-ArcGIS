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
from PIL import Image, ExifTags
from datetime import datetime
from pathlib import Path
import shutil

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [JustMessage1, LowerResolutionImages, DroneImagePoints]

class JustMessage1(object):
    def __init__(self):
        self.label = "1.0. ----- Get Dropbox Link (Run a separate Python code) -----"
        self.description = "Output is Excel file"

class LowerResolutionImages(object):
    def __init__(self):
        self.label = "1.1. Lower Image Resolution"
        self.description = "Lower Image Resolution"

    def getParameterInfo(self):
        image_folder = arcpy.Parameter(
            displayName = "Folder of Drone Images to Be Processed",
            name = "Folder of Drone Images to Be Processed",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        output_folder = arcpy.Parameter(
            displayName = "Output Folder",
            name = "Output Folder",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        params = [image_folder, output_folder]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        image_folder = params[0].valueAsText
        output_path = params[1].valueAsText
        
        def lower_image_quality(input_path, output_path, quality):
            """
            Saves a JPEG imag with a lower quality setting (1-100) to reduce file size.
            95 is considered high quality, 1 is very low.
            """
            try:
                with Image.open(input_path) as img:
                    # The quality parameter is effective for JPEG and related formats.
                    # Save with original EXIF data
    
                    # Check if EXIF data exists
                    exif_data = img.info.get('exif')
                    if exif_data:
                        img.save(output_path, quality=quality, exif=exif_data, optimize=True)
                        arcpy.AddMessage(f"Saved {output_path} with metadata. Quality = {quality}")
                    else:
                        img.save(output_path, quality=quality, optimize=True)
                        arcpy.AddMessage(f"Saved {output_path} without metadata.")

            except IOError as e:
                arcpy.AddError(f"Error processing image: {e}")

        def lower_Resolution_Images():
            arcpy.env.overwriteOutput = True

            if image_folder == output_path:
                arcpy.AddError('You are trying to overwrite raw images by choosing the same folder for input and output. Make sure to choose different folders.')
            else:
                image_files = [os.path.join(image_folder, image) for image in os.listdir(image_folder) ]
                for image_path in image_files:
                    basename = os.path.basename(image_path)
                    output_file = os.path.join(output_path, basename)
                    lower_image_quality(image_path, output_file, 10) 

        lower_Resolution_Images()

class DroneImagePoints(object):
    def __init__(self):
        self.label = "1.2. Generate Geotagged Points and Add Dropbox Link to Images"
        self.description = "Generate Geotagged Points and Add Dropbox Link to Images"

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

        pier_point_fc = arcpy.Parameter(
            displayName = "Pier Point Feature Layer",
            name = "Pier Point Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        station_point_fc = arcpy.Parameter(
            displayName = "Station Point Feature Layer",
            name = "Station Point Feature Layer",
            datatype = "GPFeatureLayer",
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

        params = [proj, image_folder, dbx_linke_file, pier_point_fc, station_point_fc, target_point_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        image_folder = params[1].valueAsText
        dbx_link_table = params[2].valueAsText
        pier_point_feauture = params[3].valueAsText
        station_point_feature = params[4].valueAsText
        target_layer = params[5].valueAsText

        def get_image_capture_time(filename):
            image = Image.open(filename)
            # Get all EXIF data
            image_exif = image._getexif()

            if image_exif:
                # Map tag codes to tag names for readability
                exif = {
                    ExifTags.TAGS[k]: v
                    for k, v in image_exif.items()
                    if k in ExifTags.TAGS and type(v) is not bytes
                }

                # Try to get the original date and time
                if 'DateTimeOriginal' in exif:
                    date_str = exif['DateTimeOriginal']
                    # Convert the string to a Python datetime object
                    date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    yyyy = date_obj.year
                    mm = date_obj.month
                    dd = date_obj.day

                    if mm < 10:
                        mm = "0" + str(mm)
                    date_str = f'{yyyy}{mm}{dd}'
                    return date_str
                else:
                    return "DateTimeOriginal tag not found"
            else:
                return "No EXIF data found for this image"

        def unique(lists):
            collect = []
            unique_list = pd.Series(lists).drop_duplicates().tolist()
            for x in unique_list:
                collect.append(x)
            return(collect)

        def Medeia_tables():
            arcpy.env.overwriteOutput = True

            # Generate geotagged points
            photo_points = "photo_points"
            badPhotoist = "photos_noGPS"
            photoOption = "ALL_PHOTOS" # "ONLY_GEOTAGGED"
            attachmentsOption = "NO_ATTACHMENTS"

            full_path = Path(image_folder)
            parts = full_path.parts
            temp_path = str(Path(*parts[:7]))
            temp_folder = os.path.join(temp_path, 'temp')

            if os.path.exists(temp_folder) and os.path.isdir(temp_folder):
                try:
                    shutil.rmtree(temp_folder)
                    print(f"Folder '{temp_folder}' and all its contents removed successfully.")
                    os.makedirs(temp_folder)
                    
                except OSError as e:
                    print(f"Error: {temp_folder}: {e.strerror}")
            else:
                print(f"Folder '{temp_folder}' does not exist. Create a new temp folder")
                os.makedirs(temp_folder)

            # Copy ONLY top-level images:
            for filename in os.listdir(image_folder):
                file_path = os.path.join(image_folder, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', 'tiff', 'TIFF')):
                    shutil.copy(file_path, temp_folder)

            arcpy.management.GeoTaggedPhotosToPoints(temp_folder, photo_points, badPhotoist, photoOption, attachmentsOption)

            fields = ['Name', 'Type', 'TimeStamp', 'temp', 'Project', 'Keyword', 'id', 'CP']
            for field in fields:
                if (field == 'temp') or (field == 'id'):
                    arcpy.management.AddField(photo_points, field, "SHORT", "", "", "", field, "NULLABLE", "REQUIRED")
                else:
                    arcpy.management.AddField(photo_points, field, "TEXT", "", "", "", field, "NULLABLE", "REQUIRED")

            imageName_field= "Name"
            type_field = "Type"
            timestamp_field = "TimeStamp"
            temp_field = "temp"
            path_field = "Path"
            project_field = "Project"
            dateTaken_field = 'dateTaken'
            station_name_field = 'Station'
            piern_field = 'PierNumber'
            keyword_field = 'Keyword'
            id_field = 'id'
            cp_field = 'CP'

            main_fields = [f.name for f in arcpy.ListFields(photo_points) if f.name not in ("OBJECTID", "Shape")]

            # Get station names from station point feature
            station_point_field = [f.name for f in arcpy.ListFields(station_point_feature) if (f.name == 'Station') or (f.name == 'station')][0]
            station_names = [f[0] for f in arcpy.da.SearchCursor(station_point_feature, [station_point_field])]
            station_names_lower = [f[0].lower() for f in arcpy.da.SearchCursor(station_point_feature, [station_point_field])]
            # Get pier number from photo points layer


            # Edit field
            ## Add project name
            with arcpy.da.UpdateCursor(photo_points, [project_field]) as cursor:
                for row in cursor:
                    row[0] = proj
                    cursor.updateRow(row)

            ## Add CP name
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, cp_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        try:
                            cp = re.search(r"[NS]-?0\d+[abc]?", row[0]).group()
                            row[1] = cp
                        except:
                            print(f"No CPs were found.")
                        cursor.updateRow(row)

            ## Add station name:
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, keyword_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        # check and get index from station point layer when station name from photolayer exists
                        idx = [(i, station) for i, station in enumerate(station_names_lower) if station in row[0].lower()]
                        if idx:
                            idx = idx[0][0]
                            row[1] = station_names[idx].title()
                    cursor.updateRow(row)

            ## Add pier numbers:
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, keyword_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        try:
                            pier_number = re.search(r"[Pp]\d+[NS]?", row[0].upper()).group()
                            print(pier_number)
                            row[1] = re.sub("P", "P-", pier_number)
                        except:
                            print(f"No pier numbers for this image.")
                        cursor.updateRow(row)

            ## Add Depot:
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, project_field, keyword_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        try:
                            depot = re.search(r"DEPOT", row[0].upper()).group()
                            print(depot)
                            if row[1] == "N2":
                                row[2] = "Mabalacat Depot"
                            elif row[1] == "SC":
                                row[2] = "Banlic Depot"
                        except:
                            print(f"No depot for this image.")
                        cursor.updateRow(row)

            ## Add type: image or video
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, type_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[1] = 'image'
                    cursor.updateRow(row)

            ## Add time stamp from the file name
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, timestamp_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        timeStamp = row[0].split('_')[-1].split('.')[0]
                        row[1] = timeStamp
                        cursor.updateRow(row)
            
            ######### For Non-Geotagged Images ##########################
            # If images are not geotagged, filter out all the geotagged layers.
            nongeo_layer = 'nongeo_images'
            x_field = 'X'
            where_clause = f"{x_field} is Null"
            arcpy.management.MakeFeatureLayer(photo_points, nongeo_layer, where_clause)

            ## Count rows of nongeotagged images
            result = arcpy.management.GetCount(nongeo_layer)
            kwds = [f[0] for f in arcpy.da.SearchCursor(nongeo_layer, [keyword_field])]

            if int(result[0]) > 0:
                # Create an empty layer for compilation
                nongeotag_layers = 'nongeotag_layers'
                arcpy.management.CopyFeatures(photo_points, nongeotag_layers)
                arcpy.management.TruncateTable(nongeotag_layers)
                timestamp = [f[0] for f in arcpy.da.SearchCursor(nongeo_layer, ['TimeStamp'])]


                def convert_nongeoimage_to_point_feature(input_point_feature, temp_layer, feature_field, kwd_field, kwd, timestamp):
                    ## Get a point feature from pier point layer:
                    where_clause = f"{feature_field} = '{kwd}'"
                    arcpy.management.MakeFeatureLayer(input_point_feature, temp_layer, where_clause)
                    arcpy.management.CopyFeatures(temp_layer, temp_layer)
                    arcpy.management.DeleteField(temp_layer, [feature_field], "KEEP_FIELDS")

                    ## Select nongeo layer
                    where_clause = f"{kwd_field} = '{kwd}'"
                    arcpy.management.SelectLayerByAttribute(nongeo_layer, "NEW_SELECTION", where_clause)
                    where_clause = f"{kwd_field} = '{kwd}' and {timestamp_field} = '{timestamp[i]}'"
                    arcpy.management.SelectLayerByAttribute(nongeo_layer, "NEW_SELECTION", where_clause)
                    arcpy.management.JoinField(temp_layer, feature_field, nongeo_layer, kwd_field, main_fields) 
                    arcpy.management.Append(temp_layer, nongeotag_layers, schema_type = 'NO_TEST')

                for i, kwd in enumerate(kwds):
                    temp_layer = 'temp_layer'
                    if kwd in tuple(station_names):
                        convert_nongeoimage_to_point_feature(station_point_feature, temp_layer, station_name_field, keyword_field, kwd, timestamp)
                    
                    else:
                        convert_nongeoimage_to_point_feature(pier_point_feauture, temp_layer, piern_field, keyword_field, kwd, timestamp)

                # Delete templayer
                arcpy.management.Delete(temp_layer)
                    
            ## Geotagged photos 
            where_clause = f"{x_field} is not Null"
            geotag_layer = arcpy.management.SelectLayerByAttribute(photo_points, "NEW_SELECTION", where_clause)
            result = arcpy.management.GetCount(geotag_layer)
            compile_layer = "compile_layer"

            if int(result[0]) > 0:
                compile_layer = arcpy.management.Append(nongeotag_layers, geotag_layer)

            else:
                arcpy.management.CopyFeatures(nongeotag_layers, compile_layer)

            # Sequantial numbers for 'temp' field
            global rec
            with arcpy.da.UpdateCursor(compile_layer, [temp_field]) as cursor:
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
            near_table = 'near_table'
            arcpy.analysis.GenerateNearTable(compile_layer, compile_layer, near_table, "", "", "", False, 1, "PLANAR", "", "")
            arcpy.management.AddField(near_table, id_field, "SHORT", "", "", "", id_field, "NULLABLE", "REQUIRED")


            # Assign group id
            fid_list = []
            prev_id = 1

            with arcpy.da.UpdateCursor(near_table, ['IN_FID', 'NEAR_FID', id_field]) as cursor:
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
            arcpy.management.JoinField(in_data=compile_layer,
                                    in_field=temp_field, 
                                    join_table=near_table,
                                    join_field="IN_FID",
                                    fields=id_field)

            # Update Path using dropbox usercontent link
            table = pd.read_excel(dbx_link_table)
            todict = table.to_dict()
            dbx_link_dict = {name[1]: link[1] for name, link in zip(todict[imageName_field].items(), todict['dbx_link'].items())}

            with arcpy.da.UpdateCursor(compile_layer, [path_field, imageName_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[0] = dbx_link_dict[row[1]]
                    cursor.updateRow(row)

            # Truncate target layer
            arcpy.TruncateTable_management(target_layer)

            # Append new point layer to target layer
            arcpy.management.Append(compile_layer, target_layer, schema_type = 'NO_TEST')

            # Delete all temporary layers
            arcpy.management.Delete([nongeotag_layers, nongeo_layer, photo_points, geotag_layer])


        Medeia_tables()
