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

def replace_strings(string, search_replace_arrays):
    """
    Replace strings
    string: string or text subject to replacement
    search_replace_arrays: list of dictionary containing (search_string, replace_string)
    Example: {
    search_replace_arrays = {
        r'\s+': '',
        r'CPN': 'N-',
        r'[,/].*' : '' # This will remove anything after ',' or '/' in the string
    }
    """
    compile = []
    for search in search_replace_arrays:
        try:
            keyword = re.search(search, string).group(0)
            new_name = re.sub(keyword, search_replace_arrays[search], string)
            compile.append(new_name)
        except:
            pass

    if compile:
        return compile[0]
    else:
        return string

def convert_nongeoimage_to_point_feature(input_point_feature, 
                                         nongeo_layer, 
                                         nongeotag_layer, 
                                         main_fields, 
                                         feature_field, 
                                         timestamp_field, 
                                         kwd_field, 
                                         kwd, 
                                         timestamp,
                                         i):
    #---- Get a point feature from pier point layer:
    where_clause = f"{feature_field} = '{kwd}'"

    #---- Define layers
    temp_layer = 'temp_layer'
    output_layer = "output_layer"
    
    #--- Process
    arcpy.management.MakeFeatureLayer(input_point_feature, temp_layer, where_clause)
    arcpy.management.CopyFeatures(temp_layer, output_layer)
    arcpy.management.DeleteField(output_layer, [feature_field], "KEEP_FIELDS")

    ## Select nongeo layer
    where_clause = f"{kwd_field} = '{kwd}'"
    arcpy.management.SelectLayerByAttribute(nongeo_layer, "NEW_SELECTION", where_clause)
    where_clause = f"{kwd_field} = '{kwd}' and {timestamp_field} = '{timestamp[i]}'"
    arcpy.management.SelectLayerByAttribute(nongeo_layer, "NEW_SELECTION", where_clause)
    arcpy.management.JoinField(output_layer, feature_field, nongeo_layer, kwd_field, main_fields) 
    arcpy.management.Append(output_layer, nongeotag_layer, schema_type = 'NO_TEST')

def get_coordinates_for_nongeotag_media(point_feature, query_field, kwd, row_values_coordinates):
    if kwd == 'SanFernando':
        kwd = 'San Fernando'
    elif kwd == 'SanPedro':
        kwd = 'San Pedro'
    elif kwd == 'Sta.Rosa':
        kwd = 'Sta. Rosa'
    elif kwd == 'Sta.Mesa':
        kwd = 'Sta. Mesa'

    arcpy.AddMessage(f"Found kwd: {kwd}")
    where_clause = f"{query_field} = '{kwd}'"
    output_layer = 'output_layer'
    arcpy.management.MakeFeatureLayer(point_feature, output_layer)
    arcpy.management.SelectLayerByAttribute(output_layer, "NEW_SELECTION", where_clause)
    xy = [f[0] for f in arcpy.da.SearchCursor(output_layer, ["SHAPE@XY"])]
    row_values_coordinates.append(xy[0])


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

def lower_Resolution_Images(image_folder, output_path):
    arcpy.env.overwriteOutput = True

    if image_folder == output_path:
        arcpy.AddError('You are trying to overwrite raw images by choosing the same folder for input and output. Make sure to choose different folders.')
    else:
        image_files = [os.path.join(image_folder, image) for image in os.listdir(image_folder) ]
        for image_path in image_files:
            if image_path.lower().endswith(('PNG', 'png')):
                image = Image.open(image_path)
                rgb_image = image.convert('RGB')
                rgb_image.save(re.sub('png|PNG', 'jpg', image_path), 'JPEG')
                shutil.copy(re.sub('png|PNG', 'jpg', image_path), output_path)
                
                new_basename = f"{Path(image_path).stem}.jpg"
                new_image_path = os.path.join(output_path, new_basename)
                output_file = os.path.join(output_path, new_basename)
                lower_image_quality(new_image_path, output_file, 10) 
            else:
                basename = os.path.basename(image_path)
                output_file = os.path.join(output_path, basename)
                lower_image_quality(image_path, output_file, 10) 

