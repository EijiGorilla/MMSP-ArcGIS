import arcpy
import pandas as pd

class Toolbox(object):
    def __init__(self):
        self.label = "PointCoordinatesFromLineBox"
        self.alias = "PointCoordinatesFromLineBox"
        self.tools = [PointCoordinateFromLine]

class PointCoordinateFromLine(object):
    def __init__(self):
        self.label = "Get Point Coordinates from Line feature for Animating symbol"
        self.description = "Get Point Coordinates from Line feature for Animating symbol"

    def getParameterInfo(self):
        # First parameter: workspace (file geodatabase)
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # second parameter: input feature layer
        in_fc = arcpy.Parameter(
            displayName = "Input Point Feature Layer",
            name = "Input_Point_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # set the filter to accept onl local (personal or file) geodatabase
        ws.filter.list = ["Local Database"]

        params = [ws, in_fc]

        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        ##workspace = params[0].valueAsText
        inFeature = params[1].valueAsText

        # 1. Calculate Geometry Attribute
        arcpy.CalculateGeometryAttributes_management(inFeature, [["latitude", "POINT_Y"],
                                                                 ["longitude", "POINT_X"]],
                                                     "", "", "", "DD")


        # 2. Add field to convert the above notation to Anime.js format
        ## var Point1 = {latitude: yy, longitude: xx};
        newField = 'pointNotation'
        arcpy.AddField_management(inFeature, newField, "TEXT", "", "", "", "", "NULLABLE")

        compiledList = []

        rec = 1
        with arcpy.da.UpdateCursor(inFeature, ['latitude', 'longitude','pointNotation']) as cursor:
            for row in cursor:
                compPoint = "{{latitude: '{0}', longitude: '{1}'}}".format(row[0], row[1])
                row[2] = compPoint

                pInterval = 1

                if rec == 1:
                    com = "var Point{0} = {1};".format(rec, compPoint)
                else:
                    com = "var Point{0} = {1};".format(rec, compPoint)
                    compiledList.append(com)
                cursor.updateRow(row)
                
                rec = rec + pInterval

        ## Re-arrange the compiled list using new lines
        compiledList = '\n'.join(compiledList)
        arcpy.AddMessage(compiledList)
        

        # 3. Create specific format for each point animation for Anime.js
        ## .add({z: 0, each row, easing: "linear"}) // 1st line onward
        ## .add({z: 0, each row, easing: "linear"}, 0) // last line

        ## 3.1. Create an empty array
        positionArray = []

        rec = 1
        with arcpy.da.SearchCursor(inFeature, ['pointNotation']) as cursor:
            for row in cursor:
                if row[0]:
                    pInterval = 1

                    if rec == 1:
                        pointAnime = ".add({{z: 0, Point{0}, easing: 'linear'}})".format(rec)
                    else:
                        pointAnime = ".add({{z: 0, Point{0}, easing: 'linear'}})".format(rec)
                        positionArray.append(pointAnime)

                    rec = rec + pInterval

        ## Re-arrange the compiled list using new lines
        positionArray = '\n'.join(positionArray)
        arcpy.AddMessage(positionArray)


