import arcpy
import pandas as pd
import os
from pathlib import Path
from datetime import date, datetime
import re
import string
import numpy as np

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateN2Viaduct"
        self.alias = "UpdateN2Viaduct"
        self.tools = [CreateWorkablePierLayer, UpdateWorkablePierLayer, CheckPierNumbers]

class CreateWorkablePierLayer(object):
    def __init__(self):
        self.label = "1. Create Pier Workable Layer (Polygon)"
        self.description = "Create Pier Workable Layer"

    def getParameterInfo(self):
        # Input Feature Layers
        workable_pier_layer = arcpy.Parameter(
            displayName = "GIS Workable Pier Layer (Polygon)",
            name = "GIS Workable Pier Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        via_layer = arcpy.Parameter(
            displayName = "GIS Viaduct Layer (Multipatch)",
            name = "GIS Viaduct Layer (Multipatch)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [workable_pier_layer, via_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workable_pier_layer = params[0].valueAsText
        via_layer = params[1].valueAsText

        arcpy.env.overwriteOutput = True
        status_field = 'Status'
        cp_field = 'CP'
        pier_number_field = 'PierNumber'
        unique_id_field = 'uniqueID'
        type_field = 'Type'

        new_cols = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']

        # Filter by Type = 2 and keep only 'CP', 'PierNumber', and 'uniqueID'
        temp_layer = 'temp_layer'
        arcpy.management.MakeFeatureLayer(via_layer, temp_layer, '"Type" = 2')

        # 'multipatch footprint'
        ## new_cols and 'Type' (sting) = 'Pile Cap'
        new_layer = 'N2_Pier_Workable'
        arcpy.ddd.MultiPatchFootprint(temp_layer, new_layer)

        ## Delete field
        arcpy.management.DeleteField(new_layer, [cp_field, pier_number_field, unique_id_field, status_field], "KEEP_FIELDS")

        # Add field
        new_fields = new_cols + ['Type']
        for field in new_fields:
            if field == 'Type':
                arcpy.management.AddField(new_layer, field, "TEXT", field_alias=field, field_is_nullable="NULLABLE")
            else:
                arcpy.management.AddField(new_layer, field, "SHORT", field_alias=field, field_is_nullable="NULLABLE")

        with arcpy.da.UpdateCursor(new_layer, [type_field, status_field, 'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']) as cursor:
            # 0: Non-workable, 1: Workable, 2: Completed
            for row in cursor:
                row[0] = 'Pile Cap'
                if row[1] == 4:
                    row[2] = 2
                    row[3] = 2
                    row[4] = 2
                    row[5] = 2
                    row[6] = 2
                    row[7] = 2
                cursor.updateRow(row)
        
        # Truncate old polygon
        arcpy.management.TruncateTable(workable_pier_layer)

        # Append the new one to the old one
        arcpy.management.Append(new_layer, workable_pier_layer, schema_type = 'NO_TEST')

        # delete
        deleteTempLayers = [new_layer, temp_layer]
        arcpy.Delete_management(deleteTempLayers)

class UpdateWorkablePierLayer(object):
    def __init__(self):
        self.label = "2. Update Pier Workable Layer (Polygon)"
        self.description = "Update Pier Workable Layer (Polygon)"

    def getParameterInfo(self):
        gis_viaduct_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory for Viaduct",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_workable_ms = arcpy.Parameter(
            displayName = "Civil Workable Pier ML (Excel)",
            name = "Civil Workable Pier ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_workable_layer = arcpy.Parameter(
            displayName = "GIS Pier Workable Layer (Polygon)",
            name = "GIS Pier Workable Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        gis_nlo_ms = arcpy.Parameter(
            displayName = "GIS NLO (ISF) ML (Excel)",
            name = "GIS NLO (ISF) ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_viaduct_dir, civil_workable_ms, gis_workable_layer, gis_nlo_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_via_dir = params[0].valueAsText
        civil_workable_ms = params[1].valueAsText
        gis_workable_layer = params[2].valueAsText
        gis_nlo_ms = params[3].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Workable_Pier_Table_Update():
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            def non_match_elements(list_a, list_b):
                non_match = []
                for i in list_a:
                    if i not in list_b:
                        non_match.append(i)
                return non_match
            
            # Read as xlsx
            # gis_via_t = pd.read_excel(gis_via_ms)
            gis_nlo_t = pd.read_excel(gis_nlo_ms)
            # civil_workable_t = pd.read_excel(civil_workable_ms,sheet_name='(S01)',skiprows=3)

            # List of fields
            cp_field = 'CP'
            type_field = 'Type'
            status_field = 'Status'
            pier_number_field = 'PierNumber'
            workability_field = 'workability'
            unique_id_field = 'uniqueID'
            lot_id_field = 'LotID'
            struc_id_field = 'StrucID'


            # 1. Clean fields
            ## cps = ['S-01','S-02','S-03a','S-03b','S-03c','S-04','S-05','S-06','S-07']
            cps = ['S-01']
            for i, cp in enumerate(cps):
                cp_civil_name = "(" + cp.replace('-','') + ")"
                civil_workable_t = pd.read_excel(civil_workable_ms, sheet_name = cp_civil_name)
                civil_workable_t = civil_workable_t.iloc[:,[14,19,22,23,24,25,26,27,28,30,32,34,35,48,51]]
                ids = civil_workable_t.index[civil_workable_t.iloc[:, 0].str.contains(r'^P-',regex=True,na=False)]
                civil_workable_t = civil_workable_t.loc[ids[0]:, ]

                col_names = [pier_number_field,'via_construct_status','workability',
                            'util1','util2','util3','util4','util5','ISF_pnr','land','structure','pnr_station','others',
                            lot_id_field, struc_id_field] # 'lot_id','struc_id'

                for j, col in enumerate(col_names):
                    civil_workable_t = civil_workable_t.rename(columns={civil_workable_t.columns[j]: col})

                # create workable columns for pre-construction work
                new_cols = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']
                for k, col in enumerate(new_cols):
                    civil_workable_t[col] = np.nan
                    # x[col] = x[col].astype(str)

                ## Clean column names
                # x[col_names[0]] = x[col_names[0]].replace(r'\s+|[^\w\s]','',regex=True)
                civil_workable_t[col_names[0]] = civil_workable_t[col_names[0]].replace(r'\s+','',regex=True)

                # Remove empty space
                ids = civil_workable_t.index[civil_workable_t[col_names[0]].isna()]
                civil_workable_t = civil_workable_t.drop(ids).reset_index(drop=True)

                civil_workable_t[cp_field] = cp

                ##################################
                # A. Update Pier Workable Layer using Civil table ##
                ##################################

                ## 1. Workable Pile Cap
                ## Status of Workable Pier
                ### 0: Non-Workable
                ### 1: Workable
                ### 2: Completedd

                ### 1.2. Workable Pile Cap
                ## 2.0. Enter Workable (1) else non-Workable (1) for AllWorkable
                completed_piers = []
                with arcpy.da.SearchCursor(gis_workable_layer, [pier_number_field, new_cols[0]]) as cursor:
                    for row in cursor:
                        if row[1] == 2:
                            completed_piers.append(row[0])

                # from civil pier workable database
                id_workable_piers = civil_workable_t.index[civil_workable_t['workability'] == 'Workable']
                id_nonworkable_piers = civil_workable_t.index[civil_workable_t['workability'] == 'Non-workable']

                workable_piers = civil_workable_t.loc[id_workable_piers, pier_number_field].values
                nonworkable_piers = civil_workable_t.loc[id_nonworkable_piers, pier_number_field].values

                incomp_workable_piers = non_match_elements(workable_piers, completed_piers)
                incomp_nonworkable_piers = non_match_elements(nonworkable_piers, completed_piers)

                # Enter 1
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(incomp_workable_piers) and row[7] == cp:
                            row[1] = 1
                            row[2] = 1
                            row[3] = 1
                            row[4] = 1
                            row[5] = 1
                            row[6] = 1
                        cursor.updateRow(row)

                # Empty cell for AllWorkable = 0 (non-workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.1 LandWorkable
                # Note that when 'land' == 1, this automatically exlucdes workable and completed piers.
                ids = civil_workable_t.index[civil_workable_t['land'] == 1]

                land_nonwork_piers = civil_workable_t.loc[ids, pier_number_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[1], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(land_nonwork_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                # Empty cell = 1 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'LandWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## 2.2 StrucWorkable
                ids = civil_workable_t.index[civil_workable_t['structure'] == 1]
                struc_nonwork_piers = civil_workable_t.loc[ids, pier_number_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[2], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(struc_nonwork_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                # Empty cell = 1 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'StrucWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## 2.3 NLOWorkable
                ### Not all non-workable structures have NLOs. So, to decide the workable status of 'NLOWorkable':
                ### 2.3.1. identify StrucID of non-workable structures
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].str.replace('\n',',')
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].replace(r'\s+','',regex=True)
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].str.upper()
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].replace(r'[(]PNR[)]','',regex=True)
                
                ids_nonna = civil_workable_t.index[civil_workable_t['structure'] == 1]
                c_t2 = civil_workable_t.loc[ids_nonna, ]

                ### 2.3.2. identify any NLOs falling under the identified non-workable structures
                nlo_obstruc_piers = []
                for i in c_t2.index:
                    obstruc_struc_ids = c_t2.loc[i, struc_id_field]
                    test = [e for e in gis_nlo_t[struc_id_field] if e in obstruc_struc_ids.split(',')]
                    if len(test) > 0:
                        # idenfity pier numbers with obstructing NLOs
                        nlo_obstruc_piers.append(civil_workable_t.loc[i, pier_number_field])
                
                ### 2.3.3. Enter NLOWorkable = 0 with identified pier numbers
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[3], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(nlo_obstruc_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)


                # Empty cell = 1 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'NLOWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## 2.4. UtilWorkable
                ids = civil_workable_t.index[(civil_workable_t['util1'] == 1) | 
                                            (civil_workable_t['util2'] == 1) | 
                                            (civil_workable_t['util3'] == 1) | 
                                            (civil_workable_t['util4'] == 1)| 
                                            (civil_workable_t['util5'] == 1)]
                util_obstruc_piers = civil_workable_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[4],cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(util_obstruc_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                # Empty cell = 1 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'UtilWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## 2.5. OthersWorkable 
                ids = civil_workable_t.index[civil_workable_t['others'] == 1]
                others_obstruc_piers = civil_workable_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[5], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(others_obstruc_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                # Empty cell = 1 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'OthersWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## Export this layer to excel
                arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(gis_via_dir, "N2_Workable_Pier.xlsx"))

        Workable_Pier_Table_Update()

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "3. Check Pier Numbers between Civil and GIS Tables"
        self.description = "Check Pier Numbers between Civil and GIS Tables"

    def getParameterInfo(self):
        gis_viaduct_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory for Viaduct",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_workable_ms = arcpy.Parameter(
            displayName = "Civil Workable Pier ML (Excel)",
            name = "Civil Workable Pier ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_viaduct_ms = arcpy.Parameter(
            displayName = "GIS N2 Viaduct Portal (Excel)",
            name = "GIS N2 Viaduct Portal (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_pier_tracker_ms = arcpy.Parameter(
            displayName = "GIS Pier Workable Tracker ML (Excel)",
            name = "GIS Pier Workable Tracker ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_viaduct_dir, civil_workable_ms, gis_viaduct_ms, gis_pier_tracker_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_via_dir = params[0].valueAsText
        civil_workable_ms = params[1].valueAsText
        gis_viaduct_ms = params[2].valueAsText
        gis_pier_tracker_ms = params[3].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Workable_Pier_Table_Update():
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            def non_match_elements(list_a, list_b):
                non_match = []
                for i in list_a:
                    if i not in list_b:
                        non_match.append(i)
                return non_match

            # List of fields
            cp_field = 'CP'
            type_field = 'Type'
            pier_num_field = 'PierNumber'
            unique_id_field = 'uniqueID'
            pier_num_field_c = 'Pier No. (P)'

            cps = ['N-01','N-02','N-03']
            for cp in cps:
                arcpy.AddMessage("Contract Package: " + cp)

                #1. Read table
                ## N2 Viaduct
                portal_t = pd.read_excel(gis_viaduct_ms)
                ids = portal_t.index[(portal_t[cp_field] == cp) & (portal_t[type_field] == 2)]
                portal_t = portal_t.loc[ids, [pier_num_field, unique_id_field]].reset_index(drop=True)
                gis_piers = portal_t[pier_num_field].values
                
                ## N2 Civil ML
                civil_t = pd.read_excel(civil_workable_ms, skiprows=2)
                civil_piers = civil_t[pier_num_field_c].values
                
                ## Pier Workable Tracker (GIS Team prepared)
                pier_track_t = pd.read_excel(gis_pier_tracker_ms, sheet_name=cp)
                pier_track_t = pier_track_t.loc[1:, [pier_num_field, unique_id_field]]
                tracker_piers = pier_track_t[pier_num_field].values
                
                #2. Check PierNumber (N2 Viaduct ML and N2 Civil Workable Pier ML)
                arcpy.AddMessage('Compare Pier Numbers between N2 Viaduct ML and N2 Civil Workable Pier ML')
                x_piers = [e for e in gis_piers if e not in civil_piers]
                if (len(x_piers) > 0):
                    arcpy.AddMessage("The following pier numbers do not match: ", x_piers)
                else:
                    arcpy.AddMessage("No Problem! All pier numbers match!")
                
                #3. Check PierNumber (N2 Viaduct ML and N2 Pier Workable Tracker)
                arcpy.AddMessage('Compare Pier Numbers between N2 Viaduct ML and N2 Pier Workable Tracker')
                x_piers = [e for e in gis_piers if e not in tracker_piers]
                if (len(x_piers) > 0):
                    arcpy.AddMessage("The following pier numbers do not match: ", x_piers)
                else:
                    arcpy.AddMessage("No Problem! All pier numbers match!")
                
                #4. Check PierNumber (N2 Civil Workable Pier ML and N2 Pier Workable Tracker)
                arcpy.AddMessage('Compare Pier Numbers between N2 Civil Workable Pier ML and N2 Pier Workable Tracker')
                x_piers = [e for e in tracker_piers if e not in civil_piers]
                if (len(x_piers) > 0):
                    arcpy.AddMessage("The following pier numbers do not match: ", x_piers)
                else:
                    arcpy.AddMessage("No Problem! All pier numbers match!")

        Workable_Pier_Table_Update()



        