def add_contents_field(point_feature, station_names, proj, project_field, name_field, cp_field, keyword_field, timestamp_field, type_field = None, type_value = None):
    #--- Add type: image or video
    if type_field:
        with arcpy.da.UpdateCursor(point_feature, [name_field, type_field]) as cursor:
            for row in cursor:
                if row[0]:
                    row[1] = type_value # 'image' or 'video'
                cursor.updateRow(row)
    
    #--- Add project name
    with arcpy.da.UpdateCursor(point_feature, [project_field]) as cursor:
        for row in cursor:
            row[0] = proj
            cursor.updateRow(row)

    #--- Add CP name
    with arcpy.da.UpdateCursor(point_feature, [name_field, cp_field]) as cursor:
        for row in cursor:
            if row[0]:
                try:
                    cp = re.search(r"[NS][-_]?0\d+[abc]?", row[0]).group()
                    cp = re.sub(r'S-', 'S', cp)
                    cp = re.sub(r'N-', 'N', cp)
                    row[1] = cp
                except:
                    pass
                cursor.updateRow(row)

    #--- Add station name:
    with arcpy.da.UpdateCursor(point_feature, [name_field, keyword_field]) as cursor:
        for row in cursor:
            if row[0]:
                # check and get index from station point layer when station name from photolayer exists
                idx = [(i, station) for i, station in enumerate(station_names) if station in row[0]]
                if idx:
                    idx = idx[0][0]
                    row[1] = station_names[idx]
                    arcpy.AddMessage(f"Statio names: {station_names[idx]}")
            cursor.updateRow(row)

    #--- Add pier numbers:
    with arcpy.da.UpdateCursor(point_feature, [name_field, keyword_field]) as cursor:
        for row in cursor:
            if row[0]:
                try:
                    fileName = row[0].split(".mp4")[0]
                    pier_number = re.search(r"P[-_]?\d+[-]\d+|P[-_]?\d+[NS]?[SB]?|P[-_]?\d+[-]?[AB]?|BUE[-_]?P\d+[NS]?|DAT[-_]?\d+[NS]?|MT[-_]?\d+-\d+|MT[-_]?\d+-[ABUT]|SCT[-_]?P\d+[NS]?|STR[-_]?[Pp]\d+[NS]?",fileName.upper()).group()
                    # pier_number = re.search(r"[Pp][-_]?\d+[NS]?", row[0].upper()).group()

                    piern = re.sub("P", "P-", pier_number)
                    piern = re.sub("--","-", piern)
                    piern = re.sub("_","", piern)
                    row[1] = piern.upper()
                    arcpy.AddMessage(f"Pier Number: {piern.upper()}")
                except:
                    pass
                cursor.updateRow(row)

    #--- Add chainage label:
    with arcpy.da.UpdateCursor(point_feature, [name_field, keyword_field]) as cursor:
        for row in cursor:
            if row[0]:
                try:
                    chainage = re.search(r'_((\d+)\+(\d+))_', row[0]).group(1)
                    row[1] = chainage.upper()
                    arcpy.AddMessage(f"Chainage: {chainage.upper()}")
                except:
                    pass
                cursor.updateRow(row)

    #--- Add Depot:
    with arcpy.da.UpdateCursor(point_feature, [name_field, project_field, keyword_field]) as cursor:
        for row in cursor:
            if row[0]:
                try:
                    depot = re.search(r"DEPOT", row[0].upper()).group()
                    if depot:
                        if row[1] == "N2":
                            row[2] = "Mabalacat Depot"
                            arcpy.AddMessage(f"Depot name: 'Mabalacat Depot'")
                        elif row[1] == "SC":
                            row[2] = "Banlic Depot"
                            arcpy.AddMessage(f"Depot name: 'Banlic Depot'")
                except:
                    pass
                cursor.updateRow(row)

    #--- Add time stamp from the file name
    with arcpy.da.UpdateCursor(point_feature, [name_field, timestamp_field]) as cursor:
        for row in cursor:
            if row[0]:
                timeStamp = row[0].split('_')[-1].split('.')[0]
                if len(timeStamp) >= 8:
                    timeStamp = timeStamp[:6]
                row[1] = timeStamp
                cursor.updateRow(row)

def assign_group_id_for_display(near_table, id_field, fid_list, prev_id):
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

