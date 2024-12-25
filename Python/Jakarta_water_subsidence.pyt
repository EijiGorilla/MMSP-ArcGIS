import arcpy
import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import string

"""
GIS in Water Resource Management
# Instruction and Description 
The main objective of this code is to process subsidence points obtained from In-SAR for visualization in GIS web application. Given the large volume of dataset, we will experiment a few methods:

## The main process:
# 0. Read and save in csv
## The original csv acquired cannot be read in ArcGIS Pro due to column names of date (i.e., the first column cannot be read as a header).
## As such, We need to read this original csv and export it to a new csv.

# 1. Subtract observed data from a reference point (can this process be skipped?)
## This process ensures that the web app shows only land subsidence values by subtracting the raw values from a reference point value.

# 2. Calculate IQR (interquartile range) for defining symbology

# 3. Create XY points from CSV file
## 3.1. Add field names ('subdiv', 'district')

# 4. Add administrative boundary to the points
## 4.1. Subdivision
## 4.2. District

# 5. Run optimized hotspot analysis
## This applies Getis and Ord G statistics to DispR_mmyr and identifies statistically signficant areas with positivie spatial autocorrelation.
## In other words, it spatially identifies positive displacement points surrounded by positive neighboring points and negative displacement points surrounded by negative neighboring points.
"""
class Toolbox(object):
    def __init__(self):
        self.label = "ProcessSarPoints"
        self.alias = "ProcessSarPoints"
        self.tools = [CreateNewCSV, ExcelSubtract, InterQuartileRange, ToXYPoints, AddAdminBoundaryToPoints, RunHotSpotAnalysisAddResults, ReformatScenarioExcel]

