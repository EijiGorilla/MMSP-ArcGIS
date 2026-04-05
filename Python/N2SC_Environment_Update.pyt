import arcpy
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl

def unique(lists):
    collect = []
    unique_list = pd.Series(lists).drop_duplicates().tolist()
    for x in unique_list:
        collect.append(x)
    return(collect)

def replace_strings_in_dataframe(table, field, search_replace_arrays):
    """
    Replace multiple strings in a DataFrame column.
    table: pandas DataFrame
    field: column name where the replacement will occur
    search_replace_arrays: list of dictionary containing (search_string, replace_string)
    Example: {
    search_replace_arrays = {
        r'\s+': '',
        r'CPN': 'N-',
        r'[,/].*' : '' # This will remove anything after ',' or '/' in the string
    }
    """
    for search in search_replace_arrays:
        # table[field] = table[field].str.replace(search, search_replace_arrays[search], regex=True)
        table[field] = table[field].apply(lambda x: re.sub(search, search_replace_arrays[search], str(x)))
    return table

def find_word_location(df, search_word):
    """
    Finds the index and column of a specific word in a Pandas DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to search.
        search_word (str): The word to search for.

    Returns:
        list: A list of dictionaries, where each dictionary represents a location
            of the word in the DataFrame. Each dictionary has 'index' and 'column' keys.
            Returns an empty list if the word is not found.
    """
    locations = []
    col_idx = {name: i for i, name in enumerate(df)}
    for col in df.columns:
        for idx, value in df[col].items():
            if isinstance(value, str) and search_word in value.title():
                locations.append({'index': idx, 'column': col, 'colidx': col_idx[col]})
            elif isinstance(value, str) and search_word in value:
                locations.append({'index': idx, 'column': col, 'colidx': col_idx[col]})       
    return locations

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateTree"
        self.alias = "UpdateTree"
        self.tools = [JustMessage1, UpdateTreeML, UpdateTreeGIS, 
                      JustMessage2, UpdateEnviMonitorML, UpdateEnviMonitorGIS]

class JustMessage1(object):
    def __init__(self):
        self.label = "1.0.----- Update N2SC Tree -----"
        self.description = "Update status of tree cutting and compensation"

