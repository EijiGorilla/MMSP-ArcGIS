import arcpy
import pandas as pd
import os

"""
# INSTRUCTION and DESCRIPTION
This python toolbox generates pier number point feature layer using viaduct multipatch layer.
1. Assign patterns to each pier based on the following structural patterns.
    Pattern 1: onpier per pier head (one pier no point)
    Pattern 2: two piers per pier head (one pier no point)
    Pattern 3: three piers per pier head (threes pier no points per pier head)

    The result is exported as Excel (.xlsx) in your local drive: "C:/temp". 
    If the directory does not exist, it will be automatically created for you.

2. Generate pier point feature layer based on No. 1 using viaduct multipatch layer
    Use the exported excel sheet (.xlsx) to generate the point feature.
"""

class Toolbox(object):
    def __init__(self):
        self.label = "CreatePierNoPointFeature"
        self.alias = "CreatePierNoPointFeature"
        self.tools = [AssignPierIds, CreatePierPointFeature]

class AssignPierIds(object):
    def __init__(self):
        self.label = "1. Assign Pier IDs for Each Pier"
        self.description = "Assign pier ids for each pier using viaduct multipatch layer"

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

        params = [ws, in_fc]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_fc = params[1].valueAsText

        arcpy.env.overwriteOutput = True

        # 0. Check if field name 'pier_id' exists
        searchField = "PierNumber"
        updateField = 'pier_id'
        fields = [f.name for f in arcpy.ListFields(in_fc)]
        test = [e for e in fields if e in updateField]
        arcpy.AddMessage(len(test))

        if len(test) >= 1:
            arcpy.AddMessage("The table already has '{0}'".format(updateField))
            arcpy.DeleteField_management(in_fc, [updateField], "DELETE_FIELDS")
        
        # 1. Get unique values for PierNumber
        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})
            
        piers = unique_values(in_fc, searchField)

        # 2. Table to Table Conversion
        tempFile = 'pierid_temp.csv'

        ## Check if a directory exists
        path = "temp"
        isDir = os.path.join("C:/",path)
        isExist = os.path.exists(isDir)
        if not isExist:
            # create a new directory
            os.makedirs(isDir)
            arcpy.AddMessage("The new directory is created.")

        excelFile = os.path.join(isDir, tempFile)

        #arcpy.conversion.TableToTable(in_fc, isDir, tempFile)
        arcpy.conversion.ExportTable(in_fc, excelFile)
        data1 = pd.read_csv(excelFile)

        # 3. Update table
        for pier in piers:
            # Get row index
            row_count = data1.index[(data1[searchField] == pier) & (data1['Type'] == 3)]

            # Count row numbers
            count = len(row_count)
            
            row_num = data1.index[data1[searchField] == pier]
            # update row for pier
            if count == 1:
                data1.loc[row_num, updateField] = 1
            elif count == 2:
                data1.loc[row_num, updateField] = 2
            elif count == 3:
                data1.loc[row_num, updateField] = 3

        ## Keep only uniqueID and pier_id
        data1 = data1[['uniqueID', updateField]]

        ## Export to csv
        exportExcel = os.path.join(isDir, "temp.xlsx")
        data1.to_excel(exportExcel, index=False, sheet_name='pier_id')

class CreatePierPointFeature(object):
    def __init__(self):
        self.label = "2. Generate Pier No Point Feature using Viaduct"
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
            displayName = "Pier ID Excel Sheet",
            name = "Pier ID Excel Sheet",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        jField = arcpy.Parameter(
            displayName = "Join Field ('uniqueID')",
            name = "Join Field",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        jField.parameterDependencies = [in_fc.name]

        addField = arcpy.Parameter(
            displayName = "Add Field (choose 'pier_id' generated during the first step)",
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