import arcpy
import re

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateTreeLayerBox"
        self.description = "UpdateTreeLayerBox"
        self.tools = [TreeLayerUpdateTool]

class TreeLayerUpdateTool(object):
    def __init__(self):
        self.label = "Update Tree Layer with Master List"
        self.description = "Update Tree Layer with Master List"

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
        
        # 1. Import the tree master list table
        out_name = "Trees_table"
        arcpy.conversion.ExportTable(inTable, out_name, "", "NOT_USE_ALIAS")

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
        arcpy.TruncateTable_management(targetFeature)

        # 5. Append the copied FGDB to the SDE
        arcpy.Append_management(copied, targetFeature, schema_type = 'NO_TEST')

        # 6. Delete
        deleteL = [out_name, out_feature_class, output_feature_class, copied]
        arcpy.Delete_management(deleteL)
