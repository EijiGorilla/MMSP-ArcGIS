import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "IdentifyTBMLocation"
        self.alias = "IdentifyTBMLocation"
        self.tools = [IdentifyTBM]

class IdentifyTBM(object):
    def __init__(self):
        self.label = "Identify TBM Location"
        self.description = "Identify the location of TBM cutter head"

    def getParameterInfo(self):
        # Input Feature Layer
        in_layer = arcpy.Parameter(
            displayName = "TBM Tunnel",
            name = "TBM Tunnel",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inFeature = params[0].valueAsText
        arcpy.env.overwriteOutput = True

        # Empty array
        SG1_NB = []
        SG1_SB = []
        SG2_NB = []
        SG2_SB = []
        SG3_NB = []
        SG3_SB = []
        SG4_NB = []
        SG4_SB = []
        SG5_NB = []
        SG5_SB = []
        SG6_NB = []
        SG6_SB = []
        SG7_NB = []
        SG7_SB = []
        SG8_NB = []
        SG8_SB = []
        SG9_NB = []
        SG9_SB = []
        SG10_NB = []
        SG10_SB = []
        SG11_NB = []
        SG11_SB = []
        SG12_NB = []
        SG12_SB = []
        SG13_NB = []
        SG13_SB = []
        SG14_NB = []
        SG14_SB = []

        # First collect segment Numbers for each TBM line where status is completed
        fields = ["line","segmentno","status"]
        with arcpy.da.SearchCursor(inFeature, fields) as cursor:
            for row in cursor:
                if row[0] == "SG1-NB" and row[2] == 3:
                    SG1_NB.append(row[1])
                elif row[0] == "SG1-SB" and row[2] == 3:
                    SG1_SB.append(row[1])

                elif row[0] == "SG2-NB" and row[2] == 3:
                    SG2_NB.append(row[1])
                elif row[0] == "SG2-SB" and row[2] == 3:
                    SG2_SB.append(row[1])

                elif row[0] == "SG3-NB" and row[2] == 3:
                    SG3_NB.append(row[1])
                elif row[0] == "SG3-SB" and row[2] == 3:
                    SG3_SB.append(row[1])

                elif row[0] == "SG4-NB" and row[2] == 3:
                    SG4_NB.append(row[1])
                elif row[0] == "SG4-SB" and row[2] == 3:
                    SG4_SB.append(row[1])

                elif row[0] == "SG5-NB" and row[2] == 3:
                    SG5_NB.append(row[1])
                elif row[0] == "SG5-SB" and row[2] == 3:
                    SG5_SB.append(row[1])

                elif row[0] == "SG6-NB" and row[2] == 3:
                    SG6_NB.append(row[1])
                elif row[0] == "SG6-SB" and row[2] == 3:
                    SG6_SB.append(row[1])

                elif row[0] == "SG7-NB" and row[2] == 3:
                    SG7_NB.append(row[1])
                elif row[0] == "SG7-SB" and row[2] == 3:
                    SG7_SB.append(row[1])

                elif row[0] == "SG8-NB" and row[2] == 3:
                    SG8_NB.append(row[1])
                elif row[0] == "SG8-SB" and row[2] == 3:
                    SG8_SB.append(row[1])

                elif row[0] == "SG9-NB" and row[2] == 3:
                    SG9_NB.append(row[1])
                elif row[0] == "SG9-SB" and row[2] == 3:
                    SG9_SB.append(row[1])

                elif row[0] == "SG10-NB" and row[2] == 3:
                    SG10_NB.append(row[1])
                elif row[0] == "SG10-SB" and row[2] == 3:
                    SG10_SB.append(row[1])

                elif row[0] == "SG11-NB" and row[2] == 3:
                    SG11_NB.append(row[1])
                elif row[0] == "SG11-SB" and row[2] == 3:
                    SG11_SB.append(row[1])

                elif row[0] == "SG12-NB" and row[2] == 3:
                    SG12_NB.append(row[1])
                elif row[0] == "SG12-SB" and row[2] == 3:
                    SG12_SB.append(row[1])

                elif row[0] == "SG13-NB" and row[2] == 3:
                    SG13_NB.append(row[1])
                elif row[0] == "SG13-SB" and row[2] == 3:
                    SG13_SB.append(row[1])

                elif row[0] == "SG14-NB" and row[2] == 3:
                    SG14_NB.append(row[1])
                elif row[0] == "SG14-SB" and row[2] == 3:
                    SG14_SB.append(row[1])

        # Now fill in tbmSpot
        fields1 = ["line","segmentno","tbmSpot", "status"] 
        with arcpy.da.UpdateCursor(inFeature, fields1) as cursor:
            cutterHeadPos = 5
            for row in cursor:
                if row[0] == "SG1-NB" and row[1] == max(SG1_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG1-SB" and row[1] == max(SG1_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG2-NB" and row[1] == max(SG2_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG2-SB" and row[1] == max(SG2_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG3-NB" and row[1] == max(SG3_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG3-SB" and row[1] == max(SG3_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG4-NB" and row[1] == max(SG4_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG4-SB" and row[1] == max(SG4_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG5-NB" and row[1] == max(SG5_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG5-SB" and row[1] == max(SG5_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG6-NB" and row[1] == max(SG6_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG6-SB" and row[1] == max(SG6_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG7-NB" and row[1] == max(SG7_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG7-SB" and row[1] == max(SG7_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG8-NB" and row[1] == max(SG8_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG8-SB" and row[1] == max(SG8_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG9-NB" and row[1] == max(SG9_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG9-SB" and row[1] == max(SG9_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG10-NB" and row[1] == max(SG10_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG10-SB" and row[1] == max(SG10_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG11-NB" and row[1] == max(SG11_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG11-SB" and row[1] == max(SG11_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG12-NB" and row[1] == max(SG12_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG12-SB" and row[1] == max(SG12_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG13-NB" and row[1] == max(SG13_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG13-SB" and row[1] == max(SG13_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2

                elif row[0] == "SG14-NB" and row[1] == max(SG14_NB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                elif row[0] == "SG14-SB" and row[1] == max(SG14_SB) + cutterHeadPos:
                    row[2] = 1
                    row[3] = 2
                cursor.updateRow(row)