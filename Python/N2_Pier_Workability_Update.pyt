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
            displayName = "N2 Pier Workability Directory",
            name = "N2 Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        workable_pier_layer = arcpy.Parameter(
            displayName = "N2 Pier Workability Layer (Polygon)",
            name = "N2 Pier Workability Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        via_layer = arcpy.Parameter(
            displayName = "N2 Viaduct Layer (Multipatch)",
            name = "N2 Viaduct Layer (Multipatch)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        pier_number_layer = arcpy.Parameter(
            displayName = "N2 Pier Number Layer (Point)",
            name = "N2 Pier Number Layer (Point)",
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
            displayName = "N2 Pier Workability Directory",
            name = "N2 Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        viaduct_ms = arcpy.Parameter(
            displayName = "N2 Viaduct GIS ML (Excel)",
            name = "N2 Viaduct GIS ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        civil_workable_ms = arcpy.Parameter(
            displayName = "N2 Pier Workability Civil ML (Excel)",
            name = "N2 Pier Workability Civil ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "N2 Pier Workability Tracker ML (Excel)",
            name = "N2 Pier Workability Tracker ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_obstruction_ms = arcpy.Parameter(
            displayName = "N2 RAP Obstructing Lot and Structure ML (Excel)",
            name = "N2 RAP Obstructing Lot and Structure ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_nlo_ms = arcpy.Parameter(
            displayName = "N2 Structure ISF/NLO ML (Excel)",
            name = "N2 Structure ISF/NLO ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_workablet_dir, viaduct_ms, civil_workable_ms, pier_workable_tracker_ms, rap_obstruction_ms, gis_nlo_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_workablet_dir = params[0].valueAsText
        viaduct_ms = params[1].valueAsText
        civil_table = params[2].valueAsText
        pier_tracker_table = params[3].valueAsText
        rap_obst_table = params[4].valueAsText
        gis_nlo_ms = params[5].valueAsText

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
            remarks_field = 'Remarks'
            struc_id_field = 'StrucID'
            nlo_obstruc_field = 'NLO'

            #**************************************************************************************************#
            #*********************  1. Update Pier Workable Tracker ML using Civil Team's ML *********************#
            #**************************************************************************************************#
            # 0: Workable
            # 1: Non-workable
            # 2: Completed

            civil_t = pd.read_excel(civil_table, skiprows=2)
            via_t = pd.read_excel(viaduct_ms)
            gis_nlo_t = pd.read_excel(gis_nlo_ms)

            # Update N2 Pier Workability Tracker
            new_cols = ['PierNumber', 'CP', 'util1', 'util2', 'Others', 'Workability']
            
            ids = civil_t.columns[civil_t.columns.str.contains(r'^Pier No.*|Contract P.*|^Name of Utilities|^Others|^OTHERS|^Pile Cap Workable.*',regex=True,na=False)]
            civil_t = civil_t.loc[:, ids]
            for i, col in enumerate(ids):
                civil_t = civil_t.rename(columns={col: new_cols[i]})
                
            ## change CP notation
            civil_t[new_cols[1]] = civil_t[new_cols[1]].replace(r'CPN','N-',regex=True)

            ids = civil_t.index[civil_t[new_cols[5]] == 'Yes']
            civil_t.loc[ids, new_cols[5]] = 'Workable'
            ids = civil_t.index[civil_t[new_cols[5]] == 'No']
            civil_t.loc[ids, new_cols[5]] = 'Non-workable'
            ids = civil_t.index[civil_t[new_cols[5]] == 'Partial']
            civil_t.loc[ids, new_cols[5]] = 'Non-workable'

            idx_workable = civil_t.index[civil_t[workability_field] == 'Workable']

            ### Update 'Utility'
            civil_t[util_obstruc_field] = np.nan
            ids = civil_t.index[(civil_t[new_cols[2]].notna()) | (civil_t[new_cols[3]].notna())]
            civil_t.loc[ids, util_obstruc_field] = 1
            civil_t = civil_t.drop([new_cols[2],new_cols[3]], axis=1)

            ### If a workable pier has some information in Utility, Utility is empty
            civil_t.loc[idx_workable, util_obstruc_field] = np.nan

            ## Update 'Others' 
            idx = civil_t.index[~civil_t[new_cols[4]].isna()]
            civil_t.loc[idx, new_cols[4]] = 1
            idx = civil_t.index[civil_t[workability_field] == 'Workable']
            civil_t.loc[idx_workable, others_field] = np.nan

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
            #*********************  2. Update Pier Workable Tracker ML using RAP Team's ML *********************#
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
                
                # Update 'Land.1' for non-workable and completed pile caps
                # idx = rap_t.index[rap_t[land_field] != 1]
                # rap_t.loc[idx, land_field] = 0
                # idx_comp = rap_t.index[rap_t[pier_num_field].isin(comp_piers)]
                # rap_t.loc[idx_comp, land_field] = 2
                
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
                # Update 'Structure.1' for non-workable and completed pile caps
                # idx = rap_t.index[rap_t[struc_field] != 1]
                # rap_t.loc[idx, struc_field] = 0
                # idx_comp = rap_t.index[rap_t[pier_num_field].isin(comp_piers)]
                # rap_t.loc[idx_comp, struc_field] = 2

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

                ## NLO
                ### using obstructing structure IDs, enter NLO
                gis_nlo_t_filter = gis_nlo_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                nlo_piers = unique(gis_nlo_t_filter[struc_id_field])

                # Inspect the Pier Tracker ML contains the above strucIDs
                nlo_piers_join = ("|").join(nlo_piers)
                idx = rap_t.index[rap_t[struc1_field].str.contains(nlo_piers_join,regex=True,na=False)]
                rap_t[nlo_obstruc_field] = np.nan
                rap_t.loc[idx, nlo_obstruc_field] = 1

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
                merged_table = merged_table.loc[:, tracker_fields_ordered + [nlo_obstruc_field]]

                ## Concat
                comp_table2 = pd.concat([comp_table2, merged_table], ignore_index=False).reset_index(drop=True)

            ## Finally update 'Workability'
            ### Completed
            idx = via_t.index[(via_t[status_field] == 4) & (via_t[type_field] == 2)]
            comp_piers = via_t.loc[idx, pier_num_field].values
            ids_comp = comp_table2.index[comp_table2[pier_num_field].isin(comp_piers)]
            comp_table2.loc[ids_comp, workability_field] = 'Completed'
            # merged_table.loc[ids_comp, [util_obstruc_field,land_field,struc_field,others_field]] = 2

            # ### Workable (0)
            # ids_work = merged_table.index[merged_table[workability_field] == 'Workable']
            # merged_table.loc[ids_work, [util_obstruc_field,land_field,struc_field,others_field]] = 0

            # ## Non-workable (1)
            # ids_nonwork = merged_table.index[merged_table[workability_field] == 'Non-workable']
            
            # ### Utility
            # ids_nonwork_util = merged_table.loc[ids_nonwork, ].index[merged_table.loc[ids_nonwork, util_obstruc_field].isna()]
            # merged_table.loc[ids_nonwork_util, util_obstruc_field] = 0

            # ### Land
            # ids_nonwork_land = merged_table.loc[ids_nonwork, ].index[merged_table.loc[ids_nonwork, land_field].isna()]
            # merged_table.loc[ids_nonwork_land, land_field] = 0

            # ### Structure
            # ids_nonwork_struc = merged_table.loc[ids_nonwork, ].index[merged_table.loc[ids_nonwork, struc_field].isna()]
            # merged_table.loc[ids_nonwork_struc, struc_field] = 0

            # ### Others
            # ids_nonwork_others = merged_table.loc[ids_nonwork, ].index[merged_table.loc[ids_nonwork, others_field].isna()]
            # merged_table.loc[ids_nonwork_others, others_field] = 0


            ##################### Identify incosistent data entry ###############################
            ## Add case of errors to Remarks field;
            ## 1. Completed and Workable piers have obstructions (in Utility, Land, Structure, Others, Land.1, Structure.1)
            ## 2. Non-workable piers have empty cells in Utility, Land, Structure, Others, Land.1, Structure.1.
            ## 3. Piers with obstructing Land (1) or Structure (1) do not have any IDs in Land.1 or Structure.1 field.
            ## 4. Piers with obstructing Lot or Structure IDs in Land.1 or Structure.1 field do not have '1' in Land or Structure field.

            comp_table2[remarks_field] = np.nan
            obstruc_fields_all = [util_obstruc_field,land_field,struc_field,others_field,land1_field,struc1_field]
            error_descriptions = [
                {
                    'case1': 'Workable or completed piers should not have obstructions in one or more columns.',
                    'case2': 'Non-workable piers should have at least one obstruction in columns.',
                    'case3': 'This pier is missing obstructing LotIDs.',
                    'case4': 'This pier is missing obstructing StructureIDs.',
                    'case5': 'This pier is missing obstruction in Land',
                    'case6': 'This pier is missing obstruction in Structure'
                }
            ]

            obstruc_fields_notna = ((~comp_table2[util_obstruc_field].isna()) |
                                    (~comp_table2[land_field].isna()) |
                                    (~comp_table2[struc_field].isna()) |
                                    (~comp_table2[others_field].isna()) |
                                    (~comp_table2[land1_field].isna()) |
                                    (~comp_table2[struc1_field].isna()))
            
            obstruc_fields_na = ((comp_table2[util_obstruc_field].isna()) &
                        (comp_table2[land_field].isna()) &
                        (comp_table2[struc_field].isna()) &
                        (comp_table2[others_field].isna()) &
                        (comp_table2[land1_field].isna()) &
                        (comp_table2[struc1_field].isna()))

            ### Case 1:
            idx = comp_table2.index[((comp_table2[workability_field] == 'Completed') | (comp_table2[workability_field] == 'Workable')) & 
                                    obstruc_fields_notna]
            comp_table2.loc[idx, remarks_field] = error_descriptions[0]['case1']

            ### Case 2:
            idx = comp_table2.index[(comp_table2[workability_field] == 'Non-workable') &
                                    obstruc_fields_na]
            comp_table2.loc[idx, remarks_field] = error_descriptions[0]['case2']

            ### Case 3:
            idx = comp_table2.index[((comp_table2[workability_field] == 'Non-workable') & (comp_table2[land_field] == 1)) &
                                    (comp_table2[land1_field].isna())]
            comp_table2.loc[idx, remarks_field] = error_descriptions[0]['case3']

            ### Case 4:
            idx = comp_table2.index[((comp_table2[workability_field] == 'Non-workable') & (comp_table2[struc_field] == 1)) &
                                    (comp_table2[struc1_field].isna())]
            comp_table2.loc[idx, remarks_field] = error_descriptions[0]['case4']

            ### Case 5:
            idx = comp_table2.index[((comp_table2[workability_field] == 'Non-workable') & (~comp_table2[land1_field].isna())) &
                                    (comp_table2[land_field].isna())]
            comp_table2.loc[idx, remarks_field] = error_descriptions[0]['case5']

            ### Case 6:
            idx = comp_table2.index[((comp_table2[workability_field] == 'Non-workable') & (~comp_table2[struc1_field].isna())) &
                                    (comp_table2[struc_field].isna())]
            comp_table2.loc[idx, remarks_field] = error_descriptions[0]['case6']

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
            displayName = "N2 Pier Workability Directory",
            name = "N2 Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "N2 Pier Workability Tracker ML (Excel)",
            name = "N2 Pier Workability Tracker ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_workable_layer = arcpy.Parameter(
            displayName = "N2 Pier Workability Layer (Polygon)",
            name = "N2 Pier Workability Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_viaduct_dir, pier_workable_tracker_ms, gis_workable_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_via_dir = params[0].valueAsText
        pier_tracker_ms = params[1].valueAsText
        gis_workable_layer = params[2].valueAsText
        
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
            nlo_obstruc_field = 'NLO'
            remarks_field = 'Remarks'

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
                ### 1: Non-Workable
                ### 0: Workable
                ### 2: Completedd

                ### 1.2. Workable Pile Cap
                ## 2.0. Enter Workable (0) else non-Workable (1) for AllWorkable
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

                # Enter 1 for workable piers with incomplete pile cap construction
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(workable_piers) and row[7] == cp:
                            row[1] = 0
                            row[2] = 0
                            row[3] = 0
                            row[4] = 0
                            row[5] = 0
                            row[6] = 0
                        cursor.updateRow(row)
                
                arcpy.AddMessage('Finished entering for workable piers with incomplete construction of pile cap.')

                # Empty cell for AllWorkable = 1 (non-workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(nonworkable_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## 2.1 LandWorkable
                # Note that when 'land' == 1, this automatically exlucdes workable and completed piers.
                ids = pier_tracker_t.index[pier_tracker_t[land_obstruc_field] == 1]
                land_nonwork_piers = pier_tracker_t.loc[ids, pier_number_field].values

                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[1], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(land_nonwork_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'LandWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(workable_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.2 StrucWorkable
                ids = pier_tracker_t.index[pier_tracker_t[struc_obstruc_field] == 1]
                struc_nonwork_piers = pier_tracker_t.loc[ids, pier_number_field].values
                
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[2], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(struc_nonwork_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'StrucWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(workable_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.3 NLOWorkable
                ids = pier_tracker_t.index[pier_tracker_t[nlo_obstruc_field] == 1]
                nlo_nonwork_piers = pier_tracker_t.loc[ids, pier_number_field].values
                
                ### 'Non-workable' (1)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, 'NLOWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(nlo_nonwork_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)


                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'NLOWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(workable_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.4. UtilWorkable
                ids = pier_tracker_t.index[pier_tracker_t[utility_obstruc_field] == 1]
                util_obstruc_piers = pier_tracker_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[4], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(util_obstruc_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'UtilWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(workable_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.5. OthersWorkable 
                ids = pier_tracker_t.index[pier_tracker_t[others_obstruc_field] == 1]
                others_obstruc_piers = pier_tracker_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[5], cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(others_obstruc_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'OthersWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(workable_piers) and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                #############################################
                ## Update Pier Workable Layer for 'Remarks'
                #############################################
                idx = pier_tracker_t.index[~pier_tracker_t[remarks_field].isna()]
                remarks_piers = pier_tracker_t.loc[idx, pier_number_field].values
                remarks_text = pier_tracker_t.loc[idx, remarks_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, remarks_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(remarks_piers):
                            # Find index of the subject pier numbers in a list (remarks_piers)
                            idx2 = [index for index, value in enumerate(remarks_piers) if value == row[0]][0]

                            # Use this index to extract the corresponding remarks
                            row[1] = remarks_text[idx2]
                        cursor.updateRow(row)

                ## Export this layer to excel
                #arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(gis_via_dir, "N2_Pier_Workability_Portal.xlsx"))

        Workable_Pier_Table_Update()

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "1. Check Pier Numbers between Civil, GIS Portal, and RAP ML"
        self.description = "Check Pier Numbers between Civil, GIS Portal, and RAP ML"

    def getParameterInfo(self):
        pier_tracker_dir = arcpy.Parameter(
            displayName = "N2 Pier Workability Directory",
            name = "N2 Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_workable_ms = arcpy.Parameter(
            displayName = "N2 Pier Workability Civil ML (Excel)",
            name = "N2 Pier Workability Civil ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_viaduct_ms = arcpy.Parameter(
            displayName = "N2 Viaduct GIS ML (Excel)",
            name = "N2 Viaduct GIS ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_pier_tracker_ms = arcpy.Parameter(
            displayName = "N2 Pier Workability Tracker ML (Excel)",
            name = "N2 Pier Workability Tracker ML (Excel)",
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
                nonmatch_piers1 = [e for e in civil_piers if e not in gis_piers]
                nonmatch_piers2 = [e for e in gis_piers if e not in civil_piers]
                nonmatch_piers_all = nonmatch_piers1 + nonmatch_piers2
                if len(nonmatch_piers_all) > 0:
                    compile_t.loc[0, cols[5]] = nonmatch_piers_all
                else:
                    compile_t.loc[0, cols[5]] = np.nan

                ## 2.2. Civil vs Pier Tracker
                compile_t.loc[0, cols[3]] = len(tracker_piers)
                compile_t.loc[0, cols[6]] = compile_t.loc[0, cols[1]] - compile_t.loc[0, cols[3]]
                nonmatch_piers1 = [e for e in civil_piers if e not in tracker_piers]
                nonmatch_piers2 = [e for e in tracker_piers if e not in civil_piers]
                nonmatch_piers_all = nonmatch_piers1 + nonmatch_piers2
                if len(nonmatch_piers_all) > 0:
                    compile_t.loc[0, cols[7]] = nonmatch_piers_all
                else:
                    compile_t.loc[0, cols[7]] = np.nan

                ## 2.3. GIS Portal vs Pier Tracker
                compile_t.loc[0, cols[8]] = compile_t.loc[0, cols[2]] - compile_t.loc[0, cols[3]]
                nonmatch_piers1 = [e for e in gis_piers if e not in tracker_piers]
                nonmatch_piers2 = [e for e in tracker_piers if e not in gis_piers]
                nonmatch_piers_all = nonmatch_piers1 + nonmatch_piers2
                if len(nonmatch_piers_all) > 0:
                    compile_t.loc[0, cols[9]] = nonmatch_piers_all
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
            displayName = "N2 Pier Layer (Point)",
            name = "N2 Pier Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_layer = arcpy.Parameter(
            displayName = "N2 Pier Workability Layer (Polygon)",
            name = "N2 Pier Workability Layer (Polygon)",
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
            displayName = "N2 Pier Layer (Point)",
            name = "N2 Pier Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        strip_map_layer = arcpy.Parameter(
            displayName = "N2 Strip Map Layer (Polygon)",
            name = "N2 Strip Map Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        cp_breakline_layer = arcpy.Parameter(
            displayName = "N2 CP Breakline Layer (Line)",
            name = "N2 CP Breakline Layer (Line)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_point_layer, strip_map_layer, cp_breakline_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_point_layer = params[0].valueAsText
        strip_map_layer = params[1].valueAsText
        cpbreak_layer = params[2].valueAsText
        
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

            ### Add second 'CP' for strip polygons overlapping with two CPs.
            #### Used to accommodate two different CPs when selected in the smart map
            cp_field = 'CP_End'
            cp2_field = 'GroupId'
            # where_clause = f"{cp_field} <> 'S-06'"

            # First enter null 'GroupId' field
            with arcpy.da.UpdateCursor(strip_map_layer, [cp2_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[0] = None
                    cursor.updateRow(row)
                    
            # Select rows

            # arcpy.management.SelectLayerByAttribute(cpbreak_layer, 'NEW_SELECTION', where_clause)
            arcpy.management.SelectLayerByAttribute(cpbreak_layer, 'NEW_SELECTION')
            arcpy.management.SelectLayerByLocation(strip_map_layer, 'INTERSECT', cpbreak_layer)

            # Enter the second CP to 'GroupId' field
            ## The second CP is always +1 from the previous
            with arcpy.da.UpdateCursor(strip_map_layer, ['CP',cp2_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        if row[0] == 'N-01':
                            row[1] = 'N-02'
                        if row[0] == 'N-02':
                            row[1] = 'N-03'
                        elif row[0] == 'N-03':
                            row[1] = 'N-04'
                    cursor.updateRow(row)           

        Strip_Map_Layer_Update()


        