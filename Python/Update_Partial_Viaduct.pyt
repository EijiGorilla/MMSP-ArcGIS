import arcpy
import pandas as pd
import os
import re

"""
# INSTRUCTION and DESCRIPTION
!----- IMPORTANT: Make sure that in_replaced_fc and in_replacing_fc have the same coordinate system

This python toolbox is used to update original viaduct layer using new parial components of viaduct.
Note that some viaduct components are periodically updated, so we need to replace old ones with these new ones in
the target (origial) viaduct layer.
However, it is challenging to transfer existing information such as bored pile numbers and pier numbers to the newely updated ones.
This code partially solves this problem by partially automating manual operations.

Please make sure to read these descriptons before you run.

First Batch
    0. Add uniqueID (sequential numbers) to new multipatch layer (i.e., replacing layer)
    1. Open the original attribute table
    2. Select the rows subject to replacement with new ones
    3. Generate footprints from the selected multipatch layer (i.e.,replaced layer)
    4. MakeFeatureLayer for each of Bored Pile, Pile Cap, Pier, Pier Head, and Precast
    5. Repeat 1 to 3 using the new multipatch layer (i.e., replacing layer)
    6. For each of the viaduct components between the replaced and the replacing layers, run spatial join
        (you have spatially joined feature layer for each of the viaduct components)
    7. Merge the spatially joined layers of all the viaduct components
    8. Delete redundant fields
    9. Join the merged feature layer to original replacing layer using newId
    10. Delete redundant fields from in_replacing_fc
    11. Delete all the temporary layers.
       
2nd Batch
    !---- IMPORTANT
    Before running the second batch, make sure:
    1. Delete replaced rows in the original layer. 
    2. Append newly edited replacing layer to the original layer

3rd Batch
    1. Sort the target layer
    2. Truncate the target (original) layer and append the sorted to the original
    3. Export to excel sheet as new master list in a selected folder

4th Batch
    This 4th batch is not required. It updates layer in portal (e.g., N2/SC_Viaduct_portal)

"""

class Toolbox(object):
    def __init__(self):
        self.label = "CreateNewPartialViaduct"
        self.alias = "CreateNewPartialViaduct"
        self.tools = [CreateNewPartialViaduct, AppendLayer, SortUpdatedFeature, TruncateAppendPortal]

