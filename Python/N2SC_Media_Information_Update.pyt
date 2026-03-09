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
        self.tools = [JustMessage1, LowerResolutionImages, DroneImagePoints, DroneViedoPoints]

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
        self.label = "1.2. Generate Drone Image Points"
        self.description = "Generate Drone Image Points"

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
            temp_path = str(Path(*parts[:9]))
            temp_folder = os.path.join(temp_path, 'temp')

            if os.path.exists(temp_folder) and os.path.isdir(temp_folder):
                try:
                    shutil.rmtree(temp_folder)
                    arcpy.AddMessage(f"Folder '{temp_folder}' and all its contents removed successfully.")
                    os.makedirs(temp_folder)
                    
                except OSError as e:
                    arcpy.AddMessage(f"Error: {temp_folder}: {e.strerror}")
            else:
                arcpy.AddMessage(f"Folder '{temp_folder}' does not exist. Create a new temp folder")
                os.makedirs(temp_folder)

            # Copy ONLY top-level images:
            for filename in os.listdir(image_folder):
                file_path = os.path.join(image_folder, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', 'tiff', 'TIFF')):
                    shutil.copy(file_path, temp_folder)

            arcpy.management.GeoTaggedPhotosToPoints(temp_folder, photo_points, badPhotoist, photoOption, attachmentsOption)

            ## Delete temp folder 
            if photo_points:
                shutil.rmtree(temp_folder)

            fields = ['Name', 'Type', 'TimeStamp', 'temp', 'Project', 'Keyword', 'CP']
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
                            cp = re.search(r"[NS][-_]?0\d+[abc]?", row[0]).group()
                            cp = re.sub(r'S-', 'S', cp)
                            cp = re.sub(r'N-', 'N', cp)
                            row[1] = cp
                        except:
                            arcpy.AddMessage(f"No CPs were found.")
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
                            pier_number = re.search(r"P[-_]?\d+[NS]?[SB]?|P[-_]?\d+[-]?[AB]?|BUE[-_]?P\d+[NS]?|DAT[-_]?\d+[NS]?|MT[-_]?\d+-\d+|MT[-_]?\d+-[ABUT]|SCT[-_]?P\d+[NS]?|STR[-_]?[Pp]\d+[NS]?", row[0].upper()).group()
                            # pier_number = re.search(r"[Pp][-_]?\d+[NS]?", row[0].upper()).group()
                            arcpy.AddMessage(pier_number)

                            piern = re.sub("P", "P-", pier_number)
                            piern = re.sub("--","-", piern)
                            piern = re.sub("_","", piern)
                            row[1] = piern.upper()
                        except:
                            arcpy.AddMessage(f"No pier numbers for this image.")
                        cursor.updateRow(row)

            ## Add Depot:
            with arcpy.da.UpdateCursor(photo_points, [imageName_field, project_field, keyword_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        try:
                            depot = re.search(r"DEPOT", row[0].upper()).group()
                            if depot:
                                if row[1] == "N2":
                                    row[2] = "Mabalacat Depot"
                                elif row[1] == "SC":
                                    row[2] = "Banlic Depot"
                        except:
                            arcpy.AddMessage(f"No depot for this image.")
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
                        if len(timeStamp) >= 8:
                            timeStamp = timeStamp[:6]
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
                    output_layer = 'output_layer'
                    arcpy.management.MakeFeatureLayer(input_point_feature, temp_layer, where_clause)
                    arcpy.management.CopyFeatures(temp_layer, output_layer)
                    arcpy.management.DeleteField(output_layer, [feature_field], "KEEP_FIELDS")

                    ## Select nongeo layer
                    where_clause = f"{kwd_field} = '{kwd}'"
                    arcpy.management.SelectLayerByAttribute(nongeo_layer, "NEW_SELECTION", where_clause)
                    where_clause = f"{kwd_field} = '{kwd}' and {timestamp_field} = '{timestamp[i]}'"
                    arcpy.management.SelectLayerByAttribute(nongeo_layer, "NEW_SELECTION", where_clause)
                    arcpy.management.JoinField(output_layer, feature_field, nongeo_layer, kwd_field, main_fields) 
                    arcpy.management.Append(output_layer, nongeotag_layers, schema_type = 'NO_TEST')

                for i, kwd in enumerate(kwds):
                    temp_layer = 'temp_layer'
                    if kwd in tuple(station_names):
                        convert_nongeoimage_to_point_feature(station_point_feature, temp_layer, station_name_field, keyword_field, kwd, timestamp)
                    
                    else:
                        convert_nongeoimage_to_point_feature(pier_point_feauture, temp_layer, piern_field, keyword_field, kwd, timestamp)
                        arcpy.AddMessage("pier")

                # Delete templayer
                # arcpy.management.Delete([temp_layer, output_layer])
                    
            ## Geotagged photos 
            where_clause = f"{x_field} is not Null"
            geotag_layer = arcpy.management.SelectLayerByAttribute(photo_points, "NEW_SELECTION", where_clause)
            result = arcpy.management.GetCount(geotag_layer)
            compile_layer = "compile_layer"

            ##
            # If no nongeotag images,  'nongeo_layer'
            # If nongeotag images exist, use 'nongeotag_layers'
            # result_nongeo = arcpy.management.GetCount(nongeotag_layers)

            ## if geotag_images and nongeotag images:
            try:
                result_nongeo = arcpy.management.GetCount(nongeotag_layers)
            except:
                result_nongeo = arcpy.management.GetCount(nongeo_layer)
            

            if int(result[0]) > 0 and int(result_nongeo[0]) > 0:
                compile_layer = arcpy.management.Append(nongeotag_layers, geotag_layer)
            
            ## only geotag_images:
            elif int(result[0]) > 0 and int(result_nongeo[0]) == 0:
                arcpy.management.CopyFeatures(geotag_layer, compile_layer)
            
            ## only nongeotag images:
            elif int(result[0]) == 0 and int(result_nongeo[0]) > 0:
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
            arcpy.AddMessage("Target layer was successfully truncated")

            # Append new point layer to target layer
            arcpy.management.Append(compile_layer, target_layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("Target layer was successfully appended")

            # Delete all temporary layers
            # arcpy.management.Delete([nongeotag_layers, nongeo_layer, photo_points, geotag_layer])


        Medeia_tables()

class DroneViedoPoints(object):
    def __init__(self):
        self.label = "1.3. Generate Drone Video Footage Points"
        self.description = "Generate Drone Video Footage Points"

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

        fgdb = arcpy.Parameter(
            displayName = "File Geodatabase",
            name = "File Geodatabase",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        video_folder = arcpy.Parameter(
            displayName = "Directory of Video Footage",
            name = "Directory of Video Footage",
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
            displayName = "Pier Point Feature Layer (prs92)",
            name = "Pier Point Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        station_point_fc = arcpy.Parameter(
            displayName = "Station Point Feature Layer (prs92)",
            name = "Station Point Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        target_point_layer = arcpy.Parameter(
            displayName = "Target Video Point Feature Layer (To be updated)",
            name = "Target Video Point Feature Layer (To be updated)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, fgdb, video_folder, dbx_linke_file, pier_point_fc, station_point_fc, target_point_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        fgdb = params[1].valueAsText
        video_folder = params[2].valueAsText
        dbx_link_table = params[3].valueAsText
        pier_point_prs92 = params[4].valueAsText
        station_point_prs92 = params[5].valueAsText
        target_layer = params[6].valueAsText

        def Medeia_tables():
            arcpy.env.overwriteOutput = True

            # Convert PRSS92 to WGS84
            station_point_feature = "station_point_feature"
            pier_point_feature = "pier_point_feature"

            # prs92 = arcpy.SpatialReference(3123)
            wgs84 = arcpy.SpatialReference(4326)
            geo_trans = "PRS_1992_To_WGS_1984_1"
            arcpy.management.Project(station_point_prs92, station_point_feature, wgs84, geo_trans)
            arcpy.management.Project(pier_point_prs92, pier_point_feature, wgs84, geo_trans)

            # Extract station names
            station_point_field = [f.name for f in arcpy.ListFields(station_point_feature) if (f.name == 'Station') or (f.name == 'station')][0]
            station_names = [f[0] for f in arcpy.da.SearchCursor(station_point_feature, [station_point_field])]
            station_names_lower = [f[0].lower() for f in arcpy.da.SearchCursor(station_point_feature, [station_point_field])]
 
            # Create an empty feature class and add fields
            geometry_type = "POINT" # Other options: POLYLINE, POLYGON, MULTIPOINT, MULTIPATCH
            spatial_reference = arcpy.SpatialReference(4326) # WGS 1984 spatial reference
            nongeo_video = 'nongeo_video'
            arcpy.management.CreateFeatureclass(fgdb, nongeo_video, geometry_type, spatial_reference=spatial_reference)

            main_fields = ['Path', 'Name', 'Type', 'TimeStamp', 'temp', 'Project', 'Keyword', 'CP']
            for field in main_fields:
                if (field == 'temp') or (field == 'id'):
                    arcpy.management.AddField(nongeo_video, field, "SHORT", "", "", "", field, "NULLABLE", "REQUIRED")
                else:
                    arcpy.management.AddField(nongeo_video, field, "TEXT", "", "", "", field, "NULLABLE", "REQUIRED")

            # Add video contents from the folder
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

            item_table = pd.DataFrame(columns=main_fields)
            items = [item for item in os.listdir(video_folder) if item.endswith('.mp4')]

            row_values = []
            for i, item in enumerate(items):
                # cp = re.search(r"[NS]-?0\d+[abc]?", item).group()
                # Add pier nuber first, so when station exists, station name is prioritized.
                try:
                    kwd = re.search(r"P[-]?\d+[NS]?[SB]?|P[-]?\d+[-]?[AB]?|BUE[-]?P\d+[NS]?|DAT[-]?\d+[NS]?|MT[-]?\d+-\d+|MT[-]?\d+-[ABUT]|SCT[-]?P\d+[NS]?|STR[-]?[Pp]\d+[NS]?", item.upper()).group().upper()
                except:
                    pass
                try:
                    kwd = [station for station in station_names_lower if station in item.lower()][0].title()
                except:
                    pass

                try:
                    kwd = re.search(r"DEPOT", item.upper()).group()
                except:
                    pass

                row_values.append((None, item, "video", item.split('_')[-1].split('.')[0], i+1, proj, kwd, re.search(r"[NS]-?0\d+[abc]?", item).group()))

            # Insert rows
            with arcpy.da.InsertCursor(nongeo_video, main_fields) as cursor:
                for row in row_values:
                    cursor.insertRow(row)

            # If keyword field is empty, it will fail to create a point:
            null_keyword = [f[0] for f in arcpy.da.SearchCursor(nongeo_video, [keyword_field]) if f[0] is None]
            if null_keyword:
                arcpy.AddMessage('You fail to extract a keyword. Check your code and run again.')

            # Fill in information in the fields
            kwds = [f[0] for f in arcpy.da.SearchCursor(nongeo_video, [keyword_field])]
            row_values_coordinates = []
            for i, kwd in enumerate(kwds):
                arcpy.AddMessage(kwd)
                if kwd == "Depot":
                    if proj == "N2":
                        kwd = "Mabalacat Depot"
                    elif proj == "SC":
                        kwd = "Banlic Depot"

                def convert_video_to_point_feature(point_feature, query_field, kwd):
                    where_clause = f"{query_field} = '{kwd}'"
                    output_layer = 'output_layer'
                    arcpy.MakeFeatureLayer_management(point_feature, output_layer)
                    arcpy.management.SelectLayerByAttribute(output_layer, "NEW_SELECTION", where_clause)
                    xy = [f[0] for f in arcpy.da.SearchCursor(output_layer, ["SHAPE@XY"])]
                    row_values_coordinates.append(xy[0])

                # print(kwd)
                if kwd in tuple(station_names):
                    convert_video_to_point_feature(station_point_feature, station_name_field, kwd)
 
                else:
                    convert_video_to_point_feature(pier_point_feature, piern_field, kwd)
                
            # Update xy coordinates in nongeo_layer
            arcpy.AddMessage(row_values_coordinates)
            with arcpy.da.UpdateCursor(nongeo_video, ['SHAPE@XY']) as cursor:
                for i, row in enumerate(cursor):
                    row[0] = row_values_coordinates[i]
                    cursor.updateRow(row)


            # Generate Near Table and assign unique numbers to 'id' field
            near_table = 'near_table'
            arcpy.analysis.GenerateNearTable(nongeo_video, nongeo_video, near_table, "", "", "", False, 1, "PLANAR", "", "")
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

            ## Join 'id' to nongeo_video layer
            # Join field
            arcpy.management.JoinField(in_data=nongeo_video,
                                    in_field=temp_field, 
                                    join_table=near_table,
                                    join_field="IN_FID",
                                    fields=id_field)
            
            # Update Path using dropbox usercontent link
            table = pd.read_excel(dbx_link_table)
            todict = table.to_dict()
            dbx_link_dict = {name[1]: link[1] for name, link in zip(todict[imageName_field].items(), todict['dbx_link'].items())}

            with arcpy.da.UpdateCursor(nongeo_video, [path_field, imageName_field]) as cursor:
                for row in cursor:
                    if row[1]:
                        row[0] = dbx_link_dict[row[1]]
                    cursor.updateRow(row)
            
            # Truncate target layer
            arcpy.TruncateTable_management(target_layer)
            arcpy.AddMessage("Target layer was successfully truncated")

            # Append new point layer to target layer
            arcpy.management.Append(nongeo_video, target_layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("Target layer was successfully appended")

            # Delete all temporary layers
            arcpy.management.Delete([station_point_feature, pier_point_feature])


        Medeia_tables()