def update_path_field(layer, path_field, name_field, cp_field, dbx_link_dict):
    with arcpy.da.UpdateCursor(layer, [path_field, name_field, cp_field]) as cursor:
        for row in cursor:
            if row[1]:
                row[0] = dbx_link_dict[row[1]]
            if row[2]:
                #--- Re-format CP notation
                row[2] = re.sub(r'--','-',re.sub(r'^N','N-',row[2]))
                row[2] = re.sub(r'--','-',re.sub(r'^S','S-',row[2]))
            cursor.updateRow(row)

def add_sequential_numbers(layer, temp_field):
    global rec
    with arcpy.da.UpdateCursor(layer, [temp_field]) as cursor:
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

def update_coordinates_to_nongeotagged_points(layer, row_values_coordinates):
    with arcpy.da.UpdateCursor(layer, ['SHAPE@XY']) as cursor:
        for i, row in enumerate(cursor):
            row[0] = row_values_coordinates[i]
            cursor.updateRow(row)

def get_values_from_field(layer, field_name):
    field = [f.name for f in arcpy.ListFields(layer) if f.name == field_name][0]
    values = [re.sub(" ", "", f[0]) for f in arcpy.da.SearchCursor(layer, [field])]
    return values

def prs92_wgs84(layers92, layers84, to_gcs_ref, to_georef):
    for i, layer in enumerate(layers92):
        arcpy.management.Project(layer, layers84[i], to_gcs_ref, to_georef)
            
class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [FixFileNames, JustMessage1, LowerResolutionImages, DroneImagePoints, DroneViedoPoints]


