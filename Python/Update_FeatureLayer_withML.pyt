import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateFeatureLayerBox"
        self.alias = "UpdateFeatureLayerBox"
        self.tools = [FeatureLayerUpdateTool]

class FeatureLayerUpdateTool(object):
    def __init__(self):
        self.label = "Update Feature Layer with Master List"
        self.description = "Update Feature Layer with Master List table"

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
            displayName = "Input Feature Layer",
            name = "Input_Feature_Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Third parameter: excel master list
        in_table = arcpy.Parameter(
            displayName = "Excel Master List",
            name = "Excel_Master_List",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        # Fourth Parameter: common field to join two tables
        join_field = arcpy.Parameter(
            displayName = "Join Field",
            name = "Join_Field",
            datatype = "Field",
            direction = "Input"
        )
        join_field.parameterDependencies = [in_fc.name]

        # set the filter to accept onl local (personal or file) geodatabase
        ws.filter.list = ["Local Database"]

        params = [ws, in_fc, in_table, join_field]

        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        inFeature = params[1].valueAsText
        inTable = params[2].valueAsText
        joinField = params[3].valueAsText

        # 1. Copy Input Feature Layer
        copyLayer = 'copiedLayer'
        copiedL = arcpy.CopyFeatures_management(inFeature, copyLayer)
        
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
        MasterList = arcpy.TableToTable_conversion(inTable, workspace, 'MasterList')

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
        arcpy.TruncateTable_management(inFeature)

        # 5. Append
        arcpy.Append_management(copiedL, inFeature, schema_type = 'NO_TEST')

        # Delete the copied feature layer
        deleteTempLayers = [copiedL, MasterList]
        arcpy.Delete_management(deleteTempLayers)