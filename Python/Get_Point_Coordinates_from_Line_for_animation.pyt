import arcpy

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
            displayName = "Input Line Feature Layer",
            name = "Input_Line_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Third parameter: choose distance between points
        in_distance = arcpy.Parameter(
            displayName = "Distance in meters between points",
            name = "Interval_Distance_between_points",
            datatype = "GPLong",
            parameterType = "Required",
            direction = "Input"
        )

        # set the filter to accept onl local (personal or file) geodatabase
        ws.filter.list = ["Local Database"]

        params = [ws, in_fc, in_distance]

        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        ##workspace = params[0].valueAsText
        inFeature = params[1].valueAsText
        inDistance = params[2].valueAsText

        # 1. Generate points at specified interval in meters
        ## Do not choose complicated polyline. As the order of points is of importance,
        ## the complicated polyline will not generate the points in order for a moving symbol.
        ## Ideally, lines that do not cross or turn back work, because of no need to consider
        ## the order of points.

        inDis = "{0} meters".format(inDistance)
        arcpy.AddMessage(inDis)
        pointFeature = arcpy.GeneratePointsAlongLines_management(inFeature, 'PointsForAnimation', 'DISTANCE', Distance=inDis,
                                                                 Include_End_Points='END_POINTS')

        # 1. Calculate Geometry Attribute
        arcpy.CalculateGeometryAttributes_management(pointFeature, [["latitude", "POINT_Y"],
                                                                 ["longitude", "POINT_X"]],
                                                     "", "", "", "DD")

        # 2. Add field to convert the above notation to Anime.js format
        ## var Point1 = {latitude: yy, longitude: xx};
        newField = 'pointNotation'
        arcpy.AddField_management(pointFeature, newField, "TEXT", "", "", "", "", "NULLABLE")

        compiledList = []
        with arcpy.da.UpdateCursor(pointFeature, ['latitude', 'longitude','pointNotation']) as cursor:
            rec = 0
            for row in cursor:
                compPoint = "{{latitude: {0}, longitude: {1}}}".format(row[0], row[1])
                row[2] = compPoint
                
                pStart = 1
                pInterval = 1

                if rec == 0:
                    com = "var point{0} = {1};".format(pStart, compPoint)
                else:
                    com = "var point{0} = {1};".format(rec, compPoint)
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
        ## Get Count: number of observations
        result = arcpy.GetCount_management(pointFeature)

        positionArray = []
        with arcpy.da.SearchCursor(pointFeature, ['pointNotation']) as cursor:
            rec = 1
            for row in cursor:
                if row[0]:
                    pStart = 1
                    pInterval = 1

                    if rec == 0:
                        pointAnime = ".add({{...point{0}, easing: 'linear'}})".format(pStart)
                    elif rec > 0 and rec < int(result[0]):
                        pointAnime = ".add({{...point{0}, easing: 'linear'}})".format(rec)
                        positionArray.append(pointAnime)
                    else:
                        pointAnime = ".add({{z: 0, easing: 'easeOutSine'}},0)".format(rec)
                        positionArray.append(pointAnime)

                    rec = rec + pInterval

        ## Re-arrange the compiled list using new lines
        positionArray = '\n'.join(positionArray)

        arcpy.AddMessage(positionArray)


