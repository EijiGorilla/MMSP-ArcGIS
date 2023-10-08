import arcpy
import os

"""
# INSTRUCTION and DESCRIPTION
This python code is used to update buidling layers using new revit files for SC stations.
THe SC BIM revit files include planned construction date and completed date, so we can
directly update existing building layers using BIM models.

Before run this tool, make sure to add existing building layers in Contents pane.

This python toolbox is comprised of two parts: Input Revit Files and Update Existing Building Layer.
1. Input Revit Files
    1.1. Define Projection to PRS92
    1.2. Convert BIM to Geodatabase (file geodatabase)
    1.3. Make building layers
    1.4. Manually 'remove empty layers' from the building layers added to Contents pane

2. Make Building Layers
    * Unfortunately, if you run arcpy.BuildingLayer_management inside Python toolbox, output will not appear in Contents pane.
    * You need to manually open this geoprocessing tool and run

3. Update Existing Building Layers
 *** Ensure to unlock existing building layers from enterprise geodatabase; otherwise, this fails.
    2.1. Join Field using new layer (tansfer field = 'Status')
    2.2. Update 'Status' for only selected rows
    2.3. Delete 'Status1'
    2.4. Repeat 2.1-2.3 for each layer
    2.5. (option) Manually delete feature dataset created in the first step
"""

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateBIMBuildingSceneLayers"
        self.alias = "UpdateBIMBuildingSceneLayers"
        self.tools = [InputRevitFiles, MakeBuildingLayers, UpdateExistingBuildingLayers]

class InputRevitFiles(object):
    def __init__(self):
        self.label = "1. Input New Revit files using Building Layers"
        self.description = "Add new revit files with new construction status and convert them to building layers"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace (file geodatabase)",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_revit = arcpy.Parameter(
            displayName = "BIM Revit files",
            name = "BIMRevitFiles",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        in_featureDatasetName = arcpy.Parameter(
            displayName = "Name of Feature Dataset in file geodatabase when revit files are added",
            name = "AddFeatureDatasetName",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [ws, in_revit, in_featureDatasetName]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_revit = params[1].valueAsText
        in_featureDatasetName = params[2].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 Web Mercator (auxiliary sphere)")
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

        # Convert BIM file to geodatabase
        spatial_reference = "PRS_1992_Philippines_Zone_III"
        arcpy.BIMFileToGeodatabase_conversion(in_revit, workspace, in_featureDatasetName, spatial_reference)

class MakeBuildingLayers(object):
    def __init__(self):
        self.label = "2.(NOT WORKING: Manually run 'Make Building Layer') Make Building Layers from feature dataset"
        self.description = "Make building layers from feature dataset created using new revit files"

    def getParameterInfo(self):
        in_featureDataset = arcpy.Parameter(
            displayName = "Feature Dataset",
            name = "NewFeatureDataset",
            datatype = "DEFeatureDataset",
            parameterType = "Required",
            direction = "Input"
        )

        in_buildingLayerName = arcpy.Parameter(
            displayName = "Name of building layers to be displayed in Contents pane",
            name = "AddBuildingLayerName",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_featureDataset, in_buildingLayerName]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_featureDataset = params[0].valueAsText
        in_buildingLayerName = params[1].valueAsText

        # Set overwrite option
        arcpy.env.overwriteOutput = True

        # 0. Make Building Layers from new building layers
        arcpy.MakeBuildingLayer_management(in_featureDataset, in_buildingLayerName)

class UpdateExistingBuildingLayers(object):
    def __init__(self):
        self.label = "3. Update Existing Building Layers"
        self.description = "Update existing building layers using the new building layers"

    def getParameterInfo(self):
        in_buildingLayers = arcpy.Parameter(
            displayName = "Input (new) Building Layers",
            name = "InputBuildingLayers",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        target_buildingLayers = arcpy.Parameter(
            displayName = "Target (existing) Building Layers",
            name = "TargetBuildingLayers",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        transfer_field = arcpy.Parameter(
            displayName = "Transfer field (i.e., 'Status')",
            name = "TransferField",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input",
        )
        transfer_field.parameterDependencies = [in_buildingLayers.name]

        params = [in_buildingLayers, target_buildingLayers, transfer_field]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_buildingLayers = params[0].valueAsText
        target_buildingLayers = params[1].valueAsText
        transfer_field = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        # 1. Compile basenames of input building layers
        new_buildingLayers = list(in_buildingLayers.split(";"))

        basename_input = []
        for feature in new_buildingLayers:
            basename = os.path.basename(feature)
            basename_input.append(basename)

        arcpy.AddMessage(basename_input)

        # 2. Join 'Status' to each building layer
        existing_buildingLayers = list(target_buildingLayers.split(";"))
        arcpy.AddMessage(existing_buildingLayers)

        joinField = 'ObjectId'

        for feature in existing_buildingLayers:
            # Get input_feature corresponding to target_feature
            basename = os.path.basename(feature)
            index = basename_input.index(basename)
            joinTable = new_buildingLayers[index]
            
            # Join
            arcpy.management.JoinField(feature, joinField, joinTable, joinField, transfer_field)

        # 3. Update 'Status' using 'Status1'
        tempField = transfer_field + "_1"

        for feature in existing_buildingLayers:
            with arcpy.da.UpdateCursor(feature, [transfer_field, tempField]) as cursor:
                for row in cursor:
                    if row[1] is None:
                        row[0] = row[0]
                    elif row[0] is not row[1]:
                        row[0] = row[1]
                    cursor.updateRow(row)

        # 4. Delete tempField
        for feature in existing_buildingLayers:
            arcpy.DeleteField_management(feature, tempField)




