import arcpy
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateEnviMonitoring"
        self.alias = "UpdateEnviMonitoring"
        self.tools = [UpdateEnviMonitorML, UpdateGIS]

class UpdateEnviMonitorML(object):
    def __init__(self):
        self.label = "1. Update Environment Monitoring ML (Excel)"
        self.description = "1. Update Environment Monitoring ML (Excel)"

    def getParameterInfo(self):   
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

        params = [gis_dir, input_ms, target_ms]
        return params

    def updateMessages(self, params):
        return
        
    def execute(self,params, messages):
        gis_dir = params[0].valueAsText
        input_ms = params[1].valueAsText
        target_ms = params[2].valueAsText

        table = pd.read_excel(input_ms)

        # Rename field names
        new_col_names = ["StationNo","CP","Location","Latitude","Longitude","samplingDate","Status","sourceLink","parameter"]
        table = table.set_axis(new_col_names, axis='columns')

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
        id = table.index[table['StationNo'].str.contains(collapsed_type,regex=True)]

        field_typeName = 'typeName'
        field_type = 'Type'

        # Initial values for type and typeName
        table[field_typeName] = str()
        table[field_type] = np.nan

        # Add values
        j=0 
        for i in id:
            j = j + 1
            name = table.loc[i,'StationNo']
            if j <= len(id)-1:
                idx = [e for e in range(i,id[j])]
                table.loc[idx,field_typeName] = name
                table.loc[idx,field_type] = typeName.get(name)
            elif j == len(id):
                last_index = max(table.index.values)
                idx = [e for e in range(i,last_index+1)]
                table.loc[idx,field_typeName] = name
                table.loc[idx,field_type] = typeName.get(name)

        # dropna when latitude is 
        table.dropna(subset=['Latitude'],inplace=True)

        # Conver float to integer
        table[field_type] = table[field_type].astype('int64')

        try:
            table['Status'] = table['Status'].astype('int64')
        except:
            pass

        # Reformat notation of Latitude and Longitude
        for coord in ['Latitude', 'Longitude']:
            table[coord] = table[coord].apply(lambda x: re.sub(r"(\s)","",x))
            table[coord] = table[coord].apply(lambda x: re.sub(r"°|’|'"," ",x))
            table[coord] = table[coord].apply(lambda x: re.sub(r'”|"',"",x))

        export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
        to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
        table.to_excel(to_excel_file, index=False)

class UpdateGIS(object):
    def __init__(self):
        self.label = "2. Update GIS Feature Layer"
        self.description = "2. Update GIS Feature Layer"

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
    
