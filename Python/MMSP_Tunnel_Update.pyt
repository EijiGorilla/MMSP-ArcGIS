import arcpy
from datetime import date, datetime
import pandas as pd
import numpy as np
import os

class Toolbox(object):
    def __init__(self):
        self.label = "IdentifyTBMLocation"
        self.alias = "IdentifyTBMLocation"
        self.tools = [UpdateExceMasterList, UpdateGISLayer]

class UpdateExceMasterList(object):
    def __init__(self):
        self.label = "1. Update Excel Master List"
        self.description = "Update Excel master list based on Google sheet provided by Civil Team"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "Civil TBM Master List (Input Table)",
            name = "Civil TBM Master List (Input Table)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "GIS Excel Master List (Target Table)",
            name = "GIS Excel Master List (Target Table)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_bakcup_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Backup Directory",
            name = "GIS Masterlist Backup Directory",
            datatype = "DEWorkspace",
            parameterType = "Optional",
            direction = "Input"
        )

        lastupdate = arcpy.Parameter(
            displayName = "Date for Backup: use 'yyyymmdd' format. eg. 20240101",
            name = "Date for Backup: use 'yyyymmdd' format. eg. 20240101",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [gis_dir, civil_ml, gis_ml, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        civil_ml = params[1].valueAsText
        gis_ml = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        def change_str_to_datetime(table, fields):
            for field in fields:
                table[field] = pd.to_datetime(table[field], errors='coerce').dt.date

        def unique(lists):
            collect = []
            unique_list = pd.Series(lists).drop_duplicates().tolist()
            for x in unique_list:
                collect.append(x)
            return(collect)
        
        # Read as xlsx
        gis_table = pd.read_excel(gis_ml)
        civil_table = pd.read_excel(civil_ml)

        # Defin field names
        start_date = 'startdate'
        end_date = 'enddate'
        target_date = 'TargetDate'
        status_name = 'status'
        line_id = 'line'
        segment_no = 'segmentno'
        tbm_spot = 'tbmSpot'
        delayed_id = 'delayed'


        # Create bakcup files
        try:
            gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + "GIS_TBM_Masterlist.xlsx"), index=False)
        except:
            pass
       
        date_fields = [start_date, end_date, 'Start_Exc', 'Finish_Exc', target_date]
        change_str_to_datetime(civil_table, date_fields)

        # Drop unnamed columns
        drop_fields = [f for f in civil_table.columns[civil_table.columns.str.contains('^Unnamed.*',regex=True)]]
        civil_table = civil_table.drop(columns = drop_fields)

        # Identiy TBM Spot
        ### identify tbm spot
        line_list = [f for f in civil_table[line_id]]
        lines = unique(line_list)

        ## Reset 'tbmSpot'
        civil_table[tbm_spot] = 0
        cutter_head_pos = 5

        for line in lines:
            id = civil_table.index[(civil_table[line_id] == line) & (civil_table[status_name] == 3)]
            if len(id) > 0:
                spot = max(civil_table[segment_no].iloc[id]) + cutter_head_pos
                id = civil_table.index[(civil_table[line_id] == line) & (civil_table[segment_no] == spot)]
                civil_table[tbm_spot].iloc[id] = 1
            else:
                pass

        ## Identify delayed segment
        today = date.today()
        civil_table[target_date] = pd.to_datetime(civil_table[target_date], errors='coerce').dt.date
        civil_table[[target_date, line_id, segment_no, status_name]].head(20)
        id = civil_table.index[(civil_table[target_date] < today) & (civil_table[status_name] < 3)]

        civil_table[delayed_id] = 0
        if len(id) > 0:
            civil_table[delayed_id].iloc[id] = 1
        else:
            pass

        ## Export to excel
        export_file_name = os.path.splitext(os.path.basename(gis_ml))[0]
        to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
        civil_table.to_excel(to_excel_file, index=False)

class UpdateGISLayer(object):
    def __init__(self):
        self.label = "2. Update Feature Layer using Excel Master List"
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

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

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

        # Check
        gis_layer = unique_values(copyLayer, joinField)
        excel_ml = unique_values(MasterList, joinField)
        
        miss_gis = [e for e in gis_layer if e not in excel_ml]
        miss_ml = [e for e in excel_ml if e not in gis_layer]

        if miss_gis or miss_ml:
            arcpy.AddMessage('The following IDs do not match between ML and GIS.')
            arcpy.AddMessage('Missing LotIDs in GIS layer: {}'.format(miss_gis))
            arcpy.AddMessage('Missing LotIDs in ML Excel table: {}'.format(miss_ml))

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
