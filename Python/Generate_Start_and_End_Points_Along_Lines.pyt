import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "GenerateStartEndPointsAlongLines"
        self.alias = "GenerateStartEndPointsAlongLines"
        self.tools = [PointsAlongLines]

class PointsAlongLines(object):
    def __init__(self):
        self.label = "Generate Start And End Points Along Lines"
        self.description = "Generate start and end points along lines"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name="workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layer
        in_line = arcpy.Parameter(
            displayName = "Polyline",
            name = "Polyline",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue=True
        )

        params = [ws, in_line]
        return params

    def updateMessage(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        inLine = params[1].valueAsText

        arcpy.env.overwriteOutput = True

        inputFeatures = inLine.split(";")

        # 1. Run 'Generate Points Along Lines' geoprocessing tool
        
        n  = 0
        tempFiles = []
        for feature in inputFeatures:
            out_fc = "output" + "_" + str(n)
            n = n + 1

            arcpy.AddMessage(out_fc)
            arcpy.GeneratePointsAlongLines_management(feature, out_fc, 'PERCENTAGE', Percentage=100, Include_End_Points='END_POINTS')

            # 2. Run 'Add XY Coordinate'
            arcpy.AddXY_management(out_fc)

            # 3. Run 'Delete Identical'
            arcpy.DeleteIdentical_management(out_fc, "POINT_X")

            # 4. Append output point feature layers
            tempFiles.append(out_fc)

        # Merge all
        outputLayer = "N2SC_CP_BreakPoints"
        arcpy.AddMessage(tempFiles)
        arcpy.management.Merge(tempFiles, outputLayer, "", "ADD_SOURCE_INFO")

        # 4. Delete the copied layer
        arcpy.Delete_management(tempFiles)




