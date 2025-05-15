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
        self.tools = [CreateWorkablePierLayer,
                      UpdatePierWorkableTrackerML,
                      UpdateWorkablePierLayer,
                      UpdatePierPointLayer,
                      CheckPierNumbers,
                      UpdateStripMapLayer]

class CreateWorkablePierLayer(object):
    def __init__(self):
        self.label = "0. Create Pier Workable Layer (Polygon)"
        self.description = "Create Pier Workable Layer"

    def getParameterInfo(self):
        pier_workable_dir = arcpy.Parameter(
            displayName = "N2 GIS Pier Tracker Masterlist Storage Directory",
            name = "N2 GIS Pier Tracker Masterlist Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

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

        pier_number_layer = arcpy.Parameter(
            displayName = "GIS Pier Number Layer (Point)",
            name = "GIS Pier Number Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [pier_workable_dir, workable_pier_layer, via_layer,pier_number_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workable_dir = params[0].valueAsText
        workable_pier_layer = params[1].valueAsText
        via_layer = params[2].valueAsText
        pier_pt_layer = params[3].valueAsText

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

        ## Delete field
        # arcpy.management.DeleteField(new_layer, ['CP','PierNumber','uniqueID','Status'], "KEEP_FIELDS")
        
        # delete
        deleteTempLayers = [new_layer, temp_layer]
        arcpy.Delete_management(deleteTempLayers)

        # Export the latest N2 Viaduct layer to excel
        arcpy.conversion.TableToExcel(via_layer, os.path.join(workable_dir, "N2_Viaduct_MasterList.xlsx"))
        
        ########################################
        ##### Update N2 Pier Point Layer #######
        ########################################
        try:
            temp_layer = 'temp_layer'
            arcpy.management.MakeFeatureLayer(via_layer, temp_layer, '"Type" = 2')
        
            # 'multipatch footprint'
            ## new_cols and 'Type' (sting) = 'Pile Cap'
            new_layer = 'N2_Pier_Point'
            arcpy.ddd.MultiPatchFootprint(temp_layer, new_layer)

            ## Feature to Point
            new_point_layer = 'N2_new_Pier_Point'
            arcpy.management.FeatureToPoint(new_layer, new_point_layer)

            ## Truncate original point layer
            arcpy.management.TruncateTable(pier_pt_layer)

            ## Append a new point layer to the original
            arcpy.management.Append(new_point_layer, pier_pt_layer, schema_type = 'NO_TEST')

            # delete
            deleteTempLayers = [new_layer, new_point_layer, temp_layer]
            arcpy.Delete_management(deleteTempLayers)

        except:
            pass

class UpdatePierWorkableTrackerML(object):
    def __init__(self):
        self.label = "2. Update Pier Workable Tracker ML (Excel)"
        self.description = "Update Pier Workable Tracker ML (Excel)"

    def getParameterInfo(self):
        pier_workablet_dir = arcpy.Parameter(
            displayName = "N2 GIS Pier Tracker Masterlist Storage Directory",
            name = "N2 GIS Pier Tracker Masterlist Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_workable_ms = arcpy.Parameter(
            displayName = "N2 Civil Workable Pier ML (Excel)",
            name = "Civil Workable Pier ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "N2 Pier Workable Tracker ML (Excel)",
            name = "Pier Workable Tracker ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_obstruction_ms = arcpy.Parameter(
            displayName = "RAP Obstructing Lot and Structure ML (Excel)",
            name = "RAP Obstructing Lot and Structure ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_workablet_dir, civil_workable_ms, pier_workable_tracker_ms, rap_obstruction_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_workablet_dir = params[0].valueAsText
        civil_table = params[1].valueAsText
        pier_tracker_table = params[2].valueAsText
        rap_obst_table = params[3].valueAsText

        def Workable_Pier_Tracker_Update():
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
            
            def flatten_extend(matrix):
                flat_list = []
                for row in matrix:
                    row = [re.sub(r'\s+','',e) for e in row]
                    flat_list.extend(row)
                return flat_list
            
            # Define field names
            cp_field = 'CP'
            type_field = 'Type'
            status_field = 'Status'
            pier_num_field = 'PierNumber'
            unique_id_field = 'uniqueID'
            workability_field = 'Workability'
            land_field = 'Land'
            land1_field = 'Land.1'
            struc_field = 'Structure'
            struc1_field = 'Structure.1'
            others_field = 'Others'
            pier_num_field_c = 'Pier No. (P)'
            util_obstruc_field = 'Utility'

            #**************************************************************************************************#
            #*********************  Update Pier Workable Tracker ML using Civil Team's ML *********************#
            #**************************************************************************************************#
            # Update N2 Pier Workability Tracker
            new_cols = ['PierNumber', 'CP', 'util1', 'util2', 'Others', 'Workability']
            civil_t = pd.read_excel(civil_table, skiprows=2)
            ids = civil_t.columns[civil_t.columns.str.contains(r'^Pier No.*|Contract P.*|^Name of Utilities|^Others|^OTHERS|^Pile Cap Workable.*',regex=True,na=False)]
            civil_t = civil_t.loc[:, ids]
            for i, col in enumerate(ids):
                civil_t = civil_t.rename(columns={col: new_cols[i]})
                
            ## change CP notation
            civil_t[new_cols[1]] = civil_t[new_cols[1]].replace(r'CPN','N-',regex=True)

            ## Compile utility
            civil_t[util_obstruc_field] = np.nan
            ids = civil_t.index[(civil_t[new_cols[2]].notna()) | (civil_t[new_cols[3]].notna())]
            civil_t.loc[ids, util_obstruc_field] = 1
            civil_t = civil_t.drop([new_cols[2],new_cols[3]], axis=1)

            ## 'Others' 
            idx = civil_t.index[~civil_t[new_cols[4]].isna()]
            civil_t.loc[idx, new_cols[4]] = 1

            ## Change labels for Workability (No = Non-workable, Yes = Workable)
            ids = civil_t.index[civil_t[new_cols[5]] == 'Yes']
            civil_t.loc[ids, new_cols[5]] = 'Workable'
            ids = civil_t.index[civil_t[new_cols[5]] == 'No']
            civil_t.loc[ids, new_cols[5]] = 'Non-workable'
            ids = civil_t.index[civil_t[new_cols[5]] == 'Partial']
            civil_t.loc[ids, new_cols[5]] = 'Non-workable'

            ## If either Utility or Others has obstruction, Pile Cap must be 'Non-Workable'
            ##.query(f"((~{land_field}.isna()) & (`{land1_field}`.isna())) | (({land_field}.isna()) & (~`{land1_field}`.isna()))")
            ids = civil_t.index[((~civil_t[util_obstruc_field].isna()) | (~civil_t[others_field].isna())) & (civil_t[workability_field] == 'Workable')]
            if len(ids) > 0:
                civil_t.loc[ids, workability_field] = 'Non-workable'

            # tracker fields ordered
            tracker_fields_ordered = [pier_num_field,
                                    type_field,
                                    unique_id_field,
                                    status_field,
                                    cp_field,
                                    workability_field,
                                    util_obstruc_field,
                                    land_field,
                                    struc_field,
                                    others_field,
                                    land1_field,
                                    struc1_field]

            cps = ['N-01', 'N-02', 'N-03']
            comp_table = pd.DataFrame()
            for cp in cps:
                print('Contract Package: ', cp)
                ## Merge civil pier workability ML to GIS N2 Pier Workability Tracker
                gis_tracker = pd.read_excel(pier_tracker_table, sheet_name = cp)
                idx = gis_tracker.iloc[:, 0].index[gis_tracker.iloc[:, 0].str.contains(r'PierNumber',regex=True,na=False)]
                # When you have two rows until the first observation
                if len(idx) > 0:
                    for i, col in enumerate(tracker_fields_ordered):
                        gis_tracker = gis_tracker.rename(columns={gis_tracker.columns[i]: col})
                    col_ids = gis_tracker.columns.get_loc(f"{struc1_field}")
                    gis_tracker = gis_tracker.drop(idx).reset_index(drop=True).iloc[:, :col_ids+1]

                gis_tracker = gis_tracker.loc[:, [pier_num_field,
                                                type_field,
                                                unique_id_field,
                                                status_field,
                                                # cp_field,
                                                land_field,
                                                struc_field,
                                                land1_field,
                                                struc1_field]]
                gis_tracker = gis_tracker.rename(columns={gis_tracker.columns[0]: pier_num_field}) 
                
                # filter civil ML using pier numbers (not CP)
                gis_piers = gis_tracker[pier_num_field].values
                civil_piers = civil_t[pier_num_field].values
                match_piers = [e for e in civil_piers if e in gis_piers]

                c_t = civil_t.query(f"{pier_num_field} in {match_piers}").reset_index(drop=True)
                c_t_piers = c_t[pier_num_field].values

                # fix CP (N-01/N-02...)
                c_t[cp_field] = c_t[cp_field].str.replace(r'/.*','',regex=True)

                # Identify pile caps with missing 'Workability' information
                ids = c_t.index[c_t['Workability'].isnull()]
                miss_info_piers = c_t.loc[ids, pier_num_field].values
                if (len(ids) > 0):
                    print(f"The following piers have no information on Workability: {miss_info_piers}")

                # Finally, merge
                new_tracker = pd.merge(left=gis_tracker, right=c_t, how='left', on=pier_num_field)
                new_tracker = new_tracker.loc[:, tracker_fields_ordered]
                # print(new_tracker.dtypes)

                # Civil Tea

                # Summary statistics between Civil ML and GIS pier workability tracker ML
                ## 'Workable' 
                xw = pd.DataFrame()
                xw.loc[0, cp_field] = cp

                xw.loc[0, 'Workable_civil'] = len(c_t.index[c_t['Workability'] == 'Workable'])
                xw.loc[0, 'Workable_new'] = len(new_tracker.index[new_tracker['Workability'] == 'Workable'])
                xw.loc[0, 'Difference'] = xw.loc[0, 'Workable_civil'] - xw.loc[0, 'Workable_new']

                if (xw.loc[0, 'Difference'] > 0):
                    print(xw)
                                        
                # Compile for CPs
                comp_table = pd.concat([comp_table, new_tracker], ignore_index=False)

            # Export as a new tracker
            # to_excel_file0 = os.path.join(pier_workablet_dir, "UPDATED_" + os.path.basename(pier_tracker_table))
            # with pd.ExcelWriter(to_excel_file0) as writer:
            #     comp_table.query(f"{cp_field} == 'N-01'").reset_index(drop=True).to_excel(writer, sheet_name='N-01', index=False)
            #     comp_table.query(f"{cp_field} == 'N-02'").reset_index(drop=True).to_excel(writer, sheet_name='N-02', index=False)
            #     comp_table.query(f"{cp_field} == 'N-03'").reset_index(drop=True).to_excel(writer, sheet_name='N-03', index=False)

            #**************************************************************************************************#
            #*********************  Update Pier Workable Tracker ML using RAP Team's ML *********************#
            #**************************************************************************************************#
            ## Add obstructing Lot and structure IDs to pier workable tracker ML
            ### 1. Read the RAP table

            comp_table2 = pd.DataFrame()
            for cp in cps:
                rap_t = pd.read_excel(rap_obst_table, skiprows = 1, sheet_name = cp)
                rap_t = rap_t.loc[:, [pier_num_field,
                                    land_field,
                                    struc_field,
                                    land1_field,
                                    struc1_field]]
                
                ## Fix format for land1_field
                rap_t[land1_field] = rap_t[land1_field].astype(str)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r'\n',',',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r';',',',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r';;',',',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r',,',',',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r',,,',',',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r',$','',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r'nan','',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.replace(r'\s+','',regex=True)
                rap_t[land1_field] = rap_t[land1_field].str.lstrip(',') # remove leading comma
                rap_t[land1_field] = rap_t[land1_field].str.rstrip(',') # remove leading comma

                ids = rap_t.index[rap_t[land1_field] == '']
                rap_t.loc[ids, land1_field] = np.nan

                ## Fix format for struc1_field
                rap_t[struc1_field] = rap_t[struc1_field].astype(str)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r'\n',',',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r';',',',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r';;',',',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r',,',',',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r',,,',',',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r',$','',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r'MCRP=','MCRP-',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r'MCRP--','MCRP-',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r'MCRO','MCRP',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r'nan','',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.replace(r'\s+','',regex=True)
                rap_t[struc1_field] = rap_t[struc1_field].str.lstrip(',') # remove leading comma
                rap_t[struc1_field] = rap_t[struc1_field].str.rstrip(',') # remove leading comma
                
                ids = rap_t.index[rap_t[struc1_field] == '']
                rap_t.loc[ids, struc1_field] = np.nan

                ### 2. Update Pier Tracker ML
                #### Remove column names to be merged from the RAP Team
                comp_table_temp = comp_table.loc[:, [pier_num_field,
                                                    type_field,
                                                    unique_id_field,
                                                    status_field,
                                                    cp_field,
                                                    workability_field,
                                                    util_obstruc_field,
                                                    others_field
                                                    ]]
                comp_table_temp = comp_table_temp.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                merged_table = pd.merge(left=comp_table_temp, right=rap_t, how='left', on=pier_num_field)
                merged_table = merged_table.loc[:, tracker_fields_ordered]
                comp_table2 = pd.concat([comp_table2, merged_table], ignore_index=False).reset_index(drop=True)

            ##################### Check consistency between Civil ML and RAP ML ###############################
            ## When obstruction is present (e.g., 'Land' = 1), there should be obstructing lot IDs. 
            ## Identify piers with inconsistent information
            ### Land
            #### 'Land.1' field 
            error_land_t = comp_table2.loc[:, [pier_num_field, cp_field, workability_field, land_field, land1_field]].query(f"((~{land_field}.isna()) & (`{land1_field}`.isna())) | (({land_field}.isna()) & (~`{land1_field}`.isna()))")
            error_land_t.to_excel(os.path.join(pier_workablet_dir, '99-CHECK_Obstruction_N2_Land_Civil_vs_RAP.xlsx'), index=False)
            
            comp_table2['error_land'] = np.nan
            ids = comp_table2.index[comp_table2[pier_num_field].isin(error_land_t[pier_num_field])]
            comp_table2.loc[ids, 'error_land'] = 1

            ### Structure
            error_struc_t = comp_table2.loc[:, [pier_num_field, cp_field, workability_field, struc_field, struc1_field]].query(f"((~{struc_field}.isna()) & (`{struc1_field}`.isna())) | (({struc_field}.isna()) & (~`{struc1_field}`.isna()))")
            error_struc_t.to_excel(os.path.join(pier_workablet_dir, '99-CHECK_Obstruction_N2_Structure_Civil_vs_RAP.xlsx'), index=False)

            comp_table2['error_struc'] = np.nan
            ids = comp_table2.index[comp_table2[pier_num_field].isin(error_struc_t[pier_num_field])]
            comp_table2.loc[ids, 'error_struc'] = 1

            # Export as a new tracker
            to_excel_file0 = os.path.join(pier_workablet_dir, os.path.basename(pier_tracker_table))
            with pd.ExcelWriter(to_excel_file0) as writer:
                comp_table2.query(f"{cp_field} == 'N-01'").reset_index(drop=True).to_excel(writer, sheet_name='N-01', index=False)
                comp_table2.query(f"{cp_field} == 'N-02'").reset_index(drop=True).to_excel(writer, sheet_name='N-02', index=False)
                comp_table2.query(f"{cp_field} == 'N-03'").reset_index(drop=True).to_excel(writer, sheet_name='N-03', index=False)

        Workable_Pier_Tracker_Update()

class UpdateWorkablePierLayer(object):
    def __init__(self):
        self.label = "3. Update Pier Workable Layer (Polygon)"
        self.description = "Update Pier Workable Layer (Polygon)"

    def getParameterInfo(self):
        gis_viaduct_dir = arcpy.Parameter(
            displayName = "N2 Pier Tracker Masterlist Storage Directory",
            name = "N2 Pier Tracker Masterlist Storage Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "N2 Pier Workable Tracker ML (Excel)",
            name = "N2 Pier Workable Tracker ML (Excel)",
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

        params = [gis_viaduct_dir, pier_workable_tracker_ms, gis_workable_layer, gis_nlo_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_via_dir = params[0].valueAsText
        pier_tracker_ms = params[1].valueAsText
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
            workability_field = 'Workability'
            unique_id_field = 'uniqueID'
            land_obstruc_field = 'Land'
            struc_id_field = 'StrucID'
            struc_obstruc_field = 'Structure'
            others_obstruc_field = 'Others'
            lot_obstrucid_field = 'Land.1'
            struc_obstrucid_field = 'Structure.1'
            utility_obstruc_field = 'Utility'


            # 1. Clean fields
            cps = ['N-01','N-02','N-03']
            for i, cp in enumerate(cps):
                pier_tracker_t = pd.read_excel(pier_tracker_ms, sheet_name = cp)
                idx = pier_tracker_t.iloc[:, 0].index[pier_tracker_t.iloc[:, 0].str.contains(r'PierNumber',regex=True,na=False)]
                pier_tracker_t = pier_tracker_t.drop(idx).reset_index(drop=True)

                # to string
                pier_tracker_t[lot_obstrucid_field] = pier_tracker_t[lot_obstrucid_field].astype(str)
                pier_tracker_t[struc_obstrucid_field] = pier_tracker_t[struc_obstrucid_field].astype(str)

                # create workable columns for pre-construction work
                workable_cols = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']

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
                with arcpy.da.SearchCursor(gis_workable_layer, [pier_number_field, workable_cols[0]]) as cursor:
                    for row in cursor:
                        if row[1] == 2:
                            completed_piers.append(row[0])

                # from pier workable tracker ML
                id_workable_piers = pier_tracker_t.index[pier_tracker_t[workability_field] == 'Workable']
                id_nonworkable_piers = pier_tracker_t.index[pier_tracker_t[workability_field] == 'Non-workable']

                workable_piers = pier_tracker_t.loc[id_workable_piers, pier_number_field].values
                nonworkable_piers = pier_tracker_t.loc[id_nonworkable_piers, pier_number_field].values

                # Identify workable piers but status is not 4 (i.e., workable piers with incompleted pile cap construction)
                incomp_workable_piers = non_match_elements(workable_piers, completed_piers)
                # incomp_nonworkable_piers = non_match_elements(nonworkable_piers, completed_piers)

                # Enter 1 for workable piers with incompleted pile cap construction
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
                
                arcpy.AddMessage('Finished entering for workable piers with incomplete construction of pile cap.')

                # Empty cell for AllWorkable = 0 (non-workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.1 LandWorkable
                # Note that when 'land' == 1, this automatically exlucdes workable and completed piers.
                ids = pier_tracker_t.index[pier_tracker_t[land_obstruc_field] == 1]
                land_nonwork_piers = pier_tracker_t.loc[ids, pier_number_field].values

                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[1], cp_field]) as cursor:
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
                ids = pier_tracker_t.index[pier_tracker_t[struc_obstruc_field] == 1]
                struc_nonwork_piers = pier_tracker_t.loc[ids, pier_number_field].values
                
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[2], cp_field]) as cursor:
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

                pier_tracker_t[struc_obstrucid_field] = pier_tracker_t[struc_obstrucid_field].replace('\n',',')
                pier_tracker_t[struc_obstrucid_field] = pier_tracker_t[struc_obstrucid_field].replace(r'\s+','',regex=True)
                pier_tracker_t[struc_obstrucid_field] = pier_tracker_t[struc_obstrucid_field].str.upper()
                # pier_tracker_t[struc_id_field] = pier_tracker_t[struc_id_field].replace(r'[(]PNR[)]','',regex=True)
                
                ids_nonna = pier_tracker_t.index[pier_tracker_t[struc_obstruc_field] == 1]
                c_t2 = pier_tracker_t.loc[ids_nonna, ]
                ids = c_t2.index[c_t2[struc_obstrucid_field].notna()]
                c_t2 = c_t2.loc[ids, ]
 
                ### 2.3.2. identify any NLOs falling under the identified non-workable structures
                nlo_obstruc_piers = []
                for i in c_t2.index:
                    obstruc_struc_ids = c_t2.loc[i, struc_obstrucid_field]
                    # obstruc_struc_ids = obstruc_struc_ids[~np.isnan(obstruc_struc_ids)]
                    test = [e for e in gis_nlo_t[struc_id_field] if e in obstruc_struc_ids.split(',')]
                    
                    if len(test) > 0:
                        # idenfity pier numbers with obstructing NLOs
                        nlo_obstruc_piers.append(pier_tracker_t.loc[i, pier_number_field])
                
                ### 2.3.3. Enter NLOWorkable = 0 with identified pier numbers
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[3], cp_field]) as cursor:
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
                ids = pier_tracker_t.index[pier_tracker_t[utility_obstruc_field] == 1]
                util_obstruc_piers = pier_tracker_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[4], cp_field]) as cursor:
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
                ids = pier_tracker_t.index[pier_tracker_t[others_obstruc_field] == 1]
                others_obstruc_piers = pier_tracker_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[5], cp_field]) as cursor:
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
                arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(gis_via_dir, "N2_Pier_Workability_Portal.xlsx"))

        Workable_Pier_Table_Update()

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "1. Check Pier Numbers between Civil, GIS Portal, and RAP ML"
        self.description = "Check Pier Numbers between Civil, GIS Portal, and RAP ML"

    def getParameterInfo(self):
        pier_tracker_dir = arcpy.Parameter(
            displayName = "N2 GIS Pier Tracker Masterlist Storage Directory",
            name = "N2 GIS Pier Tracker Masterlist Storage Directory",
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
            displayName = "GIS N2 Viaduct ML (Excel)",
            name = "GIS N2 Viaduct ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_pier_tracker_ms = arcpy.Parameter(
            displayName = "N2 Pier Workable Tracker ML (Excel)",
            name = "N2 Pier Workable Tracker ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_tracker_dir, civil_workable_ms, gis_viaduct_ms, gis_pier_tracker_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_tracker_dir = params[0].valueAsText
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

            compile_all = pd.DataFrame()
            for cp in cps:
                arcpy.AddMessage("Contract Package: " + cp)
                compile_t = pd.DataFrame()

                cols = ['CP',
                        'PierNumber_civil',
                        'PierNumber_gisportal',
                        'PierNumber_pierTracker',
                        'Diff_Civil_vs_GISportal',
                        'Non-matched_piers_Civil_vs_GISportal',
                        'Diff_Civil_vs_PierTracker',
                        'Non-matched_piers_Civil_vs_PierTracker',
                        'Diff_GISportal_vs_PierTracker',
                        'Non-matched_piers_GISportal_vs_PierTracker'
                        ]

                #1. Read table
                ## N2 Viaduct portal
                portal_t = pd.read_excel(gis_viaduct_ms)
                ids = portal_t.index[(portal_t[cp_field] == cp) & (portal_t[type_field] == 2)]
                portal_t = portal_t.loc[ids, [pier_num_field, unique_id_field]].reset_index(drop=True)
                gis_piers = portal_t[pier_num_field].values
                
                ## N2 Civil ML
                new_cols = ['PierNumber', 'CP', 'util1', 'util2', 'Others', 'Workability']
                civil_t = pd.read_excel(civil_workable_ms, skiprows=2)
                ids = civil_t.columns[civil_t.columns.str.contains(r'^Pier No.*|Contract P.*|^Name of Utilities|^Others|^Pile Cap Workable.*',regex=True,na=False)]
                civil_t = civil_t.loc[:, ids]
                for i, col in enumerate(ids):
                    civil_t = civil_t.rename(columns={col: new_cols[i]})

                civil_t[cp_field] = civil_t[cp_field].str.replace(r'/.*','',regex=True)
                civil_t[cp_field] = civil_t[cp_field].str.replace(r'CPN','N-',regex=True)
                civil_t = civil_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                arcpy.AddMessage(civil_t.head())
                
                arcpy.AddMessage(civil_t[pier_num_field])
                civil_piers = civil_t[pier_num_field].values
                
                ## Pier Workable Tracker (GIS Team prepared)
                pier_track_t = pd.read_excel(gis_pier_tracker_ms, sheet_name=cp)
                idx = pier_track_t.iloc[:, 0].index[pier_track_t.iloc[:, 0].str.contains(r'PierNumber',regex=True,na=False)]
                pier_track_t = pier_track_t.drop(idx).reset_index(drop=True)
                pier_track_t = pier_track_t.rename(columns={pier_track_t.columns[0]: pier_num_field}) 
                tracker_piers = pier_track_t[pier_num_field].values

                # 2. Comparing
                compile_t.loc[0, cols[0]] = cp

                ## 2.1. Civil vs GIS Portal
                compile_t.loc[0, cols[1]] = len(civil_piers)
                compile_t.loc[0, cols[2]] = len(gis_piers)
                compile_t.loc[0, cols[4]] = compile_t.loc[0, cols[1]] - compile_t.loc[0, cols[2]]
                nonmatch_piers = [e for e in civil_piers if e not in gis_piers]
                if len(nonmatch_piers) > 0:
                    compile_t.loc[0, cols[5]] = nonmatch_piers
                else:
                    compile_t.loc[0, cols[5]] = np.nan

                ## 2.2. Civil vs Pier Tracker
                compile_t.loc[0, cols[3]] = len(tracker_piers)
                compile_t.loc[0, cols[6]] = compile_t.loc[0, cols[1]] - compile_t.loc[0, cols[3]]
                nonmatch_piers = [e for e in civil_piers if e not in tracker_piers]
                if len(nonmatch_piers) > 0:
                    compile_t.loc[0, cols[7]] = nonmatch_piers
                else:
                    compile_t.loc[0, cols[7]] = np.nan

                ## 2.3. GIS Portal vs Pier Tracker
                compile_t.loc[0, cols[8]] = compile_t.loc[0, cols[2]] - compile_t.loc[0, cols[3]]
                nonmatch_piers = [e for e in gis_piers if e not in tracker_piers]
                if len(nonmatch_piers) > 0:
                    compile_t.loc[0, cols[9]] = nonmatch_piers
                else:
                    compile_t.loc[0, cols[9]] = np.nan

                # Compile cps
                compile_all = pd.concat([compile_all, compile_t])
                compile_all = compile_all.loc[:, cols]
                arcpy.AddMessage("Table of Non-Matched Piers:")
                arcpy.AddMessage(compile_all)
            
            # Export
            compile_all.to_excel(os.path.join(pier_tracker_dir, '99-CHECK_Summary_N2_PierNumbers_Civil_vs_GISportal_vs_pierTracker.xlsx'),
                                              index=False)

        Workable_Pier_Table_Update()

class UpdatePierPointLayer(object):
    def __init__(self):
        self.label = "4. Update Pier Layer (Point)"
        self.description = "Update Pier Layer (Point)"

    def getParameterInfo(self):
        pier_point_layer = arcpy.Parameter(
            displayName = "GIS Pier Layer (Point)",
            name = "GIS Pier Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_layer = arcpy.Parameter(
            displayName = "Pier Workability Layer (Polygon)",
            name = "Pier Workability Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_point_layer, pier_workable_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_point_layer = params[0].valueAsText
        pier_workable_layer = params[1].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Pier_Point_Layer_Update():
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
            
            unique_id_field = 'uniqueID'
            # Create N2 pier point layer from this
            ## Feature to Point
            new_point_layer = 'N2_new_Pier_Point'
            arcpy.management.FeatureToPoint(pier_workable_layer, new_point_layer)

            
            deleteFieldsList = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']

            ## Delete Fields
            arcpy.management.DeleteField(new_point_layer, deleteFieldsList)
            
            ## Join Field
            arcpy.management.JoinField(new_point_layer, unique_id_field, pier_workable_layer, unique_id_field, deleteFieldsList)

            ## Truncate original point layer
            arcpy.management.TruncateTable(pier_point_layer)

            ## Append a new point layer to the original
            arcpy.management.Append(new_point_layer, pier_point_layer, schema_type = 'NO_TEST')

            # delete
            deleteTempLayers = [new_point_layer]
            arcpy.Delete_management(deleteTempLayers)

        Pier_Point_Layer_Update()

class UpdateStripMapLayer(object):
    def __init__(self):
        self.label = "5. Update Strip Map Layer (Polygon)"
        self.description = "Update Strip Map Layer (Polygon)"

    def getParameterInfo(self):
        pier_point_layer = arcpy.Parameter(
            displayName = "GIS Pier Layer (Point)",
            name = "GIS Pier Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        strip_map_layer = arcpy.Parameter(
            displayName = "GIS Strip Map Layer (Polygon)",
            name = "GGIS Strip Map Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_point_layer, strip_map_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_point_layer = params[0].valueAsText
        strip_map_layer = params[1].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Strip_Map_Layer_Update():
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

            # 3. Update strip map polygon layer
            ## 3.1. Select pier point layer for each status in 'AllWorkable' field
            ### First, select rows with non-workable piers
            where_clause = "AllWorkable = 0"
            arcpy.management.SelectLayerByAttribute(pier_point_layer, 'NEW_SELECTION', where_clause)

            # Select strip map layer by location
            arcpy.management.SelectLayerByLocation(strip_map_layer, 'CONTAINS', pier_point_layer)

            # Update strip map layer
            with arcpy.da.UpdateCursor(strip_map_layer, ['NonWorkable']) as cursor:
                for row in cursor:
                    row[0] = 'Yes'
                    cursor.updateRow(row)

            ### Second, switch rows and these rows are workable piers
            arcpy.management.SelectLayerByAttribute(strip_map_layer, 'SWITCH_SELECTION')
            with arcpy.da.UpdateCursor(strip_map_layer, ['NonWorkable']) as cursor:
                for row in cursor:
                    row[0] = 'No'
                    cursor.updateRow(row)

        Strip_Map_Layer_Update()


        