class CreateNewPartialViaduct(object):
    def __init__(self):
        self.label = "1. Edit New (Input) Partial viaduct layer"
        self.description = "Edit new viaduct layer used to update original viaduct layer"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Target Viaduct Multipatch layer (Original Layer, e.g.,'N2/SC_Viaduct_local')",
            name = "Select Target Viaduct Multipatch layer (Original Layer, e.g.,'N2/SC_Viaduct_local')",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_replacing_fc = arcpy.Parameter(
            displayName = "Select Input Multipatch Layer (Replacing Layer)",
            name = "Select Input Multipatch Layer (Replacing Layer)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [ws, in_replaced_fc, in_replacing_fc]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_replaced_fc = params[1].valueAsText
        in_replacing_fc = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        # 0. Add unique IDs to the replacing layer
        field_newID = 'newID'
        fields = [f.name for f in arcpy.ListFields(in_replacing_fc)]
        test = [e for e in fields if e in field_newID]

        if len(test) >= 1:
            arcpy.AddMessage("The table already has '{0}'".format(field_newID))
            arcpy.DeleteField_management(in_replacing_fc, [field_newID], "DELETE_FIELDS")

        arcpy.management.AddField(in_replacing_fc, field_newID, "SHORT", "",
                                    field_alias = field_newID, field_is_nullable = "NULLABLE")

        # delete 'temp' and 'Type' fields if present
        delFields = ['temp', 'Type']
        test2 = [e for e in fields if e in delFields]
        if len(test2) >= 1:
            #arcpy.AddMessage("The table already has '{0}'".format(delFields))
            arcpy.DeleteField_management(in_replacing_fc, [delFields], "DELETE_FIELDS")

        rec=0
        with arcpy.da.UpdateCursor(in_replacing_fc, [field_newID]) as cursor:
            for row in cursor:
                pStart = 1
                pInterval = 1
                if (rec == 0):
                    rec = pStart
                    row[0] = rec
                else:
                    rec = rec + pInterval
                    row[0] = rec
                cursor.updateRow(row)

        # 3. Generate footprints from the selected multipatch layer
        replaced_layer = "replaced_multipatch"
        arcpy.ddd.MultiPatchFootprint(in_replaced_fc, replaced_layer)

        # 4. MakeFeatureLayer for each of Bored Pile, Pile Cap, Pier, Pier Head, and Precast
        output1_replaced = "pile_replaced"
        output2_replaced = "pilecap_replaced"
        output3_replaced = "pier_replaced"
        output4_replaced = "pierhead_replaced"
        output5_replaced = "precast_replaced"

        #arcpy.MakeFeatureLayer_management(replaced_layer, output1_replaced)
        tempLayer1 = arcpy.SelectLayerByAttribute_management(replaced_layer, "NEW_SELECTION", "Type = 1")
        arcpy.management.CopyFeatures(tempLayer1, output1_replaced)

        tempLayer2 = arcpy.SelectLayerByAttribute_management(replaced_layer, "NEW_SELECTION", "Type = 2")
        arcpy.management.CopyFeatures(tempLayer2, output2_replaced)

        tempLayer3 = arcpy.SelectLayerByAttribute_management(replaced_layer, "NEW_SELECTION", "Type = 3")
        arcpy.management.CopyFeatures(tempLayer3, output3_replaced)

        tempLayer4 = arcpy.SelectLayerByAttribute_management(replaced_layer, "NEW_SELECTION", "Type = 4")
        arcpy.management.CopyFeatures(tempLayer4, output4_replaced)

        tempLayer5 = arcpy.SelectLayerByAttribute_management(replaced_layer, "NEW_SELECTION", "Type = 5")
        arcpy.management.CopyFeatures(tempLayer5, output5_replaced)


        # 5. Repeat 1 to 3 using the new multipatch layer (i.e., replacing layer)
        ## Add 'Type' field
        fieldType = 'Type'
        arcpy.management.AddField(in_replacing_fc, fieldType, "SHORT", "",
                                    field_alias = fieldType, field_is_nullable = "NULLABLE")

        fieldTemp = 'temp'
        arcpy.management.AddField(in_replacing_fc, fieldTemp, "TEXT", "",
                                    field_alias = fieldTemp, field_is_nullable = "NULLABLE")

        with arcpy.da.UpdateCursor(in_replacing_fc, ["Layer", fieldTemp]) as cursor:
            for row in cursor:
                try:
                    reg = re.search(r"COLUMN|column|Column|PILECAP\b|Pilecap\b|pilecap\b|PILE\b|pile\b|Pile\b|PIER_Head|PIER_HEAD|Pier_Head|pier_head|PRECAST|precast", row[0]).group()
                    row[1] = reg
                    cursor.updateRow(row)
                except AttributeError:
                    reg = re.search(r"COLUMN|column|Column|PILECAP\b|Pilecap\b|pilecap\b|PILE\b|pile\b|Pile\b|PIER_Head|PIER_HEAD|Pier_Head|pier_head|PRECAST|precast", row[0])
                    row[1] = reg
                    cursor.updateRow(row)
                
        ## Now add 'Type' field
        with arcpy.da.UpdateCursor(in_replacing_fc, [fieldTemp, fieldType]) as cursor:
            for row in cursor:
                if row[0]:
                    temp = row[0].upper()
                    if temp == "PILE":
                        row[1] = 1
                    elif temp == "PILECAP":
                        row[1] = 2
                    elif temp == "COLUMN":
                        row[1] = 3
                    elif temp == "PIER_HEAD" or temp == "PIERHEAD":
                        row[1] = 4
                    elif temp == "PRECAST":
                        row[1] = 5
                    else:
                        row[1] = None
                    cursor.updateRow(row)

        ##  Generate footprints
        replacing_layer = "replacing_multipatch"
        arcpy.ddd.MultiPatchFootprint(in_replacing_fc, replacing_layer)

        output1_replacing = "pile_replacing"
        output2_replacing = "pilecap_replacing"
        output3_replacing = "pier_replacing"
        output4_replacing = "pierhead_replacing"
        output5_replacing = "precast_replacing"

        tempLayer1 = arcpy.SelectLayerByAttribute_management(replacing_layer, "NEW_SELECTION", "Type = 1")
        arcpy.management.CopyFeatures(tempLayer1, output1_replacing)

        tempLayer2 = arcpy.SelectLayerByAttribute_management(replacing_layer, "NEW_SELECTION", "Type = 2")
        arcpy.management.CopyFeatures(tempLayer2, output2_replacing)

        tempLayer3 = arcpy.SelectLayerByAttribute_management(replacing_layer, "NEW_SELECTION", "Type = 3")
        arcpy.management.CopyFeatures(tempLayer3, output3_replacing)

        tempLayer4 = arcpy.SelectLayerByAttribute_management(replacing_layer, "NEW_SELECTION", "Type = 4")
        arcpy.management.CopyFeatures(tempLayer4, output4_replacing)

        tempLayer5 = arcpy.SelectLayerByAttribute_management(replacing_layer, "NEW_SELECTION", "Type = 5")
        arcpy.management.CopyFeatures(tempLayer5, output5_replacing)

        # 6. For each of the viaduct components between the replaced and the replacing layers, run spatial join
        out_feature_pile = "pile_joined"
        out_feature_pilecap = "pilecap_joined"
        out_feature_pier = "pier_joined"
        out_feature_pierhead = "pierhead_joined"
        out_feature_precast = "precast_joined"

        arcpy.analysis.SpatialJoin(output1_replacing, output1_replaced, out_feature_pile)
        arcpy.analysis.SpatialJoin(output2_replacing, output2_replaced, out_feature_pilecap)
        arcpy.analysis.SpatialJoin(output3_replacing, output3_replaced, out_feature_pier)
        arcpy.analysis.SpatialJoin(output4_replacing, output4_replaced, out_feature_pierhead)
        arcpy.analysis.SpatialJoin(output5_replacing, output5_replaced, out_feature_precast)

        # 7.  Merge the spatially joined layers of all the viaduct components
        merged_joined = "merged_replacing_viaduct"
        arcpy.management.Merge([out_feature_pile, out_feature_pilecap, out_feature_pier, out_feature_pierhead, out_feature_precast], merged_joined)

        # 8. Delete redundant fields
        keepFields = ['newID', 'uniqueID', 'Type', 'nPierNumber', 'PierNumber', 'Status1', 'CP', 'Layer','Note']
        arcpy.DeleteField_management(merged_joined, keepFields, "KEEP_FIELDS")

        # 9. Join the merged feature layer to original replacing layer using newId
        arcpy.management.JoinField(in_replacing_fc, field_newID, merged_joined, field_newID, keepFields)

        # 10. Delete redundant fields from in_replacing_fc
        arcpy.DeleteField_management(in_replacing_fc, keepFields, "KEEP_FIELDS")

        # 11. Delete
        deleteOutputs = [output1_replacing, output2_replacing, output3_replacing, output4_replacing, output5_replacing,
                            output1_replaced, output2_replaced, output3_replaced, output4_replaced, output5_replaced,
                            out_feature_pile, out_feature_pilecap, out_feature_pier, out_feature_pierhead, out_feature_precast,
                            merged_joined, replaced_layer, replacing_layer,
                            tempLayer1, tempLayer2, tempLayer3, tempLayer4, tempLayer5]
        arcpy.management.Delete(deleteOutputs)

class AppendLayer(object):
    """ MAKE SURE to delete replaced rows from the original layer (SC_Viaduct_local) """
    def __init__(self):
        self.label = "2. Append newly edited replacing layer to the original layer."
        self.description = "3. Append newly edited replacing layer to the original layer." + \
            "MAKE SURE to delete replaced rows from the original layer (SC_Viaduct_local)"

    def getParameterInfo(self):
        in_fc = arcpy.Parameter(
            displayName = "Select Source Viaduct Layer (replacing, new viaduct layer)",
            name = "Select Source Viaduct Layer (replacing, new viaduct layer)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        target_fc = arcpy.Parameter(
            displayName = "Select Target Viaduct Layer (original viaduct layer e.g., SC_Viaduct_local)",
            name = "Select Target Viaduct Layer (original viaduct layer e.g., SC_Viaduct_local)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_fc, target_fc]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_fc = params[0].valueAsText
        target_fc = params[1].valueAsText
        arcpy.Append_management(in_fc, target_fc, schema_type = 'NO_TEST')

class SortUpdatedFeature(object):
    def __init__(self):
        self.label = "3. Sort Updated Original Feature (Viaduct)"
        self.description = "Sort Updated Original Feature (Viaduct)"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_fc = arcpy.Parameter(
            displayName = "Select Target Viaduct layer to be updated (Original Layer, e.g.,'N2/SC_Viaduct_local')",
            name = "Select Target Viaduct layer to be updated (Original Layer, e.g.,'N2/SC_Viaduct_local')",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_folder = arcpy.Parameter(
            displayName = "Choose Folder to Save Sorted Layer In Excel",
            name = "Choose Folder to Save Sorted Layer In Excel",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )

        in_date = arcpy.Parameter(
            displayName = "Enter date attached to exported excel file (use '20230413' yyyymmdd)",
            name = "Enter date attached to exported excel file (use '20230413' yyyymmdd)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [ws, in_fc, in_folder, in_date]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_fc = params[1].valueAsText
        in_folder = params[2].valueAsText
        in_date = params[3].valueAsText
        arcpy.env.overwriteOutput = True

        # Sort by CP, PierNumber, Type, nPierNumber
        out_dataset = "viaduct_Sort"
        sort_fields = [["CP","ASCENDING"],["PierNumber","ASCENDING"],["Type","ASCENDING"],["nPierNumber","ASCENDING"]]
        arcpy.Sort_management(in_fc, out_dataset, sort_fields, "")

        # Update uniqueID
        rec=0
        with arcpy.da.UpdateCursor(out_dataset, ["uniqueID"]) as cursor:
            for row in cursor:
                pStart = 1
                pInterval = 1
                if (rec == 0):
                    rec = pStart
                    row[0] = rec
                else:
                    rec = rec + pInterval
                    row[0] = rec
                cursor.updateRow(row)

        # Truncate and Append
        # 5. Truncate the original Viaduct layer
        arcpy.TruncateTable_management(in_fc)

        # 6. Append the sorted layer to the original layer.
        arcpy.Append_management(out_dataset, in_fc, schema_type = 'NO_TEST')

        # Export table
        tempFile = 'SC_Viaduct_ML' + "_" + in_date + ".xlsx"
        excelFile = os.path.join(in_folder, tempFile)
        arcpy.conversion.TableToExcel(in_fc, excelFile)

        # 7. Delete sorted layer
        arcpy.management.Delete(out_dataset)

class TruncateAppendPortal(object):
    def __init__(self):
        self.label = "4. Copy Viaduct Layer to Another Layer (run when necessary)"
        self.description = "Copy Viaduct Layer to Another Layer"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_fc = arcpy.Parameter(
            displayName = "Select Source Viaduct Layer",
            name = "Select Input Source Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        target_fc = arcpy.Parameter(
            displayName = "Select Target Viaduct Layer",
            name = "Select Target Viaduct Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [ws, in_fc, target_fc]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_fc = params[1].valueAsText
        target_fc = params[2].valueAsText

        # To allow overwriting the outputs change the overwrite option to true.
        arcpy.env.overwriteOutput = True
        arcpy.env.outputCoordinateSystem = arcpy.SpatialReference("PRS 1992 Philippines Zone III")
        arcpy.env.geographicTransformations = "PRS_1992_To_WGS_1984_1"


        copied = "copied_layer"
        copyL = arcpy.CopyFeatures_management(in_fc, copied)
        arcpy.TruncateTable_management(target_fc)
        arcpy.Append_management(copyL, target_fc, schema_type = 'NO_TEST')

        # Delete
        arcpy.Delete_management(copyL)
        arcpy.AddMessage("Delete copied layer is Success")
