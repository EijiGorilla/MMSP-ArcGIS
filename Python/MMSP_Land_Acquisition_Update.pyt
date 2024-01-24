import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl
import numpy as np
import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [UpdateLotExcel, UpdateStructureExcel, UpdateISFExcel, UpdateGISLayers]

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

        env_mpr_ms = arcpy.Parameter(
            displayName = "Envi MPR Status ML (Excel)",
            name = "Envi MPR Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Optional",
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

        params = [gis_dir, gis_lot_ms, env_lot_ms, env_mpr_ms, gis_bakcup_dir, lastupdate]
        return params
    
    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_lot_ms = params[1].valueAsText
        env_lot_ms = params[2].valueAsText
        env_mpr_ms = params[3].valueAsText
        gis_bakcup_dir = params[4].valueAsText
        lastupdate = params[5].valueAsText

        def MMSP_Land_Update():
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
                    table[field] = table[field].astype('float')

            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)
            
            # Read as xlsx
            gis_table = pd.read_excel(gis_lot_ms)
            env_table = pd.read_excel(env_lot_ms, skiprows=1, keep_default_na=False)

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

                # Conver to string
                # to_string_fields = [join_field]
                # toString(gis_table, to_string_fields)
                # toString(env_table, to_string_fields)
                
                #### 1. GIS Table (target table)
                ## The following fields are updated for smart maps from 'PRE Weekly Smart Maps on Land Acquisition' (Env. Team)
                ### Fields from Envi           -> Fields from GIS ###
                ### 'Status NVS'               -> 'StatusNVS3'
                ### 'Handed over to JV'        -> 'HandedOver'
                ### 'Handed_Date'              -> HandOverDate'
                ### 'Mode of Acquisition'      -> 'MOA'
                ### 'PTE'                      -> 'Lots with PTE'
                ### 'Handed over (DOTr to GC)' -> 'Handover2'
                ### 'To be handed over to JV'  -> 'not_yet'
                ### 'H_Level'                  -> 'H_Level'
                ### 'LA'                       -> 'LA'
                ### 'LA2'                      -> 'LA2'
                ### 'PP'                       -> 'PP'
                ### 'Expro'                    -> 'Expro'
                ### 'ROWUA'                    -> 'ROWUA'
                ### 'Remarks                   -> 'Remarks'

                #### 2. Env. table (input table)
                ### 1.1. Land Acquisition 
                ind_id = [e for e in env_table.columns.str.contains('^Id$',regex=True)].index(True)
                ind_status = [e for e in env_table.columns.str.contains('^Status.*NVS$',regex=True)].index(True)
                ind_jv = [e for e in env_table.columns.str.contains('^To be.*to JV$',regex=True)].index(True)
                inds = [ind_id] + [f for f in range(ind_status, ind_jv+1)]
                env_table_la = env_table.iloc[:, inds]
                
                ### 1.2. Operations Level
                ind_first = [e for e in env_table.columns.str.contains('^High.*Level$',regex=True)].index(True)
                ind_last = [e for e in env_table.columns.str.contains('^Remarks$',regex=True)].index(True)
                ind_keep = [f for f in range(ind_first, ind_last+1)]
                keep_fields = [e for e in env_table.columns[ind_keep]]
                transfer_fields = [join_field] + keep_fields
                env_table_ol = env_table[transfer_fields]

                old_fields = [f for f in env_table_ol.columns[1:7]]
                new_fields = ['H_Level', 'LA', 'LA2', 'PP', 'Expro', 'ROWUA', 'Remarks']
                
                status = [
                    # High Level
                    {"Ready for Handover / Handed Over": 1, "Pending Delivery": 2},
                    
                    # Land Acquisition
                    {
                        "On-going validation": 1,
                        "Pending Appraisal": 2,
                        "Pending compilation of documents": 3,
                        "OTB for serving": 4,
                        "Pending OTB reply (within 30 days)": 5,
                        "Pending OTB reply beyond 30 days (uncooperative)": 6,
                        "Pending OTB reply beyond 30 days (cooperative)": 7,
                        "OTB Accepted with Pending Documents from PO or other agencies": 8,
                        "OTB Accepted": 9,
                        "Expropriation": 10,
                        "ROWUA / TUA": 11
                    },
                    
                    # Land Acquisition1
                    {
                        "For Submission to Legal": 1,
                        "Pending Legal Pass": 2,
                        "Ongoing Payment Processing": 3,
                        "Paid": 4,
                        "N/A": 5
                    },
                    
                    # Payment Processing
                    {
                        "For Submission to Budget": 1,
                        "For Signing of ORS, DV and RFPP": 2,
                        "With Budget for Obligation": 3,
                        "With Accounting for CAF Issuance": 4,
                        "For DOTr signing": 5,
                        "For Notarization": 6,
                        "For Submission to CS": 7,
                        "DV with CS": 8,
                        "Paid / Checks Issued": 9,
                        "N/A": 10
                    },
                    
                    # Expro
                    {
                        "With PMO / RRE": 1,
                        "With OSG": 2,
                        "With Court": 3,
                        "Issuance of WOP": 4,
                        "WOP with COT": 5,
                        "N/A": 6
                    },
                    
                    # ROWUA
                    {
                        "On-going finalization": 1,
                        "Signed ROWUA": 2,
                        "N/A": 3
                    }
                    ]
                
                # Update status
                for i in range(len(old_fields)):
                    convert_status_to_numeric(env_table_ol, status[i], old_fields[i], new_fields[i])

                # Filter env_table and include selected fields only
                env_table_ol = env_table_ol[new_fields + [join_field]]

                ## 2.1. Merge land acquisition & operations level sub-tables above
                ### Check for Id match and then join two tables
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('----------: Check Id match between two sub-tables split for Land Acquisition and Operations Level :------------')
                gis_table_new = check_matches_list_and_merge(env_table_la, env_table_ol, join_field)

                ### Join new fiels to existing (i.e., update the original GIS table)
                #### Change field names based on the original gis table
                change_names = ['^Status.*NVS$', '^Handed.*JV$', '^Handed_Date', 'Mode of Acquisition', 'Lot with PTE', '^Handed.*over.*GC[)]$', '^To be handed over to JV', '^Expro4$', '^ROWUA2$']
                new_names = ['StatusNVS3', 'HandedOver', 'HandOverDate', 'MOA', 'PTE', 'Handover2', 'not_yet', 'Expro', 'ROWUA']

                for i in range(len(change_names)):
                    gis_table_new = rename_columns_title(gis_table_new, change_names[i], new_names[i])

                ### Delete field names from the original
                drop_fields = new_names + ['H_Level','LA','LA2','PP','Expro','ROWUA', 'Remarks']
                gis_table = gis_table.drop(columns = drop_fields)

                ### Join fiels from new table to original GIS table
                gis_table_updated = pd.merge(left=gis_table, right=gis_table_new, how='left', left_on=join_field, right_on=join_field)

                ### Fix date
                date_fields = ['Target_Date', 'HandOverDate']
                for date in date_fields:
                    gis_table_updated[date] = pd.to_datetime(gis_table_updated[date],errors='coerce').dt.date

                ### Process MPR if selected,
                try:
                    mpr_table = pd.read_excel(env_mpr_ms, keep_default_na=False)

                    ## The following fields are updated in GIS table for MPR from Env. Team
                    ### Fields from Envi           -> Fields from GIS ###
                    ### 'OTB Preparation'          -> 'OtB_Preparation'
                    ### 'Payment Processing'       -> 'Payment_Processing'
                    ### 'Expropriation'            -> 'Expropriation_Case'
                    ###
                    arcpy.AddMessage('Processing MPR data started:')

                    ## MPR Update
                    old_mpr_fields = ['stepName1', 'stepName2', 'Status1', 'Status2', 'OtB_Preparation', 'OtB_Delivered', 'Payment_Processing', 'Expropriation_Case']
                    gis_table_updated = gis_table_updated.drop(columns = old_mpr_fields)

                    ## stepName1 and stepName2            
                    steps_otb = ['OTB Preparation', 'OTB Delivered']
                    toNumeric(mpr_table, steps_otb)
                    mpr_update_stepname(mpr_table, steps_otb, old_mpr_fields[0])

                    steps_ppe =  ['Payment Processing', 'Expropriation']
                    toNumeric(mpr_table, steps_ppe)
                    mpr_update_stepname(mpr_table, steps_ppe, old_mpr_fields[1])
                    
                    ## status1 and status2
                    mpr_status12_update(mpr_table, steps_otb, old_mpr_fields[2])
                    mpr_status12_update(mpr_table, steps_ppe, old_mpr_fields[3])
                    
                    keep_fields = [join_field] + steps_otb + steps_ppe + old_mpr_fields[:4]
                    mpr_table = mpr_table[keep_fields]
                    
                    mpr_table = rename_columns_title(mpr_table, 'Preparation', old_mpr_fields[4])
                    mpr_table = rename_columns_title(mpr_table, 'Delivered', old_mpr_fields[5])
                    mpr_table = rename_columns_title(mpr_table, 'Payment', old_mpr_fields[6])
                    mpr_table = rename_columns_title(mpr_table, 'Expropriation', old_mpr_fields[7])

                    # merge to original
                    gis_table_updated = pd.merge(left=gis_table_updated, right=mpr_table, how='left', left_on=join_field, right_on=join_field)
                except:
                    pass

                ## Check Id match again between updated GIS excel table and Envi land acquisition table
                arcpy.AddMessage(".\n")
                arcpy.AddMessage('----------: Check Id match between updated GIS table and Envi Land Acquisition table :----------')
                check_field_match(gis_table_updated, env_table, join_field)
            
                # to_string_fields = [join_field]
                toString(gis_table_updated, ['CN'])

                ## Export to excel
                export_file_name = os.path.splitext(os.path.basename(gis_lot_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                gis_table_updated.to_excel(to_excel_file, index=False)

                ## Print unmatched number of StatusNVS3 between GIS tables and Envi table
                df = gis_table_updated.groupby(['Package', 'Station1', 'StatusNVS3'],as_index=False).agg(lambda x: len(x))
                df = df.iloc[:,1:4]
                df = rename_columns_title(df,df.columns[2],'count_gis')
                
                id=[e for e in env_table.columns.str.contains('^Package.*',regex=True)].index(True)
                env_table = rename_columns_title(env_table, env_table.columns[id], 'Package1') # rename to remove redundance space for 'Package'
                df1 = env_table.groupby(['Package1', 'STATION', 'Status NVS'],as_index=False).agg(lambda x: len(x))
                df1 = df1.iloc[:,1:4]
                df1 = rename_columns_title(df1,df1.columns[2],'count_env')

                merged = pd.merge(left=df, right=df1, how='left', left_on=['Station1', 'StatusNVS3'], right_on=['STATION', 'Status NVS'])
                merged['Diff'] = merged['count_gis'] - merged['count_env']
                diff = merged.loc[merged['Diff'] != 0]

                arcpy.AddMessage(".\n")
                arcpy.AddMessage('--------: Unmatched Numbers for StatusNVS3 between GIS Excel masterlist and Envi masterlist : ---------- ')
                arcpy.AddMessage(diff)

                
                ### The following fields are updated for Issue used in smart maps from ??? (Env. Team)
                ### Fields from Envi           -> Fields from GIS ###
                ### '?'                        -> 'Issue'
            
            else:
                arcpy.AddMessage('There are duplicated Ids as below in Envi table. The Process stopped. Please correct the duplicated rows.')
                arcpy.AddMessage(duplicated_Ids)
                pass

        MMSP_Land_Update()

class UpdateStructureExcel(object):
    def __init__(self):
        self.label = "1.2. Update Excel Master List (Structure)"
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
                arcpy.AddMessage('There are duplicated Ids as below in Envi table. The Process stopped. Please correct the duplicated rows.')
                arcpy.AddMessage(duplicated_Ids)
                pass

        MMSP_Structure_Update()

class UpdateISFExcel(object):
    def __init__(self):
        self.label = "1.3. Update Excel Master List (ISF)"
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
                arcpy.AddMessage('There are duplicated Ids as below in Envi table. The Process stopped. Please correct the duplicated rows.')
                arcpy.AddMessage(duplicated_Ids)
                pass
            
        MMSP_ISF_Update()

class UpdateGISLayers(object):
    def __init__(self):
        self.label = "2.1. Update GIS Attribute Tables"
        self.description = "Update feature layer for land acquisition"

    def getParameterInfo(self):
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
            displayName = "Excel MasterList (Input Table)",
            name = "Excel MasterList (LoInput Tablet)",
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

        params = [gis_layer, input_table, join_field]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inLot = params[0].valueAsText
        mlLot = params[1].valueAsText
        join_field = params[2].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        arcpy.env.overwriteOutput = True

        # For updating layer
        arcpy.AddMessage('Updating Lot status has started..')
        # 1. Copy Original Feature Layers
        copied_name = 'LA_Temp'               
        gis_copied = arcpy.CopyFeatures_management(inLot, copied_name)
            
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
        lot_ml = arcpy.conversion.ExportTable(mlLot, 'lot_ml')

        # Check if LotID match between ML and GIS
        lotid_gis = unique_values(gis_copied, join_field)
        lotid_ml = unique_values(lot_ml, join_field)
        
        lotid_miss_gis = [e for e in lotid_gis if e not in lotid_ml]
        lotid_miss_ml = [e for e in lotid_ml if e not in lotid_gis]

        if lotid_miss_ml or lotid_miss_gis:
            arcpy.AddMessage(".\n")
            arcpy.AddMessage('The following Lot IDs do not match between ML and GIS.')
            arcpy.AddMessage(".\n")
            arcpy.AddMessage('Missing LotIDs in GIS table: {}'.format(lotid_miss_gis))
            arcpy.AddMessage(".\n")
            arcpy.AddMessage('Missing LotIDs in ML Excel table: {}'.format(lotid_miss_ml))
            
        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        lot_ml_fields = [f.name for f in arcpy.ListFields(lot_ml)]
        lot_ml_transfer_fields = [e for e in lot_ml_fields if e not in (join_field,'OBJECTID')]
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        #gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in join_field]))                      
        #lot_ml_join_field =' '.join(map(str, [f for f in lot_ml_fields if f in join_field]))
            
        ## 3.4 Join
        arcpy.JoinField_management(in_data=gis_copied, in_field=join_field, join_table=lot_ml, join_field=join_field, fields=lot_ml_transfer_fields)

        # 4. Trucnate
        arcpy.TruncateTable_management(inLot)

        # 5. Append
        arcpy.Append_management(gis_copied, inLot, schema_type = 'NO_TEST')

        # Delete the copied feature layer
        deleteTempLayers = [gis_copied, lot_ml]
        arcpy.Delete_management(deleteTempLayers)