class UpdateTreeML(object):
    def __init__(self):
        self.label = "1.1. Update Tree ML (Excel)"
        self.description = "1.1. Update Tree ML (Excel)"

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

        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_ms = arcpy.Parameter(
            displayName = "Input Envi Master List (Excel)",
            name = "Input Envi Master List (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        target_ms = arcpy.Parameter(
            displayName = "Target GIS Master List (Excel)",
            name = "Target GIS Master List (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, input_ms, target_ms]
        return params

    def updateMessages(self, params):
        return
        
    def execute(self,params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        input_ms = params[2].valueAsText
        target_ms = params[3].valueAsText

        # 1. Update excel GIS Excel ML using Envi's table
        x = pd.read_excel(input_ms)

        cp_field = 'CP'

        if proj == 'N2':
            n2_cols_name = ["TreeNo", "Municipality", "CP", "CommonName", "ScientificName",
                "DBH", "MH", "TH", "Volume", "Latitude", "Longitude",
                "PNR", "Status", "Conservation", "Compensation"]
            
            # rename column names
            x = x.set_axis(n2_cols_name, axis='columns')

            # Drop empty rows
            x.dropna(subset=[cp_field],inplace=True)
            x = x.reset_index(drop=True)

            # Re-format CP
            arrays = {
                        r'\s+': '',
                        r'CP': '',
                        r'^1$': 'N-01',
                         r'^1$': 'N-01',
                         r'^2$': 'N-02',
                         r'^3$': 'N-03',
                         r'^4$': 'N-04',
                          r'^5$': 'N-05',
                    }
            x = replace_strings_in_dataframe(x, cp_field, arrays)
            x[cp_field] = x[cp_field].str.upper()

            # TreeNo is string
            x['TreeNo'] = x['TreeNo'].astype(str)

        elif proj == 'SC':
            sc_cols_name = ["TreeNo","CP","LotID","Barangay","District","Municipality","TagNo",
                "LocalName","ScientificName","DBH","MH","TH","Volume","Longitude","Latitude",
                "PNR_ROW","Status","Conservation","Compensation"]
            
            # Rename columns
            x = x.set_axis(sc_cols_name, axis='columns')
            
            # Drop empty rows
            x.dropna(subset=[cp_field],inplace=True)
            x = x.reset_index(drop=True)

            # Re-format CP
            arrays = {
                        r'\s+': '',
                        r'CP': '',
                    }
            x = replace_strings_in_dataframe(x, cp_field, arrays)
            x[cp_field] = x[cp_field].str.upper()

            # TreeNo is string
            x['TreeNo'] = x['TreeNo'].astype(str)
            x['TreeNo'] = x['TreeNo'].apply(lambda x: x.replace('.0',''))

        # overwrite existing GIS excel master list
        export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
        to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
        x.to_excel(to_excel_file, index=False)

class UpdateTreeGIS(object):
    def __init__(self):
        self.label = "1.2. Update GIS Feature Layer for Tree Cutting and Compensation"
        self.description = "1.2. Update GIS Feature Layer"

    def getParameterInfo(self):
        target_fl = arcpy.Parameter(
            displayName = "Target GIS Feature Layer",
            name = "Target_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Fourth parameter: excel master list
        x = arcpy.Parameter(
            displayName = "Tree Master List (Excel)",
            name = "Tree Master List (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [target_fl, x]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        target_fl = params[0].valueAsText
        x = params[1].valueAsText

        # 1. Import the tree master list table
        out_name = "Trees_table"
        arcpy.conversion.ExportTable(x, out_name, "", "NOT_USE_ALIAS")

        # 2. Convert the table to a point feature layer
        fNames = [f.name for f in arcpy.ListFields(out_name)]

        ## Obtain field name for latitude and longitude
        reg_long = re.compile(r"Long*|long*")
        reg_lat = re.compile(r"Lati*|lati*")

        long = list(filter(reg_long.match, fNames))
        lat = list(filter(reg_lat.match, fNames))

        out_feature_class = "Tree_points"
        arcpy.management.XYTableToPoint(out_name, out_feature_class, long[0], lat[0], "", arcpy.SpatialReference(4326))

        # create a spatial reference object for the output coordinate system
        out_coordinate_system = arcpy.SpatialReference(3857) # WGS84 Auxiliary

        # run the tool
        output_feature_class = "Tree_points_prj3857"
        arcpy.Project_management(out_feature_class, output_feature_class, out_coordinate_system)

        # 3. Copy the main FL in PRS92
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

        copied = "copied_layer"
        arcpy.CopyFeatures_management(output_feature_class, copied)

        # 4. truncates the SDE
        arcpy.TruncateTable_management(target_fl)

        # 5. Append the copied FGDB to the SDE
        arcpy.Append_management(copied, target_fl, schema_type = 'NO_TEST')

        # 6. Delete
        deleteL = [out_name, out_feature_class, output_feature_class, copied]
        arcpy.Delete_management(deleteL)

class JustMessage2(object):
    def __init__(self):
        self.label = "2.0.----- Update N2SC Environment Monitoring -----"
        self.description = "Update status of Environment monitoring"

class UpdateEnviMonitorML(object):
    def __init__(self):
        self.label = "2.1. Update Environment Monitoring ML (Excel)"
        self.description = "2.1. Update Environment Monitoring ML (Excel)"

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
    
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_ms = arcpy.Parameter(
            displayName = "Input Envi Master List (Excel)",
            name = "Input Envi Master List (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        target_ms = arcpy.Parameter(
            displayName = "Target GIS Master List (Excel)",
            name = "Target GIS Master List (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, input_ms, target_ms]
        return params

    def updateMessages(self, params):
        return
        
    def execute(self,params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        input_ms = params[2].valueAsText
        target_ms = params[3].valueAsText

        x = pd.read_excel(input_ms)
        cp_field = "CP"

        # Drop unnamed columns
        idx = x.columns[x.columns.str.contains(r'^Unnamed.*',regex=True)]
        x = x.drop(idx, axis=1)

        # Rename field names
        if proj == "N2":
            new_col_names = ["StationNo","CP","Location","Latitude","Longitude","samplingDate","Status","sourceLink","parameter","Remarks"]
            x = x.set_axis(new_col_names, axis='columns')
        else:
            new_col_names = ["StationNo","CP","Location","Latitude","Longitude","samplingDate","Status","parameter","surveyStatus","sourceLink","dateChecked"]
            x = x.set_axis(new_col_names, axis='columns')

        # Re-format CP
        x[cp_field] = x[cp_field].str.upper()
        arrays = {
                    r'\s+': '',
                    r'CP': '',
                    r'03A': '03a',
                    r'03B': '03b',
                    r'03C': '03c',
                }
        x = replace_strings_in_dataframe(x, cp_field, arrays)

        # type names of monitoring indicators
        typeName = {
            "Noise": 1,
            "Vibration": 2,
            "Ambient Air Quality": 3,
            "Soil": 4,
            "Groundwater": 5,
            "Surface Water": 6
            }

        # Collapse  all the types
        collapsed_type = "|".join(list(typeName.keys()))
        id = x.index[x['StationNo'].str.contains(collapsed_type,regex=True)]

        field_typeName = 'typeName'
        field_type = 'Type'

        # Initial values for type and typeName
        x[field_typeName] = str()
        x[field_type] = np.nan

        # Add values
        j=0 
        for i in id:
            j = j + 1
            name = x.loc[i,'StationNo']
            if j <= len(id)-1:
                idx = [e for e in range(i,id[j])]
                x.loc[idx,field_typeName] = name
                x.loc[idx,field_type] = typeName.get(name)
            elif j == len(id):
                last_index = max(x.index.values)
                idx = [e for e in range(i,last_index+1)]
                x.loc[idx,field_typeName] = name
                x.loc[idx,field_type] = typeName.get(name)

        # dropna when latitude is 
        x.dropna(subset=['Latitude'],inplace=True)
        x = x.reset_index(drop=True)

        # Conver float to integer
        x[field_type] = x[field_type].astype('int64')

        try:
            x['Status'] = x['Status'].astype('int64')
        except:
            pass

        # Reformat notation of Latitude and Longitude
        for coord in ['Latitude', 'Longitude']:
            x[coord] = x[coord].apply(lambda x: re.sub(r"(\s)","",x))
            x[coord] = x[coord].apply(lambda x: re.sub(r"°|’|'"," ",x))
            x[coord] = x[coord].apply(lambda x: re.sub(r'”|"',"",x))

        export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
        to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
        x.to_excel(to_excel_file, index=False)
   
class UpdateEnviMonitorGIS(object):
    def __init__(self):
        self.label = "2.2. Update GIS Feature Layer For Environment Monitoring"
        self.description = "2.2. Update GIS Feature Layer"

    def getParameterInfo(self):
        target_fl = arcpy.Parameter(
            displayName = "Target GIS Feature Layer",
            name = "Target_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Fourth parameter: excel master list
        input_table = arcpy.Parameter(
            displayName = "Envi Monitor Master List (Excel)",
            name = "Envi Monitor Master List (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [target_fl, input_table]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        target_fl = params[0].valueAsText
        inTable = params[1].valueAsText

        # 1. Import the Envi monitoring master list table
        out_name = "monitor_table"
        #tableGDB = arcpy.TableToTable_conversion(inTable, workspace, out_name)
        tableGDB = arcpy.conversion.ExportTable(inTable, out_name)
        
        # 2. Convert coordinate notation from DMS2 to DD2 (generate a point feature layer)
        # set parameter values
        output_points = 'env_monitor_point'
        x_field = 'Longitude'
        y_field = 'Latitude'
        input_format = 'DMS_2'
        output_format = 'DD_2'
        spatial_ref = arcpy.SpatialReference('WGS 1984')

        xyP = arcpy.ConvertCoordinateNotation_management(tableGDB, output_points, x_field, y_field, input_format, output_format, "", spatial_ref)

        # create a spatial reference object for the output coordinate system
        out_coordinate_system = arcpy.SpatialReference(3857) # WGS84 Auxiliary

        # run the tool
        output_feature_class = "env_monitor_point_prj3857"
        xyP_prj = arcpy.Project_management(xyP, output_feature_class, out_coordinate_system)

        # 3. Copy the original feature layer
        ## Note SDE (original) is PRS92, so when copied, it has to be converted to WGS84
        arcpy.env.outputCoordinateSystem = out_coordinate_system # WGS84 Auxiliary
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"
        copied = "copied_layer"
        arcpy.CopyFeatures_management(target_fl, copied)

        spf1 = arcpy.Describe(copied).spatialReference.name
        arcpy.AddMessage(spf1) # must be WGS84 

        # 4. Truncate the copied feature layer
        arcpy.TruncateTable_management(copied)

        # 5. Append the point FL to the copied FL
        arcpy.Append_management(xyP_prj, copied, schema_type = 'NO_TEST')

        # 5.1. Convert the copied back to PRS92
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"
        
        copied2 = "copied_layer2"
        arcpy.CopyFeatures_management(copied, copied2)

        spf2 = arcpy.Describe(copied2).spatialReference.name
        arcpy.AddMessage(spf2) # must be PRS92

        # 6. Truncate the original SDE
        arcpy.TruncateTable_management(target_fl)

        # 7. Appen the copied SDE to the original SDE
        arcpy.Append_management(copied2, target_fl, schema_type = 'NO_TEST')

        # Delete
        deleteL = [tableGDB, xyP, xyP_prj, copied, copied2]
        arcpy.Delete_management(deleteL)
        #End
