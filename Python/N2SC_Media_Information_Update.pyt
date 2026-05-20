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
                    fileName = re.split(r'\.mp4|\.m4v', row[0])[0]
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
    with arcpy.da.UpdateCursor(layer, ['SHAPE@XY', 'SHAPE@Z']) as cursor:
        for i, row in enumerate(cursor):
            row[0] = row_values_coordinates[i]
            row[1] = 0
            cursor.updateRow(row)

def get_values_from_field(layer, field_name):
    field = [f.name for f in arcpy.ListFields(layer) if f.name == field_name][0]
    values = [re.sub(" ", "", f[0]) for f in arcpy.da.SearchCursor(layer, [field])]
    return values

def prs92_wgs84(layers92, layers84, to_gcs_ref, geotrans):
    for i, layer in enumerate(layers92):
        if arcpy.Describe(layer).spatialReference.factoryCode == 4326:
            layers84[i] = layer
        else:
            arcpy.management.Project(layer, layers84[i], to_gcs_ref, geotrans)

def get_reference_names(ref_points, fields):
    all_names = []
    for i, point_fc in enumerate(ref_points):
        names = get_values_from_field(point_fc, fields[i])
        if fields[i] == 'PierNumber':
            names.sort(key=lambda x: int(re.findall(r'\d+', x)[0]))
        all_names.append(names)
    return all_names

def get_xyz_for_media_files(kwds, ref_points, ref_names, ref_fields, empty_list):
    for kwd in kwds:
        arcpy.AddMessage(f"Search for {kwd}:")
        station_pt, piern_pt, chainage_pt = ref_points
        station_names, piern_numbers, chainage_labels = ref_names
        station_field, piern_field, chainage_field = ref_fields

        if kwd in tuple(station_names):
            get_coordinates_for_nongeotag_media(station_pt, station_field, kwd, empty_list)
        elif kwd == "Mabalacat Depot" or kwd == "Banlic Depot":
            get_coordinates_for_nongeotag_media(station_pt, station_field, kwd, empty_list)
        elif kwd in tuple(piern_numbers):
            get_coordinates_for_nongeotag_media(piern_pt, piern_field, kwd, empty_list)
        elif kwd in tuple(chainage_labels):
            get_coordinates_for_nongeotag_media(chainage_pt, chainage_field, kwd, empty_list)
        #-- When no kwd was found:
        else:
            #--- Pier numbers:
            try:
                try:
                    search_kwds = [item for item in piern_numbers if re.search(kwd, item)]
                    kwd = search_kwds[0]
                    get_coordinates_for_nongeotag_media(piern_pt, piern_field, kwd, empty_list)
                except:
                    search_kwds = [item for item in chainage_labels if re.search(kwd, item)]
                    kwd = search_kwds[0]
                    get_coordinates_for_nongeotag_media(chainage_pt, chainage_field, kwd, empty_list)
            except:
                pass

    return empty_list
    
class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [FixFileNames, JustMessage1, LowerResolutionImages, GenerateDronePoints]


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
                    if filename.lower().endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', 'tiff', 'TIFF', 'PNG', 'png', 'mp4', 'm4v')):
                        new_filename = replace_strings(filename, search_array)
                        os.rename(os.path.join(npath, filename), os.path.join(npath, new_filename))
                        arcpy.AddMessage(f"Renamed: {filename} -> {new_filename}")

class JustMessage1(object):
    def __init__(self):
        self.label = "1.2 ----- Get Dropbox Link (Run a separate Python code) -----"
        self.description = "Output is Excel file"

