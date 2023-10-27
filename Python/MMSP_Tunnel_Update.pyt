import arcpy
from datetime import date, datetime

class Toolbox(object):
    def __init__(self):
        self.label = "IdentifyTBMLocation"
        self.alias = "IdentifyTBMLocation"
        self.tools = [UpdateUsingMasterList, IdentifyTBM, DelayedSegment]

class UpdateUsingMasterList(object):
    def __init__(self):
        self.label = "1.Update Feature Layer using Excel Master List"
        self.description = "Update any type of feature layers using excel master list table"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_fc = arcpy.Parameter(
            displayName = "Input Feature Layer",
            name = "Input Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        ml = arcpy.Parameter(
            displayName = "Excel Master List",
            name = "Excel Master List",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        jField = arcpy.Parameter(
            displayName = "Join Field",
            name = "Join Field",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"            
        )
        jField.parameterDependencies = [in_fc.name]

        params = [ws, in_fc, ml, jField]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_fc = params[1].valueAsText
        ml = params[2].valueAsText
        joinField = params[3].valueAsText

        arcpy.env.overwriteOutput = True

        # 1. Copy feature layer
        copyLayer = 'copiedLayer'

        copiedL = arcpy.CopyFeatures_management(in_fc, copyLayer)

        # 2. Delete Field
        fieldNames= [f.name for f in arcpy.ListFields(copiedL)]

        ## 2.1. Identify fields to be droppeds
        baseField = ['Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','OBJECTID_1','GlobalID']
        fieldsKeep = tuple([joinField]) + tuple(baseField)

        dropField = [e for e in fieldNames if e not in fieldsKeep]

        ## 2.2. Extract existing fields
        inField = [f.name for f in arcpy.ListFields(copiedL)]

        arcpy.AddMessage("Stage 1: Extract existing fields was success")

        ## 2.3. Check if there are fields to be dropped
        finalDropField = [f for f in inField if f in tuple(dropField)]

        arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")

        ## 2.4 Drop
        if len(finalDropField) == 0:
            arcpy.AddMessage("There is no field that can be dropped from the feature layer")
        else:
            arcpy.DeleteField_management(copiedL, finalDropField)
            
        arcpy.AddMessage("Stage 1: Dropping Fields was success")
        arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

        # 3. Join Field
        ## 3.1. Convert Excel tables to feature table
        MasterList = arcpy.TableToTable_conversion(ml, workspace, 'MasterList')

        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        inputField = [f.name for f in arcpy.ListFields(MasterList)]

        toBeJoinedField = tuple([joinField]) + tuple(['OBJECTID'])
        joiningField = [e for e in inputField if e not in toBeJoinedField]

        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        tLot = [f.name for f in arcpy.ListFields(copiedL)]

        in_field = ' '.join(map(str, [f for f in tLot if f in tuple([joinField])]))
        uLot = [f.name for f in arcpy.ListFields(MasterList)]

        join_field=' '.join(map(str, [f for f in uLot if f in tuple([joinField])]))

        ## 3.4 Join
        arcpy.JoinField_management(in_data=copiedL, in_field=in_field, join_table=MasterList, join_field=join_field, fields=joiningField)

        # 4. Trucnate
        arcpy.TruncateTable_management(in_fc)

        # 5. Append
        arcpy.Append_management(copiedL, in_fc, schema_type = 'NO_TEST')

        # Delete the copied feature layer
        deleteTempLayers = [copiedL, MasterList]
        arcpy.Delete_management(deleteTempLayers)

class IdentifyTBM(object):
    def __init__(self):
        self.label = "2.Identify TBM Location"
        self.description = "Identify the location of TBM cutter head"

    def getParameterInfo(self):
        # Input Feature Layer
        in_layer = arcpy.Parameter(
            displayName = "Input Feature layer",
            name = "Input Feature layer",
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

        segmentsAll = ['SG1']

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
                if row[0] == "SG1-NB":
                    if len(SG1_NB) != 0 and row[1] == max(SG1_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG1-SB":
                    if len(SG1_SB) != 0 and row[1] == max(SG1_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG2-NB":
                    if len(SG2_NB) != 0 and row[1] == max(SG2_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG2-SB":
                    if len(SG2_SB) != 0 and row[1] == max(SG2_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG3-NB":
                    if len(SG3_NB) != 0 and row[1] == max(SG3_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG3-SB":
                    if len(SG3_SB) != 0 and row[1] == max(SG3_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG4-NB":
                    if len(SG4_NB) != 0 and row[1] == max(SG4_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG4-SB":
                    if len(SG4_SB) != 0 and row[1] == max(SG4_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG5-NB":
                    if len(SG5_NB) != 0 and row[1] == max(SG5_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG5-SB":
                    if len(SG5_SB) != 0 and row[1] == max(SG5_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG6-NB":
                    if len(SG6_NB) != 0 and row[1] == max(SG6_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG6-SB":
                    if len(SG6_SB) != 0 and row[1] == max(SG6_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG7-NB":
                    if len(SG7_NB) != 0 and row[1] == max(SG7_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG7-SB":
                    if len(SG7_SB) != 0 and row[1] == max(SG7_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG8-NB":
                    if len(SG8_NB) != 0 and row[1] == max(SG8_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG8-SB":
                    if len(SG8_SB) != 0 and row[1] == max(SG8_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG9-NB":
                    if len(SG9_NB) != 0 and row[1] == max(SG9_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG9-SB":
                    if len(SG9_SB) != 0 and row[1] == max(SG9_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG10-NB":
                    if len(SG10_NB) != 0 and row[1] == max(SG10_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG10-SB":
                    if len(SG10_SB) != 0 and row[1] == max(SG10_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG11-NB":
                    if len(SG11_NB) != 0 and row[1] == max(SG11_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG11-SB":
                    if len(SG11_SB) != 0 and row[1] == max(SG11_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG12-NB":
                    if len(SG12_NB) != 0 and row[1] == max(SG12_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG12-SB":
                    if len(SG12_SB) != 0 and row[1] == max(SG12_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG13-NB":
                    if len(SG13_NB) != 0 and row[1] == max(SG13_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG13-SB":
                    if len(SG13_SB) != 0 and row[1] == max(SG13_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG14-NB":
                    if len(SG14_NB) != 0 and row[1] == max(SG14_NB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue

                if row[0] == "SG14-SB":
                    if len(SG14_SB) != 0 and row[1] == max(SG14_SB) + cutterHeadPos:
                        row[2] = 1
                        row[3] = 2
                    else:
                        continue
                cursor.updateRow(row)

class DelayedSegment(object):
    def __init__(self):
        self.label = "3.Identify Delayed Segment in TBM tunnel"
        self.description = "Identify the location of TBM segment being delayed"
    
    def getParameterInfo(self):
        # Input Feature Layer
        in_layer = arcpy.Parameter(
            displayName = "Input Feature layer",
            name = "Input Feature layer",
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

        today = date.today()

        with arcpy.da.UpdateCursor(inFeature, ["TargetDate", "delayed", "status"]) as cursor:
            for row in cursor:
                d2 = row[0].date()
                if d2 < today and row[2] < 3: # 3 = completed [when status is not completed]
                    row[1] = 1
                else:
                    row[1] = None
                cursor.updateRow(row)