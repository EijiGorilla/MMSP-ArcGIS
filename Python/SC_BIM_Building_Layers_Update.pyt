import arcpy
import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import string

"""
# Instruction and Description 
This Python toolbox is used to implement two main processes:
A. Create building layers from Revit files.
B. Update construction status in existing building layers.  

# Process
## A. Create building layers from Revit files
### 1.1. BIM to Geodatabase
### 1.2. Make Building Layers from the Geodatabase

## B. Update construction status in existing building layers
## For SC station structures and depot buildings, BIM Team will provide
## revit files monthly with updated construction status.
## The same steps can be used to replace old revit with new refit files..

### Repeat step 1 and 2 in A above.
### 2.1. Add fields [Station, CP, and Types]
### 2.2. Delete existing building layers.
### 2.3. Add new buildings to the existing building layers.
### 2.4. Export building layers to excel
### 2.5. Update Master excel file
### 2.6. Update existing building layers using the master excel

"""

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateN2StationStructures"
        self.alias = "pdateN2StationStructures"
        self.tools = [CreateBIMtoGeodatabase, CreateBuildingLayers,
                      StationStructureMessage, DepotBuildingMessage, AddFieldsToBuildingLayerStation, AddFieldsToBuildingLayerDepot,
                      EditBuildingLayerStation, EditBuildingLayerDepot, UseExcelForUpdate, ExportToExcel, UpdateGISExcel, UpdateBuildingLayer]