class LowerResolutionImages(object):
    def __init__(self):
        self.label = "1.0. Lower Image Resolution"
        self.description = "Lower Image Resolution"

    def getParameterInfo(self):
        image_folder = arcpy.Parameter(
            displayName = "Folder of Drone Images to Be Processed (raw)",
            name = "Folder of Drone Images to Be Processed",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        output_folder = arcpy.Parameter(
            displayName = "Output Folder (Images)",
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

        lower_Resolution_Images(image_folder, output_path)

class FixFileNames(object):
    def __init__(self):
        self.label = "1.1. Fix File Names"
        self.description = "Fix File Names"

    def getParameterInfo(self):
        image_folder = arcpy.Parameter(
            displayName = "Media Folder of Drone Images and Videos Being Stored",
            name = "Media Folder of Drone Images and Videos Being Stored",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        params = [image_folder]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        local_main_dir = params[0].valueAsText #"C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/99-Media"

        search_array = {
                            r'[Ss]ta.*[Rr]osa': "Sta.Rosa",
                            r'[Ss]ta.*[Mm]esa': "Sta.Mesa",
                            r'[Ss]an.*[fF]ernando': "SanFernando",
                            r'[Ss]an.*[Pp]edro': "SanPedro",
                            r'apalit|APALIT': 'Apalit',
                            r'angeles|ANGELES': 'Angeles',
                            r'clark|CLARK': 'Clark',
                            r'calumpit|CALUMPIT': 'Calumpit',
                            r'cabuyao|CABUYAO': 'Cabuyao',
                            r'muntinlupa|MUNTINLUPA': 'Muntinlupa',
                            r'pacita|PACITA': 'Pacita',
                            r'biñan': 'Biñan',
                            r'abalang|ABALANG': 'Abalang',
                            r'españa': 'España',
                            r'senate-DepEd|senate-depEd|SENATE-DepEd|SENATE-DEPED|Senate|SENATE|senate': 'Senate-DepEd',
                            r'paco|PACO': 'Paco',
                            r'calamba|CALAMBA': 'Calamba',
                            r'blumentritt|BLUMENTRITT': 'Blumentritt',
                            r'banlic|BANLIC': 'Banlic',
                            r'makati|MAKATI': 'Makati',
                            r'megallanes|MEGALLANES': 'Megallanes',
                            r'bicutan|BICUTAN': 'Bicutan',
                        }
        
        for media in ["Images", "Videos"]:
            for proj in ["N2", "SC"]:
                npath = os.path.join(local_main_dir, proj, media)
                for filename in os.listdir(npath):
                    if filename.lower().endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', 'tiff', 'TIFF', 'PNG', 'png', 'mp4')):
                        new_filename = replace_strings(filename, search_array)
                        os.rename(os.path.join(npath, filename), os.path.join(npath, new_filename))
                        arcpy.AddMessage(f"Renamed: {filename} -> {new_filename}")

class JustMessage1(object):
    def __init__(self):
        self.label = "1.2 ----- Get Dropbox Link (Run a separate Python code) -----"
        self.description = "Output is Excel file"

class DroneImagePoints(object):
    def __init__(self):
        self.label = "1.3. Generate Drone Image Points"
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

        chainage_point_fc = arcpy.Parameter(
            displayName = "Chainage Point Feature Layer",
            name = "Chainage Point Feature Layer",
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

        params = [proj, image_folder, dbx_linke_file, pier_point_fc, station_point_fc, chainage_point_fc, target_point_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        image_folder = params[1].valueAsText
        dbx_link_table = params[2].valueAsText
        pier_point_prs92 = params[3].valueAsText
        station_point_prs92 = params[4].valueAsText
        chainage_point_prs92 = params[5].valueAsText
        target_layer = params[6].valueAsText

        def Medeia_tables():
            arcpy.env.overwriteOutput = True

            # Generate geotagged points
            photo_points = "photo_points"
            badPhotoist = "photos_noGPS"
            photoOption = "ALL_PHOTOS" # "ONLY_GEOTAGGED"
            attachmentsOption = "NO_ATTACHMENTS"


            # Convert PRSS92 to WGS84
            station_point_feature = "station_point_feature"
            pier_point_feature = "pier_point_feature"
            chainage_point_feature = "chainage_point_feature"
            ref_points_wgs84 = [station_point_feature, pier_point_feature, chainage_point_feature]
            ref_points_prs92 = [station_point_prs92, pier_point_prs92, chainage_point_prs92]

            wgs84 = arcpy.SpatialReference(4326)
            geo_trans = "PRS_1992_To_WGS_1984_1"

            prs92_wgs84(ref_points_prs92, ref_points_wgs84, wgs84, geo_trans)

            #--------------------------------------------------------------#
            #         Proprocess files & Create Geotagged Images           #
            #--------------------------------------------------------------#

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

            #--- Copy ONLY top-level images:
            for filename in os.listdir(image_folder):
                file_path = os.path.join(image_folder, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', 'tiff', 'TIFF')):
                    shutil.copy(file_path, temp_folder)

            #--- Create point features using images
            arcpy.management.GeoTaggedPhotosToPoints(temp_folder, photo_points, badPhotoist, photoOption, attachmentsOption)

            #--- Add main fiedls
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
            station_name_field = 'Station'
            piern_field = 'PierNumber'
            chainage_point_field = 'KmSpot'
            keyword_field = 'Keyword'
            id_field = 'id'
            cp_field = 'CP'
        
            #--- Get station names from station point feature
            station_names = get_values_from_field(station_point_feature, station_name_field)

            #--- Get chainage labels from chainage point feature
            chainage_labels = get_values_from_field(chainage_point_feature, 'KmSpot')

            #--- Get pier numbers
            pier_numbers = get_values_from_field(pier_point_feature, 'PierNumber')
            pier_numbers.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

            #--- Add contents to fields (project, CP, station name, pier number, depot, time stamp) based on the file name
            add_contents_field(photo_points, station_names, proj, project_field, imageName_field, cp_field, keyword_field, timestamp_field, type_field, 'image')

            #--- Add cooridnates using keyword
            kwds = [f[0] for f in arcpy.da.SearchCursor(photo_points, [keyword_field])]


            row_values_coordinates = []

            for kwd in kwds:
                arcpy.AddMessage(f"Search for {kwd}:")
                if kwd in tuple(station_names):
                    get_coordinates_for_nongeotag_media(station_point_feature, station_name_field, kwd, row_values_coordinates)
                elif kwd == "Mabalacat Depot" or kwd == "Banlic Depot":
                    get_coordinates_for_nongeotag_media(station_point_feature, station_name_field, kwd, row_values_coordinates)
                elif kwd in tuple(chainage_labels):
                    get_coordinates_for_nongeotag_media(chainage_point_feature, chainage_point_field, kwd, row_values_coordinates)
                elif kwd in tuple(pier_numbers):
                    get_coordinates_for_nongeotag_media(pier_point_feature, piern_field, kwd, row_values_coordinates)

                #-- When no kwd was found:
                else:
                    #--- Pier numbers:
                    try:
                        search_kwds = [item for item in pier_numbers if re.search(kwd, item)]
                        kwd = search_kwds[0]
                        get_coordinates_for_nongeotag_media(pier_point_feature, piern_field, kwd, row_values_coordinates)
                    
                    #--- Chainage:
                    except:
                        search_kwds = [item for item in chainage_labels if re.search(kwd, item)]
                        kwd = search_kwds[0]
                        get_coordinates_for_nongeotag_media(chainage_point_feature, piern_field, kwd, row_values_coordinates)

            #--- Update xy coordinates in nongeo_layer
            arcpy.AddMessage(f"row_values_coordinates: {row_values_coordinates}")
            update_coordinates_to_nongeotagged_points(photo_points, row_values_coordinates)

            #--- Sequantial numbers for 'temp' field            
            add_sequential_numbers(photo_points, temp_field)

            # Generate Near Table
            near_table = 'near_table'
            arcpy.analysis.GenerateNearTable(photo_points, photo_points, near_table, "", "", "", False, 1, "PLANAR", "", "")
            arcpy.management.AddField(near_table, temp_field, "SHORT", "", "", "", temp_field, "NULLABLE", "REQUIRED")
            add_sequential_numbers(near_table, temp_field)
            arcpy.management.AddField(near_table, id_field, "SHORT", "", "", "", id_field, "NULLABLE", "REQUIRED")           # Assign group id

            fid_list = []
            prev_id = 1
            assign_group_id_for_display(near_table, id_field, fid_list, prev_id)

            # Join field
            arcpy.management.JoinField(in_data=photo_points,
                                    in_field=temp_field, 
                                    join_table=near_table,
                                    join_field=temp_field,
                                    fields=id_field)

            # Update Path using dropbox usercontent link
            table = pd.read_excel(dbx_link_table)
            todict = table.to_dict()
            dbx_link_dict = {name[1]: link[1] for name, link in zip(todict[imageName_field].items(), todict['dbx_link'].items())}
            update_path_field(photo_points, path_field, imageName_field, cp_field, dbx_link_dict)

            # Truncate target layer
            arcpy.TruncateTable_management(target_layer)
            arcpy.AddMessage("Target layer was successfully truncated")

            # Append new point layer to target layer
            arcpy.management.Append(photo_points, target_layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("Target layer was successfully appended")

            # Delete all temporary layers
            arcpy.management.Delete([photo_points])

            #--- Delete temp folder 
            # if photo_points:
            #     shutil.rmtree(temp_folder)


        Medeia_tables()

class DroneViedoPoints(object):
    def __init__(self):
        self.label = "1.4. Generate Drone Video Footage Points"
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

        chainage_point_fc = arcpy.Parameter(
            displayName = "Chainage Point Feature Layer",
            name = "Chainage Point Feature Layer",
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

        params = [proj, fgdb, video_folder, dbx_linke_file, pier_point_fc, station_point_fc, chainage_point_fc, target_point_layer]
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
        chainage_point_prs92 = params[6].valueAsText
        target_layer = params[7].valueAsText

        def Medeia_tables():
            arcpy.env.overwriteOutput = True

            # Convert PRSS92 to WGS84
            station_point_feature = "station_point_feature"
            pier_point_feature = "pier_point_feature"
            chainage_point_feature = "chainage_point_feature"
            ref_points_wgs84 = [station_point_feature, pier_point_feature, chainage_point_feature]
            ref_points_prs92 = [station_point_prs92, pier_point_prs92, chainage_point_prs92]

            # prs92 = arcpy.SpatialReference(3123)
            wgs84 = arcpy.SpatialReference(4326)
            geo_trans = "PRS_1992_To_WGS_1984_1"
            prs92_wgs84(ref_points_prs92, ref_points_wgs84, wgs84, geo_trans)

            #--- Get station names from station point feature
            station_names = get_values_from_field(station_point_feature, "Station")

            #--- Get chainage labels from chainage point feature
            chainage_labels = get_values_from_field(chainage_point_feature, 'KmSpot')

            #--- Get pier numbers
            pier_numbers = get_values_from_field(pier_point_feature, 'PierNumber')
            pier_numbers.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))

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
            videoName_field= "Name"
            type_field = "Type"
            timestamp_field = "TimeStamp"
            temp_field = "temp"
            path_field = "Path"
            project_field = "Project"
            station_name_field = 'Station'
            piern_field = 'PierNumber'
            chainage_point_field = 'KmSpot'
            keyword_field = 'Keyword'
            id_field = 'id'
            cp_field = 'CP'

            # item_table = pd.DataFrame(columns=main_fields)
            items = [item for item in os.listdir(video_folder) if item.endswith('.mp4')]

            row_values = []
            for i, item in enumerate(items):
                row_values.append((None, item, "video", None, i+1, None, None, None))
                
            # Insert rows
            with arcpy.da.InsertCursor(nongeo_video, main_fields) as cursor:
                for row in row_values:
                    cursor.insertRow(row)

            #--- Add contents to fields (project, CP, station name, pier number, depot, time stamp) based on the file name
            add_contents_field(nongeo_video, station_names, proj, project_field, videoName_field, cp_field, keyword_field, timestamp_field)          

            ## Add xy coordinates based on station names and pier numbers:
            kwds = [f[0] for f in arcpy.da.SearchCursor(nongeo_video, [keyword_field])]
            row_values_coordinates = []

            for kwd in kwds:
                arcpy.AddMessage(f"Search for {kwd}:")
                if kwd in tuple(station_names):
                    get_coordinates_for_nongeotag_media(station_point_feature, station_name_field, kwd, row_values_coordinates)
                elif kwd == "Mabalacat Depot" or kwd == "Banlic Depot":
                    get_coordinates_for_nongeotag_media(station_point_feature, station_name_field, kwd, row_values_coordinates)
                elif kwd in tuple(chainage_labels):
                    get_coordinates_for_nongeotag_media(chainage_point_feature, chainage_point_field, kwd, row_values_coordinates)
                elif kwd in tuple(pier_numbers):
                    get_coordinates_for_nongeotag_media(pier_point_feature, piern_field, kwd, row_values_coordinates)
        
                #-- When no kwd was found:
                else:
                    #--- Pier numbers:
                    try:
                        search_kwds = [item for item in pier_numbers if re.search(kwd, item)]
                        kwd = search_kwds[0]
                        get_coordinates_for_nongeotag_media(pier_point_feature, piern_field, kwd, row_values_coordinates)
                    
                    #--- Chainage:
                    except:
                        search_kwds = [item for item in chainage_labels if re.search(kwd, item)]
                        kwd = search_kwds[0]
                        get_coordinates_for_nongeotag_media(chainage_point_feature, piern_field, kwd, row_values_coordinates)
                
            #--- Update xy coordinates in nongeo_layer
            arcpy.AddMessage(row_values_coordinates)
            update_coordinates_to_nongeotagged_points(nongeo_video, row_values_coordinates)

            # Generate Near Table and assign unique numbers to 'id' field
            near_table = 'near_table'
            arcpy.analysis.GenerateNearTable(nongeo_video, nongeo_video, near_table, "", "", "", False, 1, "PLANAR", "", "")
            arcpy.management.AddField(near_table, temp_field, "SHORT", "", "", "", temp_field, "NULLABLE", "REQUIRED")
            add_sequential_numbers(near_table, temp_field)
            arcpy.management.AddField(near_table, id_field, "SHORT", "", "", "", id_field, "NULLABLE", "REQUIRED")

            # Assign group id
            fid_list = []
            prev_id = 1
            assign_group_id_for_display(near_table, id_field, fid_list, prev_id)

            ## Join 'id' to nongeo_video layer
            # Join field
            arcpy.management.JoinField(in_data=nongeo_video,
                                    in_field=temp_field, 
                                    join_table=near_table,
                                    join_field=temp_field,
                                    fields=id_field)
            
            # Update Path using dropbox usercontent link
            table = pd.read_excel(dbx_link_table)
            todict = table.to_dict()
            dbx_link_dict = {name[1]: link[1] for name, link in zip(todict[videoName_field].items(), todict['dbx_link'].items())}
            update_path_field(nongeo_video, path_field, videoName_field, cp_field, dbx_link_dict)
            
            # Truncate target layer
            arcpy.TruncateTable_management(target_layer)
            arcpy.AddMessage("Target layer was successfully truncated")

            # Append new point layer to target layer
            arcpy.management.Append(nongeo_video, target_layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("Target layer was successfully appended")

            # Delete all temporary layers
            arcpy.management.Delete([station_point_feature, pier_point_feature])


        Medeia_tables()
