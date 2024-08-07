import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl
import numpy as np
import arcpy
# V1.0.1

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [UpdateLotExcel, UpdateLotMPRExcel, CheckLotUpdatedStatusEnvGIS, CheckLotUpdatedStatusGIS, UpdateStructureExcel, UpdateISFExcel, UpdateGISLayers, CheckMissingLotIDs, CopyInputToTargetLayer]

class UpdateLotExcel(object):
    def __init__(self):
        self.label = "1.0. Update Excel Master List (Lot)"
        self.description = "Update Excel Master List (Lot)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        
        gis_lot_ms = arcpy.Parameter(
            displayName = "GIS Land Status ML (Excel)",
            name = "GIS Land Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        env_lot_ms = arcpy.Parameter(
            displayName = "Envi Land Status ML (Excel)",
            name = "Envi Land Status ML (Excel)",
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

        params = [gis_dir, gis_lot_ms, env_lot_ms, gis_bakcup_dir, lastupdate]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_lot_ms = params[1].valueAsText
        env_lot_ms = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        def MMSP_Land_Update():
            def remove_all_space(table,field):
                table[field] = table[field].str.replace(r's\+','')

            def whitespace_removal(dataframe, field):
                try:
                    dataframe[field] = dataframe[field].apply(lambda x: x.strip())
                except:
                    pass

            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)

            def rename_columns_title(table, search_names, renamed_word): # one by one
                colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
                try:
                    table = table.rename(columns={str(colname_change[0]): renamed_word})
                except:
                    pass
                return table
            
            def check_matches_list_and_merge(target_table, input_table, join_field):
                id1 =  unique(target_table[join_field])
                id2 = unique(input_table[join_field])
                    
                target_table_miss = [f for f in id1 if f not in id2]
                input_table_miss = [f for f in id2 if f not in id1]

                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in Envi Excel MasterList: {}'.format(target_table_miss))
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in GIS MasterList: {}'.format(input_table_miss))

                #arcpy.AddMessage('{} matches between the tables. The two tables are joined'.format(join_field))
                table = pd.merge(left=target_table, right=input_table, how='left', left_on=join_field, right_on=join_field)
                return table
            
            def check_field_match(target_table, input_table, join_field):
                id1 =  unique(target_table[join_field])
                id2 = unique(input_table[join_field])
                    
                target_table_miss = [f for f in id1 if f not in id2]
                input_table_miss = [f for f in id2 if f not in id1]

                arcpy.AddMessage('Missing in Envi Excel MasterList: {}'.format(target_table_miss))
                arcpy.AddMessage('Missing in GIS MasterList: {}'.format(input_table_miss))
            
            def convert_status_to_numeric(table, dic, input_field, new_field):
                for i in range(len(dic)):
                    id = table.index[table[input_field] == list(dic.keys())[i]]
                    table.loc[id, new_field] = list(dic.values())[i]

            def check_status_hl(table,gis_status,env_status_field):
                # gis_staus = dictionary, env_status_fields=list
                id = table.index[table[env_status_field] == '']
                table1 = table.drop(id)
                
                hl_status = list(gis_status.keys())
                hl_status_env = unique(table1[env_status_field])
                
                # Print miss-matched Ids from Envi table
                check_list = [e for e in hl_status_env if e not in hl_status]
                
                arcpy.AddMessage(env_status_field)
                arcpy.AddMessage(check_list)

            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)

            
            def drop_empty_rows(table, field):
                id = table.index[(table[field] == '') | (table[field].isna()) | (table[field].isnull())] # Do not use isna() as 'keep_default_na = False'
                table = table.drop(id)
                table = table.reset_index(drop=True)
                return table
            
            # Read as xlsx
            gis_table = pd.read_excel(gis_lot_ms)
            env_table = pd.read_excel(env_lot_ms, skiprows=1, keep_default_na=False) # keep_default=False for High_Level Columns
 
            arcpy.AddMessage(f"gis_table fields: {gis_table.dtypes}")
            # Create bakcup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + "GIS_Land_MasterList.xlsx"),index=False)
            except:
                pass

            # Status parameters for High Level Operations
            status_hl = [
                # High Level
                {"Ready for Handover/Handed Over": 1, "Pending Delivery": 2, "For Appraisal/Offer to Buy": 3},
                
                # Land Acquisition
                {
                    "On-going Validation": 1,
                    "Pending Appraisal": 2,
                    "Pending Compilation of Documents": 3,
                    "OTB for Serving": 4,
                    "Pending OTB Reply (Within 30 Days)": 5,
                    "Pending OTB Reply Beyond 30 Days (Uncooperative)": 6,
                    "Pending OTB Reply Beyond 30 Days (Cooperative)": 7,
                    "OTB Accepted with Pending Documents From PO or Other Agencies": 8,
                    "OTB Accepted": 9,
                    "Expropriation": 10,
                    "ROWUA/TUA": 11
                },
                
                # Land Acquisition1
                {
                    "On-going Validation": 1,
                    "For Submission to Legal": 2,
                    "Pending Legal Pass": 3,
                    "On-going Payment Processing": 4,
                    "Paid": 5,
                    "N/A": 6
                },
                
                # Payment Processing
                {
                    "For Submission to Budget": 1,
                    "For Signing of ORS, DV and RFPP": 2,
                    "With Budget for Obligation": 3,
                    "With Accounting for CAF Issuance": 4,
                    "For DOTr Signing": 5,
                    "For Notarization": 6,
                    "For Submission to CS": 7,
                    "DV with CS": 8,
                    "Paid/Checks Issued": 9,
                    "N/A": 10
                },
                
                # Expro
                {
                    "With PMO/RRE": 1,
                    "With OSG": 2,
                    "With Court": 3,
                    "Issuance of WOP": 4,
                    "WOP with COT": 5,
                    "N/A": 6
                },
                
                # ROWUA
                {
                    "On-going Finalization": 1,
                    "Signed ROWUA": 2,
                    "N/A": 3
                }
                ]

            ###################  0.0. Check matching of status in High Level Operation Status between Envi and GIS tables: ##################
            env_status_fields = ['High_Level', 'Land_Acquisition','Land_Acquisition.1','Payment_Processing','Expro.1','ROWUA']

            # Remove head and tail space
            for field in env_status_fields:
                whitespace_removal(env_table,field) 

            # Run 
            # arcpy.AddMessage('-- 0.0. Unmatched Status Parameters between GIS and Envi')
            # for i in range(len(status_hl)):
            #     check_status_hl(env_table,status_hl[i],env_status_fields[i])
            
            ######################################################################################
            # Field definitions
            join_field = 'Id'
            pte_field = 'PTE'
            h_level_field = 'H_Level'
            la_field = 'LA'
            la2_field = 'LA2'
            pp_field = 'PP'
            expro_field = 'Expro'
            rowua_field = 'ROWUA'
            remarks_field = 'Remarks'
            issue_field = 'Issue'
            status_nvs3_field = 'StatusNVS3'
            handedover_field = 'HandedOver'
            handover_date_field = 'HandOverDate'
            handedover_year_field = 'HandedOverYear'
            handover_2_field = 'Handover2'
            not_yet_field = 'not_yet'
            moa_field = 'MOA'
            target_date_field = 'Target_Date'
            
            # Remove any empty rows outside the main table
            try:
                env_table = drop_empty_rows(env_table, 'STATION')
                # id = env_table.index[env_table['STATION'] == ''] # Do not use isna() as 'keep_default_na = False'
                # env_table = env_table.drop(id)
                # env_table = env_table.reset_index(drop=True)
            except:
                pass

            # if there are duplicated observations in Envi's table, stop the process and exit
            duplicated_Ids = env_table[env_table.duplicated([join_field]) == True][join_field]
            arcpy.AddMessage(duplicated_Ids)

            # check status parameters defined above = status parameters in Envi.
            ## High Level
            check_field1 = 'High_Level'
            h_level_envi = unique(env_table[check_field1])

            if len(duplicated_Ids) == 0:
                #### 0. Remove white space from join field                
                whitespace_removal(gis_table, join_field)
                whitespace_removal(env_table, join_field)
                
                #### 1. GIS Table (target table)
                ## The following fields are updated for smart maps from 'PRE Weekly Smart Maps on Land Acquisition' (Env. Team)
                ### Fields from Envi           -> Fields from GIS ###
                
                #-- Main Status (StatusNVS3 and Hdanded Over) --#
                ### 'Status NVS'               -> 'StatusNVS3'
                ### 'Handed over to JV'        -> 'HandedOver'
                ### 'Handed_Date'              -> HandOverDate'
                ### 'Mode of Acquisition'      -> 'MOA'
                ### 'Lot with PTE'             -> 'PTE'
                ### 'Handed over (DOTr to GC)' -> 'Handover2'
                ### 'To be handed over to JV'  -> 'not_yet'

                #-- High Level Operation Statuses --#
                ### 'High_Level'               -> 'H_Level'
                ### 'Land_Acquisition'         -> 'LA'
                ### 'Land_Acquisition1'        -> 'LA2'
                ### 'Payment_Processing'       -> 'PP'
                ### 'Expro'                    -> 'Expro'
                ### 'ROWUA'                    -> 'ROWUA'
                ### 'Remarks                   -> 'Remarks'
                ### 'Issue'                    -> 'Issue'

                ## 2. Env. table (input table)
                ### 2.1. Land Acquisition (StatusNVS3)
                ind_id = [e for e in env_table.columns.str.contains('^Id$',regex=True)].index(True)
                ind_status = [e for e in env_table.columns.str.contains('^Status.*NVS$',regex=True)].index(True)
                ind_jv = [e for e in env_table.columns.str.contains('^To be.*to JV$',regex=True)].index(True)
                inds = [ind_id] + [f for f in range(ind_status, ind_jv+1)]
                env_table_la = env_table.iloc[:, inds]
                
                ### 2.2. Operations Level
                ind_first = [e for e in env_table.columns.str.contains('^High.*Level$',regex=True)].index(True)
                ind_last = [e for e in env_table.columns.str.contains('^Issue$',regex=True)].index(True)
                ind_keep = [f for f in range(ind_first, ind_last+1)]
                keep_fields = [e for e in env_table.columns[ind_keep]]
                transfer_fields = [join_field] + keep_fields
                env_table_ol = env_table[transfer_fields]

                old_fields = [f for f in env_table_ol.columns[1:7]] # H_Level to ROWUA
                new_fields = [h_level_field, la_field, la2_field, pp_field, expro_field, rowua_field, remarks_field, issue_field]

                ### 2.2.1 Update status for Operation Level
                for i in range(len(old_fields)):
                    convert_status_to_numeric(env_table_ol, status_hl[i], old_fields[i], new_fields[i])

                # Filter env_table and include selected fields only
                env_table_ol = env_table_ol[new_fields + [join_field]]

                ### 2.3. Merge land acquisition & operations level sub-tables above
                ### 2.3.1. Check for Id match and then join two tables
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('----------: Check Id match between two sub-tables split for Land Acquisition and Operations Level :------------')
                gis_table_new = check_matches_list_and_merge(env_table_la, env_table_ol, join_field)

                ### 2.3.2. Join new fiels to existing (i.e., update the original GIS table)
                #### Change field names based on the original gis table
                change_names = ['^Status.*NVS$', '^Handed.*JV$', '^Handed_Date', 'Mode of Acquisition', 'Lot with PTE', '^Handed.*over.*GC[)]$', '^To be handed over to JV', '^Expro4$', '^ROWUA2$']
                new_names = [status_nvs3_field, handedover_field, handover_date_field, moa_field, pte_field, handover_2_field, not_yet_field, expro_field, rowua_field]

                for i in range(len(change_names)):
                    gis_table_new = rename_columns_title(gis_table_new, change_names[i], new_names[i])

                ### 2.3.3. Delete field names from the original
                drop_fields = new_names + new_fields # ['H_Level','LA','LA2','PP','Expro','ROWUA', 'Remarks', 'Issue']
                gis_table = gis_table.drop(columns = drop_fields)

                # 3. GIS table (updated)
                ## 3.1. Join fiels from new table to original GIS table
                ### Before merge, check duplicated fields
                gis_table_fields = gis_table.columns
                gis_table_new_fields = gis_table_new.columns
                dup1 = [f for f in gis_table_fields if f in gis_table_new_fields]
                duplicated_fields = [f for f in dup1 if f not in join_field]
                if len(duplicated_fields) > 0:
                    gis_table = gis_table.drop(columns = duplicated_fields)

                gis_table_updated = pd.merge(left=gis_table, right=gis_table_new, how='left', left_on=join_field, right_on=join_field)

                ## 3.2. Fix date
                date_fields = [target_date_field, handover_date_field]
                for date in date_fields:
                    gis_table_updated[date] = pd.to_datetime(gis_table_updated[date],errors='coerce').dt.date

                ## 3.3. Check Id match again between updated GIS excel table and Envi land acquisition table
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('----------: Check Id match between updated GIS table and Envi Land Acquisition table :----------')
                check_field_match(gis_table_updated, env_table, join_field)
            
                # to_string_fields = [join_field]
                toString(gis_table_updated, ['CN'])

                # Get HandedOverYear from HandOverDate
                ## Convert object to pandas datetime
                gis_table_updated[handover_date_field] = pd.to_datetime(gis_table_updated[handover_date_field])
                gis_table_updated[handedover_year_field] = gis_table_updated[handover_date_field].dt.year

                # Recover the original date format
                gis_table_updated[handover_date_field] = pd.to_datetime(gis_table_updated[handover_date_field], errors='coerce').dt.date
 
                # 4. Export to excel
                export_file_name = os.path.splitext(os.path.basename(gis_lot_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                gis_table_updated.to_excel(to_excel_file, index=False)
            
            else:
                arcpy.AddMessage('---------------- Duplicated Ids -----------------')
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids as above in Envi table. The Process stopped. Please correct the duplicated rows.')
                pass

        MMSP_Land_Update()

class CheckLotUpdatedStatusEnvGIS(object):
    def __init__(self):
        self.label = "1.1 Summary Stats for Lot Status (Envi ML and GIS ML)"
        self.description = "1.1 Summary Stats for Lot Status (Envi ML and GIS ML)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        
        gis_lot_ms = arcpy.Parameter(
            displayName = "GIS Land Status ML (Excel)",
            name = "GIS Land Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        env_lot_ms = arcpy.Parameter(
            displayName = "Envi Land Status ML (Excel)",
            name = "Envi Land Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_dir, gis_lot_ms, env_lot_ms]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_lot_ms = params[1].valueAsText
        env_lot_ms = params[2].valueAsText

        def MMSP_Land_Update():
            def remove_all_space(table,field):
                table[field] = table[field].str.replace(r's\+','')

            def rename_columns_title(table, search_names, renamed_word): # one by one
                colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
                try:
                    table = table.rename(columns={str(colname_change[0]): renamed_word})
                except:
                    pass
                return table
           
            def convert_status_to_numeric(table, dic, input_field):
                for i in range(len(dic)):
                    id = table.index[table[input_field] == list(dic.keys())[i]]
                    table.loc[id, input_field] = list(dic.values())[i]

            def drop_empty_rows(table, field):
                id = table.index[(table[field] == '') | (table[field].isna()) | (table[field].isnull())] # Do not use isna() as 'keep_default_na = False'
                table = table.drop(id)
                table = table.reset_index(drop=True)
                return table

            # Read as xlsx
            gis_table = pd.read_excel(gis_lot_ms)
            env_table_ol = pd.read_excel(env_lot_ms, skiprows=1, keep_default_na=False) # keep_default=False for Operations Level Columns
            env_table_nvs = pd.read_excel(env_lot_ms, skiprows=1) # Do not use 'keep_default_na=False'. this is used for only checking 'StatusNVS3'
            
            ###################  Check and Print Statuses between Envi excel ML and GIS excel ML ##############################
            # 0. Define field names
            ## Existing Env table
            nvs3_field_env = 'StatusNVS'
            nvs3_field_gis = 'StatusNVS3'
            package_field = 'Package'
            station_field = 'STATION'
            station1_field = 'Station1'
            type_field = 'Type'
            id_field = 'Id'
            count_name = 'counts'
            lsuffix_env = '_ENV'
            rsuffix_gis = '_GIS'
            counts_env = count_name + '_ENV'
            counts_gis = count_name + '_GIS'

            export_file_name = 'CHECK-LA_Summary_Statistics_Envi_and_GIS_ML.xlsx'
            to_excel_file = os.path.join(gis_dir, export_file_name)
 
            ######################################
            ############ 'StatusNVS3' ############
            ######################################

            ## remove space from columns
            env_table_nvs.columns = env_table_nvs.columns.str.replace(r'\s+','',regex=True)
            for field in [package_field,id_field]:
                remove_all_space(env_table_nvs, field)

            #### remove empty StatusNVS
            id = env_table_nvs.index[env_table_nvs[nvs3_field_env].isna()]
            env_table_nvs = env_table_nvs.drop(id)

            # Remove any empty rows outside the main table
            try:
                env_table_nvs = drop_empty_rows(env_table_nvs, station_field)
                env_table_ol = drop_empty_rows(env_table_ol, station_field)
            except:
                pass

            #### Add 'Type': Station or Subterranean
            arcpy.AddMessage(env_table_nvs.tail())
            id = env_table_nvs.index[env_table_nvs['Id'].str.contains(r'Sub|SUB',regex=True)]
            env_table_nvs[type_field] = 'Station'
            env_table_nvs.loc[id,type_field] = 'Subterranean'

            groupby_fields = [package_field, station_field, type_field, nvs3_field_env]
            nvs3_env = env_table_nvs.groupby(groupby_fields)[nvs3_field_env].count().reset_index(name=count_name)
            nvs3_env = nvs3_env.sort_values(by=[package_field, station_field, type_field])

            arcpy.AddMessage('03.')

            # 2. GIS table
            groupby_fields = [package_field, station1_field, type_field, nvs3_field_gis]
            nvs3_gis = gis_table.groupby(groupby_fields)[nvs3_field_gis].count().reset_index(name=count_name)
            nvs3_gis = nvs3_gis.sort_values(by=[package_field, station1_field, type_field]) 

            arcpy.AddMessage('04.')

            # Merge
            ## We need to rename Station and StatusNVS in the envi table to match GIS.
            ### 'STATION'(x) -> 'Station1'
            ### 'StatusNVS(x) -> 'StatusNVS3'
            nvs3_env = nvs3_env.rename(columns={station_field: str(station1_field), nvs3_field_env: str(nvs3_field_gis)})

            table_nvs3 = pd.merge(left=nvs3_env, right=nvs3_gis, how='outer',
                                  left_on=[package_field, station1_field, type_field, nvs3_field_gis],
                                  right_on=[package_field, station1_field, type_field, nvs3_field_gis])
            # table_nvs3 = nvs3_env.join(nvs3_gis,lsuffix=lsuffix_env,rsuffix=rsuffix_gis)
            table_nvs3['count_diff'] = np.NAN
            # table_nvs3['count_diff'] = table_nvs3[counts_gis] - table_nvs3[counts_env]
            table_nvs3['count_diff'] = table_nvs3['counts_y'] - table_nvs3['counts_x']
            table_nvs3 = table_nvs3.rename(columns={"counts_x": str(counts_env), "counts_y": str(counts_gis)})

            ############################################
            ############ 'Operations Level' ############
            ############################################
            ## 2.1. Data Preparation
            ## Existing fields (Env)
            hl_field = 'High_Level'
            la_field = 'Land_Acquisition'
            la2_field = 'Land_Acquisition.1'
            payp_field = 'Payment_Processing'
            expro_field = 'Expro.1'
            rowua_field = 'ROWUA'

            ## rename fields for status
            h_level_rename = 'H_Level'
            la_field_rename = 'LA'
            la2_field_rename = 'LA2'
            pp_field_rename = 'PP'
            expro_field_rename = 'Expro'

            ## remove space from column names
            env_table_ol.columns = env_table_ol.columns.str.replace(r'\s+','',regex=True)

            ### 2.1.0. Keep fields
            env_table_ol = env_table_ol[[package_field, id_field, station_field, hl_field, la_field, la2_field, payp_field, expro_field, rowua_field]]

            ### 2.1.1. Rename status fields
            status_fields_old = [hl_field, la_field, la2_field, payp_field, expro_field]
            status_fields_new = [h_level_rename, la_field_rename, la2_field_rename, pp_field_rename, expro_field_rename]
            
            for i in range(len(status_fields_old)):
                env_table_ol = rename_columns_title(env_table_ol, status_fields_old[i], status_fields_new[i])

            ### 2.1.2. Remove empty space
            ## No space for 'Package' and 'Id'
            for field in [package_field, id_field]:
                remove_all_space(env_table_ol, field)

            ### 2.1.4. Convert status
            # Status parameters for High Level Operations
            status_ol = [
                # High Level
                {"Ready for Handover/Handed Over": 1, "Pending Delivery": 2, "For Appraisal/Offer to Buy": 3},
                
                # Land Acquisition
                {
                    "On-going Validation": 1,
                    "Pending Appraisal": 2,
                    # "Pending Delivery": 3,
                    "Pending Compilation of Documents": 3,
                    "OTB for Serving": 4,
                    "Pending OTB Reply (Within 30 Days)": 5,
                    "Pending OTB Reply Beyond 30 Days (Uncooperative)": 6,
                    "Pending OTB Reply Beyond 30 Days (Cooperative)": 7,
                    "OTB Accepted with Pending Documents From PO or Other Agencies": 8,
                    "OTB Accepted": 9,
                    "Expropriation": 10,
                    "ROWUA/TUA": 11
                },
                
                # Land Acquisition1
                {
                    "On-going Validation": 1,
                    "For Submission to Legal": 2,
                    "Pending Legal Pass": 3,
                    "On-going Payment Processing": 4,
                    "Paid": 5,
                    "N/A": 6
                },
                
                # Payment Processing
                {
                    "For Submission to Budget": 1,
                    "For Signing of ORS, DV and RFPP": 2,
                    "With Budget for Obligation": 3,
                    "With Accounting for CAF Issuance": 4,
                    "For DOTr Signing": 5,
                    "For Notarization": 6,
                    "For Submission to CS": 7,
                    "DV with CS": 8,
                    "Paid/Checks Issued": 9,
                    "N/A": 10
                },
                
                # Expro
                {
                    "With PMO/RRE": 1,
                    "With OSG": 2,
                    "With Court": 3,
                    "Issuance of WOP": 4,
                    "WOP with COT": 5,
                    "N/A": 6
                },
                
                # ROWUA
                {
                    "On-going Finalization": 1,
                    "Signed ROWUA": 2,
                    "N/A": 3
                }
                ]
            
            for i in range(len(status_fields_new)):
                convert_status_to_numeric(env_table_ol, status_ol[i], status_fields_new[i])
                # env_table_ol[status_fields_new[i]] = env_table_ol[status_fields_new[i]].astype(int)

            ### 2.1.5. Add 'Type': Station or Subterranean
            id = env_table_ol.index[env_table_ol['Id'].str.contains(r'Sub|SUB',regex=True)]
            env_table_ol['Type'] = 'Station'
            env_table_ol.loc[id,'Type'] = 'Subterranean'
            
            data_store = {}
            n_step = -1

            ## 2.2. Calculate Summary Statistics for Status Fields
            for field in status_fields_new:
                n_step = n_step + 1

                ### 2.2.1. Env Table
                groupby_fields = [package_field,station_field,type_field,field]
                env_sum = env_table_ol.groupby(groupby_fields)[field].count().reset_index(name=count_name)
                env_sum = env_sum.sort_values(by=[package_field,station_field,type_field])

                ### Remove empty status
                id = env_sum.index[(env_sum[field] == '') | (env_sum[field].isna()) | (env_sum[field].isnull())]
                env_sum = env_sum.drop(id)
                env_sum = env_sum.reset_index(drop=True)

                ### 2.2.2. GIS table
                groupby_fields = [package_field, station1_field, type_field, field]
                gis_sum = gis_table.groupby(groupby_fields)[field].count().reset_index(name=count_name)
                gis_sum = gis_sum.sort_values(by=[package_field, station1_field, type_field]) 

                # Merge
                ## Rename
                env_sum = env_sum.rename(columns={station_field: str(station1_field)})

                # if field == h_level_rename:
                table_ol = pd.merge(left=env_sum, right=gis_sum, how='outer',
                        left_on=[package_field, station1_field, type_field, field],
                        right_on=[package_field, station1_field, type_field, field])

                table_ol['count_diff'] = np.NAN
                table_ol['count_diff'] = table_ol['counts_y'] - table_ol['counts_x']
                table_ol = table_ol.rename(columns={"counts_x": str(counts_env), "counts_y": str(counts_gis)})

                data_store[n_step] = table_ol

            # Export
            with pd.ExcelWriter(to_excel_file) as writer:
                table_nvs3.to_excel(writer, sheet_name=nvs3_field_gis, index=False)
                data_store[0].to_excel(writer, sheet_name=status_fields_new[0], index=False)
                data_store[1].to_excel(writer, sheet_name=status_fields_new[1], index=False)
                data_store[2].to_excel(writer, sheet_name=status_fields_new[2], index=False)
                data_store[3].to_excel(writer, sheet_name=status_fields_new[3], index=False)
                data_store[4].to_excel(writer, sheet_name=status_fields_new[4], index=False)
    
        MMSP_Land_Update()

class UpdateLotMPRExcel(object):
    def __init__(self):
        self.label = "1.2. Update MPR Excel Master List (Lot)"
        self.description = "Update MPR Excel Master List (Lot)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        
        gis_lot_ms = arcpy.Parameter(
            displayName = "GIS Land Status ML (Excel)",
            name = "GIS Land Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        env_mpr_ms = arcpy.Parameter(
            displayName = "Envi MPR Status ML (Excel)",
            name = "Envi MPR Status ML (Excel)",
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

        params = [gis_dir, gis_lot_ms, env_mpr_ms, gis_bakcup_dir, lastupdate]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_lot_ms = params[1].valueAsText
        env_mpr_ms = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        def MMSP_Land_MPR_Update():
            def whitespace_removal(dataframe, field):
                try:
                    dataframe[field] = dataframe[field].apply(lambda x: x.strip())
                except:
                    pass

            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)

            def rename_columns_title(table, search_names, renamed_word): # one by one
                colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
                try:
                    table = table.rename(columns={str(colname_change[0]): renamed_word})
                except:
                    pass
                return table
            
            def check_matches_list_and_merge(target_table, input_table, join_field):
                id1 =  unique(target_table[join_field])
                id2 = unique(input_table[join_field])
                    
                target_table_miss = [f for f in id1 if f not in id2]
                input_table_miss = [f for f in id2 if f not in id1]

                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in Envi Excel MasterList: {}'.format(target_table_miss))
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in GIS MasterList: {}'.format(input_table_miss))

                #arcpy.AddMessage('{} matches between the tables. The two tables are joined'.format(join_field))
                table = pd.merge(left=target_table, right=input_table, how='left', left_on=join_field, right_on=join_field)
                return table
            
            def check_field_match(target_table, input_table, join_field):
                id1 =  unique(target_table[join_field])
                id2 = unique(input_table[join_field])
                    
                target_table_miss = [f for f in id1 if f not in id2]
                input_table_miss = [f for f in id2 if f not in id1]

                arcpy.AddMessage('Missing in Envi Excel MasterList: {}'.format(target_table_miss))
                arcpy.AddMessage('Missing in GIS MasterList: {}'.format(input_table_miss))
            
            def convert_status_to_numeric(table, dic, input_field, new_field):
                for i in range(len(dic)):
                    id = table.index[table[input_field] == list(dic.keys())[i]]
                    table.loc[id, new_field] = list(dic.values())[i]

            def mpr_update_stepname(table, steps, new_field):
                for i in range(len(steps)):
                    id = table.index[table[steps[i]] >= 1]
                    table.loc[id, new_field] = steps[i]

            def mpr_status12_update(table, steps, new_field):
                for i in range(len(steps)):
                    id = table.index[table[steps[i]] >= 1]
                    if steps[i] == 'OTB Delivered':
                        table.loc[id,new_field] = table[steps[i]] + 5
                    elif steps[i] == 'Expropriation':
                        table.loc[id,new_field] = table[steps[i]] + 4
                    else:
                        table.loc[id,new_field] = table[steps[i]]
            
                    # else = 0
                    id0 = table.index[table[new_field].isnull()]
                    table.loc[id0,new_field] = 0

            def toNumeric(table, fields):
                for field in fields:
                    table[field] = pd.to_numeric(table[field], errors='coerce')

            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)
            
            # Read as xlsx
            gis_table = pd.read_excel(gis_lot_ms)
            env_table = pd.read_excel(env_mpr_ms, keep_default_na=False)

            # Join Field
            join_field = 'Id'

            # Create bakcup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + "GIS_Land_MasterList.xlsx"),index=False)
            except:
                pass
            
            # if there are duplicated observations in Envi's table, stop the process and exit
            duplicated_Ids = env_table[env_table.duplicated([join_field]) == True][join_field]

            if len(duplicated_Ids) == 0:
                #### 0. Remove white space from join field                
                whitespace_removal(gis_table, join_field)
                whitespace_removal(env_table, join_field)
              
                ## The following fields are updated in GIS table for MPR from Env. Team
                ### Fields from Envi           -> Fields from GIS ###
                ### 'OTB Preparation'          -> 'OtB_Preparation'
                ### 'Payment Processing'       -> 'Payment_Processing'
                ### 'Expropriation'            -> 'Expropriation_Case'
                ###
                arcpy.AddMessage('Processing MPR data started:')

                ## MPR Update
                old_mpr_fields = ['stepName1', 'stepName2', 'Status1', 'Status2', 'OtB_Preparation', 'OtB_Delivered', 'Payment_Processing', 'Expropriation_Case']
                gis_table = gis_table.drop(columns = old_mpr_fields)

                ## Fill in stepName1 and stepName2
                ### Fields from Envi           -> Fields from GIS ###
                ###  OTB Preparation = 1             stepName1 = 'OTB Preparation'
                ###  OTB Delivered = 1               stepName1 = 'OTB Delivered'
                ###  Payment Processing = 1          stepName2 = 'Payment_Processing'
                ###  Expropriation_Case = 1          stepName2 = 'Expropriation_Case'                    

                steps_otb = ['OTB Preparation', 'OTB Delivered']
                toNumeric(env_table, steps_otb)
                mpr_update_stepname(env_table, steps_otb, old_mpr_fields[0])

                steps_ppe =  ['Payment Processing', 'Expropriation']
                toNumeric(env_table, steps_ppe)
                mpr_update_stepname(env_table, steps_ppe, old_mpr_fields[1])
                
                ## status1 and status2
                ### 'stepName1'          'OTB Preparation'   -     'Status1'
                ###  'OTB Preparation'         1                        1          
                ###  'OTB Preparation'         2                        2       
                ###  'OTB Preparation'         3                        3         
                ###  'OTB Preparation'         4                        4  
                ###  'OTB Preparation'         5                        5  
                ###  'OTB Delivered'           1                        6  
                ###  'OTB Delivered'           2                        7  
                ###  'OTB Delivered'           3                        8  
                ###  'OTB Delivered'           4                        9  
                ###  'OTB Delivered'           5                        10  
                ###  'OTB Delivered'           6                        11  
                ###  'OTB Delivered'           7                        12  
                ###  'OTB Delivered'           8                        13  

                ### 'stepName2'          'Payment_Processing'   -  'Status2'
                ###  'Payment_Processing'         1                        1          
                ###  'Payment_Processing'         2                        2       
                ###  'Payment_Processing'         3                        3         
                ###  'Payment_Processing'         4                        4  
                ###  'Expropriation_Case'         1                        5  
                ###  'Expropriation_Case'         2                        6  
                ###  'Expropriation_Case'         3                        7  
                ###  'Expropriation_Case'         4                        8  
                ###  'Expropriation_Case'         5                        9  
                ###  'Expropriation_Case'         6                        10  
                ###  'Expropriation_Case'         7                        11  

                mpr_status12_update(env_table, steps_otb, old_mpr_fields[2])
                mpr_status12_update(env_table, steps_ppe, old_mpr_fields[3])
                
                keep_fields = [join_field] + steps_otb + steps_ppe + old_mpr_fields[:4]
                env_table = env_table[keep_fields]

                env_table = rename_columns_title(env_table, 'Preparation', old_mpr_fields[4])
                env_table = rename_columns_title(env_table, 'Delivered', old_mpr_fields[5])
                env_table = rename_columns_title(env_table, 'Payment', old_mpr_fields[6])
                env_table = rename_columns_title(env_table, 'Expropriation', old_mpr_fields[7])

                # merge to original
                gis_table_updated = pd.merge(left=gis_table, right=env_table, how='left', left_on=join_field, right_on=join_field)
                arcpy.AddMessage('Merging MPR to GIS table was successful.')
                arcpy.AddMessage(".\n")

                ## Export to excel
                export_file_name = os.path.splitext(os.path.basename(gis_lot_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                gis_table_updated.to_excel(to_excel_file, index=False)

                arcpy.AddMessage('Updated GIS Excel ML is successfully exported.')

            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids as below in Envi table. The Process stopped. Please correct the duplicated rows.')
                
                pass

        MMSP_Land_MPR_Update()

class UpdateStructureExcel(object):
    def __init__(self):
        self.label = "2.0. Update Excel Master List (Structure)"
        self.description = "Update Excel Master List (Structure)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        
        gis_struc_ms = arcpy.Parameter(
            displayName = "GIS Structure Status ML (Excel)",
            name = "GIS Structure Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        env_struc_ms = arcpy.Parameter(
            displayName = "Envi Structure Status ML (Excel)",
            name = "Envi Structure Status ML (Excel)",
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

        params = [gis_dir, gis_struc_ms, env_struc_ms, gis_bakcup_dir, lastupdate]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_struc_ms = params[1].valueAsText
        env_struc_ms = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        def MMSP_Structure_Update():
            def whitespace_removal(dataframe, field):
                try:
                    dataframe[field] = dataframe[field].apply(lambda x: x.strip())
                except:
                    pass

            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)

            def rename_columns_title(table, search_names, renamed_word): # one by one
                colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
                try:
                    table = table.rename(columns={str(colname_change[0]): renamed_word})
                except:
                    pass
                return table
            
            def check_matches_list_and_merge(target_table, input_table, join_field):
                id1 =  unique(target_table[join_field])
                id2 = unique(input_table[join_field])
                    
                target_table_miss = [f for f in id1 if f not in id2]
                input_table_miss = [f for f in id2 if f not in id1]

                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in Envi Excel MasterList: {}'.format(target_table_miss))
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in GIS MasterList: {}'.format(input_table_miss))

                #arcpy.AddMessage('{} matches between the tables. The two tables are joined'.format(join_field))
                table = pd.merge(left=target_table, right=input_table, how='left', left_on=join_field, right_on=join_field)
                return table
            
            # Read as xlsx
            gis_table = pd.read_excel(gis_struc_ms)
            env_table = pd.read_excel(env_struc_ms, keep_default_na=False)

            # Join Field
            join_field = 'Id'

            # Create bakcup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + "GIS_Structure_MasterList.xlsx"),index=False)
            except:
                pass
            
            # if there are duplicated observations in Envi's table, stop the process and exit
            duplicated_Ids = env_table[env_table.duplicated([join_field]) == True][join_field]

            if len(duplicated_Ids) == 0:
                #### 0. Remove white space from join field           
                whitespace_removal(gis_table, join_field)
                whitespace_removal(env_table, join_field)

                #### 2. Env. table (input table)
                ind_id = [e for e in env_table.columns.str.contains('^Id$',regex=True)].index(True)
                ind_status = [e for e in env_table.columns.str.contains('^Status$',regex=True)].index(True)
                ind_remark = [e for e in env_table.columns.str.contains('^Cleared/.*',regex=True)].index(True)
                inds = [ind_id] + [ind_status] + [ind_remark]
                env_table = env_table.iloc[:, inds]

                env_table = rename_columns_title(env_table, 'Cleared/Demolished', 'REMARKS')
                arcpy.AddMessage(env_table.columns)
    
                new_fields = ['Status', 'REMARKS']

                ### GIS table
                gis_table_new = gis_table.drop(columns = new_fields)

                ### Merge
                gis_table_new = check_matches_list_and_merge(gis_table_new, env_table, join_field)

                ## Export to excel
                export_file_name = os.path.splitext(os.path.basename(gis_struc_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                gis_table_new.to_excel(to_excel_file, index=False)
            
            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids as below in Envi table. The Process stopped. Please correct the duplicated rows.')
                
                pass

        MMSP_Structure_Update()

class UpdateISFExcel(object):
    def __init__(self):
        self.label = "3.0. Update Excel Master List (ISF)"
        self.description = "Update Excel Master List (ISF)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        
        gis_isf_ms = arcpy.Parameter(
            displayName = "GIS ISF Status ML (Excel)",
            name = "GIS ISF Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        env_isf_ms = arcpy.Parameter(
            displayName = "Envi ISF Status ML (Excel)",
            name = "Envi ISF Status ML (Excel)",
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

        params = [gis_dir, gis_isf_ms, env_isf_ms, gis_bakcup_dir, lastupdate]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_isf_ms = params[1].valueAsText
        env_isf_ms = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        def MMSP_ISF_Update():
            def whitespace_removal(dataframe, field):
                try:
                    dataframe[field] = dataframe[field].apply(lambda x: x.strip())
                except:
                    pass

            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)

            def rename_columns_title(table, search_names, renamed_word): # one by one
                colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
                try:
                    table = table.rename(columns={str(colname_change[0]): renamed_word})
                except:
                    pass
                return table
            
            def check_matches_list_and_merge(target_table, input_table, join_field):
                id1 =  unique(target_table[join_field])
                id2 = unique(input_table[join_field])
                    
                target_table_miss = [f for f in id1 if f not in id2]
                input_table_miss = [f for f in id2 if f not in id1]

                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in Envi Excel MasterList: {}'.format(target_table_miss))
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('Missing in GIS MasterList: {}'.format(input_table_miss))

                #arcpy.AddMessage('{} matches between the tables. The two tables are joined'.format(join_field))
                table = pd.merge(left=target_table, right=input_table, how='left', left_on=join_field, right_on=join_field)
                return table
            
            
            # Read as xlsx
            gis_table = pd.read_excel(gis_isf_ms)
            env_table = pd.read_excel(env_isf_ms, keep_default_na=False)

            # Join Field
            join_field = 'Id'

            # Create bakcup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + "GIS_ISF_MasterList.xlsx"),index=False)
            except:
                pass

            # if there are duplicated observations in Envi's table, stop the process and exit
            duplicated_Ids = env_table[env_table.duplicated([join_field]) == True][join_field]

            if len(duplicated_Ids) == 0:
                #### 0. Remove white space from join field            
                whitespace_removal(gis_table, join_field)
                whitespace_removal(env_table, join_field)

                #### 2. Env. table (input table)
                ind_id = [e for e in env_table.columns.str.contains('^Id$',regex=True)].index(True)
                ind_relo = [e for e in env_table.columns.str.contains('^RELOC_.*$',regex=True)].index(True)
                ind_date = [e for e in env_table.columns.str.contains('^DATE_.*',regex=True)].index(True)
                ind_remark = [e for e in env_table.columns.str.contains('^REMARKS$',regex=True)].index(True)
                ind_pwd = [e for e in env_table.columns.str.contains('^PWD$',regex=True)].index(True)

                inds = [ind_id] + [ind_relo] + [ind_date] + [ind_remark] + [ind_pwd]
                env_table = env_table.iloc[:, inds]

                env_table = rename_columns_title(env_table, 'RELOC_STATUS', 'RELOCATION')
    
                new_fields = ['RELOCATION', 'DATE_RELOC', 'PWD', 'REMARKS']

                ### GIS table
                gis_table_new = gis_table.drop(columns = new_fields)

                ### Merge
                gis_table_new = check_matches_list_and_merge(gis_table_new, env_table, join_field)

                ### Fix date
                date_field = 'DATE_RELOC'
                gis_table_new[date_field] = pd.to_datetime(gis_table_new[date_field],errors='coerce').dt.date

                ## Export to excel
                export_file_name = os.path.splitext(os.path.basename(gis_isf_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                gis_table_new.to_excel(to_excel_file, index=False)

            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids as below in Envi table. The Process stopped. Please correct the duplicated rows.')
                
                pass
            
        MMSP_ISF_Update()

class UpdateGISLayers(object):
    def __init__(self):
        self.label = "4.0. Update GIS Attribute Tables"
        self.description = "Update feature layer for land acquisition"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_layer = arcpy.Parameter(
            displayName = "GIS Feature Layer (Target Layer)",
            name = "GIS Feature Layer (Target Layer)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Excel master list tables
        input_table = arcpy.Parameter(
            displayName = "GIS Excel MasterList (Input Table)",
            name = "GIS Excel MasterList (LoInput Tablet)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Excel master list tables
        join_field = arcpy.Parameter(
            displayName = "Join Field",
            name = "Join Field",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        join_field.parameterDependencies = [gis_layer.name]

        params = [gis_dir, gis_layer, input_table, join_field]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_portal = params[1].valueAsText
        gis_ml = params[2].valueAsText
        join_field = params[3].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        arcpy.env.overwriteOutput = True

        # For updating layer
        arcpy.AddMessage('Updating Lot status has started..')
        # 1. Copy Original Feature Layers
        copied_name = 'LA_Temp'               
        gis_copied = arcpy.CopyFeatures_management(gis_portal, copied_name)
            
        arcpy.AddMessage("Step 1: Copy feature layer was success")
                
        # 2. Delete Field
        gis_fields = [f.name for f in arcpy.ListFields(gis_copied)]
            
        ## 2.1. Identify fields to be dropped
        gis_drop_fields_check = [e for e in gis_fields if e not in (join_field,'Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
        ## 2.3. Check if there are fields to be dropped
        gis_drop_fields = [f for f in gis_fields if f in tuple(gis_drop_fields_check)]
            
        arcpy.AddMessage("Step 2: Checking for Fields to be dropped was success")
            
        ## 2.4 Drop
        if len(gis_drop_fields) == 0:
            arcpy.AddMessage("There is no field that can be dropped from the feature layer")
        else:
            arcpy.DeleteField_management(gis_copied, gis_drop_fields)
                
        arcpy.AddMessage("Step 3: Dropping Fields was success")

        # 3. Join Field
        ## 3.1. Convert Excel tables to feature table
        lot_ml = arcpy.conversion.ExportTable(gis_ml, 'lot_ml')

        # Check if LotID match between ML and GIS
        lotid_gis = unique_values(gis_copied, join_field)
        lotid_ml = unique_values(lot_ml, join_field)
        
        lotid_miss_ml = [e for e in lotid_gis if e not in lotid_ml]
        lotid_miss_gis = [e for e in lotid_ml if e not in lotid_gis]

        if lotid_miss_ml or lotid_miss_gis:
            arcpy.AddMessage(".\n")
            arcpy.AddMessage('The following Lot IDs do not match between GIS Excel ML and GIS Portal.')
            arcpy.AddMessage('Missing LotIDs in GIS Excel ML: {}'.format(lotid_miss_ml))
            arcpy.AddMessage(".\n")
            arcpy.AddMessage('Missing LotIDs in GIS Portal: {}'.format(lotid_miss_gis))
            
        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        lot_ml_fields = [f.name for f in arcpy.ListFields(lot_ml)]
        lot_ml_transfer_fields = [e for e in lot_ml_fields if e not in (join_field,'OBJECTID')]
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        #gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in join_field]))                      
        #lot_ml_join_field =' '.join(map(str, [f for f in lot_ml_fields if f in join_field]))
            
        ## 3.4 Join
        arcpy.JoinField_management(in_data=gis_copied, in_field=join_field, join_table=lot_ml, join_field=join_field, fields=lot_ml_transfer_fields)

        # 4. Trucnate
        arcpy.TruncateTable_management(gis_portal)

        # 5. Append
        arcpy.Append_management(gis_copied, gis_portal, schema_type = 'NO_TEST')

        # Delete the copied feature layer
        deleteTempLayers = [gis_copied, lot_ml]
        arcpy.Delete_management(deleteTempLayers)

        # Export the updated GIS portal to excel sheet for checking lot IDs
        arcpy.conversion.TableToExcel(gis_portal, os.path.join(gis_dir, 'GIS_Land_Portal.xlsx'))

class CheckLotUpdatedStatusGIS(object):
    def __init__(self):
        self.label = "4.1. Summary Stats for Lot Status (GIS Portal and GIS ML)"
        self.description = "Summary Stats for Lot Status (GIS Portal and GIS ML)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_layer = arcpy.Parameter(
            displayName = "GIS Portal File (Excel)",
            name = "GIS Portal File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "GIS ML File (Excel)",
            name = "GIS ML File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_dir, gis_layer, gis_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_layer = params[1].valueAsText
        gis_ml = params[2].valueAsText

        # Read table
        gis_table = pd.read_excel(gis_ml)
        gis_portal = pd.read_excel(gis_layer)

        # 0. Defin field names
        nvs3_field_gis = 'StatusNVS3'

        ## Operations Level Status
        hl_field = 'H_Level'
        la_field = 'LA'
        la2_field = 'LA2'
        pp_field = 'PP'
        expro_field = 'Expro'
        rowua_field = "ROWUA"

        package_field = 'Package'
        station_field = 'Station1'
        type_field = 'Type'
        count_name = 'counts'
        lsuffix_portal = '_Portal'
        rsuffix_excel = '_Excel'
        counts_portal = count_name + lsuffix_portal
        counts_excel = count_name + rsuffix_excel

        to_excel_file = os.path.join(gis_dir,'CHECK-LA_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx')

        #####################
        #### Main Status ####
        #####################
        keep_fields = [package_field,station_field,type_field,nvs3_field_gis]

        ## GIS Portal
        nvs3_gis_portal = gis_portal.groupby(keep_fields)[nvs3_field_gis].count().reset_index(name=count_name)
        nvs3_gis_portal = nvs3_gis_portal.sort_values(by=[package_field,station_field,type_field])

        ## GIS ML
        nvs3_gis_ml = gis_table.groupby(keep_fields)[nvs3_field_gis].count().reset_index(name=count_name)
        nvs3_gis_ml = nvs3_gis_ml.sort_values(by=[package_field,station_field,type_field])

        ## Merge
        table_nvs3 = pd.merge(left=nvs3_gis_portal, right=nvs3_gis_ml, how='outer',
                              left_on=[package_field,station_field,type_field,nvs3_field_gis],
                              right_on=[package_field,station_field,type_field,nvs3_field_gis])
        # table_nvs3 = nvs3_gis_portal.join(nvs3_gis_ml,lsuffix=lsuffix_portal,rsuffix=rsuffix_excel)
        table_nvs3['count_diff'] = np.NAN
        table_nvs3['count_diff'] = table_nvs3['counts_y'] - table_nvs3['counts_x']
        table_nvs3 = table_nvs3.rename(columns={"counts_x": str(counts_portal), "counts_y": str(counts_excel)})

        arcpy.AddMessage('Merge completed..')
        arcpy.AddMessage('The summary statistics table for StatusNVS3 field is successfully produced.')

        ##########################
        #### Operations Level ####
        ##########################
        status_fields_ol = [hl_field, la_field, la2_field, pp_field, expro_field, rowua_field]
        data_store = {}
        n_step = -1

        for field in status_fields_ol:
            keep_fields = [package_field,station_field,type_field,field]
            n_step = n_step + 1
            
            # 1. GIS Portal
            gis_p = gis_portal.groupby(keep_fields)[field].count().reset_index(name=count_name)
            gis_p = gis_p.sort_values(by=[package_field,station_field,type_field])
            
            # 2. GIS ML
            gis_ml = gis_table.groupby(keep_fields)[field].count().reset_index(name=count_name)
            gis_ml = gis_ml.sort_values(by=[package_field,station_field,type_field])

            # Merge
            table_ol = pd.merge(left=gis_p, right=gis_ml, how='outer',
                                left_on=[package_field,station_field,type_field,field],
                                right_on=[package_field,station_field,type_field,field])
            # table_nvs3 = nvs3_gis_portal.join(nvs3_gis_ml,lsuffix=lsuffix_portal,rsuffix=rsuffix_excel)
            table_ol['count_diff'] = np.NAN
            table_ol['count_diff'] = table_ol['counts_y'] - table_ol['counts_x']
            table_ol = table_ol.rename(columns={"counts_x": str(counts_portal), "counts_y": str(counts_excel)})
            
            # store data
            data_store[n_step] = table_ol
            arcpy.AddMessage("The summary statistics for '{}' is successfully produced..".format(field))
            
        # Compile and Export
        arcpy.AddMessage("Compile all summary statistics for StatusNVS3 and Operation Level status..")
        with pd.ExcelWriter(to_excel_file) as writer:
            table_nvs3.to_excel(writer, sheet_name=nvs3_field_gis, index=False)
            data_store[0].to_excel(writer, sheet_name=status_fields_ol[0], index=False)
            data_store[1].to_excel(writer, sheet_name=status_fields_ol[1], index=False)
            data_store[2].to_excel(writer, sheet_name=status_fields_ol[2], index=False)
            data_store[3].to_excel(writer, sheet_name=status_fields_ol[3], index=False)
            data_store[4].to_excel(writer, sheet_name=status_fields_ol[4], index=False)

        arcpy.AddMessage('The compilation is successful and the table is exported to your directory..')
  
class CheckMissingLotIDs(object):
    def __init__(self):
        self.label = "4.2. Check Missing Lot IDs (Envi. ML, GIS ML, and GIS Portal)"
        self.description = "Check Missing Lot IDs (Envi. ML, GIS ML, and GIS Portal)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_table_ml = arcpy.Parameter(
            displayName = "GIS ML (Excel)",
            name = "GIS ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_portal_ml = arcpy.Parameter(
            displayName = "GIS Portal (Excel)",
            name = "GIS Portal (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        envi_table_ml = arcpy.Parameter(
            displayName = "Envi ML (Excel)",
            name = "Envi ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_dir, gis_table_ml, gis_portal_ml, envi_table_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_table_ml = params[1].valueAsText
        gis_portal_ml = params[2].valueAsText
        env_table_ml = params[3].valueAsText

        def drop_empty_rows(table, field):
            id = table.index[(table[field] == '') | (table[field].isna()) | (table[field].isnull())] # Do not use isna() as 'keep_default_na = False'
            table = table.drop(id)
            table = table.reset_index(drop=True)
            return table

        def rename_columns_title(table, search_names, renamed_word): # one by one
            colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
            try:
                table = table.rename(columns={str(colname_change[0]): renamed_word})
            except:
                pass
            return table
        
        def unique(lists):
            collect = []
            unique_list = pd.Series(lists).drop_duplicates().tolist()
            for x in unique_list:
                collect.append(x)
            return(collect)
        
        env_table = pd.read_excel(env_table_ml, skiprows=1, keep_default_na=False) # for checking NVS3, do not use default_na = false
        gis_table = pd.read_excel(gis_table_ml)
        gis_portal = pd.read_excel(gis_portal_ml)

        join_field = 'Id'
        env_status_field = 'Status NVS'
        env_status_new_field = 'Envi_Status'
        package_field = 'Package'
        package_x_field = 'Package_x'
        package_y_field = 'Package_y'
        env_field = 'Env_ML'
        gis_field = 'GIS_ML'
        gis_portal_field = 'GIS_Portal'
        need_to_check_field = 'Need_to_Check'

        try:
            env_table = drop_empty_rows(env_table, join_field)
        except:
            pass

        ## Drop fields
        bool_list = [e for e in env_table.columns.str.contains(r'Id|Package|Status NVS',regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        env_table = env_table.iloc[:, ind_id]

        bool_list = [e for e in gis_table.columns.str.contains(r'Id|Package',regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_table = gis_table.iloc[:, ind_id]

        bool_list = [e for e in gis_portal.columns.str.contains(r'Id|Package',regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_portal = gis_portal.iloc[:, ind_id]

        ## Filter
        env_lot_ids = unique(env_table[join_field])
        gis_lot_ids = unique(gis_table[join_field])
        gis_portal_lot_ids = unique(gis_portal[join_field])

        env_gis_no_ids = [e for e in env_lot_ids if e not in gis_lot_ids]
        env_gis_portal_no_ids = [e for e in env_lot_ids if e not in gis_portal_lot_ids]

        ## compare env_gis_no_ids with env_gis_portal_no_ids
        ## Lot ids not commonly observed between these two table => 'GIS ML' = 1
        gis_add_lot_ids = [e for e in env_gis_portal_no_ids if e not in env_gis_no_ids]

        ###
        gis_no_ids = env_table[env_table[join_field].isin(env_gis_no_ids)]
        gis_no_ids[gis_field] = 'No'

        gis_portal_no_ids = env_table[env_table[join_field].isin(env_gis_portal_no_ids)]
        gis_portal_no_ids[gis_portal_field] = 'No'

        ## Concatenate two tables (rbind)
        dataframes = [gis_no_ids,gis_portal_no_ids]
        table = pd.concat(dataframes)
        table = table.reset_index(drop=True)
        duplicated_ids = table.index[table.duplicated([join_field]) == True]
        table = table.drop(duplicated_ids)
        table[gis_portal_field] = 'No'

        ## Update 'GIS_ML' and 'Env_ML'
        id = table.index[table[join_field].isin(gis_add_lot_ids)]
        table.loc[id, gis_field] = 'Yes'
        table[env_field] = 'Yes'

        ## Add check field
        table = rename_columns_title(table, env_status_field, env_status_new_field)
        table[env_status_new_field] = pd.to_numeric(table[env_status_new_field], errors='coerce')
        table['Need_to_Check'] = 'No?'
        id = table.index[table[env_status_new_field].notna()]

        table.loc[id,'Need_to_Check'] = 'Yes'

        ## This table shows lot ids which are missing in either GIS ML or GIS Portal or both.
        ## Check the following lots with Envi Team: lots with status in Envi Table but not reflected in GIS ML or GIS Portal or both.
        file_name = os.path.join(gis_dir, 'CHECK-LA_Missing_Lot_IDs.xlsx')
        table.to_excel(file_name, index=False)

class CopyInputToTargetLayer(object):
    def __init__(self):
        self.label = "4.3. Copy Input Layer to Target Layer (GIS Layers)"
        self.description = "4.3. Copy Input Layer to Target Layer (GIS Layers)"

    def getParameterInfo(self):
        # Input Feature Layers
        input_layer = arcpy.Parameter(
            displayName = "Input Feature Layer",
            name = "Input Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        target_layer = arcpy.Parameter(
            displayName = "Target Feature Layer",
            name = "Target Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [input_layer, target_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        input_layer = params[0].valueAsText
        target_layer = params[1].valueAsText

        # To allow overwriting the outputs change the overwrite option to true.
        arcpy.env.overwriteOutput = True
        
        # 1. Copy the source SDE
        copied = "copied_layer"

        ## 1.1 Check if target_fgdb is 32651 or 3857
        sp_target = arcpy.Describe(target_layer).spatialReference.factoryCode # WKID
        sp_input = arcpy.Describe(input_layer).spatialReference.factoryCode
        
        sp_target_name = arcpy.Describe(target_layer).spatialReference.name
        sp_input_name = arcpy.Describe(input_layer).spatialReference.name

        arcpy.AddMessage('Spatial Reference of Input Layer: {}'.format(sp_input_name))
        arcpy.AddMessage('Spatial Reference of Target Layer: {}'.format(sp_target_name))

        wgs84_output = "WGS 1984 Web Mercator (auxiliary sphere)"
        prs92_output = "PRS 1992 Philippines Zone III"
        wgs84_utm_output = "WGS 1984 UTM Zone 51N"
        prs92_wgs84_transform = "PRS_1992_To_WGS_1984_1"

        if sp_target == 3857 and sp_input == 3857:
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(wgs84_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(wgs84_output, 'None'))

        elif sp_target == 3857 and sp_input == 32651:
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(wgs84_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(wgs84_output, 'None'))

        elif sp_target == 3857 and sp_input == 3123:
            arcpy.env.geographicTransformations = prs92_wgs84_transform
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(wgs84_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(wgs84_output, prs92_wgs84_transform))

        elif sp_target == 3123 and sp_input == 3857:
            arcpy.env.geographicTransformations = prs92_wgs84_transform
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(prs92_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(prs92_output, prs92_wgs84_transform))
            
        elif sp_target == 3123 and sp_input == 32651:
            arcpy.env.geographicTransformations = prs92_wgs84_transform
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(prs92_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(prs92_output, prs92_wgs84_transform))

        elif sp_target == 3123 and sp_input == 3123:
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(prs92_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(prs92_output, 'None'))

        elif sp_target == 32651 and sp_input == 3857:
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(wgs84_utm_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(wgs84_utm_output, 'None'))

        elif sp_target == 32651 and sp_input == 32651:
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(wgs84_utm_output)
            arcpy.AddMessage('Output Coordinate System: {0}, Geographic Transformation: {1}'.format(wgs84_utm_output, 'None'))
            
        elif sp_target == 32651 and sp_input == 3123:
            arcpy.env.geographicTransformations = prs92_wgs84_transform
            arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(wgs84_utm_output)
            arcpy.AddMessage('Output Coordinate System: {}, Geographic Transformation: {}'.format(wgs84_utm_output, prs92_wgs84_transform))

        copyL = arcpy.CopyFeatures_management(input_layer, copied)
        arcpy.TruncateTable_management(target_layer)
        arcpy.Append_management(copyL, target_layer, schema_type = 'NO_TEST')

        # Delete
        arcpy.Delete_management(copyL)
        arcpy.AddMessage("Delete copied layer is Success")