class CreateBIMtoGeodatabase(object):
    def __init__(self):
        self.label = "1.1. Create BIM To Geodatabase using revit files"
        self.description = "Create BIM To Geodatabase using revit files"

    def getParameterInfo(self):
        fgdb_dir = arcpy.Parameter(
            displayName = "File Geodatabase",
            name = "File Geodatabase",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_revit = arcpy.Parameter(
            displayName = "Input BIM Workspace (revit files)",
            name = "Input BIM Workspace (revit files)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        export_name = arcpy.Parameter(
            displayName = "Display Name of Feature Dataset",
            name = "Display Name of Feature Dataset",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [fgdb_dir, input_revit, export_name]
        return params

    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        fgdb_dir = params[0].valueAsText
        input_revit = params[1].valueAsText
        export_name = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        revit_tables = list(input_revit.split(';'))
        
        arcpy.AddMessage(revit_tables)

        # 1. BIM to Geodatabase
        spatial_reference = "PRS_1992_Philippines_Zone_III"
        arcpy.BIMFileToGeodatabase_conversion(revit_tables, fgdb_dir, export_name, spatial_reference)
        
        arcpy.AddMessage("BIM To Geodatabase was successful.")

class CreateBuildingLayers(object):
    def __init__(self):
        self.label = "1.2. (Message ONLY) Make Building Layers using Feature Dataset"
        self.description = "Make Building Layers using Feature Dataset"

    # def getParameterInfo(self):
    #     bim_fd = arcpy.Parameter(
    #         displayName = "Input BIM Feature Dataset",
    #         name = "Input BIM Feature Dataset",
    #         datatype = "DEFeatureDataset",
    #         parameterType = "Required",
    #         direction = "Input",
    #         # multiValue = True
    #     )

    #     params = [bim_fd]
    #     return params

    # def updateMessages(self, params):
    #     return
    
    # def execute(self, params, messages):
    #     bim_fd = params[0].valueAsText

    #     arcpy.env.overwriteOutput = True

    #     # 2. Make Building Layer
    #     buildingLayerName = 'input_BuildingLayers'
    #     arcpy.MakeBuildingLayer_management(bim_fd,buildingLayerName)

    #     arcpy.AddMessage("Make Building Layer was successful.")

class StationStructureMessage(object):
    def __init__(self):
        self.label = "2.0. ---------- Station Structures ------------"
        self.description = "2.0. ---------- Station Structures ------------"

class DepotBuildingMessage(object):
    def __init__(self):
        self.label = "3.0. ---------- Depot Buildings ------------"
        self.description = "3.0. ---------- Depot Buildings ------------"

class AddFieldsToBuildingLayerStation(object):
    def __init__(self):
        self.label = "2.1. Add Fields to New Building Layers (Station Structures ONLY)"
        self.description = "2.1. Add Fields to New Building Layers (Station Structures ONLY)"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Sublayers in Building Layers (e.g., StructuralColumns)",
            name = "Select Sublayers in Building Layers", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [in_replaced_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        input_layers = params[0].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(input_layers.split(";"))

        # 1. Add fields
        add_fields = ['Station', 'Types', 'CP', 'Status']

        arcpy.AddMessage("Add Fields start...")
        try:
            for layer in layers:
                for field in add_fields:
                    if field in ('CP', 'Station'):
                        arcpy.AddField_management(layer, field, "TEXT", "", "", "", field, "NULLABLE", "")
                    else:
                        arcpy.AddField_management(layer, field, "SHORT", "", "", "", field, "NULLABLE", "")
        except:
            arcpy.AddError("Fields already exist.")
            pass

        # 2. Initial set for Status
        arcpy.AddMessage("Convert 'Status' = 1.")
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['Status']) as cursor:
                for row in cursor:
                    row[0] = 1
                    cursor.updateRow(row)

        # 3. Types of categories
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['Category', 'Types']) as cursor:
                for row in cursor:
                    if row[0] == 'Structural Foundations':
                        row[1] = 1
                    elif row[0] == 'Structural Columns':
                        row[1] = 2
                    elif row[0] == 'Structural Framing':
                        row[1] = 3
                    elif row[0] == 'Roofs':
                        row[1] = 4
                    elif row[0] == 'Floors':
                        row[1] = 5
                    elif row[0] == 'Walls':
                        row[1] = 6
                    elif row[0] == 'Columns':
                        row[1] = 7
                    else:
                        row[1] = 8
                    cursor.updateRow(row)
                    
        ## Use 'DocName' field to extract CP and Station
        stations = {
            "BLUSTN": 11,
            "ESPSTN": 12,
            "STMSTN": 13,
            "PACSTN": 14,
            "BUESTN": 15,
            "EDSA": 16,
            "EDSB": 31,
            "FTISTN": 18,
            "BCTSTN": 19,
            "SCTSTN": 20,
            "ALASTN": 21,
            "MTNSTN": 22,
            "SPDSTN": 23,
            "PCTSTN": 24,
            "BINSTN": 25,
            "STRSTN": 26,
            "CBYSTN": 27,
            "BANSTN": 29,
            "CMBSTN": 30
        }

        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['DocName', 'CP', 'Station']) as cursor:
                for row in cursor:

                    try:
                        cp_all = re.search(r'[S]0\d+?[abcABC]|[S]0\d+',row[0]).group()
                    except AttributeError:
                        cp_all = re.search(r'[S]0\d+?[abcABC]|[S]0\d+',row[0])
                    
                    st_name = re.search(r'\w+STN',row[0]).group()
                    cp_name = re.sub(r'0','-0',str(cp_all))

                    row[2] = stations[st_name]
                    row[1] = cp_name
                    cursor.updateRow(row)