class CreateNewCSV(object):
    def __init__(self):
        self.label = "0. Reformat original CSV and Export new CSV"
        self.description = "Reformat original CSV and Export new CSV"

    def getParameterInfo(self):
        directory = arcpy.Parameter(
            displayName = "Data Storage Directory",
            name = "GData Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_table = arcpy.Parameter(
            displayName = "Input Original CSV table (SAR points)",
            name = "Input Original CSV table (SAR points)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
        )

        output_name = arcpy.Parameter(
            displayName = "Name of New CSV File",
            name = "Name of New CSV File",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [directory, input_table, output_name]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        directory = params[0].valueAsText
        input_table = params[1].valueAsText
        output_name = params[2].valueAsText

        x = pd.read_csv(input_table, header=0)
        fixed_columns = x.columns[x.columns.str.contains(r'^20*',regex=True)]

        # Add 'X' to year columns
        for col in fixed_columns:
            new_col= 'X'+col
            x = x.rename(columns={str(col): new_col})

        # x['id'] = x.reset_index().index

        # Change decimal places for subsidence level
        # fix_cols = x.columns[x.columns.str.contains(r'^X|^Disp',regex=True)]
        # x[fix_cols] = x[fix_cols].round(3)

        # Export
        to_csv_file = os.path.join(directory, output_name + ".csv")
        x.to_csv(to_csv_file, index=False)

        # Wide to Long format
        # x = pd.wide_to_long(x, ["X"], i="id", j="year").reset_index()
        # x= x.rename(columns={str("X"): "y"})

class ExcelSubtract(object):
    def __init__(self):
        self.label = "1. Subtract Observed Data from A Reference Point"
        self.description = "Subtract Observed Data from A Reference Point"

    def getParameterInfo(self):
        directory = arcpy.Parameter(
            displayName = "Data Storage Directory",
            name = "GData Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_table = arcpy.Parameter(
            displayName = "Re-formatted CSV table (SAR points)",
            name = "Re-formatted CSV table (SAR points)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
        )

        reference_id = arcpy.Parameter(
            displayName = "Reference Point ID Number for Subtraction",
            name = "Reference Point ID Number for Subtraction",
            datatype = "GPLong",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [directory, input_table, reference_id]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        directory = params[0].valueAsText
        input_table = params[1].valueAsText
        reference_id = params[2].valueAsText

        x = pd.read_csv(input_table, header=0)

        id_field = 'id'

        # extract only years
        years = x.columns[x.columns.str.contains(r'^X',regex=True)]
        ref_values = x.loc[x[id_field] == int(reference_id), years].values.flatten()       
        x1 = x[years].sub(ref_values)

        joined_fields = x.columns[x.columns.str.contains(r'deg$|^Disp|id',regex=True)]
        x0 = x[joined_fields]

        final_x = pd.merge(x0, x1, left_index=True, right_index=True)

        # Export
        basename = os.path.splitext(os.path.basename(input_table))[0]
        to_csv_file = os.path.join(directory, basename + "_subtr" + ".csv")
        final_x.to_csv(to_csv_file, index=False)

class InterQuartileRange(object):
    def __init__(self):
        self.label = "2. Calculate Interquartile Range (IQR) for Symbology"
        self.description = "Calculate Interquartile Range (IQR) for Symbology"

    def getParameterInfo(self):
        directory = arcpy.Parameter(
            displayName = "Data Storage Directory",
            name = "GData Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_table = arcpy.Parameter(
            displayName = "Re-formatted CSV table (SAR points)",
            name = "Re-formatted CSV table (SAR points)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
        )

        params = [directory, input_table]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        directory = params[0].valueAsText
        input_table = params[1].valueAsText

        x = pd.read_csv(input_table, header=0)

        # Calculate interquartile range (Q1 and Q3) for updating visualVariables
        ## 20-80 may be better instead of 25 and 75
        fields = x.columns[x.columns.str.contains(r'^X',regex=True)]
        table = pd.DataFrame(columns=['dates', 'min', 'Q1','Q3', 'max'])
        for field in fields:
            values = x[field]
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            minv = values.min()
            maxv = values.max()
            row_to_append = pd.DataFrame([{'dates':field, 'min':minv, 'Q1':q1, 'Q3':q3, 'max':maxv}])
            table = pd.concat([table, row_to_append])

        
        basename = os.path.splitext(os.path.basename(input_table))[0]
        iq_name = 'IQR'
        output_basename = basename + "_" + iq_name
        to_csv_file = os.path.join(directory, output_basename + ".csv")
        table.to_csv(to_csv_file, index=False)

class ToXYPoints(object):
    def __init__(self):
        self.label = "3. Create XY Points from CSV File"
        self.description = "Create XY Points from CSV File"

    def getParameterInfo(self):
        input_table = arcpy.Parameter(
            displayName = "Input CSV table (SAR points)",
            name = "Input CSV table (SAR points)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input",
        )

        output_feature_name = arcpy.Parameter(
            displayName = "Name of Output feature layer",
            name = "Name of Output feature layer",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        x_coords = arcpy.Parameter(
            displayName = "Choose X-coordinate (Longitude)",
            name = "Choose X-coordinate (Longitude)",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        x_coords.parameterDependencies = [input_table.name]

        y_coords = arcpy.Parameter(
            displayName = "Choose Y-coordinate (Latitude)",
            name = "Choose Y-coordinate (Latitude)",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        y_coords.parameterDependencies = [input_table.name]

        params = [input_table, output_feature_name, x_coords, y_coords]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        input_table = params[0].valueAsText
        out_feature_class = params[1].valueAsText
        x_coords = params[2].valueAsText
        y_coords = params[3].valueAsText

        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3857)

        arcpy.management.XYTableToPoint(input_table, out_feature_class, x_coords, y_coords, "", arcpy.SpatialReference(4326)) # default: 4326
        altered_field = 'Field1'

        # 2. If field name 'Field1' exists, rename it to 'id'
        new_field_name = 'id'
        new_field_alias = 'id'
        field_type = ""
        field_length = ""
        field_is_nullable = "NULLABLE"
        clear_field_alias = ""

        try:
            arcpy.management.AlterField(out_feature_class,
                                    altered_field,
                                    new_field_name,
                                    new_field_alias,
                                    field_type,
                                    field_length,
                                    field_is_nullable,
                                    clear_field_alias)
        except:
            pass
        
class AddAdminBoundaryToPoints(object):
    def __init__(self):
        self.label = "4. Add Admin Boundary to SAR Point Layer"
        self.description = "Add Admin Boundary to SAR Point Layer"

    def getParameterInfo(self):
        input_layer = arcpy.Parameter(
            displayName = "SAR Points Layer",
            name = "SAR Points Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
        )

        subdivison_layer =  arcpy.Parameter(
            displayName = "Administrative Boundary Layer (Subdivision)",
            name = "Administrative Boundary Layer (Subdivision)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
        )

        district_layer =  arcpy.Parameter(
            displayName = "Administrative Boundary Layer (District)",
            name = "Administrative Boundary Layer (District)",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input",
        )

        params = [input_layer, subdivison_layer, district_layer]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        sar_points_layer = params[0].valueAsText
        subdivision_boundary_layer = params[1].valueAsText
        district_boundary_layer = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        subsiv_field_name = 'subdiv'
        district_field_name = 'district'

        # 1. Add field names
        field_names = [subsiv_field_name, district_field_name]
        # for field in field_names:
        #     arcpy.management.AddField(sar_points_layer, field, "TEXT", "", "", "", field, "NULLABLE", "", "")
        arcpy.management.AddField(sar_points_layer, subsiv_field_name, "TEXT", "", "", "", subsiv_field_name, "NULLABLE", "", "")

        # 3.1. Subdivision
        search_field = "NAMOBJ"
        subdiv_names = []

        ## Select each boudary
        with arcpy.da.SearchCursor(subdivision_boundary_layer, [search_field]) as cursor:
            for row in cursor:
                subdiv_names.append(row[0])

        for name in subdiv_names:
            # Select each division name in the boundary layer
            where_clause = "NAMOBJ = '{}'".format(name)
            arcpy.management.SelectLayerByAttribute(subdivision_boundary_layer, 'NEW_SELECTION', where_clause)
            
            # Select sar_points_layer by this location
            arcpy.management.SelectLayerByLocation(sar_points_layer, 'WITHIN', subdivision_boundary_layer)
            
            # Add corresponding subdivision names
            with arcpy.da.UpdateCursor(sar_points_layer, [subsiv_field_name]) as cursor:
                for row in cursor:
                    row[0] = name
                    cursor.updateRow(row)

        # 3.2. District
        # search_field = "NAMOBJ"
        # district_names = []

        # ## Select each boudary
        # with arcpy.da.SearchCursor(district_boundary_layer, [search_field]) as cursor:
        #     for row in cursor:
        #         district_names.append(row[0])

        # for name in subdiv_names:
        #     # Select each division name in the boundary layer
        #     where_clause = "NAMOBJ = '{}'".format(name)
        #     arcpy.management.SelectLayerByAttribute(district_boundary_layer, 'NEW_SELECTION', where_clause)
            
        #     # Select sar_points_layer by this location
        #     arcpy.management.SelectLayerByLocation(sar_points_layer, 'WITHIN', district_boundary_layer)
            
        #     # Add corresponding subdivision names
        #     with arcpy.da.UpdateCursor(sar_points_layer, [district_field_name]) as cursor:
        #         for row in cursor:
        #             row[0] = name
        #             cursor.updateRow(row)

class RunHotSpotAnalysisAddResults(object):
    def __init__(self):
        self.label = "5. Run Host Spot Analysis and Add Results"
        self.description = "Run Host Spot Analysis and Add Results"

    def getParameterInfo(self):
        input_layer = arcpy.Parameter(
            displayName = "Input Features (SAR Point Layer)",
            name = "Input Features (SAR Point Layer)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
        )

        output_layer = arcpy.Parameter(
            displayName = "Output Features",
            name = "Output Features",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
        )

        analysis_field = arcpy.Parameter(
            displayName = "Analysis Field",
            name = "Analysis Field",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        analysis_field.parameterDependencies = [input_layer.name]

        # join_field_sar =  arcpy.Parameter(
        #     displayName = "Join Field (id) in SAR Points (Add Hot Spot Analysis)",
        #     name = "Join Field (id) in SAR Points (Add Hot Spot Analysis)",
        #     datatype = "Field",
        #     parameterType = "Required",
        #     direction = "Input",
        # )
        # join_field_sar.parameterDependencies = [input_layer.name]

        params = [input_layer, output_layer, analysis_field]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        input_layer = params[0].valueAsText
        output_layer = params[1].valueAsText
        analysis_field = params[2].valueAsText
        # join_field_sar = params[3].valueAsText

        arcpy.env.overwriteOutput = True
        arcpy.env.parallelProcessingFactor = "50%"

        # Run optimized hot spot analysis
        arcpy.stats.OptimizedHotSpotAnalysis(input_layer, output_layer, analysis_field)
        input_alias_field = "Gi_Bin" # 'Gi_Bin Fixed 48_FDR'
        join_field_ohsa = "SOURCE_ID"

        # When "Gi_Bin Fixed 48_FDR" already exists in the input layer, remove it.
        fields_sar = [f.name for f in arcpy.ListFields(input_layer)]
        bools = [e for e in fields_sar if e in [input_alias_field]]

        if len(bools) == 1:
            arcpy.management.DeleteField(input_layer, [input_alias_field], "DELETE_FIELDS")
        arcpy.management.JoinField(input_layer, "OBJECTID", output_layer, join_field_ohsa, [input_alias_field])
        
        # Join 'Gi_Bin Fixed 48_FDR'
        ## This field indicates the following:
        ## -3: Cold Spot with 99% Confidence
        ## -2: Cold Spot with 95% Confidence
        ## -1: Cold Spot with 90% Confidence
        ## 0 : Not Significant
        ## 1 : Hot Spot with 90% Confidence
        ## 2 : Hot Spot with 95% Confidence
        ## 3 : Hot Spot with 99% Confidence

class ReformatScenarioExcel(object):
    def __init__(self):
        self.label = "6. Re-format Scenario Table"
        self.description = "Re-format Scenario Table"

    def getParameterInfo(self):
        directory = arcpy.Parameter(
            displayName = "Data Storage Directory",
            name = "GData Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_table = arcpy.Parameter(
            displayName = "Input Excel table (Scenario)",
            name = "Input Excel table (Scenario)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
        )

        params = [directory, input_table]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        directory = params[0].valueAsText
        input_table = params[1].valueAsText

        arcpy.env.overwriteOutput = True

        x1 = pd.read_excel(input_table,sheet_name=1) # status quo
        x2 = pd.read_excel(input_table,sheet_name=0)

        # Edit field names
        search_cols = x1.columns[x1.columns.str.contains(r'Time|^Obs|Calc',regex=True)]
        renamed_cols = ['date', 'obs', 'calc']
        for i in range(len(search_cols)):
            x1 = x1.rename(columns={str(search_cols[i]): renamed_cols[i]})
            x2 = x2.rename(columns={str(search_cols[i]): renamed_cols[i]})

        x1 = x1.rename(columns={str(renamed_cols[2]): 'scenario1'})
        x2 = x2.rename(columns={str(renamed_cols[2]): 'scenario2'})

        x1 = x1.reset_index()
        x2 = x2.reset_index()

        # Merge tables
        join_fields = ['index','date','obs']
        xx = pd.merge(left=x1, right=x2, how='left', left_on=join_fields, right_on=join_fields)
        xx = xx.drop(columns="index")

        # Add dummy scenario for now
        xx['scenario3'] = np.nan
        xx['scenario4'] = np.nan
        xx['scenario5'] = np.nan

        # add area
        # xx['area'] = 'Kapukmuara'

        # Change date format
        xx[renamed_cols[0]] = pd.to_datetime(xx[renamed_cols[0]],errors='coerce').dt.date

        basename = os.path.splitext(os.path.basename(input_table))[0]

        to_excel_file = os.path.join(directory, basename + "_Scenario_compiled" + ".xlsx")
        xx.to_excel(to_excel_file, index=False)
