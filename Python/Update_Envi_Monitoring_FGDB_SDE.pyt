import arcpy
import re

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateEnviMonitoringLayerBox"
        self.description = "UpdateEnviMonitoringLayerBox"
        self.tools = [EnviMonitoringUpdateTool]

class EnviMonitoringUpdateTool(object):
    def __init__(self):
        self.label = "Update Envi Monitoring Layer with Master List"
        self.description = "Update Environment Monitoring Layer with Master List"

    def getParameterInfo(self):
        # First parameter: workspace (file geodatabase)
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # third parameter: target feature layer (SDE)
        target_fc = arcpy.Parameter(
            displayName = "Target Feature Layer (SDE)",
            name = "Target_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Fourth parameter: excel master list
        in_table = arcpy.Parameter(
            displayName = "Excel Master List",
            name = "Excel_Master_List",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        # set the filter to accept onl local (persoinputLayerOriginnal or file) geodatabase
        ws.filter.list = ["Local Database"]

        params = [ws, target_fc, in_table]

        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        targetFeature = params[1].valueAsText
        inTable = params[2].valueAsText

        # 1. Import the Envi monitoring master list table
        out_name = "monitor_table"
        tableGDB = arcpy.TableToTable_conversion(inTable, workspace, out_name)
        
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
        arcpy.CopyFeatures_management(targetFeature, copied)

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
        arcpy.TruncateTable_management(targetFeature)

        # 7. Appen the copied SDE to the original SDE
        arcpy.Append_management(copied2, targetFeature, schema_type = 'NO_TEST')

        # Delete
        deleteL = [tableGDB, xyP, xyP_prj, copied, copied2]
        arcpy.Delete_management(deleteL)
        #End






