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

        # second parameter: Source Feature Layer (FGDB)
        source_fc = arcpy.Parameter(
            displayName = "Source Feature Layer (FGDB)",
            name = "Source_Feature_Layer",
            datatype = "GPFeatureLayer",
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

        params = [ws, source_fc, target_fc, in_table]

        return params

    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        sourceFeature = params[1].valueAsText
        targetFeature = params[2].valueAsText
        inTable = params[3].valueAsText
        
        # 1. Import the tree master list table
        out_name = "Trees_table"
        treeTableGDB = arcpy.TableToTable_conversion(inTable, workspace, out_name)

        # 2. Convert the table to a point feature layer
        fNames = [f.name for f in arcpy.ListFields(treeTableGDB)]

        ## Obtain field name for latitude and longitude
        reg_long = re.compile(r"Long*|long*")
        reg_lat = re.compile(r"Lati*|lati*")

        long = list(filter(reg_long.match, fNames))
        lat = list(filter(reg_lat.match, fNames))

        out_feature_class = "Tree_points"
        xyP = arcpy.management.XYTableToPoint(treeTableGDB, out_feature_class, long[0], lat[0], "", arcpy.SpatialReference(4326))

        # create a spatial reference object for the output coordinate system
        out_coordinate_system = arcpy.SpatialReference(3857) # WGS84 Auxiliary

        # run the tool
        output_feature_class = "Tree_points_prj3857"
        xyP_prj = arcpy.Project_management(xyP, output_feature_class, out_coordinate_system)


        # 3. Truncate the main feature layer
        arcpy.TruncateTable_management(sourceFeature)

        # 4. Append the point FL to the main FL
        arcpy.Append_management(xyP_prj, sourceFeature, schema_type = 'NO_TEST')

        # 5. Copy the main FL in PRS92
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"

        copied = "copied_layer"
        copyL = arcpy.CopyFeatures_management(sourceFeature, copied)

        # 6. truncates the SDE
        arcpy.TruncateTable_management(targetFeature)

        # 7, Append the copied FGDB to the SDE
        arcpy.Append_management(copyL, targetFeature, schema_type = 'NO_TEST')

        # Delete
        deleteL = [treeTableGDB, xyP, xyP_prj, copyL]
        arcpy.Delete_management(deleteL)