class AddFieldsToBuildingLayerDepot(object):
    def __init__(self):
        self.label = "3.1. Add Fields to New Building Layers (Depot Buildings ONLY)"
        self.description = "3.1. Add Fields to New Building Layers (Depot Buildings ONLY)"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Sublayers in Building Layers (e.g., StructuralColumns)",
            name = "Select Sublayers in Building Layers", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [in_replaced_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        input_layers = params[0].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(input_layers.split(";"))

        # 1. Add fields
        add_fields = ['Name', 'Status']

        arcpy.AddMessage("Add Fields start...")
        try:
            for layer in layers:
                for field in add_fields:
                    arcpy.AddField_management(layer, field, "TEXT", "", "", "", field, "NULLABLE", "")

        except:
            arcpy.AddError("Fields already exist.")
            pass

        # 2. Initial set for Status
        arcpy.AddMessage("Convert 'Status' = 1.")
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['Status']) as cursor:
                for row in cursor:
                    row[0] = 1
                    cursor.updateRow(row)
                    
        ## Use 'DocName' field to extract CP and Station
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['DocName', 'Name']) as cursor:
                for row in cursor:                    
                    try:
                        building_name = re.search(r'BAN\w+|BAN\w+[12]',row[0]).group()
                    except AttributeError:
                        building_name = re.search(r'BAN\w+|BAN\w+[12]',row[0])
                    
                    final_name = re.sub(r'BAN','',building_name)
                    row[1] = final_name
                    cursor.updateRow(row)