class GenerateDronePoints(object):
    def __init__(self):
        self.label = "1.3. Generate Media Points"
        self.description = "Generate Media Points"

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

        media_type = arcpy.Parameter(
            displayName = "Type of Media (image or video)",
            name = "Type of Media (image or video)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        media_type.filter.type = "ValueList"
        media_type.filter.list = ['image', 'video']

        media_folder = arcpy.Parameter(
            displayName = "Directory of Drone Files (Images or Videos)",
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

        params = [proj, fgdb, media_type, media_folder, dbx_linke_file, pier_point_fc, station_point_fc, chainage_point_fc, target_point_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        fgdb = params[1].valueAsText
        media_type = params[2].valueAsText
        media_folder = params[3].valueAsText
        dbx_link_table = params[4].valueAsText
        pier_point_prs92 = params[5].valueAsText
        station_point_prs92 = params[6].valueAsText
        chainage_point_prs92 = params[7].valueAsText
        target_layer = params[8].valueAsText

        def Medeia_tables():
            arcpy.env.overwriteOutput = True

            # Convert PRSS92 to WGS84
            station_point_feature = "station_point_feature"
            pier_point_feature = "pier_point_feature"
            chainage_point_feature = "chainage_point_feature"
            ref_points_wgs84 = [station_point_feature, pier_point_feature, chainage_point_feature]
            ref_points_prs92 = [station_point_prs92, pier_point_prs92, chainage_point_prs92]

            wgs84 = arcpy.SpatialReference(4326)
            geo_trans = "PRS_1992_To_WGS_1984_1"
            prs92_wgs84(ref_points_prs92, ref_points_wgs84, wgs84, geo_trans)

            #--- Fields
            name_field= "Name"
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
            ref_fields = [station_name_field, piern_field, chainage_point_field]

            #--- Lists of reference names            
            ref_names = get_reference_names(ref_points_wgs84, ref_fields)

            #--- Create an empty feature class and add fields
            spatial_reference = arcpy.SpatialReference(4326) # WGS 1984 spatial reference
            media_point = 'media_point'
            arcpy.management.CreateFeatureclass(fgdb, media_point, "POINT", has_z="ENABLED", spatial_reference=spatial_reference)

            main_fields = ['Path', 'Name', 'Type', 'TimeStamp', 'temp', 'Project', 'Keyword', 'CP']
            for field in main_fields:
                if (field == 'temp') or (field == 'id'):
                    arcpy.management.AddField(media_point, field, "SHORT", "", "", "", field, "NULLABLE", "REQUIRED")
                else:
                    arcpy.management.AddField(media_point, field, "TEXT", "", "", "", field, "NULLABLE", "REQUIRED")


            #--- Add contents from the folder
            items = [item for item in os.listdir(media_folder) if item.endswith(('.jpg', '.JPG', '.jpeg', '.JPEG', 'tiff', 'TIFF', 'mp4', 'm4v'))]

            row_values = []
            for i, item in enumerate(items):
                row_values.append((None, item, media_type, None, i+1, None, None, None))
                
            # Insert rows
            with arcpy.da.InsertCursor(media_point, main_fields) as cursor:
                for row in row_values:
                    cursor.insertRow(row)

            # Add contents to fields (project, CP, station name, pier number, depot, time stamp) based on the file name
            add_contents_field(media_point, ref_names[0], proj, project_field, name_field, cp_field, keyword_field, timestamp_field)          

            #--- Add xy coordinates based on reference names:
            kwds = [f[0] for f in arcpy.da.SearchCursor(media_point, [keyword_field])]
            xyz_values = []            
            xyz_values = get_xyz_for_media_files(kwds, ref_points_wgs84, ref_names, ref_fields, [])

            #--- Update xy coordinates in nongeo_layer
            arcpy.AddMessage(xyz_values)
            update_coordinates_to_nongeotagged_points(media_point, xyz_values)

            #--- Generate Near Table and assign unique numbers to 'id' field
            near_table = 'near_table'
            search_radius = '' # '50 Meters'
            location = 'NO_LOCATION'
            angle = 'NO_ANGLE'
            closest = 'CLOSEST'
            closest_count = 1
            near_table = 'near_table'
            arcpy.analysis.GenerateNearTable(media_point, media_point, near_table, search_radius, location, angle, closest, closest_count)
            
            for field in [temp_field, id_field]:
                arcpy.management.AddField(near_table, field, "SHORT", "", "", "", field, "NULLABLE", "REQUIRED")
            add_sequential_numbers(near_table, temp_field)

            # Assign group id
            fid_list = []
            prev_id = 1
            assign_group_id_for_display(near_table, id_field, fid_list, prev_id)

            #--- Join 'id' to media_point layer
            arcpy.management.JoinField(in_data=media_point,
                                    in_field=temp_field, 
                                    join_table=near_table,
                                    join_field=temp_field,
                                    fields=id_field)
            
            #--- Update Path using dropbox usercontent link
            table = pd.read_excel(dbx_link_table)
            todict = table.to_dict()
            dbx_link_dict = {name[1]: link[1] for name, link in zip(todict[name_field].items(), todict['dbx_link'].items())}
            update_path_field(media_point, path_field, name_field, cp_field, dbx_link_dict)
            
            #--- Truncate target layer
            arcpy.TruncateTable_management(target_layer)
            arcpy.AddMessage("Target layer was successfully truncated")

            #--- Append new point layer to target layer
            arcpy.management.Append(media_point, target_layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("Target layer was successfully appended")

            #--- Delete all temporary layers
            arcpy.management.Delete([station_point_feature, pier_point_feature])

        Medeia_tables()
