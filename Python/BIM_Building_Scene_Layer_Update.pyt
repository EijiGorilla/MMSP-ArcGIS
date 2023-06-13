import arcpy
import os

"""
# INSTRUCTION and DESCRIPTION
This python toolbox is comprised of two parts: Input Revit Files and Update Existing Building Layer.
1. Input Revit Files
    1.1. Defin Projection to PRS92
    1.2. Convert BIM to Geodatabase (file geodatabase)
    1.3. Make building layers
    1.4. Manually 'remove empty layers' from the building layers added to Contents pane

2. Update Existing Building Layers
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
        self.tools = [InputRevitFiles, UpdateExistingBuildingLayers]

class InputRevitFiles(object):
    def __init__(self):
        self.label = "1. Input New Revit files using Building Layers"
        self.description = "Add new revit files with new construction status and convert them to building layers"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
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

        in_buildingLayerName = arcpy.Parameter(
            displayName = "Add building layer name to be displayed in Contental panel",
            name = "AddBuildingLayerName",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        in_featureDatasetName = arcpy.Parameter(
            displayName = "Add feature dataset name when revit files are added to file geodatabase",
            name = "AddFeatureDatasetName",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [ws, in_revit, in_buildingLayerName, in_featureDatasetName]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_revit = params[1].valueAsText
        in_buildingLayerName = params[2].valueAsText
        in_featureDatasetName = params[3].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("WGS 1984 Web Mercator (auxiliary sphere)")
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

        # Convert BIM file to geodatabase
        spatial_reference = "PRS_1992_Philippines_Zone_III"
        arcpy.BIMFileToGeodatabase_conversion(in_revit, workspace, in_featureDatasetName, spatial_reference)

        # Make Building Layers
        out_dataset = os.path.join(workspace, in_featureDatasetName)
        arcpy.MakeBuildingLayer_management(out_dataset, in_buildingLayerName)

class UpdateExistingBuildingLayers(object):
    def __init__(self):
        self.label = "2. Update Existing Building Layers"
        self.description = "Update existing building layers using the new building layers"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

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

        params = [ws, in_buildingLayers, target_buildingLayers, transfer_field]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_buildingLayers = params[1].valueAsText
        target_buildingLayers = params[2].valueAsText
        transfer_field = params[3].valueAsText

        arcpy.env.overwriteOutput = True

        # 1. Compile basenames of input building layers
        basename_input = []
        for feature in in_buildingLayers:
            basename = os.path.basename(feature)
            basename_input.append(basename)

        # 2. Join 'Status' to each building layer
        joinField = 'ObjectId'

        for feature in target_buildingLayers:
            # Get input_feature corresponding to target_feature
            basename = os.path.basename(feature)
            index = basename_input.index(basename)
            joinTable = in_buildingLayers[index]
            
            # Join
            arcpy.management.JoinField(feature, joinField, joinTable, joinField, transfer_field)

        # 3. Update 'Status' using 'Status1'
        tempField = transfer_field + "_1"

        for feature in target_buildingLayers:
            with arcpy.da.UpdateCursor(feature, [transfer_field, tempField]) as cursor:
                for row in cursor:
                    if row[1] is None:
                        row[0] = row[0]
                    elif row[0] is not row[1]:
                        row[0] = row[1]
                    cursor.updateRow(row)

        # 4. Delete tempField
        for feature in target_buildingLayers:
            arcpy.DeleteField_management(feature, tempField)




