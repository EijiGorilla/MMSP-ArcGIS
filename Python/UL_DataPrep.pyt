import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "ULToolbox"
        self.alias = "ULToolbox"
        self.tools = [ULTool]

class ULTool(object):
    def __init__(self):
        self.label = "Prepare Utility Relocation Data"
        self.description = "Prepared utility relocation data for both points and lines"

    def getParameterInfo(self):
        # Define parameter definition

        # First parameter
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Second parameter
        in_fc = arcpy.Parameter(
            displayName = "Input Feature Layer",
            name = "Input_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        # set the filter to accept only local (personal or file) geodatabases
        ws.filter.list = ["Local Database"]
        #in_fc.parameterDependencies = [ws.name]

        params = [ws, in_fc]

        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inFeatures  = params[1].valueAsText
        testL = inFeatures.replace("'","")
        listLayers = testL.split(';')

        for inFeature in listLayers:
            # Check Geometry Type
            arcpy.AddMessage(inFeature)
            geometryType = arcpy.Describe(inFeature).shapeType
            
            if geometryType == 'Point':
                # Force a value for 'Type' field to be 'Point'
                with arcpy.da.UpdateCursor(inFeature, ['Type']) as cursor:
                    for row in cursor:
                        row[0] = 'Point'
                        cursor.updateRow(row)

                 ## 1. Enter Facitlity (1. Overhead, 2. Underground, 3. At-Grade) using UtilType2
                with arcpy.da.UpdateCursor(inFeature, ['Facility','UtilType2']) as cursor:
                    for row in cursor:
                        # Enter Facility
                        if row[1] in [1, 2, 5, 18, 7, 8, 19, 14]:
                            row[0] = 3
                        elif row[1] in [3, 4, 10, 11, 17, 6]:
                            row[0] = 2
                        cursor.updateRow(row)

                ## 2. Enter Height
                ### At-Grade: Height = 0
                with arcpy.da.UpdateCursor(inFeature, ['Facility', 'Height', 'UtilType2']) as cursor:
                    for row in cursor:
                        if row[0] == 3:
                            row[1] = 0
                        elif row[2] in (3, 4, 10, 11, 17):
                            row[1] = -1
                        elif row[2] == 6:
                            row[1] = -3
                        cursor.updateRow(row)
            
                ## 3. Enter Size
                with arcpy.da.UpdateCursor(inFeature, ['SIZE', 'UtilType2']) as cursor:
                    for row in cursor:
                        if row[1] in (1, 2, 7, 8, 19):
                            row[0] = 8
                        elif row[1] in (3, 4, 5, 10, 11, 17, 18, 6):
                            row[0] = 0.5
                        elif row[1] == 14:
                            row[0] = 3
                        cursor.updateRow(row)
            else:
                # Force a value for 'Type' field to be 'Point'
                with arcpy.da.UpdateCursor(inFeature, ['Type']) as cursor:
                    for row in cursor:
                        row[0] = 'Line'
                        cursor.updateRow(row)
            
                ## 1. Enter Height
                with arcpy.da.UpdateCursor(inFeature, ['UtilType2', 'Facility', 'Height']) as cursor:
                    for row in cursor:
                        # Height = 0 when Facility is at-grade (3).
                        if row[1] == 3:
                            row[2] = 0

                        # Telecom Line and Underground, Height = -2.0
                        elif row[0] == 1 and row[1] == 2: 
                            row[2] = -2
                
                        # Telecome Line/Internet Cable Line/Electric Line and Aboveground, height = 8.0
                        elif row[0] in (1, 2, 8) and row[1] == 1:
                            row[2] = 8

                        # Internet Cable Line for Underground
                        elif row[0] == 2 and row[1] == 2:
                            row[2] = -3

                        # Sewerage/Drainage/Canal/Creek and Underground, Height = -3.0
                        elif row[0] in (4, 5, 6, 7, 11):
                            row[1] == 2
                            row[2] = -3

                        # Water Distribution Pipe and Underground, Height = -3.5
                        elif row[0] == 3:
                            row[1] == 2
                            row[2] = -3.5

                        # Electric Line and Underground, Height = -2.5
                        elif row[0] == 8 and row[1] == 2:
                            row[2] = -2.5
                        cursor.updateRow(row)