class EditBuildingLayerStation(object):
    def __init__(self):
        self.label = "2.2 Update Building Layers (Station Structures ONLY)"
        self.description = "2.2 Update Building Layers (Station Structures ONLY)"

    def getParameterInfo(self):
        station_update = arcpy.Parameter(
            displayName = "Removed (Replaced) Stations",
            name = "Removed (Replaced) Stations",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )
        station_update.filter.type = "ValueList"
        station_update.filter.list = [
            "BLUSTN",
            "ESPSTN",
            "STMSTN",
            "PACSTN",
            "BUESTN",
            "EDSA",
            "EDSB",
            "FTISTN",
            "BCTSTN",
            "SCTSTN",
            "ALASTN",
            "MTNSTN",
            "SPDSTN",
            "PCTSTN",
            "BINSTN",
            "STRSTN",
            "CBYSTN",
            "BANSTN",
            "CMBSTN"
        ]

        delete_fc = arcpy.Parameter(
            displayName = "Target Building Sublayers (To Be Updated)",
            name = "Target Building Sublayers (To Be Updated)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        new_fc = arcpy.Parameter(
            displayName = "Input Building Sublayers (New)",
            name = "Input Building Sublayers (New)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [station_update, delete_fc, new_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        station_update = params[0].valueAsText
        delete_bim = params[1].valueAsText
        new_bim = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        # Stations domains
        stations = {
            "BLUSTN": '11',
            "ESPSTN": '12',
            "STMSTN": '13',
            "PACSTN": '14',
            "BUESTN": '15',
            "EDSA": '16',
            "EDSB": '31',
            "FTISTN": '18',
            "BCTSTN": '19',
            "SCTSTN": '20',
            "ALASTN": '21',
            "MTNSTN": '22',
            "SPDSTN": '23',
            "PCTSTN": '24',
            "BINSTN": '25',
            "STRSTN": '26',
            "CBYSTN": '27',
            "BANSTN": '29',
            "CMBSTN": '30'
            }
        
        del_layers = list(delete_bim.split(";"))
        new_layers = list(new_bim.split(";"))
        new_stations = list(station_update.split(";"))
        
        arcpy.AddMessage(new_layers)
        # Convert station names to station domain numbers
        station_numbers = tuple([stations[e] for e in new_stations])

        # 1. Check names are matched between deleted layers and new layers
        del_basenames = []
        new_basenames = []

        for layer in del_layers:
            del_basenames.append(os.path.basename(layer))

        for layer in new_layers:
            new_basenames.append(os.path.basename(layer))

        # 2. Add and Delete
        if sorted(del_basenames) == sorted(new_basenames):

            # 2.1. Delete layers from existing
            for layer in del_layers:
                del_basename = os.path.basename(layer)

                # Select layer by attribute
                if len(new_stations) == 1:
                    where_clause = "Station = '{}'".format(station_numbers[0])
                else:
                    where_clause = "Station IN {}".format(station_numbers)

                arcpy.management.SelectLayerByAttribute(layer, 'SUBSET_SELECTION',where_clause)

                # Truncate
                arcpy.TruncateTable_management(layer)
            
                # 2.2. Add new layer
                new_layers_series = pd.Series(new_layers)
                id = new_layers_series.index[new_layers_series.str.contains(del_basename,regex=True)][0]
                arcpy.AddMessage(del_basename + "; " + new_layers[id])
                arcpy.Append_management(new_layers[id], layer, schema_type = 'NO_TEST')
        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class EditBuildingLayerDepot(object):
    def __init__(self):
        self.label = "3.2 Update Building Layers (Depot Buildings ONLY)"
        self.description = "3.2 Update Building Layers (Depot Buildings ONLY)"

    def getParameterInfo(self):
        building_update = arcpy.Parameter(
            displayName = "Removed (Replaced) Depot Buildings",
            name = "Removed (Replaced) Depot Buildings",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )
        building_update.filter.type = "ValueList"
        building_update.filter.list = [
            "OCC",
            "LRS",
            "URS",
            "WRS",
            "CMV",
            "LOS",
            "DHS",
            "LGS",
            "TGB",
            "TMO",
            "MCS",
            "DBS1",
            "WPH1",
            "WPH2",
            "SH1",
            "BPS",
            "MPS",
            "CPS",
            "CNT",
            "CWT",
            "FP1",
            "DB1",
            "DB2"
            "DSP"
        ]

        delete_fc = arcpy.Parameter(
            displayName = "Target Building Sublayers (To Be Updated)",
            name = "Target Building Sublayers (To Be Updated)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        new_fc = arcpy.Parameter(
            displayName = "Input Building Sublayers (New)",
            name = "Input Building Sublayers (New)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [building_update, delete_fc, new_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        building_update = params[0].valueAsText
        delete_bim = params[1].valueAsText
        new_bim = params[2].valueAsText

        arcpy.env.overwriteOutput = True
        arcpy.AddMessage("0.")

        # Building names = domain names for depot building layers    
        del_layers = list(delete_bim.split(";"))
        new_layers = list(new_bim.split(";"))
        new_list_buildings = list(building_update.split(";"))
        new_buildings = tuple([e for e in new_list_buildings])

        # 1. Check names are matched between deleted layers and new layers
        del_basenames = []
        new_basenames = []

        for layer in del_layers:
            del_basenames.append(os.path.basename(layer))

        for layer in new_layers:
            new_basenames.append(os.path.basename(layer))

        arcpy.AddMessage(del_basenames)
        arcpy.AddMessage(new_basenames)

        # 2. Add and Delete
        if sorted(del_basenames) == sorted(new_basenames):
            # # 2.1. Delete layers from existing
            for layer in del_layers:
                del_basename = os.path.basename(layer)

                # Select layer by attribute
                if len(new_list_buildings) == 1:
                    where_clause = "Name = '{}'".format(new_list_buildings[0])
                else:
                    where_clause = "Name IN {}".format(new_buildings)
                
                arcpy.AddMessage(where_clause)
                arcpy.management.SelectLayerByAttribute(layer, 'SUBSET_SELECTION',where_clause)

                # Truncate
                arcpy.TruncateTable_management(layer)
            
                # 2.2. Add new layer
                new_layers_series = pd.Series(new_layers)
                id = new_layers_series.index[new_layers_series.str.contains(del_basename,regex=True)][0]
                arcpy.AddMessage("Checking Match: ")
                arcpy.AddMessage("Updated Subylayer: " + del_basename + "; " + "New Sublayer: " + new_layers[id])
                
                arcpy.Append_management(new_layers[id], layer, schema_type = 'NO_TEST')
                arcpy.AddMessage(del_basename + " was successfully updated.")
        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class UseExcelForUpdate(object):
    def __init__(self):
        self.label = "4.0. ---------- Update Excel Master List ------------"
        self.description = "4.0. ---------- Update Excel Master List ------------"

class ExportToExcel(object):
    def __init__(self):
        self.label = "4.1. Export Building Layers to Excel"
        self.description = "4.1. Export each building layer to excel and compile into one sheet"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Sublayers in Building Layers",
            name = "Select Sublayers in Building Layers ",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        in_fl = arcpy.Parameter(
            displayName = "Directory that stores exported excel file",
            name = "Export Directory",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )

        export_name = arcpy.Parameter(
            displayName = "Exported File Name",
            name = "Exported File Name",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_replaced_fc, in_fl, export_name]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_replaced_fc = params[0].valueAsText
        in_fl = params[1].valueAsText
        export_name = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        inputLayers = list(in_replaced_fc.split(";"))
        arcpy.AddMessage(inputLayers)

        # 1. merge all the input layers
        mergedLayer = "mergedLayers"
        arcpy.management.Merge(inputLayers, mergedLayer,"","")

        # 3. Export to excel
        #home = Path.home()
        #path = os.path.join(home, "Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/02-Station Structure/01-Masterlist/01-Compiled")
        arcpy.conversion.TableToExcel(mergedLayer, os.path.join(in_fl, export_name + ".xlsx"))

        # 6. Delete copied files
        deletedLayers = [mergedLayer]
        arcpy.management.Delete(deletedLayers)

class UpdateGISExcel(object):
        def __init__(self):
            self.label = "4.2. Update Master Excel File"
            self.description = "4.2. Update Master Excel File for GIS"

        def getParameterInfo(self):
            gis_dir = arcpy.Parameter(
                displayName = "Directory of Master Excel File",
                name = "Directory of Master Excel File",
                datatype = "DEWorkspace",
                parameterType = "Required",
                direction = "Input"
            )

            target_ms = arcpy.Parameter(
                displayName = "Master Excel File",
                name = "Master Excel File",
                datatype = "DEFile",
                parameterType = "Required",
                direction = "Input"
            )

            input_ms = arcpy.Parameter(
                displayName = "Input Excel File",
                name = "Input Excel File",
                datatype = "DEFile",
                parameterType = "Required",
                direction = "Input"
            )

            gis_bakcup_dir = arcpy.Parameter(
                displayName = "GIS Masterlist Backup Directory",
                name = "GIS Masterlist Backup Directory",
                datatype = "DEWorkspace",
                parameterType = "Optional",
                direction = "Input"
            )

            lastupdate = arcpy.Parameter(
                displayName = "Date for Backup: use 'yyyymmdd' format. eg. 20240101",
                name = "Date for Backup: use 'yyyymmdd' format. eg. 20240101",
                datatype = "GPString",
                parameterType = "Optional",
                direction = "Input"
            )

            join_field = arcpy.Parameter(
                displayName = "Join Field",
                name = "Join Field",
                datatype = "Field",
                parameterType = "Required",
                direction = "Input"
            )
            join_field.parameterDependencies = [target_ms.name]

            params = [gis_dir, target_ms, input_ms, gis_bakcup_dir, lastupdate,join_field]
            return params

        def updateMessage(self, params):
            return
        
        def execute(self, params, messages):
            gis_dir = params[0].valueAsText
            target_ms = params[1].valueAsText
            input_ms = params[2].valueAsText
            gis_bakcup_dir = params[3].valueAsText
            lastupdate = params[4].valueAsText
            join_field = params[5].valueAsText

            arcpy.env.overwriteOutput = True

            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)

            # 1. Read excel files
            input_table = pd.read_excel(input_ms)
            target_table = pd.read_excel(target_ms)

            # 2. Create bakcup files
            export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
            to_excel_file = os.path.join(gis_bakcup_dir, lastupdate + "_" + export_file_name + ".xlsx")
            
            try:
                target_table.to_excel(to_excel_file, index=False)
                arcpy.AddMessage("The master list was successfully exported.")
            except:
                pass

            # toString join_field
            toString(target_table, [join_field])
            toString(input_table,[join_field])

            # add temp field to new table
            temp_field = 'temp'
            input_table[temp_field] = 1

            # join input_table to target table using unique id field
            input_table2 = input_table[[temp_field,join_field]]
            joined_table = pd.merge(left=target_table, right=input_table2, how='left', left_on=join_field, right_on=join_field, validate='one_to_one')

            # Delete rows with temp == 1 (i.e., deleting ObjectsIds of input_table from target_table)
            id = joined_table.index[joined_table[temp_field] != 1]
            joined_table = joined_table.iloc[id]

            # Append joined_table to input_table
            final_table = pd.concat([joined_table, input_table], ignore_index=True)

            # sort by join_field
            final_table = final_table.sort_values(by=[join_field])

            # Delete temp field
            final_table = final_table.drop(columns = temp_field)

            # Export
            # export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
            # to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            final_table.to_excel(target_ms, index=False)

class UpdateBuildingLayer(object):
    def __init__(self):
        self.label = "4.3. Update Building Layers using ML"
        self.description = "4.3. Update building layers using excel ML"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Existing Building Layers",
            name = "Select Existing Building Layers ",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        in_ml = arcpy.Parameter(
            displayName = "Excel Master List",
            name = "Excel Master List",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        id_field = arcpy.Parameter(
            displayName = "Select Unique ID FIeld",
            name = "Select Unique ID FIeld",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        id_field.parameterDependencies = [in_ml.name]

        params = [in_replaced_fc, in_ml, id_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_replaced_fc = params[0].valueAsText
        in_ml = params[1].valueAsText
        id_field = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        old_buildingLayers = list(in_replaced_fc.split(";"))
        arcpy.AddMessage(old_buildingLayers)

        for layer in old_buildingLayers:
            # 1. Copy the existing building layers
            basename = os.path.basename(layer)
            output_name = basename + "_copy"
            arcpy.management.CopyFeatures(layer, output_name)
            arcpy.AddMessage(basename + " building layer is successfully copied.")
            
            # 2. Delete fields
            arcpy.DeleteField_management(output_name, [id_field], "KEEP_FIELDS")
            arcpy.AddMessage("All fields other than uniqueID were successfully deleted from " + output_name)

            # 3. Join Field
            ## 3.1. Remove uniqueID and OBJECTID from transferFiedls; otherwise, it fails
            fields = [f.name for f in arcpy.ListFields(in_ml)]
            transferFieldsRev = []
            search_words = '|'.join([id_field,'^Object'])
            
            for field in fields:
                try:
                    reg = re.search(search_words,field).group() 
                    if reg is None:
                        transferFieldsRev.append(field)
                except AttributeError:
                    reg = re.search(search_words,field)
                    if reg is None:
                        transferFieldsRev.append(field)
            arcpy.management.JoinField(output_name, id_field, in_ml, id_field, transferFieldsRev)
            arcpy.AddMessage(in_ml + " was successfully joined to " + output_name)

          #  ## 3.2. If Status = 1 and target_date < current_date, Status = 3 (delayed) [This will be done by R]
          #  codeblock = """
          #  import re
          #  def reclass(id, target, status):
          #      
          #      try:
          #          reg = re.search('\\d+',pier).group()
          #          return reg
          #      except AttributeError:
          #          reg = re.search('\\d+',pier)
          #          return reg
          #  """
            expression = "reclass(!{}!)".format(id_field, "target_date", "Status")
            #arcpy.CalculateField_management(inputFeature, field_temp, expression, "PYTHON3", codeblock)

            # 4. Truncate the existing building layer
            arcpy.TruncateTable_management(layer)
            arcpy.AddMessage("The existing building layer, " + layer + " was successfully truncated for joining.")

            # 5. Append the updated copied to the existing building layer
            arcpy.Append_management(output_name, layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("The existing building layer, " + layer + " was successfully updated.")

            # 6. Delete copied files
            arcpy.management.Delete(output_name)
