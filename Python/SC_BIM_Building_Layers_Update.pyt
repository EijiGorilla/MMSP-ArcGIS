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

## Depot Civil Works:
### What is Type to be monitored, Dwall and U-Type?
### 1. Create a field 'Type' (short integer)

### Repeat step 1 and 2 in A above.
### 2.1. Add fields [Station, CP, and Types]
### 2.2. Delete existing building layers.
### 2.3. Add new buildings to the existing building layers.
** 2.4, 2.5, and 2.6 are not mandatory. Run only when you want to keep attribute information in excel files
### 2.4. Export building layers to excel
### 2.5. Update Master excel file
### 2.6. Update existing building layers using the master excel

"""

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateN2StationStructures"
        self.alias = "pdateN2StationStructures"
        self.tools = [CreateBIMtoGeodatabase, CreateBuildingLayers,
                      StationStructureMessage, AddFieldsToBuildingLayerStation, EditBuildingLayerStation, DomainSettingStationStructure,
                      DepotBuildingMessage, AddFieldsToBuildingLayerDepot, EditBuildingLayerDepot, DomainSettingDepotBuilding,
                      DepotCivilWorksMessage, AddFieldsToDepotCivilWorksLayer, EditDepotCivilWorks, DomainSettingDepotCivilWorks]

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

class AddFieldsToBuildingLayerStation(object):
    def __init__(self):
        self.label = "2.1. Add Fields to New Building Layers (Station Structures ONLY)"
        self.description = "2.1. Add Fields to New Building Layers (Station Structures ONLY)"

    def getParameterInfo(self):
        input_layers = arcpy.Parameter(
            displayName = "Select Sublayers in Building Layers (e.g., StructuralColumns)",
            name = "Select Sublayers in Building Layers", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [input_layers]
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
        for layer in layers:
            for field in add_fields:
                if field == 'CP':
                    arcpy.management.AddField(layer, field, "TEXT", "", "", "", field, "NULLABLE", "")
                else:
                    arcpy.management.AddField(layer, field, "SHORT", "", "", "", field, "NULLABLE", "")
  
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

                    cp_name = re.sub('A','a',cp_name)
                    cp_name = re.sub('B','b',cp_name)
                    cp_name = re.sub('C','c',cp_name)

                    row[2] = stations[st_name]
                    row[1] = cp_name
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

        # define fields
        status_field = 'Status'
        finish_date_field = 'Finish_date'

        # Stations domains
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
                    where_clause = "Station = {}".format(station_numbers[0])
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

                # Update 'Status' field based on 'Target_date' and 'Finish_date'
                ## if finish date is empty or null, status = 1 (to be constructed).
                ## if finish date is entered, status = 4 (Completed)
                with arcpy.da.UpdateCursor(layer, [status_field, finish_date_field]) as cursor:
                    for row in cursor:
                        if row[1] is None:
                            row[0] = 1
                        elif row[1] is not None:
                            row[0] = 4
                        cursor.updateRow(row)
        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class DomainSettingStationStructure(object):
    def __init__(self):
        self.label = "2.3. Apply Domain to Fields in SDE (Station Structure ONLY)"
        self.description = "2.3. Apply Domain to Fields in SDE (Station Structure ONLY)"

    def getParameterInfo(self):
        gis_layers = arcpy.Parameter(
            displayName = "Building Layers (e.g., StructuralColumns)",
            name = "Building Layers (e.g., StructuralColumns)", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        domain_field = arcpy.Parameter(
            displayName = "Domain Field Name",
            name = "Domain Field Name", 
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        domain_field.filter.type = "ValueList"
        domain_field.filter.list = ['Types','Status','Station']

        params = [gis_layers, domain_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        gis_layers = params[0].valueAsText
        domain_field = params[1].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(gis_layers.split(";"))

        # # Apply symbology changes to lyr, which will create a new finalLayer:
        # finalLayer = arcpy.management.ApplySymbologyFromLayer(lyr, "Q:\GIS_Data\Symbology_Layers\TypeSymbology.lyr")
        # # Remove the original lyr from aprxMap
        # aprxMap.removeLayer(lyr)
        # # Add the new layer that has the symbology applied
        # aprxMap.addLayer(finalLayer[0])
        
        domainList = ['Station Structures_TYPE', 'Station Structures_STATUS', 'Station_nscrex']
        
        for layer in layers:
            if domain_field == 'Status':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[1])
            elif domain_field == 'Types':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[0])
            elif domain_field == 'Station':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[2])
            else:
                arcpy.AddError("Your specified field was not found in doman lists...please check.")

class DepotBuildingMessage(object):
    def __init__(self):
        self.label = "3.0. ---------- Depot Buildings ------------"
        self.description = "3.0. ---------- Depot Buildings ------------"

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
                    if layer == 'Name':
                        arcpy.AddField_management(layer, field, "TEXT", "", "", "", field, "NULLABLE", "")
                    else:
                        arcpy.management.AddField(layer, field, "SHORT", "", "", "", field, "NULLABLE", "")

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

        # Define fields
        status_field = 'Status'
        finish_date_field = 'Finish_date'

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

                # Update 'Status' field based on 'Target_date' and 'Finish_date'
                ## if finish date is empty or null, status = 1 (to be constructed).
                ## if finish date is entered, status = 4 (Completed)
                with arcpy.da.UpdateCursor(layer, [status_field, finish_date_field]) as cursor:
                    for row in cursor:
                        if row[1] is None:
                            row[0] = 1
                        elif row[1] is not None:
                            row[0] = 4
                        cursor.updateRow(row)
        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class DomainSettingDepotBuilding(object):
    def __init__(self):
        self.label = "3.3. Apply Domain to Fields in SDE (Depot Building ONLY)"
        self.description = "3.3. Apply Domain to Fields in SDE (Depot Building ONLY)"

    def getParameterInfo(self):
        gis_layers = arcpy.Parameter(
            displayName = "Building Layers (e.g., StructuralColumns)",
            name = "Building Layers (e.g., StructuralColumns)", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        domain_field = arcpy.Parameter(
            displayName = "Domain Field Name",
            name = "Domain Field Name", 
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        domain_field.filter.type = "ValueList"
        domain_field.filter.list = ['Type','Status','Name']

        params = [gis_layers, domain_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        gis_layers = params[0].valueAsText
        domain_field = params[1].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(gis_layers.split(";"))

        # # Apply symbology changes to lyr, which will create a new finalLayer:
        # finalLayer = arcpy.management.ApplySymbologyFromLayer(lyr, "Q:\GIS_Data\Symbology_Layers\TypeSymbology.lyr")
        # # Remove the original lyr from aprxMap
        # aprxMap.removeLayer(lyr)
        # # Add the new layer that has the symbology applied
        # aprxMap.addLayer(finalLayer[0])
        
        domainList = ['Station Structures_TYPE', 'Station Structures_STATUS', 'SC_Depot_Building_NAME']
        
        for layer in layers:
            if domain_field == 'Status':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[1])
            elif domain_field == 'Type':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[0])
            elif domain_field == 'Name':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[2])
            else:
                arcpy.AddError("Your specified field was not found in doman lists...please check.")

class DepotCivilWorksMessage(object):
    def __init__(self):
        self.label = "4.0. ---------- Depot Civil Works ------------"
        self.description = "4.0. ---------- Depot Civil Works ------------"

class AddFieldsToDepotCivilWorksLayer(object):
    def __init__(self):
        self.label = "4.1. Add Fields to New Civil Works Layers (Depot Civil Works ONLY)"
        self.description = "4.1. Add Fields to New Civil Works Layers (Depot Civil Works ONLY)"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Sublayers in Depot Civil Works Layers (e.g., StructuralColumns)",
            name = "Select Sublayers in Depot Civil Works Layers", 
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
        add_fields = ['Types', 'Status']

        arcpy.AddMessage("Add Fields start...")
        try:
            for layer in layers:
                for field in add_fields:
                    arcpy.management.AddField(layer, field, "SHORT", "", "", "", field, "NULLABLE", "")

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
                    
        ## which information is used to identify 'Type' for monitoring? Dwall and U-Type
        ## Dwall and U-Type are two separate revit files, so find something unique
        # for layer in layers:
        #     with arcpy.da.UpdateCursor(layer, ['DocName', 'Name']) as cursor:
        #         for row in cursor:                    
        #             try:
        #                 building_name = re.search(r'BAN\w+|BAN\w+[12]',row[0]).group()
        #             except AttributeError:
        #                 building_name = re.search(r'BAN\w+|BAN\w+[12]',row[0])
                    
        #             final_name = re.sub(r'BAN','',building_name)
        #             row[1] = final_name
        #             cursor.updateRow(row)

class EditDepotCivilWorks(object):
    # For Depot Civil works, simply replace all existing layers with new ones.
    def __init__(self):
        self.label = "4.2 Update Depot Civil Works Layers (Depot Civil Works ONLY)"
        self.description = "4.2 Update Depot Civil Works Layers (Depot Civil Works ONLY)"

    def getParameterInfo(self):
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

        params = [delete_fc, new_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        delete_bim = params[0].valueAsText
        new_bim = params[1].valueAsText

        arcpy.env.overwriteOutput = True

        # Define field
        target_date_field = 'Target_date'
        finish_date_field = 'Finish_date'
        status_field = 'Status'

        del_layers = list(delete_bim.split(";"))
        new_layers = list(new_bim.split(";"))
        
        arcpy.AddMessage(new_layers)

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

                # Truncate
                arcpy.TruncateTable_management(layer)
            
                # 2.2. Add new layer
                new_layers_series = pd.Series(new_layers)
                id = new_layers_series.index[new_layers_series.str.contains(del_basename,regex=True)][0]
                arcpy.AddMessage(del_basename + "; " + new_layers[id])
                arcpy.Append_management(new_layers[id], layer, schema_type = 'NO_TEST')

                # Update 'Status' field based on 'Target_date' and 'Finish_date'
                ## if finish date is empty or null, status = 1 (to be constructed).
                ## if finish date is entered, status = 4 (Completed)
                with arcpy.da.UpdateCursor(layer, [status_field, finish_date_field]) as cursor:
                    for row in cursor:
                        if row[1] is None:
                            row[0] = 1
                        elif row[1] is not None:
                            row[0] = 4
                        cursor.updateRow(row)
        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class DomainSettingDepotCivilWorks(object):
    def __init__(self):
        self.label = "4.3. Apply Domain to Fields in SDE (Depot Civil Works ONLY)"
        self.description = "4.3. Apply Domain to Fields in SDE (Depot Civil Works ONLY)"

    def getParameterInfo(self):
        gis_layers = arcpy.Parameter(
            displayName = "Building Layers (e.g., StructuralColumns)",
            name = "Building Layers (e.g., StructuralColumns)", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        domain_field = arcpy.Parameter(
            displayName = "Domain Field Name",
            name = "Domain Field Name", 
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        domain_field.filter.type = "ValueList"
        domain_field.filter.list = ['Type','Status']

        params = [gis_layers, domain_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        gis_layers = params[0].valueAsText
        domain_field = params[1].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(gis_layers.split(";"))

        # # Apply symbology changes to lyr, which will create a new finalLayer:       
        domainList = ['Depot_Civil_Works_TYPE', 'Station Structures_STATUS']
        
        for layer in layers:
            if domain_field == 'Status':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[1])
            elif domain_field == 'Type':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[0])
            else:
                arcpy.AddError("Your specified field was not found in doman lists...please check.")
