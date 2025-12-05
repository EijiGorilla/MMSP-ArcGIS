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
B. Update construction status in existing building layers for FTI Station.  

# Process
## A. Create building layers from Revit files
### 1.1. BIM to Geodatabase
### 1.2. Make Building Layers from the Geodatabase

## B. Update construction status in existing building layers
## For SC station structures and depot buildings, BIM Team will provide
## revit files with updated construction status.
## The same steps can be used to replace old revit with new refit files..

## Depot Civil Works:
### What is Type to be monitored, Dwall and U-Type?
### 1. Create a field 'Type' (text)

### Repeat step 1 and 2 in A above.
### 2.1. Add fields [Station, CP, and Types]
### 2.2. Delete existing building layers.
### 2.3. Add new buildings to the existing building layers.
#***********************************************************************************************#
#### You can first add input (new) sublayers and then corresponding target (existing) sublayers.
#### For example, if you only see structuralColumns and StructuralFoundation sublayers in the input building layer, 
#### you should add the only corresponding target sublayers (because the sublayers in the input building layer
#### are the ONLY updates)
#***********************************************************************************************#
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
                      AddFieldsToBuildingLayerStation,
                      EditBuildingLayerStation,
                      DomainSettingStationStructure]

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

class AddFieldsToBuildingLayerStation(object):          
    def __init__(self):
        self.label = "2.1. Add Fields to New Building Layers (FTI)"
        self.description = "2.1. Add Fields to New Building Layers (FTI)"

    def getParameterInfo(self):
        input_layers = arcpy.Parameter(
            displayName = "Select Sublayers in Building Layers (e.g., StructuralColumns)",
            name = "Select Sublayers in Building Layers", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        # Process sublayers ONLY when a sublayer has "t00__Description" field.

        # Make sure to add the follwing sublayers:
        ## Architectural:
        ## 1. Site
        ## Structural:
        ### 1. StructralFoundation
        ### 2. StructuralColumns
        ### 3. StructuralFraming


        # input_layers.filter.type = "ValueList"
        # iput_layers.filter

        params = [input_layers]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        input_layers = params[0].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(input_layers.split(";"))

        finish_date_field = 'Finish_date'
        add_fields = ['Station', 'Types', 'CP', 'Status']
        component_source_field = "t00__Description"

        # 0. Filter sublayers 
        # sublayers = []
        # ## Process sublayers only when they have "t00__Description" field.
        # for layer in layers:
        #     fields = [f.name for f in arcpy.ListFields(layer)]
        #     if component_source_field in fields:
        #         sublayers.append(layer)

        # 1. Add fields
        arcpy.AddMessage("Add Fields start...")
        for layer in layers:
            for field in add_fields:
                if field == 'CP' or field == 'Types':
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
        ## 3.1. Create a 'temp' field to easily separate underground (UTG) from aboveground (ATG).
        component_field = "Component"
        for layer in layers:
            arcpy.management.AddField(layer, component_field, "TEXT", "", "", "", component_field, "NULLABLE", "")

        
        # Add 'UG' or 'ATG'
        ug_n = ['000001', '000002', '000021', '000031', '000041']
        ag_n = ['000011']

        # For all layers
        for layer in layers:
            arcpy.AddMessage(layer)
            with arcpy.da.UpdateCursor(layer, ["DocName", component_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        component_n = row[0][-6:]
                        if component_n in ug_n:
                            row[1] = "UG"
                        elif component_n in ag_n:
                            row[1] = "ATG"
                    cursor.updateRow(row)
        
        # Add sub-components for Below-ground
        ## Only sublayers (with t00__Description)
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, [component_field, "Types", "Family", "Workset"]) as cursor:
                for row in cursor:
                    # Underground
                    if row[0] and row[2]:
                        if row[0] == "UG":
                            if "D-Wall" in row[2]:
                                row[1] = "D-Wall"
                            elif "Floor" in row[2]:
                                row[1] = "Underground Slab"
                            elif "Column" in row[2]:
                                row[1] = "Underground Piles"
                            elif "Basic Wall" in row[2]:
                                row[1] = "Underground Walls"
                    cursor.updateRow(row)

        # Add sub-components for Above-ground
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, [component_field, 'Types', "Family", "Workset"]) as cursor:
                for row in cursor:
                    # Underground
                    if row[0] and row[2] and row[3]:
                        if row[0] == "ATG":
                            if "Slab" in row[3] or "Foundation" in row[3]:
                                row[1] = "Foundation"
                            elif "Column" in row[2]:
                                row[1] = "Piles"
                            elif "Roof" in row[3]:
                                row[1] = "Roof"
                            elif "Beam" in row[2]:
                                row[1] = "Beam"
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
                    row[2] = 18
                    row[1] = "S-03b"
                    cursor.updateRow(row)

class EditBuildingLayerStation(object):
    def __init__(self):
        self.label = "2.2 Update Building Layers (FTI)"
        self.description = "2.2 Update Building Layers (FTI)"

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

        # finish_field = arcpy.Parameter(
        #     displayName = "Field indicating completed construction dates",
        #     name = "Field indicating completed construction dates",
        #     datatype = "Field",
        #     parameterType = "Required",
        #     direction = "Input",
        # )
        # finish_field.parameterDependencies = [delete_fc.name]

        params = [delete_fc, new_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        delete_bim = params[0].valueAsText
        new_bim = params[1].valueAsText
        # finish_date_field = params[3].valueAsText

        arcpy.env.overwriteOutput = True

        # define fields
        status_field = 'Status'
        # finish_date_field = 'Finish_date'

        # Stations domains
        FTI_domain_number = 18
        
        del_layers = list(delete_bim.split(";"))
        new_layers = list(new_bim.split(";"))

        # 0. Filter sublayers 
        # component_source_field = "t00__Description"
        # del_sublayers = []
        # new_sublayers = []

        # ## Process sublayers only when they have "t00__Description" field.
        # for layer in del_layers:
        #     fields = [f.name for f in arcpy.ListFields(layer)]
        #     if component_source_field in fields:
        #         del_sublayers.append(layer)

        # for layer in new_layers:
        #     fields = [f.name for f in arcpy.ListFields(layer)]
        #     if component_source_field in fields:
        #         new_sublayers.append(layer)

        # 1. Check names are matched between deleted layers and new layers
        del_basenames = []
        new_basenames = []

        for layer in del_layers:
            del_basenames.append(os.path.basename(layer))

        for layer in new_layers:
            new_basenames.append(os.path.basename(layer))

        arcpy.AddMessage(f"deleted layer names: {sorted(del_basenames)}")
        arcpy.AddMessage(f"new layer names: {sorted(new_basenames)}")

        # # 2. Add and Delete
        if sorted(del_basenames) == sorted(new_basenames):
            arcpy.AddMessage('Sublayer names are all matched.')
    
            for target_layer in del_layers:
                del_basename = os.path.basename(target_layer)

                # 1. Add new layer
                new_layers_series = pd.Series(new_layers)
                id = new_layers_series.index[new_layers_series.str.contains(del_basename,regex=True)][0]
                new_layer = new_layers[id]
                arcpy.AddMessage(del_basename + "; " + new_layer)

                # 2. Update 'Status' field in new_layer using 'xx_Status or xx_status' field from Revit
                # empty cell (null): 1. To be Constructed, 4. Completed
                # 2. Extract fields
                bim_fields = [e.name for e in arcpy.ListFields(new_layer)]

                ## 3. Search field name excluding 'Project_'
                try:
                    bim_status_field = [re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e).group() for e in bim_fields if re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e) is not None]
                except AttributeError:
                    bim_status_field = [re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e) for e in bim_fields if re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e) is not None]

                arcpy.AddMessage(f"The name of status field in BIM models: {bim_status_field}")

                # 4. Update 'Status' field in new_layer
                if len(bim_status_field) == 1: # Update only When status field exists in the BIM model (input)
                    with arcpy.da.UpdateCursor(new_layer, [bim_status_field, status_field]) as cursor:
                        for row in cursor:
                            if row[0] == 'Completed':
                                row[1] = 4
                            elif row[0] is None:
                                row[1] = 1
                            cursor.updateRow(row)

                # 5. Replace target layer with new observations
                where_clause = "Station = {}".format(FTI_domain_number)
                arcpy.management.SelectLayerByAttribute(target_layer, 'SUBSET_SELECTION',where_clause)

                # Truncate
                arcpy.management.DeleteRows(target_layer)

                # Append
                arcpy.management.Append(new_layer, target_layer, schema_type = 'NO_TEST', expression = where_clause)
        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class DomainSettingStationStructure(object):
    def __init__(self):
        self.label = "2.3. Apply Domain to Fields in SDE (FTI)"
        self.description = "2.3. Apply Domain to Fields in SDE (FTI)"

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
        domain_field.filter.list = ['Status','Station']

        params = [gis_layers, domain_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        gis_layers = params[0].valueAsText
        domain_field = params[1].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(gis_layers.split(";"))

        # component_source_field = "t00__Description"

        # # 0. Filter sublayers 
        # sublayers = []
        # ## Process sublayers only when they have "t00__Description" field.
        # for layer in layers:
        #     fields = [f.name for f in arcpy.ListFields(layer)]
        #     if component_source_field in fields:
        #         sublayers.append(layer)

        # # Apply symbology changes to lyr, which will create a new finalLayer:
        # finalLayer = arcpy.management.ApplySymbologyFromLayer(lyr, "Q:\GIS_Data\Symbology_Layers\TypeSymbology.lyr")
        # # Remove the original lyr from aprxMap
        # aprxMap.removeLayer(lyr)
        # # Add the new layer that has the symbology applied
        # aprxMap.addLayer(finalLayer[0])
        
        domainList = ['Station Structures_STATUS', 'Station_nscrex']
        
        for layer in layers:
            if domain_field == 'Status':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[0])
            elif domain_field == 'Station':
                arcpy.AssignDomainToField_management(layer, domain_field, domainList[1])
            else:
                arcpy.AddError("Your specified field was not found in doman lists...please check.")