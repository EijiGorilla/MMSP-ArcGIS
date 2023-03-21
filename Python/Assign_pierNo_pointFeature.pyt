import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "CreatePierNoPointFeature"
        self.alias = "CreatePierNoPointFeature"
        self.tools = [CreatePierPointFeature]

class CreatePierPointFeature(object):
    def __init__(self):
        self.label = "Generate Pier No Point Feature using Viaduct"
        self.description = "Create pier number point feature layer using pre-assigned pierIds of viadcut"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_fc = arcpy.Parameter(
            displayName = "Input Viaduct Multipatch Layer",
            name = "Input Viaduct Multipatch Layer",
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

        addField = arcpy.Parameter(
            displayName = "Add Field",
            name = "Add Field",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        addField.parameterDependencies = [ml.name]

        params = [ws, in_fc, ml, jField, addField]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_fc = params[1].valueAsText
        ml = params[2].valueAsText
        joinField = params[3].valueAsText
        addField = params[4].valueAsText

        arcpy.env.overwriteOutput = True

        # 0. join field
        ## addField = "pier_id"
        arcpy.JoinField_management(in_data=in_fc, in_field=joinField, join_table=ml, join_field=joinField, fields=addField)

        # 1. Define output features for each pier id (1, 2, and 3)
        ## pier_id = 1: onpier per pier head (one pier no point)
        ## pier_id = 2: two piers per pier head (one pier no point)
        ## pier_id = 3: three piers per pier head (threes pier no points per pier head)
        output1 = "pierId1"
        output2 = "pierId2"
        output3 = "pierId3"

        # 2. Make temporary feature layer
        arcpy.MakeFeatureLayer_management(in_fc, output1)
        arcpy.MakeFeatureLayer_management(in_fc, output2)
        arcpy.MakeFeatureLayer_management(in_fc, output3)

        # 3. Select layer by viaduct type
        arcpy.SelectLayerByAttribute_management(output1, "SUBSET_SELECTION", "Type = 4 AND pier_id = 1")
        arcpy.SelectLayerByAttribute_management(output2, "SUBSET_SELECTION", "Type = 4 AND pier_id = 2")
        arcpy.SelectLayerByAttribute_management(output3, "SUBSET_SELECTION", "Type = 3 AND pier_id = 3") # use pier

        # 4. Feature to point
        outFeature1 = output1 + "_" + "feaPt"
        outFeature2 = output2 + "_" + "feaPt"
        outFeature3 = output3 + "_" + "feaPt"

        arcpy.management.FeatureToPoint(output1, outFeature1)
        arcpy.management.FeatureToPoint(output2, outFeature2)
        arcpy.management.FeatureToPoint(output3, outFeature3)

        # 5. Merge
        mergedPierPoints = "merged_pierNo_points"
        arcpy.management.Merge([outFeature1, outFeature2, outFeature3], mergedPierPoints)

        # 6. Field management
        ## keep field
        fieldNames = [f.name for f in arcpy.ListFields(mergedPierPoints)]
        baseField = ['Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','OBJECTID_1','GlobalID']
        keepFields = ["PierNumber", "CP"]
        keepFieldsAll = baseField + keepFields
    
        dropField = [e for e in fieldNames if e not in keepFieldsAll]

        arcpy.DeleteField_management(mergedPierPoints, dropField)

        # 7. Alter field
        ## 'PierNumber' to 'PIER'
        new_field_name = "PIER"
        field_type = "TEXT"
        field_is_nullable = "NULLABLE"
        clear_field_alias = "FALSE"
        arcpy.management.AlterField(mergedPierPoints,
                                    keepFields[0], new_field_name, new_field_name,
                                    field_type, "",
                                    field_is_nullable, clear_field_alias)
        
        # 8. Add new fields
        ## 'AccessDate', 'Notes'
        fieldName1 = "AccessDate"
        fieldName2 = "Notes"

        arcpy.management.AddField(mergedPierPoints, fieldName1, "DATE", "",
                                  field_alias = fieldName1, field_is_nullable = "NULLABLE")
        
        arcpy.management.AddField(mergedPierPoints, fieldName2, "TEXT", "",
                                  field_alias = fieldName2, field_is_nullable = "NULLABLE")


        # 9. Delete
        deleteOutputs = [outFeature1, outFeature2, outFeature3]
        arcpy.management.Delete(deleteOutputs)



