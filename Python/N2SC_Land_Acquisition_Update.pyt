import arcpy
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [RestoreScaleForLot, JustMessage1, UpdateLot, UpdateISF, UpdateStructure, UpdateBarangay,
                      JustMessage10, N2UpdateWorkablePierLandTable, N2UpdateWorkablePierStructureTable, SCUpdateWorkablePierLandTable, SCUpdateWorkablePierStructureTable,
                      JustMessage2, UpdateLotGIS, UpdateStructureGIS, UpdateBarangayGIS,
                      JustMessage3, CheckLotUpdatedStatusGIS, CheckStructureUpdatedStatusGIS, CheckIsfUpdatedStatusGIS,
                      JustMessage4, CheckMissingLotIDs, CheckMissingStructureIDs, CheckMissingIsfIDs
                      ]

class RestoreScaleForLot(object):
    def __init__(self):
        self.label = "0.0. Add Scale To GIS Excel ML (Lot)"
        self.description = "Add Scale To GIS Excel ML (Lot)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_lot_ms = arcpy.Parameter(
            displayName = "Input GIS Land ML (Excel)",
            name = "Input GIS Land ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        target_lot_ms = arcpy.Parameter(
            displayName = "Target GIS Land ML (Excel)",
            name = "Target GIS Land ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_dir, input_lot_ms, target_lot_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        input_lot_ms = params[1].valueAsText
        target_lot_ms = params[2].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def N2SC_Restore_Scale():           
            input_table = pd.read_excel(input_lot_ms)
            target_table = pd.read_excel(target_lot_ms)

            joinField = 'LotID'

            # Convert to numeric
            transfer_field = "Scale"

            target_table.head()
            # remove all spaces if any
            target_table[transfer_field] = target_table[transfer_field].replace(r'\s+|[^\w\s]', '', regex=True)
            target_table[transfer_field] = pd.to_numeric(target_table[transfer_field])

            # Add scale from old master list
            target_table = target_table.drop(transfer_field,axis=1)
            lot_scale = input_table[[transfer_field, joinField]]
            target_table_new = pd.merge(left=target_table, right=lot_scale, how='left', left_on=joinField, right_on=joinField)

            export_file_name = os.path.splitext(os.path.basename(target_lot_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            target_table_new.to_excel(to_excel_file, index=False)

        N2SC_Restore_Scale()

class JustMessage1(object):
    def __init__(self):
        self.label = "1.0. ----- Update Excel Master List -----"
        self.description = "Update Excel Master List"

class UpdateLot(object):
    def __init__(self):
        self.label = "1.1. Update Excel Master List (Lot)"
        self.description = "Update Excel Master List (Lot)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']

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

        rap_lot_ms = arcpy.Parameter(
            displayName = "RAP Land Status ML (Excel)",
            name = "RAP Land Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_lot_sc1_ms = arcpy.Parameter(
            displayName = "RAP SC1 Land Status ML for SC (SC ONLY)",
            name = "RAP SC1 Land Status for SC",
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

        params = [proj, gis_dir, gis_lot_ms, rap_lot_ms, rap_lot_sc1_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_lot_ms = params[2].valueAsText
        rap_lot_ms = params[3].valueAsText
        rap_lot_sc1_ms = params[4].valueAsText
        gis_bakcup_dir = params[5].valueAsText
        lastupdate = params[6].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def N2SC_Land_Update():
            # Definitions
            if proj == 'N2':
                cp_suffix = 'N-'
            else:
                cp_suffix = 'S-'

            ## 2. Return unique values
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            ## 3. Return non-matched values between two lists
            def non_match_elements(list_a, list_b):
                non_match = []
                for i in list_a:
                    if i not in list_b:
                        non_match.append(i)
                return non_match
            
            def toString(table, to_string_fields):
                for field in to_string_fields:
                    table[field] = table[field].astype(str)
                    table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
                return table

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].str.title()
                return table
            
            # Read as xlsx
            rap_table_stats = pd.read_excel(rap_lot_ms)
            rap_table = pd.read_excel(rap_lot_ms)
            gis_table = pd.read_excel(gis_lot_ms)

            # Join Field & Define all fields
            joinField = 'LotID'
            rap_citymuni_field = 'City/Municipality'
            rap_city_field = 'City'
            rap_muni_field = 'Munici'
            rap_sc1_contsub = 'ContSubm'
            rap_sc1_subcon = 'Subcon'
            rap_sc1_priority1 = 'Priority1'
            rap_sc1_new_priority = 'Priority1_1'
            rap_sc1_reqs = 'Reqs'

            package_field = 'CP'
            land_use_field = 'LandUse'
            endorsed_field = 'Endorsed'
            total_area_field = 'TotalArea'
            affected_area_field = 'AffectedArea'
            remaining_area_field = 'RemainingArea'
            handedover_area_field = 'HandedOverArea'
            handedover_field = 'HandedOver'
            handover_date_field = 'HandOverDate'
            target_actual_field = 'TargetActual'
            target_actual_date_field = 'TargetActualDate'
            handedover_date_field = 'HandedOverDate'
            percent_handedover_area_field = 'percentHandedOver'
            priority_field = 'Priority'
            statusla_field = 'StatusLA'
            moa_field = 'MoA'
            pte_field = 'PTE'
            scale_field = 'Scale'
            renamed_city = 'Municipality'

            count_name = 'counts'
            counts_rap = count_name + '_RAP'
            counts_gis = count_name + '_GIS'

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Land_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Land_Status'))

            # If there are duplicated observations in RAP table, stop the process and exit
            duplicated_Ids = rap_table[rap_table.duplicated([joinField]) == True][joinField]

            if len(duplicated_Ids) == 0:
                # Common query and definitions
                search_names_city = [rap_citymuni_field, rap_city_field, rap_muni_field]

            # SC1
                ## Join SC1 Lot to SC
                if proj == 'SC':
                    try:
                        joinedFields = [joinField, rap_sc1_contsub, rap_sc1_subcon, rap_sc1_priority1, rap_sc1_reqs]

                        rap_table_sc1 = pd.read_excel(rap_lot_sc1_ms)
                        
                        # Add contractors submission
                        rap_table_sc1[rap_sc1_contsub] = 1
                        
                        # Rename Municipality
                        colname_change = rap_table.columns[rap_table.columns.str.contains('|'.join(search_names_city))]
                        rap_table = rap_table.rename(columns={str(colname_change[0]): renamed_city})

                        colname_change = rap_table_sc1.columns[rap_table_sc1.columns.str.contains('|'.join(search_names_city))]
                        rap_table_sc1 = rap_table_sc1.rename(columns={str(colname_change[0]): renamed_city})

                        rap_table = first_letter_capital(rap_table, [renamed_city])
                        rap_table = first_letter_capital(rap_table, [renamed_city])

                        # Convert to numeric
                        rap_table_sc1[rap_sc1_priority1] = rap_table_sc1[rap_sc1_priority1].replace(r'\s+|^\w\s$','',regex=True)
                        rap_table_sc1[rap_sc1_priority1] = pd.to_numeric(rap_table_sc1[rap_sc1_priority1])
                            
                        # Create Priority1_1 for web mapping purpose only
                        ## Unique priority values
                        uniques = unique(rap_table_sc1[rap_sc1_priority1].dropna())
                        rap_table_sc1[rap_sc1_new_priority] = None
                        for num in uniques:
                            id = rap_table_sc1.index[rap_table_sc1[rap_sc1_priority1] == num]
                            if num == 2:
                                rap_table_sc1.loc[id, rap_sc1_new_priority] = (str(num) + 'nd').replace('.0','')
                            elif num == 3:
                                rap_table_sc1.loc[id, rap_sc1_new_priority] = (str(num) + 'rd').replace('.0','')
                            else:
                                rap_table_sc1.loc[id, rap_sc1_new_priority] = (str(num) + 'st').replace('.0','')

                        # Filter fields
                        rap_table_sc1 = rap_table_sc1[joinedFields + [rap_sc1_new_priority]]
                        rap_table = rap_table.drop(joinedFields[2:], axis=1)

                        # Left join
                        rap_table[joinField] = rap_table[joinField].astype(str)
                        rap_table_sc1[joinField] = rap_table_sc1[joinField].astype(str)
                        rap_table = pd.merge(left=rap_table, right=rap_table_sc1, how='left', left_on=joinField, right_on=joinField)

                        # Check if any missing LotID when joined
                        id = rap_table.index[rap_table[rap_sc1_contsub] == 1]
                        lotID_sc = unique(rap_table.loc[id,joinField])
                        lotID_sc1 = unique(rap_table_sc1[joinField])
                        non_match_LotID = non_match_elements(lotID_sc, lotID_sc1)
                        if (len(non_match_LotID) > 0):
                            arcpy.AddMessage('LotIDs do not match between SC and SC1 tables.')

                    except Exception:
                        arcpy.AddMessage('You did not select {0} master list for updating contractors submission status.'.format('SC1_Land_Status '))

                # Rename City for Municipality and upper case letter for the first letter
                colname_change = rap_table.columns[rap_table.columns.str.contains('|'.join(search_names_city))]
                rap_table = rap_table.rename(columns={str(colname_change[0]): renamed_city})
                rap_table = first_letter_capital(rap_table, [renamed_city])
                
                # Convert to numeric
                numeric_fields_common = [total_area_field, affected_area_field, remaining_area_field, handedover_area_field, handedover_field, priority_field, statusla_field, moa_field, pte_field]

                if proj == 'N2':
                    to_numeric_fields = numeric_fields_common + [endorsed_field]
                else:
                    to_numeric_fields = numeric_fields_common
                
                cols = rap_table.columns
                non_match_col = non_match_elements(to_numeric_fields, cols)
                [to_numeric_fields.remove(non_match_col[0]) if non_match_col else arcpy.AddMessage('no need to remove field from the list for numeric conversion')]

                for field in to_numeric_fields:
                    # you need to keep [] a set of characters in regex; otherwise, error.
                    rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s$]','',regex=True)
                    rap_table[field] = pd.to_numeric(rap_table[field])

                    rap_table_stats[field] = rap_table_stats[field].replace(r'\s+|[^\w\s$]','',regex=True)
                    rap_table_stats[field] = pd.to_numeric(rap_table_stats[field])
                    
                # Conver to string
                to_string_fields = [joinField, package_field]
                rap_table = toString(rap_table, to_string_fields)
                rap_table_stats = toString(rap_table_stats, to_string_fields)

                # Reformat CP
                # if proj == 'N2':
                if proj == 'N2':
                    rap_table[package_field] = rap_table[package_field].str.replace(r'N','N-',regex=True)

                else:
                    # rap_table[package_field] = rap_table[package_field].str.replace(r'S','S-',regex=True)
                    rap_table[package_field] = rap_table[package_field].replace(r'3A|3A|3a', '3a',regex=True)
                    rap_table[package_field] = rap_table[package_field].replace(r'3B|3B|3b', '3b',regex=True)
                    rap_table[package_field] = rap_table[package_field].replace(r'3C|3C|3c', '3c',regex=True)
                    
                    # Conver the following LotIDs to S-01
                    ## 10155, 10156, 10158-5
                    ids = rap_table.index[rap_table[joinField].str.contains(r'10155|10156|10158-5',regex=True,na=False)]
                    rap_table.loc[ids, package_field] = 'S-01'

                    # Convert the following LotIDs to S-04
                    idx = rap_table.index[rap_table[joinField] == '60136-A']
                    rap_table.loc[idx, package_field] = 'S-04'

                    # Convert the following LotIDs to S-06
                    idx = rap_table.index[rap_table[joinField].str.contains(r'^100003$|^100004$|^100005$|^100010$',regex=True,na=False)]
                    rap_table.loc[idx, package_field] = 'S-06'

                rap_table[package_field] = rap_table[package_field].apply(lambda x: re.sub(r',.*','',x))

                ## for stats
                rap_table_stats[package_field] = rap_table_stats[package_field].replace(r'3A|3A|3a', '3a',regex=True)
                rap_table_stats[package_field] = rap_table_stats[package_field].replace(r'3B|3B|3b', '3b',regex=True)
                rap_table_stats[package_field] = rap_table_stats[package_field].replace(r'3C|3C|3c', '3c',regex=True)
                rap_table_stats[package_field] = rap_table_stats[package_field].apply(lambda x: re.sub(r',.*','',x))
                    
                # Conver to date   
                to_date_fields = [handover_date_field, handedover_date_field]
                for field in to_date_fields:
                    rap_table[field] = pd.to_datetime(rap_table[field],errors='coerce').dt.date
            
                ## Convert to uppercase letters for LandUse
                if proj == 'N2':
                    try:
                        rap_table = first_letter_capital(rap_table, [land_use_field])
                        # [] is a set of caracters, so this removes hypen or underline along with space
                        rap_table[land_use_field] = rap_table[land_use_field].replace(r'\s+|[^\w\s$]','',regex=True)
                    except:
                        pass

                # Add scale from old master list
                rap_table = rap_table.drop(scale_field,axis=1)
                lot_gis_scale = gis_table[[scale_field, joinField]]
                rap_table = pd.merge(left=rap_table, right=lot_gis_scale, how='left', left_on=joinField, right_on=joinField)

                # Check and Fix StatusLA, HandedOverDate, HandOverDate, and HandedOverArea
                ## 1. StatusLA =0 -> StatusLA = empty
                id = rap_table.index[rap_table[statusla_field] == 0]
                rap_table.loc[id, statusla_field] = None

                ## 2. HandedOver = 1 & !is.na(HandOverDate) -> HandedOverDate = HandOverDate
                id = rap_table.index[(rap_table[handedover_field] == 1) & (rap_table[handover_date_field].notna())]
                rap_table.loc[id, handedover_date_field] = rap_table.loc[id, handover_date_field]
                rap_table.loc[id, handover_date_field] = None

                ## 3. HandedOver = 0 & !is.na(HandedOverDate) -> HandedOverDate = empty
                id = rap_table.index[(rap_table[handedover_field] == 0) & (rap_table[handedover_date_field].notna())]
                rap_table.loc[id, handedover_date_field] = None

                ## 4. if the first row is empty, temporarily add the first row for 'HandedOverDate' and 'HandOverDate'
                for field in to_date_fields:
                    date_item = rap_table[field].iloc[:1].item()
                    if date_item is None or pd.isnull(date_item):
                        rap_table.loc[0, field] = pd.to_datetime('1990-01-01')

                ## 5. is.na(HandedOverArea) -> HandedOverArea = 0
                id = rap_table.index[(rap_table[handedover_area_field] == None) | (rap_table[handedover_area_field].isna())]
                rap_table.loc[id, handedover_area_field] = 0

                # Calculate percent handed-over
                rap_table[percent_handedover_area_field] = round((rap_table[handedover_area_field] / rap_table[affected_area_field])*100,0)

                ## 6. Fill HandOverDateTarget (only N2 as of Jan.26, 2025)
                ### For creating cumulative monthly bar chart for target (HandOverDate) and handed-over (HandedOver = 1)
                ### HandOverDateTarget = 1 (HandedOver =  0 & HandOverDate is not null)
                rap_table[target_actual_field] = 0
                rap_table[target_actual_date_field] = ""
                rap_table[target_actual_date_field] = pd.to_datetime(rap_table[target_actual_date_field],errors='coerce').dt.date

                # 'TargetActual':  Target = 1, Actual = 2
                ## Enter for actual
                id = rap_table.index[rap_table[handedover_field] == 1]
                rap_table.loc[id, target_actual_field] = 2
                rap_table.loc[id, target_actual_date_field] = rap_table[handedover_date_field]

                # Enter for target
                id = rap_table.index[(rap_table[handedover_field] == 0) & (rap_table[handover_date_field].notna())]
                rap_table.loc[id, target_actual_field] = 1
                rap_table.loc[id, target_actual_date_field] = rap_table[handover_date_field]

                rap_table[target_actual_date_field] = pd.to_datetime(rap_table[target_actual_date_field],errors='coerce').dt.date

                # Export
                export_file_name = os.path.splitext(os.path.basename(gis_lot_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                rap_table.to_excel(to_excel_file, index=False)

                arcpy.AddMessage("The master list was successfully exported.")

                ##############################################################################
                # Create summary statistics between original rap_table and updated rap_table
                ### 1.0. StatusLA = 0 -> NA          
                ## 1.0.1. Original rap_table (before updating)
                colname_change = rap_table_stats.columns[rap_table_stats.columns.str.contains('|'.join(search_names_city))]
                rap_table_stats = rap_table_stats.rename(columns={str(colname_change[0]): renamed_city})
                rap_table_stats = first_letter_capital(rap_table_stats, [renamed_city])
                
                id = rap_table_stats.index[rap_table_stats[statusla_field] == 0]
                rap_table_stats.loc[id, statusla_field] = np.NAN

                groupby_fields = [renamed_city, statusla_field]
                rap_table0_stats = rap_table_stats.groupby(groupby_fields)[statusla_field].count().reset_index(name=count_name)
                rap_table0_stats = rap_table0_stats.sort_values(by=groupby_fields)

                ## 1.0.2. Updated rap_table (After updating)
                rap_table1_stats = rap_table.groupby(groupby_fields)[statusla_field].count().reset_index(name=count_name)
                rap_table1_stats = rap_table1_stats.sort_values(by=groupby_fields)

                ## 1.0.3. Merge
                # table_stats = rap_table0_stats.join(rap_table1_stats, lsuffix=lsuffix_rap, rsuffix=rsuffix_gis)
                table_stats = pd.merge(left=rap_table0_stats, right=rap_table1_stats, how='outer', left_on=[renamed_city, statusla_field], right_on=[renamed_city, statusla_field])
                table_stats['count_diff'] = np.NAN
                table_stats['count_diff'] = table_stats['counts_y'] - table_stats['counts_x']
                table_stats = table_stats.rename(columns={"counts_x": str(counts_rap), "counts_y": str(counts_gis)})
            
                ### 2.0. HandedOver = 1
                ## 2.0.1. Original rap_table (before updating)
                id = rap_table_stats.index[rap_table_stats[handedover_field] == 1]
                groupby_fields = [renamed_city, handedover_field]
                rap_table0_stats = rap_table_stats.groupby(groupby_fields)[handedover_field].count().reset_index(name=count_name)
                rap_table0_stats = rap_table0_stats.sort_values(by=groupby_fields)

                ## 2.0.2. Updated rap_table (After updating)
                rap_table1_stats = rap_table.groupby(groupby_fields)[handedover_field].count().reset_index(name=count_name)
                rap_table1_stats = rap_table1_stats.sort_values(by=groupby_fields)

                ## 2.0.3. Merge
                # table_stats_handedover = rap_table0_stats.join(rap_table1_stats, lsuffix=lsuffix_rap, rsuffix=rsuffix_gis)
                table_stats_handedover = pd.merge(left=rap_table0_stats, right=rap_table1_stats, how='outer', left_on=[renamed_city, handedover_field], right_on=[renamed_city, handedover_field])
                table_stats_handedover['count_diff'] = np.NAN
                table_stats_handedover["count_diff"] = table_stats_handedover['counts_y'] - table_stats_handedover['counts_x']
                table_stats_handedover = table_stats_handedover.rename(columns={"counts_x": str(counts_rap), "counts_y": str(counts_gis)})

                ### 3.0. Export summary statistics table
                file_name_stats = 'CHECK-' + proj + '_LA_Summary_Statistics_Rap_and_GIS_ML.xlsx'
                to_excel_file0 = os.path.join(gis_dir, file_name_stats)

                with pd.ExcelWriter(to_excel_file0) as writer:
                    table_stats.to_excel(writer, sheet_name=statusla_field, index=False)
                    table_stats_handedover.to_excel(writer, sheet_name=handedover_field, index=False)

            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids in RAP table shown above. The Process stopped. Please correct the duplicated rows.')
                pass

        N2SC_Land_Update()

class UpdateISF(object):
    def __init__(self):
        self.label = "1.2. Update Excel Master List (ISF)"
        self.description = "Update Excel Master List (ISF)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']

        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_isf_ms = arcpy.Parameter(
            displayName = "GIS ISF Relocation Status ML (Excel)",
            name = "GIS ISF Relocation Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_isf_ms = arcpy.Parameter(
            displayName = "RAP ISF Relocation Status ML (Excel)",
            name = "RAP ISF Relocation Status ML (Excel)",
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

        params = [proj, gis_dir, gis_isf_ms, rap_isf_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_isf_ms = params[2].valueAsText
        rap_isf_ms = params[3].valueAsText
        gis_bakcup_dir = params[4].valueAsText
        lastupdate = params[5].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True
        def N2SC_ISF_Update():
            ## 2. Return unique values
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            ## 3. Return non-matched values between two lists
            def non_match_elements(list_a, list_b):
                non_match = []
                for i in list_a:
                    if i not in list_b:
                        non_match.append(i)
                return non_match
            
            def toString(table, to_string_fields):
                for field in to_string_fields:
                    table[field] = table[field].astype(str)
                    table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
                return table

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].str.title()
                return table
            
            ####################################################
            # Update Excel Master List Tables
            ####################################################
            if proj == 'N2':
                cp_suffix = 'N-'
            else:
                cp_suffix = 'S-'
        
            rap_table_stats = pd.read_excel(rap_isf_ms)
            rap_table = pd.read_excel(rap_isf_ms)
            gis_table = pd.read_excel(gis_isf_ms)

            # Field definitions
            municipality_field = 'Municipality'
            barangay_field = 'Barangay'
            structure_id_field = 'StrucID'
            nlo_status_field = 'StatusRC'
            cp_field = 'CP'
            count_name = 'counts'
            counts_rap = count_name + '_RAP'
            counts_gis = count_name + '_GIS'

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_" + "ISF_Relocation_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format('ISF_Relocation_Status'))
            
            # Rename 'City' to Municipality
            try:
                renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['City','city', 'Muni']))]
                rap_table = rap_table.rename(columns={str(renamed_col[0]): municipality_field})
                rap_table = first_letter_capital(rap_table, [municipality_field])

                # For Summary Stats
                renamed_col = rap_table_stats.columns[rap_table_stats.columns.str.contains('|'.join(['City','city', 'Muni']))]
                rap_table_stats = rap_table_stats.rename(columns={str(renamed_col[0]): municipality_field})
                rap_table_stats = first_letter_capital(rap_table_stats, [municipality_field])
            

            except:
                pass

            # Rename Barangay
            try:
                renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['Bara','bara']))]
                rap_table = rap_table.rename(columns={str(renamed_col[0]): barangay_field})
                #first_letter_capital(rap_table, [renamed_brgy])

                # For summary stats
                renamed_col = rap_table_stats.columns[rap_table_stats.columns.str.contains('|'.join(['Bara','bara']))]
                rap_table_stats = rap_table_stats.rename(columns={str(renamed_col[0]): barangay_field})
            except:
                pass

            # force dtypes as string
            to_string_fields = [municipality_field, barangay_field, structure_id_field, cp_field]
            for field in to_string_fields:
                rap_table[field] = rap_table[field].astype(str)
                rap_table_stats[field] = rap_table_stats[field].astype(str)

            # Re-format CP
            rap_table[cp_field] = rap_table[cp_field].replace(r'03A|3A|3a', '03a',regex=True)
            rap_table[cp_field] = rap_table[cp_field].replace(r'03B|3B|3b', '03b',regex=True)
            rap_table[cp_field] = rap_table[cp_field].replace(r'03C|3C|3c', '03c',regex=True)

            rap_table_stats[cp_field] = rap_table_stats[cp_field].replace(r'03A|3A|3a', '03a',regex=True)
            rap_table_stats[cp_field] = rap_table_stats[cp_field].replace(r'03B|3B|3b', '03b',regex=True)
            rap_table_stats[cp_field] = rap_table_stats[cp_field].replace(r'03C|3C|3c', '03c',regex=True)

            ## If Projec is N2
            if proj == 'N2':
                rap_table[cp_field] = rap_table[cp_field].replace(r'N', 'N-',regex=True)
                rap_table_stats[cp_field] = rap_table_stats[cp_field].replace(r'N', 'N-',regex=True)

            # Conver join field (StrucID) to upper case
            rap_table[structure_id_field] = rap_table[structure_id_field].str.upper()

            # Convert to numeric
            to_numeric_fields = [nlo_status_field, "TypeRC", "HandOver"]
            cols = rap_table.columns
            non_match_col = non_match_elements(to_numeric_fields, cols)
            [to_numeric_fields.remove(non_match_col[0]) if non_match_col else print('no need to remove field from the list for numeric conversion')]

            for field in to_numeric_fields:
                rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
                rap_table[field] = pd.to_numeric(rap_table[field])

                # For Summary stats
                rap_table_stats[field] = rap_table_stats[field].replace(r'\s+|[^\w\s]', '', regex=True)
                rap_table_stats[field] = pd.to_numeric(rap_table_stats[field])

            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_isf_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

            ##############################################################################
            # Create summary statistics between original rap_table and updated rap_table
            ### 1.0. StatusRC = 0 -> NA          
            ## 1.0.1. Original rap_table (before updating)
            # For summary stats
            id = rap_table_stats.index[rap_table_stats[nlo_status_field] == 0]
            rap_table_stats.loc[id, nlo_status_field] = np.NAN

            groupby_fields = [municipality_field, nlo_status_field]
            rap_table0_stats = rap_table_stats.groupby(groupby_fields)[nlo_status_field].count().reset_index(name=count_name)
            rap_table0_stats = rap_table0_stats.sort_values(by=groupby_fields)

            ## 1.0.2. Updated rap_table (After updating)
            rap_table1_stats = rap_table.groupby(groupby_fields)[nlo_status_field].count().reset_index(name=count_name)
            rap_table1_stats = rap_table1_stats.sort_values(by=groupby_fields)

            ## 1.0.3. Merge
            # table_stats = rap_table0_stats.join(rap_table1_stats, lsuffix=lsuffix_rap, rsuffix=rsuffix_gis)
            table_stats = pd.merge(left=rap_table0_stats, right=rap_table1_stats, how='outer', left_on=[municipality_field, nlo_status_field], right_on=[municipality_field, nlo_status_field])
            table_stats['count_diff'] = np.NAN
            table_stats['count_diff'] = table_stats['counts_y'] - table_stats['counts_x']
            table_stats = table_stats.rename(columns={"counts_x": str(counts_rap), "counts_y": str(counts_gis)})

            ### 3.0. Export summary statistics table
            file_name_stats = 'CHECK-' + proj + '_ISF_Summary_Statistics_Rap_and_GIS_ML.xlsx'
            to_excel_file0 = os.path.join(gis_dir, file_name_stats)

            table_stats.to_excel(to_excel_file0, index=False)

        N2SC_ISF_Update()

class UpdateStructure(object):
    def __init__(self):
        self.label = "1.3. Update Excel Master List (Structure)"
        self.description = "Update Excel Master List (Structure)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']

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

        rap_struc_ms = arcpy.Parameter(
            displayName = "RAP Structure Status ML (Excel)",
            name = "RAP Structure Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_struc_sc1_ms = arcpy.Parameter(
            displayName = "RAP SC1 Structure Status ML for SC (Excel)",
            name = "RAP SC1 Structure Status for SC (Excel)",
            datatype = "DEFile",
            parameterType = "Optional",
            direction = "Input"
        )

        rap_relo_ms = arcpy.Parameter(
            displayName = "RAP Structure ISF Relocation Status ML (Excel)",
            name = "RAP Structure Relocation Status ML (Excel)",
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

        params = [proj, gis_dir, gis_struc_ms,
                  rap_struc_ms, rap_struc_sc1_ms, rap_relo_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_struc_ms = params[2].valueAsText
        rap_struc_ms = params[3].valueAsText
        rap_struc_sc1_ms = params[4].valueAsText
        rap_relo_ms = params[5].valueAsText
        gis_bakcup_dir = params[6].valueAsText
        lastupdate = params[7].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def N2SC_Structure_Update():
            # Definitions
            if proj == 'N2':
                cp_suffix = 'N-'
            else:
                cp_suffix = 'S-'

            ## 2. Return unique values
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            ## 3. Return non-matched values between two lists
            def non_match_elements(list_a, list_b):
                non_match = []
                for i in list_a:
                    if i not in list_b:
                        non_match.append(i)
                return non_match
            
            ## 4. Return matched elements
            def match_elements(list_a, list_b):
                matched = []
                for i in list_a:
                    if i in list_b:
                        matched.append(i)
                return matched
            
            def toString(table, to_string_fields):
                for field in to_string_fields:
                    table[field] = table[field].astype(str)
                    table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
                return table

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].str.title()
                return table
            
            ####################################################
            # Update Excel Master List Tables
            ####################################################
            rap_table_stats = pd.read_excel(rap_struc_ms)
            rap_table = pd.read_excel(rap_struc_ms)
            rap_relo_table = pd.read_excel(rap_relo_ms)
            gis_table = pd.read_excel(gis_struc_ms)

            # Join Field
            joinField = 'StrucID'
            cp_field = 'CP'
            municipality_field = 'Municipality'
            sc1_contsubm = 'ContSubm'
            sc1_subcon = 'Subcon'
            sc1_basic_plan = 'BasicPlan'

            total_area_field = 'TotalArea'
            affected_area_field = 'AffectedArea'
            remaining_area_field = 'RemainingArea'
            handover_field = 'HandOver'
            structure_status_field = 'StatusStruc'
            landowner_status_field = 'Status'
            moa_field = 'MoA'
            pte_field = 'PTE'
            occupancy_field = 'Occupancy'
            structure_use_field = 'StructureUse'
            family_number_field = 'FamilyNumber'

            count_name = 'counts'
            counts_rap = count_name + '_RAP'
            counts_gis = count_name + '_GIS'

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Structure_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Structure_Status'))
            
            # if there are duplicated observations in Envi's table, stop the process and exit
            duplicated_Ids = rap_table[rap_table.duplicated([joinField]) == True][joinField]

            if len(duplicated_Ids) == 0:
                # Common query and definitions
                search_names_city = ['City/Municipality', 'City', 'Munici']

                # SC
                if proj == 'SC':
                    ## Update SC1_table
                    try:
                        arcpy.AddMessage("ok0")
                        joinedFields = [joinField, sc1_contsubm, sc1_subcon, sc1_basic_plan]

                        arcpy.AddMessage("ok00")
                        rap_table_sc1 = pd.read_excel(rap_struc_sc1_ms)
                        
                        arcpy.AddMessage("ok1")
                        # Add contractors submission
                        rap_table_sc1[sc1_contsubm] = 1

                        # Conver to string with white space removal and uppercase
                        to_string_fields = [joinField]
                        toString(rap_table_sc1, to_string_fields)

                        rap_table[joinField] = rap_table[joinField].apply(lambda x: x.upper())
                        rap_table_sc1[joinField] = rap_table_sc1[joinField].apply(lambda x: x.upper())
                        
                        arcpy.AddMessage("ok4")

                        # Filter fields
                        rap_table_sc1 = rap_table_sc1[joinedFields]
                        rap_table = rap_table.drop(joinedFields[2:], axis=1)
                        
                        arcpy.AddMessage("ok5")

                        # Left join
                        rap_table[joinField] = rap_table[joinField].astype(str)
                        rap_table_sc1[joinField] = rap_table_sc1[joinField].astype(str)
                        rap_table = pd.merge(left=rap_table, right=rap_table_sc1, how='left', left_on=joinField, right_on=joinField)
                    
                        arcpy.AddMessage("ok6")

                        # Check if any missing StrucID when joined
                        id = rap_table.index[rap_table[sc1_contsubm] == 1]
                        lotID_sc = unique(rap_table.loc[id,joinField])
                        lotID_sc1 = unique(rap_table_sc1[joinField])
                        non_match_LotID = non_match_elements(lotID_sc, lotID_sc1)
                        if (len(non_match_LotID) > 0):
                            print('StrucIDs do not match between SC and SC1 tables.')
                        arcpy.AddMessage("ok7")

                    except Exception:
                        arcpy.AddMessage('Did you select {0} master list for updating contractors submission status.'.format('SC1_Structure_Status '))
                        arcpy.AddMessage('Or some geoprocessing process failed. Please check again.')


                # Rename column names
                colname_change = rap_table.columns[rap_table.columns.str.contains('|'.join(search_names_city))]
                rap_table = rap_table.rename(columns={str(colname_change[0]): municipality_field})
                        
                rap_table = first_letter_capital(rap_table, [municipality_field])

                # Convert to numeric DO WE NEED THIS?
                # to_numeric_fields = [total_area_field, affected_area_field, remaining_area_field, handover_field, structure_status_field, landowner_status_field, moa_field, pte_field, occupancy_field]
                # cols = rap_table.columns
                # non_match_col = non_match_elements(to_numeric_fields, cols)
                # [to_numeric_fields.remove(non_match_col[0]) if non_match_col else arcpy.AddMessage('no need to remove field from the list for numeric conversion')]

                # for field in to_numeric_fields:
                #     rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
                #     rap_table[field] = pd.to_numeric(rap_table[field])

                #     # For Summary Stats later
                #     rap_table_stats[field] = rap_table_stats[field].replace(r'\s+|[^\w\s]', '', regex=True)
                #     rap_table_stats[field] = pd.to_numeric(rap_table_stats[field])
                    
                # Conver to string
                common_fields = [joinField, cp_field]
                if proj == 'N2':
                    to_string_fields = common_fields + [structure_use_field]
                else:
                    to_string_fields = common_fields
                for field in to_string_fields:
                    rap_table[field] = rap_table[field].astype(str)
                    rap_table_stats[field] = rap_table_stats[field].astype(str)
                
                if proj == 'N2':
                    rap_table[cp_field] = rap_table[cp_field].replace(r'N', 'N-',regex=True)
                else: ## SC
                    rap_table[cp_field] = rap_table[cp_field].replace(r'03A|3A|3a', '03a',regex=True)
                    rap_table[cp_field] = rap_table[cp_field].replace(r'03B|3B|3b', '03b',regex=True)
                    rap_table[cp_field] = rap_table[cp_field].replace(r'03C|3C|3c', '03c',regex=True)

                    # Conver the following LotIDs to S-01
                    ## NSRP-01-08-ML046
                    ids = rap_table.index[rap_table[joinField].str.contains(r'NSRP-01-08-ML046',regex=True,na=False)]
                    rap_table.loc[ids, cp_field] = 'S-01'

                rap_table[cp_field] = rap_table[cp_field].apply(lambda x: re.sub(r',.*','',x))
                rap_table_stats[cp_field] = rap_table_stats[cp_field].apply(lambda x: re.sub(r',.*','',x))
                
                # Conver join field (StrucID) to upper case
                rap_table[joinField] = rap_table[joinField].str.upper()

                # Remove white space and convert to string
                to_string_fields = [joinField]
                toString(rap_table, to_string_fields)

                # Check and Fix StatusStruc, 
                ## 1. StatusStruc =0 -> StatusStruc = empty
                id = rap_table.index[rap_table[structure_status_field] == 0]
                rap_table.loc[id, structure_status_field] = None
                
                # Join the number of families to table
                rap_relo_table.head()
                toString(rap_relo_table, [joinField])
                rap_relo_table[family_number_field] = 0
                df = rap_relo_table.groupby(joinField).count()[[family_number_field]]
                rap_table = pd.merge(left=rap_table, right=df, how='left', left_on=joinField, right_on=joinField)
                
                # MoA is 'No Need to Acquire' -> StatusStruc is null: What is THIS?
                # id = rap_table.index[rap_table['MoA'] == 4 & (rap_table[status_field] >= 1)]
                # rap_table.loc[id, status_field] = None
            
                # Export
                export_file_name = os.path.splitext(os.path.basename(gis_struc_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                rap_table.to_excel(to_excel_file, index=False)

                arcpy.AddMessage("The {} master list for structure was successfully exported.".format(proj))

                ##############################################################################
                # Create summary statistics between original rap_table and updated rap_table
                ### 1.0. StatusLA = 0 -> NA          
                ## 1.0.1. Original rap_table (before updating)
                colname_change = rap_table_stats.columns[rap_table_stats.columns.str.contains('|'.join(search_names_city))]
                rap_table_stats = rap_table_stats.rename(columns={str(colname_change[0]): municipality_field})
                rap_table_stats = first_letter_capital(rap_table_stats, [municipality_field])
                
                id = rap_table_stats.index[rap_table_stats[structure_status_field] == 0]
                rap_table_stats.loc[id, structure_status_field] = np.NAN

                groupby_fields = [municipality_field, structure_status_field]
                rap_table0_stats = rap_table_stats.groupby(groupby_fields)[structure_status_field].count().reset_index(name=count_name)
                rap_table0_stats = rap_table0_stats.sort_values(by=groupby_fields)

                ## 1.0.2. Updated rap_table (After updating)
                rap_table1_stats = rap_table.groupby(groupby_fields)[structure_status_field].count().reset_index(name=count_name)
                rap_table1_stats = rap_table1_stats.sort_values(by=groupby_fields)

                ## 1.0.3. Merge
                # table_stats = rap_table0_stats.join(rap_table1_stats, lsuffix=lsuffix_rap, rsuffix=rsuffix_gis)
                table_stats = pd.merge(left=rap_table0_stats, right=rap_table1_stats, how='outer', left_on=[municipality_field, structure_status_field], right_on=[municipality_field, structure_status_field])
                table_stats['count_diff'] = np.NAN
                table_stats['count_diff'] = table_stats['counts_y'] - table_stats['counts_x']
                table_stats = table_stats.rename(columns={"counts_x": str(counts_rap), "counts_y": str(counts_gis)})
                            
                ### 2.0. HandedOver = 1
                ## 2.0.1. Original rap_table (before updating)
                id = rap_table_stats.index[rap_table_stats[handover_field] == 1]
                groupby_fields = [municipality_field, handover_field]
                rap_table0_stats = rap_table_stats.groupby(groupby_fields)[handover_field].count().reset_index(name=count_name)
                rap_table0_stats = rap_table0_stats.sort_values(by=groupby_fields)

                ## 2.0.2. Updated rap_table (After updating)
                rap_table1_stats = rap_table.groupby(groupby_fields)[handover_field].count().reset_index(name=count_name)
                rap_table1_stats = rap_table1_stats.sort_values(by=groupby_fields)

                ## 2.0.3. Merge
                # table_stats_handedover = rap_table0_stats.join(rap_table1_stats, lsuffix=lsuffix_rap, rsuffix=rsuffix_gis)
                table_stats_handedover = pd.merge(left=rap_table0_stats, right=rap_table1_stats, how='outer', left_on=[municipality_field, handover_field], right_on=[municipality_field, handover_field])
                table_stats_handedover['count_diff'] = np.NAN
                table_stats_handedover["count_diff"] = table_stats_handedover['counts_y'] - table_stats_handedover['counts_x']
                table_stats_handedover = table_stats_handedover.rename(columns={"counts_x": str(counts_rap), "counts_y": str(counts_gis)})

                ### 3.0. Export summary statistics table
                file_name_stats = 'CHECK-' + proj + '_Structure_Summary_Statistics_Rap_and_GIS_ML.xlsx'
                to_excel_file0 = os.path.join(gis_dir, file_name_stats)

                with pd.ExcelWriter(to_excel_file0) as writer:
                    table_stats.to_excel(writer, sheet_name=structure_status_field, index=False)
                    table_stats_handedover.to_excel(writer, sheet_name=handover_field, index=False)

            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids in Envi table shown above. The Process stopped. Please correct the duplicated rows.')
                pass

        N2SC_Structure_Update()

class UpdateBarangay(object):
    def __init__(self):
        self.label = "1.4. Update Excel Master List (SC1 Barangay )"
        self.description = "Update Excel Master List (SC1 Barangay )"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_barangay_ms = arcpy.Parameter(
            displayName = "GIS SC1 Barangay Status ML (Excel)",
            name = "GIS SC1 Barangay Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_barangay_ms = arcpy.Parameter(
            displayName = "RAP SC1 Barangay Status ML (Excel)",
            name = "RAP SC1 Barangay Status ML (Excel)",
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

        params = [gis_dir, gis_barangay_ms, rap_barangay_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_barangay_ms = params[1].valueAsText
        rap_barangay_ms = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def SC1_Barangay_Update():
            def whitespace_removal(dataframe): # remove leading and trailing white space
                for i in dataframe.columns:
                    try:
                        dataframe[i] = dataframe[i].apply(lambda x: x.strip())
                    except AttributeError:
                        print("Not processed: " + '{}'.format(i))

            ## 2. Return unique values
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            ## 3. Return non-matched values between two lists
            def non_match_elements(list_a, list_b):
                non_match = []
                for i in list_a:
                    if i not in list_b:
                        non_match.append(i)
                return non_match
            
            def toString(table, to_string_fields):
                for field in to_string_fields:
                    table[field] = table[field].astype(str)
                    table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
                return table

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].str.title()
                return table
            
            ####################################################
            # Update Excel Master List Tables
            ####################################################
            rap_table = pd.read_excel(rap_barangay_ms)
            gis_table = pd.read_excel(gis_barangay_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + "SC1_Barangay_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format('SC1_Barangay_Status'))
            
            # Rename 'City' to Municipality
            renamed_city = 'Municipality'
            renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['City','city']))]
            rap_table = rap_table.rename(columns={str(renamed_col[0]): renamed_city})
            rap_table = first_letter_capital(rap_table, [renamed_city])

            # Rename Barangay
            renamed_brgy = 'Barangay'
            renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['Bgy','bgy']))]
            rap_table = rap_table.rename(columns={str(renamed_col[0]): renamed_brgy})
            rap_table = first_letter_capital(rap_table, [renamed_brgy])

            # Remove 'Barangay'
            # rap_table['Barangay'] = rap_table['Barangay'].apply(lambda x: x.replace(regex="^Barangay", value=""))
            rap_table = rap_table.replace(regex="^Barangay", value="")
            whitespace_removal(rap_table)

            # Make sure no space
            rap_table = toString(rap_table, ['Municipality', 'Barangay', 'Subcon'])

            # Convert to numeric
            to_numeric_fields = ["Coop"]
            cols = rap_table.columns
            non_match_col = non_match_elements(to_numeric_fields, cols)
            [to_numeric_fields.remove(non_match_col[0]) if non_match_col else print('no need to remove field from the list for numeric conversion')]

            for field in to_numeric_fields:
                rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
                rap_table[field] = pd.to_numeric(rap_table[field])

            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_barangay_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

        SC1_Barangay_Update()

class JustMessage10(object):
    def __init__(self):
        self.label = "1.6.0 ----- Update Land & Structure for Workable Pier -----"
        self.description = "Update Excel Master List"

class N2UpdateWorkablePierLandTable(object):
    def __init__(self):
        self.label = "1.6.1 (N2) Add Obstruction to Excel Master List (Lot)"
        self.description = "(N2) Add Obstruction to Excel Master List (Lot)"

    def getParameterInfo(self):
        gis_rap_dir = arcpy.Parameter(
            displayName = "N2 GIS RAP Directory",
            name = "N2 GIS RAP Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_lot_ms = arcpy.Parameter(
            displayName = "N2 GIS Land Status ML (Excel)",
            name = "N2 GIS Land Status ML (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_lot_portal = arcpy.Parameter(
            displayName = "N2 GIS Land Portal ML (Excel)",
            name = "N2 GIS Land Portal ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_via_dir = arcpy.Parameter(
            displayName = "N2 Pier Tracker Directory",
            name = "N2 Pier Tracker Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker = arcpy.Parameter(
            displayName = "N2 Pier Workable Tracker (Excel)",
            name = "N2 Pier Workability Tracker (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_rap_dir, gis_lot_ms, gis_lot_portal, gis_via_dir, pier_workable_tracker]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_rap_dir = params[0].valueAsText
        gis_lot_ms = params[1].valueAsText
        gis_lot_portal = params[2].valueAsText
        gis_via_dir = params[3].valueAsText
        pier_workable_tracker = params[4].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Obstruction_Land_ML_Update():           
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
            
            def remove_empty_strings(string_list):
                return [string for string in string_list if string]
            
            def unlist_brackets(nested_list): ## Remove nested list in a list
                return [item for sublist in nested_list for item in sublist]
            
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            # Define field names
            cp_field = 'CP'
            land1_field = 'Land.1'
            obstruc_field = 'Obstruction'
            lot_id_field = 'LotID'
            pier_num_field = 'PierNumber'

            # Read as xlsx
            gis_lot_table = pd.read_excel(gis_lot_ms)
            gis_lot_portal_t = pd.read_excel(gis_lot_portal)

            # 0. Reset 'Obstruction' to 'No' first
            gis_lot_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_land = pd.DataFrame()
            sum_lot_compile = pd.DataFrame()
            tnon_matched_lot_ids = []

            cps = ['N-01','N-02','N-03']
            for i, cp in enumerate(cps):
                gis_lot_t = gis_lot_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                
                pier_wtracker_t = pd.read_excel(pier_workable_tracker, sheet_name=cp)

                ################################################################
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                ################################################################
                #### Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps
                #### are obstructed by the same lots or structures.

                ### 1. Land
                pier_wtracker_t = pier_wtracker_t.dropna(subset=[land1_field]).reset_index(drop=True)
                pier_wtracker_t[land1_field] = pier_wtracker_t[land1_field].astype(str)
                pier_wtracker_t[land1_field] = pier_wtracker_t[land1_field].str.lstrip(',')
                lot_ids = flatten_extend(pier_wtracker_t[land1_field].str.split(','))          
                x_lot_ids = unique(lot_ids)
                x_lot_ids = remove_empty_strings(x_lot_ids)  
                # arcpy.AddMessage(x_lot_ids)

                ## Remove some
                # id_drop = np.where(x_lot_ids == '')[0]
                # x_lot_ids = np.delete(x_lot_ids, id_drop)
                # id_drop = np.where(x_lot_ids == ' ')[0]
                # x_lot_ids = np.delete(x_lot_ids, id_drop)
                # arcpy.AddMessage(x_lot_ids)

                ### Add these obstructing LotIDs to GIS Structure master list
                #### First, reset 'obstruction' field
                gis_lot_t[obstruc_field] = np.nan
                gis_lot_t.loc[:, obstruc_field] = 'No'

                ids = gis_lot_t.index[gis_lot_t[lot_id_field].isin(x_lot_ids)]
                y_lot_ids = gis_lot_t.loc[ids, lot_id_field].values
                gis_lot_t.loc[ids, obstruc_field] = 'Yes'

                # #### Extract obstructing LotIDs from the GIS Attribute table (GIS_portal)
                idcp = gis_lot_portal_t.index[gis_lot_portal_t[cp_field] == cp]
                # arcpy.AddMessage(x_lot_ids)
                ids_portal = gis_lot_portal_t.loc[idcp, ].index[gis_lot_portal_t.loc[idcp, lot_id_field].isin(x_lot_ids)]
                y_lot_portal_ids = gis_lot_portal_t.loc[ids_portal, lot_id_field].values

                ## compile for cps
                compile_land = pd.concat([compile_land, gis_lot_t])

                ############################# Summary Statistics ################################
                non_matched_lot_ids = []
                sum_lot = pd.DataFrame()
                sum_cols = ['CP',
                            'RAP',
                            'GIS_ML',
                            'GIS_Portal',
                            'Diff_RAP_GISML',
                            'Diff_RAP_GISPortal',
                            'Miss_IDs_RAP_GISML',
                            'Miss_IDs_RAP_GISPortal']
                sum_lot.loc[0,sum_cols[0]] = cp
                sum_lot.loc[0,sum_cols[1]] = len(x_lot_ids)
                sum_lot.loc[0,sum_cols[2]] = len(y_lot_ids)
                sum_lot.loc[0,sum_cols[3]] = len(y_lot_portal_ids)
                sum_lot.loc[0,sum_cols[4]] = sum_lot.loc[0,sum_cols[1]] - sum_lot.loc[0,sum_cols[2]]
                sum_lot.loc[0,sum_cols[5]] = sum_lot.loc[0,sum_cols[1]] - sum_lot.loc[0,sum_cols[3]]

                # Identify unmatched obstructing LotIDs in reference to the civil table
                ### Important to note that when a pier and lots obstruction ids cross between two cps,
                ### it is not possible to properly assign obstruction ('yes' or 'no') to these LotIDs.
                ### Simply assign the following non-matched LotIDs to 'Yes' in the obstruction field. 
                non_matched_elms = non_match_elements(x_lot_ids,y_lot_ids)
                sum_lot.loc[0,sum_cols[6]] = ",".join(non_matched_elms)
                non_matched_lot_ids.append(non_matched_elms)               
                tnon_matched_lot_ids.append(pd.Series(non_matched_lot_ids)[0]) # pd.Series removes nested list

                sum_lot.loc[0,sum_cols[7]] = ",".join(non_match_elements(x_lot_ids,y_lot_portal_ids))

                ### Add remarks for manually assigned LotIDs due to the problem mentioned above.
                sum_lot['Remark'] = np.nan
                if len(non_matched_elms) > 0:
                    sum_lot['Remark'] = f"**{non_matched_elms} were manually assigned 'Yes' in the Obstruction field of GIS_N2_Land_ML.xlsx."
                sum_lot_compile = pd.concat([sum_lot_compile, sum_lot], ignore_index=False)

            #################################################################################
            ### Overwrite existing GIS_Lot_ML and GIS_Structure_ML with the updated tables ##
            #################################################################################
            ##### Add missing CPs (N-04 & N-05) to the compiled table
            # gis_lot_tn04 = gis_lot_table.query(f"{cp_field} in ('N-04', 'N-05')")
            compile_cps = unique(compile_land[cp_field])
            gis_cps = unique(gis_lot_table[cp_field])
 
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            # arcpy.AddMessage(miss_cp)
            gis_lot_misst = gis_lot_table.query(f"{cp_field} in {miss_cp}")
            gis_lot_misst[obstruc_field] = 'No'
            compile_land = pd.concat([compile_land, gis_lot_misst]).reset_index(drop=True)

            # Manually Assign non-matched lot ids (overlapping CPs and piers) to 'Yes' in the Obstruction field
            # non_matched_lot_ids = flatten_extend(non_matched_lot_ids)
            arcpy.AddMessage(f"The following non-matched LotIDs were assigned to 'Yes' in the Obstruction field separately due to the associated overlapping piers and cps")
            arcpy.AddMessage(unlist_brackets(tnon_matched_lot_ids))
            ids = compile_land.index[compile_land[lot_id_field].isin(unlist_brackets(tnon_matched_lot_ids))]
            compile_land.loc[ids, obstruc_field] = 'Yes'

            # Finally export
            compile_land.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_lot_ms)), index=False)

            ## Export summary table
            sum_lot_compile.to_excel(os.path.join(gis_via_dir, '99-N2_Non-Matched_Obstruction_for_Land_RAP_vs_GIS.xlsx'), sheet_name='Land', index=False)

        Obstruction_Land_ML_Update()

class N2UpdateWorkablePierStructureTable(object):
    def __init__(self):
        self.label = "1.6.1 (N2) Add Obstruction to Excel Master List (Structure/NLO)"
        self.description = "(N2) Add Obstruction to Excel Master List (Structure/NLO)"

    def getParameterInfo(self):
        gis_rap_dir = arcpy.Parameter(
            displayName = "N2 GIS RAP Directory",
            name = "N2 GIS RAP Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_struc_ms = arcpy.Parameter(
            displayName = "N2 GIS Structure Status ML (Excel)",
            name = "N2 GIS Structure Status ML (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_struc_portal = arcpy.Parameter(
            displayName = "N2 GIS Structure Portal ML (Excel)",
            name = "N2 GIS Structure Portal ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_nlo_ms = arcpy.Parameter(
            displayName = "N2 GIS Structure NLO (ISF) ML (Excel)",
            name = "N2 GIS Structure NLO (ISF) ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_via_dir = arcpy.Parameter(
            displayName = "N2 Pier Tracker Directory",
            name = "N2 Pier Tracker Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker = arcpy.Parameter(
            displayName = "N2 Pier Workability Tracker (Excel)",
            name = "N2 Pier Workability Tracker (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_rap_dir, gis_struc_ms, gis_struc_portal, gis_nlo_ms ,gis_via_dir, pier_workable_tracker]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_rap_dir = params[0].valueAsText
        gis_struc_ms = params[1].valueAsText
        gis_struc_portal = params[2].valueAsText
        gis_nlo_ms = params[3].valueAsText
        gis_via_dir = params[4].valueAsText
        pier_workable_tracker = params[5].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Obstruction_Structure_ML_Update():           
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
            
            def remove_empty_strings(string_list):
                return [string for string in string_list if string]
            
            def unlist_brackets(nested_list): ## Remove nested list in a list
                return [item for sublist in nested_list for item in sublist]
            
            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            # Define field names
            cp_field = 'CP'
            struc1_field = 'Structure.1'
            obstruc_field = 'Obstruction'
            struc_id_field = 'StrucID'

            # Read as xlsx
            gis_struc_table = pd.read_excel(gis_struc_ms)
            gis_struc_portal_t = pd.read_excel(gis_struc_portal)
            gis_nlo_table = pd.read_excel(gis_nlo_ms)

            # 0. Reset 'Obstruction' to 'No' first
            gis_struc_table.loc[:, obstruc_field] = np.nan
            gis_nlo_table.loc[:, obstruc_field] = np.nan

            # Define how obstructing lot and structure IDs are entered for each pier
            ## '\n' or ','
            split_mark = ","

            # 1. Clean fields
            compile_struc = pd.DataFrame()
            compile_nlo = pd.DataFrame()
            sum_struc_compile = pd.DataFrame()
            tnon_matched_struc_ids = []
            cps = ['N-01','N-02','N-03']

            for i, cp in enumerate(cps):
                gis_struc_t = gis_struc_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                gis_nlo_t = gis_nlo_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                pier_wtracker_t = pd.read_excel(pier_workable_tracker, sheet_name=cp)

                ################################################################
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                ################################################################
                #### Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps
                #### are obstructed by the same lots or structures.

                ### 1. Structure
                pier_wtracker_t = pier_wtracker_t.dropna(subset=[struc1_field]).reset_index(drop=True)
                pier_wtracker_t[struc1_field] = pier_wtracker_t[struc1_field].astype(str)
                struc_ids = flatten_extend(pier_wtracker_t[struc1_field].str.split(","))
                x_struc_ids = unique(struc_ids)
                x_struc_ids = remove_empty_strings(x_struc_ids)  

                ### Add these obstructing StrucIDs to GIS Structure master list
                #### First, reset 'obstruction' field
                gis_struc_t[obstruc_field] = np.nan
                gis_struc_t.loc[:, obstruc_field] = 'No'

                ids = gis_struc_t.index[gis_struc_t[struc_id_field].isin(x_struc_ids)]
                y_struc_ids = gis_struc_t.loc[ids, struc_id_field].values
                gis_struc_t.loc[ids, obstruc_field] = 'Yes'

                # #### Extract obstructing LotIDs from the GIS Attribute table (GIS_portal)
                idcp = gis_struc_portal_t.index[gis_struc_portal_t[cp_field] == cp]
                ids_portal = gis_struc_portal_t.loc[idcp, ].index[gis_struc_portal_t.loc[idcp, struc_id_field].isin(x_struc_ids)]
                y_struc_portal_ids = gis_struc_portal_t.loc[ids_portal, struc_id_field].values

                ### 2. NLO
                #### Add these obstructing StrucIDs to GIS ISF master list
                #### Note that regardless of NLO' status, all the NLOs falling under obstructing structures must be visualized.
                gis_nlo_t[obstruc_field] = np.nan
                gis_nlo_t.loc[:, obstruc_field] = 'No'

                ids = gis_nlo_t.index[gis_nlo_t[struc_id_field].isin(x_struc_ids)]
                gis_nlo_t.loc[ids, obstruc_field] = 'Yes'

                ### 3. Check obstructing StrucIDS between NLO and Structure GIS master list
                ids = gis_struc_t.index[gis_struc_t[obstruc_field] == 'Yes']
                gis_struc_ids = gis_struc_t.loc[ids, struc_id_field].values

                ids = gis_nlo_t.index[gis_nlo_t[obstruc_field] == 'Yes']
                gis_nlo_ids = unique(gis_nlo_t.loc[ids, struc_id_field])    
                unmatched_struc_ids = non_match_elements(gis_nlo_ids, gis_struc_ids)
                arcpy.AddMessage(f"Any obstructing StrucIDs in the NLO ML that do not exist in the structure ML for {cp}?")
                if len(unmatched_struc_ids) > 0:
                    arcpy.AddMessage('Yes, you have the following unmatched obstructing StrucIDs between these master list tables.')
                    arcpy.AddMessage(unmatched_struc_ids)
                    arcpy.AddMessage('Please ensure that these unmatched StrucIDs share the same information on CP.')
                else:
                    arcpy.AddMessage('No, everything is fine.')

                ### 4. Compile for cps
                compile_struc = pd.concat([compile_struc, gis_struc_t])
                compile_nlo = pd.concat([compile_nlo, gis_nlo_t])

                ######################################## Summary Stats ###################################
                non_matched_struc_ids = []
                sum_struc = pd.DataFrame()
                sum_cols = ['CP',
                            'Civil',
                            'GIS_ML',
                            'GIS_Portal',
                            'Diff_Civil_GISML',
                            'Diff_Civil_GISPortal',
                            'Miss_IDs_Civil_GISML',
                            'Miss_IDs_Civil_GISPortal']
                sum_struc.loc[0,sum_cols[0]] = cp
                sum_struc.loc[0,sum_cols[1]] = len(x_struc_ids)
                sum_struc.loc[0,sum_cols[2]] = len(y_struc_ids)
                sum_struc.loc[0,sum_cols[3]] = len(y_struc_portal_ids)
                sum_struc.loc[0,sum_cols[4]] = sum_struc.loc[0,sum_cols[1]] - sum_struc.loc[0,sum_cols[2]]
                sum_struc.loc[0,sum_cols[5]] = sum_struc.loc[0,sum_cols[1]] - sum_struc.loc[0,sum_cols[3]]

                # Identify unmatched obstructing LotIDs in reference to the civil table
                sum_struc.loc[0,sum_cols[6]] = ",".join(non_match_elements(x_struc_ids, y_struc_ids))
                non_matched_struc_ids.append(non_match_elements(x_struc_ids,y_struc_ids))
                tnon_matched_struc_ids.append(pd.Series(non_matched_struc_ids)[0])
                                            
                sum_struc.loc[0,sum_cols[7]] = ",".join(non_match_elements(x_struc_ids, y_struc_portal_ids))
                sum_struc_compile = pd.concat([sum_struc_compile, sum_struc], ignore_index=False)

                
            ###################################################################################
            ### Overwrite existing GIS_Lot_ML and GIS_Structure_ML with the updated tables ####
            ###################################################################################
            #### Structure
            arcpy.AddMessage('Structure')
            ##### Add missing CPs to compiled table
            compile_cps = unique(compile_struc[cp_field])
            gis_cps = unique(gis_struc_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            gis_struc_misst = gis_struc_table.query(f"{cp_field} in {miss_cp}")
            gis_struc_misst[obstruc_field] = 'No'
            compile_struc = pd.concat([compile_struc, gis_struc_misst])

            #####
            arcpy.AddMessage(f"The following non-matched StrucIDs were assigned to 'Yes' in the Obstruction field separately due to the associated overlapping piers and cps")
            arcpy.AddMessage(unlist_brackets(tnon_matched_struc_ids))
            ids = compile_struc.index[compile_struc[struc_id_field].isin(unlist_brackets(tnon_matched_struc_ids))]
            compile_struc.loc[ids, obstruc_field] = 'Yes'

            compile_struc.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_struc_ms)), index=False) ## gis_struc
           
            #### NLO
            arcpy.AddMessage('NLO')
            ##### Add missing CPs to compiled table
            compile_cps = unique(compile_nlo[cp_field])
            gis_cps = unique(gis_nlo_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            gis_nlo_misst = gis_nlo_table.query(f"{cp_field} in {miss_cp}")
            gis_nlo_misst[obstruc_field] = 'No'
            compile_nlo = pd.concat([compile_nlo, gis_nlo_misst])

            #####
            arcpy.AddMessage(f"The following non-matched StrucIDs were assigned to 'Yes' in the Obstruction field separately due to the associated overlapping piers and cps")
            arcpy.AddMessage(unlist_brackets(tnon_matched_struc_ids))
            ids = compile_nlo.index[compile_nlo[struc_id_field].isin(unlist_brackets(tnon_matched_struc_ids))]
            compile_nlo.loc[ids, obstruc_field] = 'Yes'

            compile_nlo.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_nlo_ms)), index=False) ## gis_isf

            ## Compile SummaryStatus in one excel sheet
            sum_struc_compile.to_excel(os.path.join(gis_via_dir, '99-N2_Non-Matched_Obstruction_for_Structure_RAP_vs_GIS.xlsx'), sheet_name='Structure', index=False)

        Obstruction_Structure_ML_Update()

class SCUpdateWorkablePierLandTable(object):
    def __init__(self):
        self.label = "1.6.2 (SC) Add Obstruction to Excel Master List (Lot)"
        self.description = "(SC) Add Obstruction to Excel Master List (Lot)"

    def getParameterInfo(self):
        gis_rap_dir = arcpy.Parameter(
            displayName = "SC GIS RAP Directory",
            name = "GIS RAP Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_lot_ms = arcpy.Parameter(
            displayName = "SC GIS Land Status ML (Excel)",
            name = "GIS Land Status ML (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_lot_portal = arcpy.Parameter(
            displayName = "SC GIS Land Portal ML (Excel)",
            name = "GIS Land Portal ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_via_dir = arcpy.Parameter(
            displayName = "SC Pier Tracker Directory",
            name = "SC Pier Tracker Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "SC Pier Workable Tracker (Excel)",
            name = "SC Pier Workable Tracker (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_rap_dir, gis_lot_ms, gis_lot_portal, gis_via_dir, pier_workable_tracker_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_rap_dir = params[0].valueAsText
        gis_lot_ms = params[1].valueAsText
        gis_lot_portal = params[2].valueAsText
        gis_via_dir = params[3].valueAsText
        pier_tracker_ms = params[4].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Obstruction_Land_ML_Update():
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
            
            def remove_empty_strings(string_list):
                return [string for string in string_list if string]
            
            def unlist_brackets(nested_list): ## Remove nested list in a list
                return [item for sublist in nested_list for item in sublist]
            
            # Read as xlsx
            gis_lot_table = pd.read_excel(gis_lot_ms)
            gis_lot_portal_t = pd.read_excel(gis_lot_portal)
            pier_tracker_t = pd.read_excel(pier_tracker_ms)

            # List of fields
            obstruc_field = 'Obstruction' ## ('Yes' or 'No')
            lot_id_field = 'LotID'
            pier_number_field = 'PierNumber'
            cp_field = 'CP'
            land_obstruc_field = 'Land'
            land_obstrucid_field = 'Land.1'

            # 0. Reset 'Obstruction' to 'No' first
            gis_lot_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_land = pd.DataFrame()
            sum_lot_compile = pd.DataFrame()
            tnon_matched_lot_ids = []
            
            # cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
            cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
            for i, cp in enumerate(cps):
                gis_lot_t = gis_lot_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                pier_workable_t = pd.read_excel(pier_tracker_ms)
                pier_t = pier_workable_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                civil_piers = pier_t[pier_number_field].values

                ################################################################
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                ################################################################
                #### Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps
                #### are obstructed by the same lots or structures.

                ### 1. Land
                ids = pier_t.index[pier_t[land_obstruc_field] == 1]
                lot_ids = flatten_extend(pier_t.loc[ids, land_obstrucid_field].str.split(","))
                x_lot_ids = unique(lot_ids)
                x_lot_ids = remove_empty_strings(x_lot_ids)

                arcpy.AddMessage(x_lot_ids)

                ### Add these obstructing LotIDs to GIS Structure master list
                gis_lot_t[obstruc_field] = np.nan
                gis_lot_t.loc[:, obstruc_field] = 'No'

                ids = gis_lot_t.index[gis_lot_t[lot_id_field].isin(x_lot_ids)]
                y_lot_ids = gis_lot_t.loc[ids, lot_id_field].values
                gis_lot_t.loc[ids, obstruc_field] = 'Yes'

                # #### Extract obstructing LotIDs from the GIS Attribute table (GIS_portal)
                idcp = gis_lot_portal_t.index[gis_lot_portal_t[cp_field] == cp]
                ids_portal = gis_lot_portal_t.loc[idcp, ].index[gis_lot_portal_t.loc[idcp, lot_id_field].isin(x_lot_ids)]
                y_lot_portal_ids = gis_lot_portal_t.loc[ids_portal, lot_id_field].values

                ## compile for cps
                compile_land = pd.concat([compile_land, gis_lot_t])

               ############################# Summary Statistics ################################
                sum_lot = pd.DataFrame()
                sum_cols = ['CP',
                    'Civil',
                    'GIS_ML',
                    'GIS_Portal',
                    'Diff_Civil_GISML',
                    'Diff_Civil_GISPortal',
                    'Miss_IDs_Civil_GISML',
                    'Miss_IDs_Civil_GISPortal']
                sum_lot.loc[0,sum_cols[0]] = cp
                sum_lot.loc[0,sum_cols[1]] = len(x_lot_ids)
                sum_lot.loc[0,sum_cols[2]] = len(y_lot_ids)
                sum_lot.loc[0,sum_cols[3]] = len(y_lot_portal_ids)
                sum_lot.loc[0,sum_cols[4]] = sum_lot.loc[0,sum_cols[1]] - sum_lot.loc[0,sum_cols[2]]
                sum_lot.loc[0,sum_cols[5]] = sum_lot.loc[0,sum_cols[1]] - sum_lot.loc[0,sum_cols[3]]

                # Identify unmatched obstructing LotIDs in reference to the civil table
                sum_lot.loc[0,sum_cols[6]] = ",".join(non_match_elements(x_lot_ids,y_lot_ids))
                sum_lot.loc[0,sum_cols[7]] = ",".join(non_match_elements(x_lot_ids,y_lot_portal_ids))
                sum_lot_compile = pd.concat([sum_lot_compile, sum_lot], ignore_index=False)

            #################################################################################
            ### Overwrite existing GIS_Lot_ML with the updated tables ##
            #################################################################################
            compile_cps = unique(compile_land[cp_field])
            gis_cps = unique(gis_lot_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            arcpy.AddMessage(miss_cp)
            if len(miss_cp) > 0:
                gis_lot_misst = gis_lot_table.query(f"{cp_field} in {miss_cp}")
                # gis_lot_misst[obstruc_field] = 'No'
                compile_land = pd.concat([compile_land, gis_lot_misst])
            compile_land.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_lot_ms)), index=False) ## gis_land
 
            ## Export summary table
            sum_lot_compile.to_excel(os.path.join(gis_via_dir, '99-SC_Pier_Workable_Obstruction_Land_summaryStats.xlsx'), sheet_name='Land', index=False)

        Obstruction_Land_ML_Update()

class SCUpdateWorkablePierStructureTable(object):
    def __init__(self):
        self.label = "1.6.3 (SC) Add Obstruction to Excel Master List (Structure & NLO)"
        self.description = "(SC) Add Obstruction to Excel Master List (Structure & NLO)"

    def getParameterInfo(self):
        gis_rap_dir = arcpy.Parameter(
            displayName = "SC GIS RAP Directory",
            name = "SC GIS RAP Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_struc_ms = arcpy.Parameter(
            displayName = "SC GIS Structure Status ML (Excel)",
            name = "SC GIS Structure Status ML (Excel))",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_struc_portal = arcpy.Parameter(
            displayName = "SC GIS Structure Portal ML (Excel)",
            name = "SC GIS Structure Portal ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_nlo_ms = arcpy.Parameter(
            displayName = "SC GIS Structure NLO (ISF) ML (Excel)",
            name = "SC GIS Structure NLO (ISF) ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_via_dir = arcpy.Parameter(
            displayName = "SC Pier Tracker Directory",
            name = "SC Pier Tracker Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "SC Pier Workable Tracker (Excel)",
            name = "SC Pier Workable Tracker (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_rap_dir, gis_struc_ms, gis_struc_portal, gis_nlo_ms, gis_via_dir, pier_workable_tracker_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_rap_dir = params[0].valueAsText
        gis_struc_ms = params[1].valueAsText
        gis_struc_portal = params[2].valueAsText
        gis_nlo_ms = params[3].valueAsText
        gis_via_dir = params[4].valueAsText
        pier_tracker_ms = params[5].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Obstruction_Structure_ML_Update():
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
            
            def remove_empty_strings(string_list):
                return [string for string in string_list if string]
            
            def unlist_brackets(nested_list): ## Remove nested list in a list
                return [item for sublist in nested_list for item in sublist]
            
            # Read as xlsx
            gis_struc_table = pd.read_excel(gis_struc_ms)
            gis_struc_portal_t = pd.read_excel(gis_struc_portal)
            gis_nlo_table = pd.read_excel(gis_nlo_ms)

            # List of fields
            obstruc_field = 'Obstruction' ## ('Yes' or 'No')
            pier_number_field = 'PierNumber'
            cp_field = 'CP'
            struc_id_field = 'StrucID'
            struc_obstruc_field = 'Structure'
            struc_obstrucid_field = 'Structure.1'


            # 0. Reset 'Obstruction' to 'No' first
            gis_struc_table.loc[:, obstruc_field] = np.nan
            gis_nlo_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_struc = pd.DataFrame()
            compile_nlo = pd.DataFrame()
            sum_struc_compile = pd.DataFrame()
            ## cps = ['S-01','S-02','S-03a','S-03b','S-03c','S-04','S-05','S-06','S-07']
            cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
            for i, cp in enumerate(cps):
                gis_struc_t = gis_struc_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                gis_nlo_t = gis_nlo_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                pier_workable_t = pd.read_excel(pier_tracker_ms)
                pier_t = pier_workable_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                civil_piers = pier_t[pier_number_field].values

                ################################################################
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                ################################################################
                #### Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps
                #### are obstructed by the same lots or structures.

                ### 2. Structure and ISF
                ids = pier_t.index[pier_t[struc_obstruc_field] == 1]
                struc_ids = flatten_extend(pier_t.loc[ids, struc_obstrucid_field].str.split(","))
                x_struc_ids = unique(struc_ids)
                x_struc_ids = remove_empty_strings(x_struc_ids)

                ### Add these obstructing StrucIDs to GIS Structure master list
                gis_struc_t[obstruc_field] = np.nan
                gis_struc_t.loc[:, obstruc_field] = 'No'

                ids = gis_struc_t.index[gis_struc_t[struc_id_field].isin(x_struc_ids)]
                y_struc_ids = gis_struc_t.loc[ids, struc_id_field].values
                gis_struc_t.loc[ids, obstruc_field] = 'Yes'

                #### Extract obstructing StrucIDs from the GIS Attribute table (GIS_portal)
                ids_portal = gis_struc_portal_t.index[gis_struc_portal_t[struc_id_field].isin(x_struc_ids)]
                y_struc_portal_ids = gis_struc_portal_t.loc[ids_portal,struc_id_field].values

                ### 2. NLO
                #### 2.1. Add these obstructing StrucIDs to GIS ISF master list
                #### Note that regardless of NLO' status, all the NLOs falling under obstructing structures must be visualized.
                gis_nlo_t[obstruc_field] = np.nan
                gis_nlo_t.loc[:, obstruc_field] = 'No'

                ids = gis_nlo_t.index[gis_nlo_t[struc_id_field].isin(x_struc_ids)]
                gis_nlo_t.loc[ids, obstruc_field] = 'Yes'

                #### 2.2. Check obstructing StrucIDS between NLO and Structure GIS master list
                ids = gis_struc_t.index[gis_struc_t[obstruc_field] == 'Yes']
                gis_struc_ids = gis_struc_t.loc[ids, struc_id_field].values

                ids = gis_nlo_t.index[gis_nlo_t[obstruc_field] == 'Yes']
                gis_nlo_ids = unique(gis_nlo_t.loc[ids, struc_id_field])    
                unmatched_struc_ids = non_match_elements(gis_nlo_ids, gis_struc_ids)

                arcpy.AddMessage(f"Any obstructing StrucIDs in the NLO ML that do not exist in the structure ML for {cp}?")
                if len(unmatched_struc_ids) > 0:
                    arcpy.AddMessage('Yes, you have the following unmatched obstructing StrucIDs between these master list tables.')
                    arcpy.AddMessage(unmatched_struc_ids)
                    arcpy.AddMessage('Please ensure that these unmatched StrucIDs share the same information on CP.')
                else:
                    arcpy.AddMessage('No, everything is fine.')

                ## Compile for cps
                compile_struc = pd.concat([compile_struc, gis_struc_t])
                compile_nlo = pd.concat([compile_nlo, gis_nlo_t])

                ######################################## Summary Stats ###################################
                sum_struc_compile = pd.DataFrame()
                sum_cols = ['CP',
                            'Civil',
                            'GIS_ML',
                            'GIS_Portal',
                            'Diff_Civil_GISML',
                            'Diff_Civil_GISPortal',
                            'Miss_IDs_Civil_GISML',
                            'Miss_IDs_Civil_GISPortal']

                sum_struc = pd.DataFrame()
                sum_struc.loc[0,sum_cols[0]] = 'S-01'
                sum_struc.loc[0,sum_cols[1]] = len(x_struc_ids)
                sum_struc.loc[0,sum_cols[2]] = len(y_struc_ids)
                sum_struc.loc[0,sum_cols[3]] = len(y_struc_portal_ids)
                sum_struc.loc[0,sum_cols[4]] = sum_struc.loc[0,sum_cols[1]] - sum_struc.loc[0,sum_cols[2]]
                sum_struc.loc[0,sum_cols[5]] = sum_struc.loc[0,sum_cols[1]] - sum_struc.loc[0,sum_cols[3]]

                # Identify unmatched obstructing LotIDs in reference to the civil table
                sum_struc.loc[0,sum_cols[6]] = ",".join(non_match_elements(x_struc_ids,y_struc_ids))
                sum_struc.loc[0,sum_cols[7]] = ",".join(non_match_elements(x_struc_ids,y_struc_portal_ids))
                sum_struc_compile = pd.concat([sum_struc_compile, sum_struc], ignore_index=False)

            ###################################################################################
            ### Overwrite existing GIS_Structure_ML with the updated tables ####
            ###################################################################################
            ### need to missing cps from the original
            #### Structure
            compile_cps = unique(compile_struc[cp_field])
            gis_cps = unique(gis_struc_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            if len(miss_cp) > 0:
                gis_struc_misst = gis_struc_table.query(f"{cp_field} in {miss_cp}")
                # gis_struc_misst[obstruc_field] = 'No'
                compile_struc = pd.concat([compile_struc, gis_struc_misst])

            compile_struc.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_struc_ms)), index=False) ## gis_struc
           
            #### NLO
            compile_cps = unique(compile_nlo[cp_field])
            gis_cps = unique(gis_nlo_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            arcpy.AddMessage(miss_cp)
            if len(miss_cp) > 0:
                gis_nlo_misst = gis_nlo_table.query(f"{cp_field} in {miss_cp}")
                # gis_nlo_misst[obstruc_field] = 'No'
                compile_nlo = pd.concat([compile_nlo, gis_nlo_misst])
           
            compile_nlo.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_nlo_ms)), index=False) ## gis_isf

            ## Export summary statistics table
            sum_struc_compile.to_excel(os.path.join(gis_via_dir, '99-SC_Workable_Pier_obstructing_structure_summaryStats.xlsx'), sheet_name='Land', index=False)

        Obstruction_Structure_ML_Update()

class JustMessage2(object):
    def __init__(self):
        self.label = "2.0. ----- Update GIS Layers -----"
        self.description = "Update Excel Master List"

class UpdateLotGIS(object):
    def __init__(self):
        self.label = "2.1. Update GIS Attribute Table (Lot)"
        self.description = "Update feature layer for land acquisition"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']

        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        in_lot = arcpy.Parameter(
            displayName = "Land Feature Layer (Polygon)",
            name = "Land Feature Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Excel master list tables
        ml_lot = arcpy.Parameter(
            displayName = "GIS Land Status ML (Feature Table)",
            name = "GIS Land Status ML (Feature Table)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, in_lot, ml_lot]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        inLot = params[2].valueAsText
        mlLot = params[3].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        arcpy.env.overwriteOutput = True
        ### Remove temporary date added
        try:
            arcpy.AddMessage('Removing temporary added date from Lot excel master list has started...')
            to_date_fields = ['HandOverDate', 'HandedOverDate']
            for field in to_date_fields:
                with arcpy.da.UpdateCursor(mlLot, [field]) as cursor:
                    for row in cursor:
                        if row[0]:
                            year = row[0].strftime("%Y")
                            if int(year) < 2000:
                                row[0] = None
                            else:
                                row[0] = row[0]
                        cursor.updateRow(row)
        except:
            pass


        # For updating lot
        target_actual_field = "TargetActual"
        target_actual_date_field = "TargetActualDate"
        try:
            arcpy.AddMessage('Updating Lot status has started..')
            # 1. Copy Original Feature Layers
            copied_name = 'LA_Temp'               
            gis_copied = arcpy.CopyFeatures_management(inLot, copied_name)
                
            arcpy.AddMessage("Stage 1: Copy feature layer was success")
                    
            # 2. Delete Field
            gis_fields = [f.name for f in arcpy.ListFields(gis_copied)]
                
            ## 2.1. Identify fields to be dropped
            gis_drop_fields_check = [e for e in gis_fields if e not in ('LotId', 'LotID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
                
            ## 2.2. Extract existing fields
            arcpy.AddMessage("Stage 1: Extract existing fields was success")
                
            ## 2.3. Check if there are fields to be dropped
            gis_drop_fields = [f for f in gis_fields if f in tuple(gis_drop_fields_check)]
                
            arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")
                
            ## 2.4 Drop
            if len(gis_drop_fields) == 0:
                arcpy.AddMessage("There is no field that can be dropped from the feature layer")
            else:
                arcpy.DeleteField_management(gis_copied, gis_drop_fields)
                    
            arcpy.AddMessage("Stage 1: Dropping Fields was success")
            arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

            # 3. Join Field
            ## 3.1. Convert Excel tables to feature table
            lot_ml = arcpy.conversion.ExportTable(mlLot, 'lot_ml')

            # Check if LotID match between ML and GIS
            lotid_field = 'LotID'
            lotid_gis = unique_values(gis_copied, lotid_field)
            lotid_ml = unique_values(lot_ml, lotid_field)
            
            lotid_miss_gis = [e for e in lotid_gis if e not in lotid_ml]
            lotid_miss_ml = [e for e in lotid_ml if e not in lotid_gis]

            if lotid_miss_ml or lotid_miss_gis:
                arcpy.AddMessage('The following Lot IDs do not match between ML and GIS.')
                arcpy.AddMessage('Missing LotIDs in GIS table: {}'.format(lotid_miss_gis))
                arcpy.AddMessage('Missing LotIDs in ML Excel table: {}'.format(lotid_miss_ml))
                
            ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
            lot_ml_fields = [f.name for f in arcpy.ListFields(lot_ml)]
            lot_ml_transfer_fields = [e for e in lot_ml_fields if e not in ('LotId', lotid_field,'OBJECTID')]
                
            ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
            gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in ('LotId', lotid_field)]))                      
            lot_ml_join_field =' '.join(map(str, [f for f in lot_ml_fields if f in ('LotId', lotid_field)]))
                
            ## 3.4 Join
            arcpy.JoinField_management(in_data=gis_copied, in_field=gis_join_field, join_table=lot_ml, join_field=lot_ml_join_field, fields=lot_ml_transfer_fields)

            # 4. Trucnate
            arcpy.TruncateTable_management(inLot)

            # 5. Append
            arcpy.Append_management(gis_copied, inLot, schema_type = 'NO_TEST')

            # 6. Delete temporary date from the updated GIS layer
            try:
                with arcpy.da.UpdateCursor(inLot, target_actual_date_field) as cursor:
                    for row in cursor:
                        if row[0]:
                            if int(row[0].year) < 1991:
                                row[0] = None
                        cursor.updateRow(row)
            except:
                pass

            # 7. Delete temporary date from 'TargetActualDate'
            try:
                with arcpy.da.UpdateCursor(mlLot, [target_actual_field, target_actual_date_field]) as cursor:
                    for row in cursor:
                        if int(row[1].year) < 1991:
                            row[0] = None
                            row[1] = None
                        cursor.updateRow(row)
            except:
                pass

            # Delete the copied feature layer
            deleteTempLayers = [gis_copied, lot_ml]
            arcpy.Delete_management(deleteTempLayers)

            # Export the updated GIS portal to excel sheet for checking lot IDs
            file_name = project + "_" + "GIS_Land_Portal.xlsx"
            arcpy.conversion.TableToExcel(inLot, os.path.join(gis_dir, file_name))

        except:
            pass

class UpdateStructureGIS(object):
    def __init__(self):
        self.label = "2.2. Update GIS Attribute Tables (Structures/Occupancy/ISF Relocation)"
        self.description = "Update feature layers for structures including occupany and ISF Relocation"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']

        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
    
        in_structure = arcpy.Parameter(
            displayName = "Structure Status Layer (Polygon)",
            name = "Structure Status Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_occupancy = arcpy.Parameter(
            displayName = "Structure Occupancy Layer (Point)",
            name = "Structure Occupancy Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_isf = arcpy.Parameter(
            displayName = "Structure ISF Relocation (Point)",
            name = "Structure ISF Relocation (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        ml_structure = arcpy.Parameter(
            displayName = "GIS Structure Status Table (Feature Table)",
            name = "GIS Structure Status Table (Feature Table)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        ml_isf = arcpy.Parameter(
            displayName = "GIS Structure ISF Table (Feature Table)",
            name = "GIS Structure ISF Table (Feature Table)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, in_structure, in_occupancy, in_isf, ml_structure, ml_isf]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        inStruc = params[2].valueAsText
        inOccup = params[3].valueAsText
        inISF = params[4].valueAsText
        mlStruct = params[5].valueAsText
        mlISF = params[6].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})
            
        def non_match_elements(list_a, list_b):
            non_match = []
            for i in list_a:
                if i not in list_b:
                    non_match.append(i)
            return non_match
                    
        def check_field_match(target_table, input_table, join_field):
            id1 =  unique_values(target_table[join_field])
            id2 = unique_values(input_table[join_field])
                
            target_table_miss = [f for f in id1 if f not in id2]
            input_table_miss = [f for f in id2 if f not in id1]

            arcpy.AddMessage('Missing Ids in target table: {}'.format(target_table_miss))
            arcpy.AddMessage('Missing Ids in input table: {}'.format(input_table_miss))
 

        arcpy.env.overwriteOutput = True

        # 1. Copy Original Feature Layers
        join_field = 'StrucID'
        Struc_Temp = 'Struc_Temp'

        # if there are duplicated observations in Portal and exit
        struc_ids_list = [f[0] for f in arcpy.da.SearchCursor(inStruc, [join_field])]
        dup = [x for x in struc_ids_list if struc_ids_list.count(x) > 1]
        if len(dup) == 0:
            # 1. Copy structure layer
            arcpy.management.CopyFeatures(inStruc, Struc_Temp)
            arcpy.AddMessage("Stage 1: Copy feature layer was success")
                    
            # 2. Fields to be dropped
            gis_fields = [f.name for f in arcpy.ListFields(Struc_Temp)]
            drop_fields = [e for e in gis_fields if e not in (join_field, 'strucID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            arcpy.management.DeleteField(Struc_Temp, drop_fields)   

            # 3. Join Field
            ## 3.1. Convert Excel tables to feature table
            struc_ml = arcpy.conversion.ExportTable(mlStruct, 'structure_ml')
                
            ##########################################################################
            ##### STAGE 1: Update Existing Structure Layer ######
            ###########################################################################
            ## 3.2. Gain all fields except 'StrucID'
            struc_ml_fields = [f.name for f in arcpy.ListFields(struc_ml)]
            struc_ml_transfer_fields = [e for e in struc_ml_fields if e not in (join_field, 'strucID','OBJECTID')]
            
            ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables               
            ## 3.4 Join
            arcpy.management.JoinField(in_data=Struc_Temp, in_field=join_field, join_table=struc_ml, join_field=join_field, fields=struc_ml_transfer_fields)

            # 4. Trucnate
            arcpy.management.TruncateTable(inStruc)

            # 5. Append
            schemaType = "NO_TEST"
            fieldMappings = ""
            subtype = ""
            arcpy.management.Append(Struc_Temp, inStruc, schemaType, fieldMappings, subtype)

            ##########################################################################
            ##### STAGE 2: Update Existing Structure (Occupancy) & Structure (ISF) ######
            ###########################################################################
            ## Copy original feature layer           
            # STAGE: 2-1. Create Structure (point) for Occupany
            ## 2-1.1. Feature to Point for Occupany
            outFeatureClassPointStruc = 'Struc_pt_occupancy_temp'
            pointStruc = arcpy.management.FeatureToPoint(inStruc, outFeatureClassPointStruc, "CENTROID")
            
            ## 2-1.2. Add XY Coordinates
            arcpy.management.AddXY(pointStruc)
            
            ## 2-1.3. Truncate original point structure layer (Occupancy)
            arcpy.management.TruncateTable(inOccup)

            ## 2-1.4. Append to the original FL
            arcpy.management.Append(pointStruc, inOccup, schema_type = 'NO_TEST')

            # STAGE: 2-2. Create and Update ISF Feture Layer
            ## 2-2.1. Convert ISF (Relocation excel) to Feature table
            ##MasterListISF = arcpy.TableToTable_conversion(mlISF, workspace, 'MasterListISF')
            MasterListISF = arcpy.conversion.ExportTable(mlISF, 'MasterListISF')

            ## 2-2.2. Gain all fields except 'StrucId'
            inputFieldISF = [f.name for f in arcpy.ListFields(MasterListISF)]
            joinFieldISF = [e for e in inputFieldISF if e not in ('StrucId', 'strucID','OBJECTID')]

            ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
            tISF = [f.name for f in arcpy.ListFields(inOccup)] # Note 'inputLayerOccupOrigin' must be used, not ISF
            in_fieldISF= ' '.join(map(str, [f for f in tISF if f in (join_field,'strucID')]))

            uISF = [f.name for f in arcpy.ListFields(MasterListISF)]
            join_fieldISF = ' '.join(map(str, [f for f in uISF if f in (join_field, 'strucID')]))

            ## Join
            xCoords = "POINT_X"
            yCoords = "POINT_Y"
            zCoords = "POINT_Z"

            # Join only 'POINT_X' and 'POINT_Y' in the 'inputLayerOccupOrigin' to 'MasterListISF'
            arcpy.management.JoinField(in_data=MasterListISF, in_field=join_fieldISF, join_table=inOccup, join_field=in_fieldISF, fields=[xCoords, yCoords, zCoords])

            ## 2-2.3. XY Table to Points (FL)
            out_feature_class = "Status_for_Relocation_ISF_temp"
            sr = arcpy.SpatialReference(3123)
            outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords, zCoords, sr)

            ### Delete 'POINT_X', 'POINT_Y', 'POINT_Z'; otherwise, it gives error for the next batch
            dropXYZ = [xCoords, yCoords, zCoords]
            arcpy.management.DeleteField(outLayerISF, dropXYZ)
            
            ## Check if StrucIDs match between ISF excel ML and GIS point feature layer
            arcpy.AddMessage(".\n")
            try:
                check_field_match(outLayerISF, MasterListISF, join_field)
            except:
                pass

            ## 2-2.5. Truncate original ISF point FL
            arcpy.management.TruncateTable(inISF)

            ## 2-2.6. Append to the Original ISF
            arcpy.management.Append(outLayerISF, inISF, schema_type = 'NO_TEST')

            # Delete the copied feature layer
            deleteTempLayers = [Struc_Temp, struc_ml, pointStruc, outLayerISF, MasterListISF] 
            arcpy.management.Delete(deleteTempLayers)

            #########################################################
            ### Export updated GIS Layers to Excel Sheet (used for summary stats and missing IDs)
            ##########################################################
            # Structure
            file_name_structure = project + "_" + "GIS_Structure_Portal.xlsx"
            arcpy.conversion.TableToExcel(inStruc, os.path.join(gis_dir, file_name_structure))

            # Occupancy (not necessary. )
            # file_name_occupancy = project + "_" + "GIS_Structure_Occupancy_Portal.xlsx"
            # arcpy.conversion.TableToExcel(inStruc, os.path.join(gis_dir, file_name_occupancy))

            # NLO
            file_name_nlo = project + "_" + "GIS_ISF_Portal.xlsx"
            arcpy.conversion.TableToExcel(inISF, os.path.join(gis_dir, file_name_nlo))

        else:
            arcpy.AddMessage('The following Struc IDs are duplicated in the GIS attribute table:')
            arcpy.AddMessage(dup)
            arcpy.AddError('There are duplicated StrucIDs in the GIS attribute table. The process stops. Please fix this first.')

class UpdateBarangayGIS(object):
    def __init__(self):
        self.label = "2.4. Update GIS Attribute Tables (SC1 Barangay)"
        self.description = "Update GIS Attribute Tables (SC1 Barangay)"

    def getParameterInfo(self):
        in_pier = arcpy.Parameter(
            displayName = "GIS SC1 arangay (Polygon)",
            name = "GIS SC1 arangay (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        ml_barangay = arcpy.Parameter(
            displayName = "Excel MasterList (SC1 Barangay)",
            name = "Excel MasterList (SC1 Barangay)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_pier, ml_barangay]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inPier = params[0].valueAsText
        mlPier = params[1].valueAsText

        arcpy.env.overwriteOutput = True

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        # 1. For Pier
        try:
            join_field = 'Barangay'
            arcpy.AddMessage('Updating SC1 Barangay has started..')
            barangay_copied_name = 'N2_Pier_barangay'
            barangay_copied_gis = arcpy.CopyFeatures_management(inPier, barangay_copied_name)
            
            # 2. Delete fields: 'Municipality' and 'AccessDate'
            barangay_gis_fields = [f.name for f in arcpy.ListFields(barangay_copied_gis)]
            
            ## 2.1. Fields to be dropped
            barangay_drop_fields = [e for e in barangay_gis_fields if e not in (join_field,'Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
            ## 2.3. Check if there are fields to be dropped
            barangay_drop_fields_check = [f for f in barangay_gis_fields if f in tuple(barangay_drop_fields)]
            
            ## 2.4 Drop
            if len(barangay_drop_fields_check) == 0:
                arcpy.AddMessage("There is no field that can be dropped from the feature layer")
            else:
                arcpy.DeleteField_management(barangay_copied_gis, barangay_drop_fields_check)

            # 3. Join Field
            ## 3.1. Convert Excel tables to feature table
            ##MasterListN2Pier = arcpy.TableToTable_conversion(mlPier, workspace, 'MasterListN2Pier')
            barangay_ml_table = arcpy.conversion.ExportTable(mlPier, 'barangay_ml_table')

            # Check if pier numbers match between ML and GIS
            barangay_field = 'PIER'
            piers_gis = unique_values(barangay_copied_gis, barangay_field)
            piers_ml = unique_values(barangay_ml_table, barangay_field)
            
            piers_miss_gis = [e for e in piers_gis if e not in piers_ml] # missing in gis
            piers_miss_ml = [e for e in piers_ml if e not in piers_gis] # missing in ML

            if piers_miss_ml:
                arcpy.AddMessage('The following pier numbers do not match between ML and GIS.')
                arcpy.AddMessage('Subject piers for GIS: {}'.format(piers_miss_gis))
                arcpy.AddMessage('Subject piers for ML: {}'.format(piers_miss_ml))
            
            ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
            barangay_ml_fields = [f.name for f in arcpy.ListFields(barangay_ml_table)]
            transfer_fields = [e for e in barangay_ml_fields if e not in (join_field, 'barangay','OBJECTID')]
            
            ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
            gis_join_field = ' '.join(map(str, [f for f in barangay_gis_fields if f in (join_field, 'barangay')]))
            ml_join_field =' '.join(map(str, [f for f in barangay_ml_fields if f in (join_field, 'barangay')]))
            
            ## 3.4 Join
            arcpy.JoinField_management(in_data=barangay_copied_gis, in_field=gis_join_field, join_table=barangay_ml_table, join_field=ml_join_field, fields=transfer_fields)
            
            # 4. Trucnate
            arcpy.TruncateTable_management(inPier)
            
            # 5. Append
            arcpy.Append_management(barangay_copied_gis, inPier, schema_type = 'NO_TEST')

            # Delete the copied feature layer
            deleteTempLayers = [barangay_copied_gis, barangay_ml_table]
            arcpy.Delete_management(deleteTempLayers)
            
        except:
            arcpy.AddError("Something went wrong..process stopped.")
            pass

class JustMessage3(object):
    def __init__(self):
        self.label = "3.0. ----- Summary Statistics GIS ML and GIS Portal -----"
        self.description = "Update Excel Master List"

class CheckLotUpdatedStatusGIS(object):
    def __init__(self):
        self.label = "3.1. Summary Stats for Lot Status (GIS Portal and GIS ML)"
        self.description = "Summary Stats for Lot Status (GIS Portal and GIS ML)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']
    
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
            displayName = "GIS Lot ML File (Excel)",
            name = "GIS Lot ML File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_layer, gis_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_layer = params[2].valueAsText
        gis_ml = params[3].valueAsText

        # Read table
        gis_table = pd.read_excel(gis_ml)
        gis_portal = pd.read_excel(gis_layer)

        # 0. Defin field names
        statusla_field = 'StatusLA'
        handedover_field = 'HandedOver'
        package_field = 'CP'
        municipality_field = 'Municipality'
        count_name = 'counts'
        lsuffix_portal = '_Portal'
        rsuffix_excel = '_Excel'
        counts_portal = count_name + lsuffix_portal
        counts_excel = count_name + rsuffix_excel

        # 1.0 Status LA
        keep_fields = [municipality_field, statusla_field]

        ## 1.0.1. GIS Portal
        gis_portal_statusla = gis_portal.groupby(keep_fields)[statusla_field].count().reset_index(name=count_name)
        gis_portal_statusla = gis_portal_statusla.sort_values(by=keep_fields)

        ## 1.0.2. GIS ML
        gis_ml_statusla = gis_table.groupby(keep_fields)[statusla_field].count().reset_index(name=count_name)
        gis_ml_statusla = gis_ml_statusla.sort_values(by=keep_fields)

        ## 1.0.3. Merge
        table = pd.merge(left=gis_portal_statusla, right=gis_ml_statusla, how='outer', left_on=[municipality_field, statusla_field], right_on=[municipality_field, statusla_field])
        table['count_diff'] = np.NAN
        table['count_diff'] = table['counts_y'] - table['counts_x']
        table = table.rename(columns={"counts_x": str(counts_portal), "counts_y": str(counts_excel)})

        arcpy.AddMessage('Merge completed..')
        arcpy.AddMessage('The summary statistics table for StatusLA field is successfully produced.')

        # 2.0. HandedOver
        keep_fields = [municipality_field, handedover_field]

        ## 2.0.1. GIS Portal
        gis_portal_handedover = gis_portal.groupby(keep_fields)[handedover_field].count().reset_index(name=count_name)
        gis_portal_handedover = gis_portal_handedover.sort_values(by=keep_fields)

        ## 2.0.2. GIS ML
        gis_ml_handedover = gis_table.groupby(keep_fields)[handedover_field].count().reset_index(name=count_name)
        gis_ml_handedover = gis_ml_handedover.sort_values(by=keep_fields)

        ## 2.0.3. Merge
        table_handedover = pd.merge(left=gis_portal_handedover, right=gis_ml_handedover, how='outer', left_on=[municipality_field, handedover_field], right_on=[municipality_field, handedover_field])
        table_handedover['count_diff'] = np.NAN
        table_handedover['count_diff'] = table_handedover['counts_y'] - table_handedover['counts_x']
        table_handedover = table_handedover.rename(columns={"counts_x": str(counts_portal), "counts_y": str(counts_excel)})

        arcpy.AddMessage('Merge completed..')
        arcpy.AddMessage('The summary statistics table for HandedOver field is successfully produced.')
        
        # Export the updated GIS portal to excel sheet for checking lot IDs
        try:
            file_name = "CHECK-" + project + "_" + "LA_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx"
        except:
            file_name = "CHECK-LA_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx"
            
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            table.to_excel(writer, sheet_name=statusla_field, index=False)
            table_handedover.to_excel(writer, sheet_name=handedover_field, index=False)

class CheckStructureUpdatedStatusGIS(object):
    def __init__(self):
        self.label = "3.2. Summary Stats for Structure Status (GIS Portal and GIS ML)"
        self.description = "Summary Stats for Structure Status (GIS Portal and GIS ML)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']
    
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_layer = arcpy.Parameter(
            displayName = "GIS Structure Portal File (Excel)",
            name = "GIS Structure Portal File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "GIS Structure ML File (Excel)",
            name = "GIS Structure ML File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_layer, gis_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_layer = params[2].valueAsText
        gis_ml = params[3].valueAsText

        # Read table
        gis_table = pd.read_excel(gis_ml)
        gis_portal = pd.read_excel(gis_layer)

        # 0. Defin field names
        statusla_field = 'StatusStruc'
        package_field = 'CP'
        municipality_field = 'Municipality'
        count_name = 'counts'
        lsuffix_portal = '_Portal'
        rsuffix_excel = '_Excel'
        counts_portal = count_name + lsuffix_portal
        counts_excel = count_name + rsuffix_excel

        # 1.0 Status LA
        keep_fields = [municipality_field, statusla_field]

        ## 1.0.1. GIS Portal
        gis_portal_statusla = gis_portal.groupby(keep_fields)[statusla_field].count().reset_index(name=count_name)
        gis_portal_statusla = gis_portal_statusla.sort_values(by=keep_fields)

        ## 1.0.2. GIS ML
        gis_ml_statusla = gis_table.groupby(keep_fields)[statusla_field].count().reset_index(name=count_name)
        gis_ml_statusla = gis_ml_statusla.sort_values(by=keep_fields)

        ## 1.0.3. Merge
        table = pd.merge(left=gis_portal_statusla, right=gis_ml_statusla, how='outer', left_on=[municipality_field, statusla_field], right_on=[municipality_field, statusla_field])
        table['count_diff'] = np.NAN
        table['count_diff'] = table['counts_y'] - table['counts_x']
        table = table.rename(columns={"counts_x": str(counts_portal), "counts_y": str(counts_excel)})
        
        # table = gis_portal_statusla.join(gis_ml_statusla,lsuffix=lsuffix_portal,rsuffix=rsuffix_excel)
        # table['count_diff'] = np.NAN
        # table['count_diff'] = table[counts_portal] - table[counts_excel]

        arcpy.AddMessage('Merge completed..')
        arcpy.AddMessage('The summary statistics table for StatusLA field is successfully produced.')
        
        # Export the updated GIS portal to excel sheet for checking lot IDs
        try:
            file_name = "CHECK-" + project + "_" + "Structure_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx"
        except:
            file_name = "CHECK-Structure_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx"
            
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            table.to_excel(writer, sheet_name=statusla_field, index=False)

class CheckIsfUpdatedStatusGIS(object):
    def __init__(self):
        self.label = "3.3. Summary Stats for ISF Status (GIS Portal and GIS ML)"
        self.description = "Summary Stats for ISF Status (GIS Portal and GIS ML)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']
    
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_layer = arcpy.Parameter(
            displayName = "GIS ISF Portal File (Excel)",
            name = "GIS ISF Portal File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "GIS ISF ML File (Excel)",
            name = "GIS ISF ML File (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_layer, gis_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_layer = params[2].valueAsText
        gis_ml = params[3].valueAsText

        # Read table
        gis_table = pd.read_excel(gis_ml)
        gis_portal = pd.read_excel(gis_layer)

        # 0. Defin field names
        statusla_field = 'StatusRC'
        package_field = 'CP'
        municipality_field = 'Municipality'
        count_name = 'counts'
        lsuffix_portal = '_Portal'
        rsuffix_excel = '_Excel'
        counts_portal = count_name + lsuffix_portal
        counts_excel = count_name + rsuffix_excel

        # 1.0 Status LA
        keep_fields = [municipality_field, statusla_field]

        ## 1.0.1. GIS Portal
        gis_portal_statusla = gis_portal.groupby(keep_fields)[statusla_field].count().reset_index(name=count_name)
        gis_portal_statusla = gis_portal_statusla.sort_values(by=keep_fields)

        ## 1.0.2. GIS ML
        gis_ml_statusla = gis_table.groupby(keep_fields)[statusla_field].count().reset_index(name=count_name)
        gis_ml_statusla = gis_ml_statusla.sort_values(by=keep_fields)

        ## 1.0.3. Merge
        table = pd.merge(left=gis_portal_statusla, right=gis_ml_statusla, how='outer', left_on=[municipality_field, statusla_field], right_on=[municipality_field, statusla_field])
        table['count_diff'] = np.NAN
        table['count_diff'] = table['counts_y'] - table['counts_x']
        table = table.rename(columns={"counts_x": str(counts_portal), "counts_y": str(counts_excel)})
        
        # table = gis_portal_statusla.join(gis_ml_statusla,lsuffix=lsuffix_portal,rsuffix=rsuffix_excel)
        # table['count_diff'] = np.NAN
        # table['count_diff'] = table[counts_portal] - table[counts_excel]

        arcpy.AddMessage('Merge completed..')
        arcpy.AddMessage('The summary statistics table for StatusLA field is successfully produced.')
        
        # Export the updated GIS portal to excel sheet for checking lot IDs
        try:
            file_name = "CHECK-" + project + "_" + "ISF_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx"
        except:
            file_name = "CHECK-ISF_Summary_Statistics_GIS_Portal_and_GIS_ML.xlsx"
            
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            table.to_excel(writer, sheet_name=statusla_field, index=False)

class JustMessage4(object):
    def __init__(self):
        self.label = "4.0. ----- Identify Missing IDs -----"
        self.description = "Update Excel Master List"

class CheckMissingLotIDs(object):
    def __init__(self):
        self.label = "4.1. Check Missing Lot IDs (Rap ML, GIS ML, and GIS Portal)"
        self.description = "Check Missing Lot IDs (Rap ML, GIS ML, and GIS Portal)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']
    
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

        rap_table_ml = arcpy.Parameter(
            displayName = "Rap ML (Excel)",
            name = "Rap ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_table_ml, gis_portal_ml, rap_table_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_table_ml = params[2].valueAsText
        gis_portal_ml = params[3].valueAsText
        rap_table_ml = params[4].valueAsText

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
        
        def toString(table, to_string_fields):
            for field in to_string_fields:
                table[field] = table[field].astype(str)
                table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
            return table
        
        rap_table = pd.read_excel(rap_table_ml) # for checking NVS3, do not use default_na = false
        gis_table = pd.read_excel(gis_table_ml)
        gis_portal = pd.read_excel(gis_portal_ml)

        # rename City/Municipality or City => 'Municipality'
        colname_change = rap_table.columns[rap_table.columns.str.contains('^City|Municipality',regex=True)]
        rap_table = rename_columns_title(rap_table, colname_change[0], 'Municipality')

        join_field = 'LotID'
        rap_status_field = 'StatusLA'
        rap_status_new_field = 'Rap_Status'
        package_field = 'CP'
        municipality_field = 'Municipality'
        handedover_field = 'HandedOver'
        handedover_new_field = 'Rap_HandedOver'
        package_x_field = 'Package_x'
        package_y_field = 'Package_y'
        rap_field = 'Rap_ML'
        gis_field = 'GIS_ML'
        gis_portal_field = 'GIS_Portal'
        need_to_check_field = 'Need_to_Check'

        # Convert to strings
        to_string_fields = [join_field, municipality_field]
        rap_table = toString(rap_table, to_string_fields)
        gis_table = toString(gis_table, to_string_fields)
        gis_portal = toString(gis_portal, to_string_fields)

        ## 1. StatusLA =0 -> StatusLA = empty
        id = rap_table.index[rap_table[rap_status_field] == 0]
        rap_table.loc[id, rap_status_field] = None

        ### 1.0. Keep only 'LotID', 'CP', and 'StatusLA' fields
        #### 1.0.1. RAP ML
        search_names = '|'.join([join_field, municipality_field, rap_status_field])
        bool_list = [e for e in rap_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        rap_table_statusla = rap_table.iloc[:, ind_id]

        #### 1.0.2. GIS ML
        search_names = '|'.join([join_field, municipality_field])
        bool_list = [e for e in gis_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_table_statusla = gis_table.iloc[:, ind_id]

        #### 1.0.3. GIS Portal
        bool_list = [e for e in gis_portal.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_portal_statusla = gis_portal.iloc[:, ind_id]

        ## 1.2. Filter
        rap_lot_ids = unique(rap_table_statusla[join_field])
        gis_lot_ids = unique(gis_table_statusla[join_field])
        gis_portal_lot_ids = unique(gis_portal_statusla[join_field])

        ### 1.3. Identify Lot IDs missing in GIS ML and GIS Portal Ids in reference to RAP ML
        rap_gis_no_ids = [e for e in rap_lot_ids if e not in gis_lot_ids]
        rap_gis_portal_no_ids = [e for e in rap_lot_ids if e not in gis_portal_lot_ids]

        ## compare rap_gis_no_ids with rap_gis_portal_no_ids
        ## Lot ids not commonly observed between these two GIS tables => 'GIS ML' = 'Yes'
        gis_add_lot_ids = [e for e in rap_gis_portal_no_ids if e not in rap_gis_no_ids]

        ## Lot ids from RAP ML missing in GIS ML
        gis_no_ids = rap_table_statusla[rap_table_statusla[join_field].isin(rap_gis_no_ids)]
        gis_no_ids[gis_field] = 'No'

        ## Lot ids from RAP ML missing in GIS Portal
        gis_portal_no_ids = rap_table_statusla[rap_table_statusla[join_field].isin(rap_gis_portal_no_ids)]
        gis_portal_no_ids[gis_portal_field] = 'No'

        ## 1.4. Concatenate two tables (rbind)
        dataframes = [gis_no_ids,gis_portal_no_ids]
        table = pd.concat(dataframes)
        table = table.reset_index(drop=True)
        duplicated_ids = table.index[table.duplicated([join_field]) == True]
        table = table.drop(duplicated_ids)
        table[gis_portal_field] = 'No'

        ## 1.5. Update 'GIS_ML' and 'Env_ML'
        id = table.index[table[join_field].isin(gis_add_lot_ids)]
        table.loc[id, gis_field] = 'Yes'
        table[rap_field] = 'Yes'

        ## 1.6. Add check field
        table = rename_columns_title(table, rap_status_field, rap_status_new_field)
        table[rap_status_new_field] = pd.to_numeric(table[rap_status_new_field], errors='coerce')
        table['Need_to_Check'] = 'No?'
        id = table.index[table[rap_status_new_field].notna()]
        table.loc[id,'Need_to_Check'] = 'Yes'

        ## 1. HandedOver

        ### 1.0. Keep only 'LotID', 'CP', and 'HandedOver' fields
        #### 1.0.1. RAP ML
        handedover_field_search = "^" + handedover_field + "$"
        search_names = '|'.join([join_field, municipality_field, handedover_field_search])
        bool_list = [e for e in rap_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        rap_table_handedover = rap_table.iloc[:, ind_id]

        #### 1.0.2. GIS ML
        search_names = '|'.join([join_field, municipality_field])
        bool_list = [e for e in gis_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_table_handedover = gis_table.iloc[:, ind_id]

        #### 1.0.3. GIS Portal
        bool_list = [e for e in gis_portal.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_portal_handedover = gis_portal.iloc[:, ind_id]

        ## 1.2. Filter
        rap_lot_ids = unique(rap_table_handedover[join_field])
        gis_lot_ids = unique(gis_table_handedover[join_field])
        gis_portal_lot_ids = unique(gis_portal_handedover[join_field])

        ### 1.3. Identify Lot IDs missing in GIS ML and GIS Portal Ids in reference to RAP ML
        rap_gis_no_ids = [e for e in rap_lot_ids if e not in gis_lot_ids]
        rap_gis_portal_no_ids = [e for e in rap_lot_ids if e not in gis_portal_lot_ids]

        ## compare rap_gis_no_ids with rap_gis_portal_no_ids
        ## Lot ids not commonly observed between these two GIS tables => 'GIS ML' = 'Yes'
        gis_add_lot_ids = [e for e in rap_gis_portal_no_ids if e not in rap_gis_no_ids]

        ## Lot ids from RAP ML missing in GIS ML
        gis_no_ids = rap_table_handedover[rap_table_handedover[join_field].isin(rap_gis_no_ids)]
        gis_no_ids[gis_field] = 'No'

        ## Lot ids from RAP ML missing in GIS Portal
        gis_portal_no_ids = rap_table_handedover[rap_table_handedover[join_field].isin(rap_gis_portal_no_ids)]
        gis_portal_no_ids[gis_portal_field] = 'No'

        ## 1.4. Concatenate two tables (rbind)
        dataframes = [gis_no_ids,gis_portal_no_ids]
        table_handedover = pd.concat(dataframes)
        table_handedover = table_handedover.reset_index(drop=True)
        duplicated_ids = table_handedover.index[table_handedover.duplicated([join_field]) == True]
        table_handedover = table_handedover.drop(duplicated_ids)
        table_handedover[gis_portal_field] = 'No'

        ## 1.5. Update 'GIS_ML' and 'Env_ML'
        id = table_handedover.index[table_handedover[join_field].isin(gis_add_lot_ids)]
        table_handedover.loc[id, gis_field] = 'Yes'
        table_handedover[rap_field] = 'Yes'

        ## 1.6. Add check field
        table_handedover = rename_columns_title(table_handedover, handedover_field, handedover_new_field)
        table_handedover[handedover_new_field] = pd.to_numeric(table_handedover[handedover_new_field], errors='coerce')
        table_handedover['Need_to_Check'] = 'No?'
        id = table_handedover.index[table_handedover[handedover_new_field].notna()]
        table_handedover.loc[id,'Need_to_Check'] = 'Yes'

        ## This table shows lot ids which are missing in either GIS ML or GIS Portal or both.
        ## Check the following lots with Envi Team: lots with status in Envi Table but not reflected in GIS ML or GIS Portal or both.
        try:
            file_name = "CHECK-" + project + "_" + "LA_Missing_Lot_IDs.xlsx"
        except:
            file_name = "_" + "LA_Missing_Lot_IDs.xlsx"
        
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            table.to_excel(writer, sheet_name=rap_status_field, index=False)
            table_handedover.to_excel(writer, sheet_name=handedover_field, index=False)

class CheckMissingStructureIDs(object):
    def __init__(self):
        self.label = "4.2. Check Missing Structure IDs (Rap ML, GIS ML, and GIS Portal)"
        self.description = "Check Missing Structure IDs (Rap ML, GIS ML, and GIS Portal)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']
    
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_table_ml = arcpy.Parameter(
            displayName = "GIS Structure ML (Excel)",
            name = "GIS Structure ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_portal_ml = arcpy.Parameter(
            displayName = "GIS Structure Portal (Excel)",
            name = "GIS Structure Portal (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_table_ml = arcpy.Parameter(
            displayName = "Rap Structure ML (Excel)",
            name = "Rap Structure ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_table_ml, gis_portal_ml, rap_table_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_table_ml = params[2].valueAsText
        gis_portal_ml = params[3].valueAsText
        rap_table_ml = params[4].valueAsText

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
        
        def toString(table, to_string_fields):
            for field in to_string_fields:
                table[field] = table[field].astype(str)
                table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
            return table
        
        rap_table = pd.read_excel(rap_table_ml) # for checking NVS3, do not use default_na = false
        gis_table = pd.read_excel(gis_table_ml)
        gis_portal = pd.read_excel(gis_portal_ml)

        # rename City/Municipality or City => 'Municipality'
        colname_change = rap_table.columns[rap_table.columns.str.contains('^City|Municipality',regex=True)]
        rap_table = rename_columns_title(rap_table, colname_change[0], 'Municipality')

        join_field = 'StrucID'
        rap_status_field = 'StatusStruc'
        rap_status_new_field = 'Rap_Status'
        package_field = 'CP'
        municipality_field = 'Municipality'
        rap_field = 'Rap_ML'
        gis_field = 'GIS_ML'
        gis_portal_field = 'GIS_Portal'
        need_to_check_field = 'Need_to_Check'

        # Convert to strings
        to_string_fields = [join_field, municipality_field]
        rap_table = toString(rap_table, to_string_fields)
        gis_table = toString(gis_table, to_string_fields)
        gis_portal = toString(gis_portal, to_string_fields)

        ## 1. StatusLA =0 -> StatusLA = empty
        id = rap_table.index[rap_table[rap_status_field] == 0]
        rap_table.loc[id, rap_status_field] = None

        ### 1.0. Keep only 'LotID', 'CP', and 'StatusLA' fields
        #### 1.0.1. RAP ML
        search_names = '|'.join([join_field, municipality_field, rap_status_field])
        bool_list = [e for e in rap_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        rap_table_statusla = rap_table.iloc[:, ind_id]

        #### 1.0.2. GIS ML
        search_names = '|'.join([join_field, municipality_field])
        bool_list = [e for e in gis_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_table_statusla = gis_table.iloc[:, ind_id]

        #### 1.0.3. GIS Portal
        bool_list = [e for e in gis_portal.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_portal_statusla = gis_portal.iloc[:, ind_id]

        ## 1.2. Filter
        rap_lot_ids = unique(rap_table_statusla[join_field])
        gis_lot_ids = unique(gis_table_statusla[join_field])
        gis_portal_lot_ids = unique(gis_portal_statusla[join_field])

        ### 1.3. Identify Lot IDs missing in GIS ML and GIS Portal Ids in reference to RAP ML
        rap_gis_no_ids = [e for e in rap_lot_ids if e not in gis_lot_ids]
        rap_gis_portal_no_ids = [e for e in rap_lot_ids if e not in gis_portal_lot_ids]

        ## compare rap_gis_no_ids with rap_gis_portal_no_ids
        ## Lot ids not commonly observed between these two GIS tables => 'GIS ML' = 'Yes'
        gis_add_lot_ids = [e for e in rap_gis_portal_no_ids if e not in rap_gis_no_ids]

        ## Lot ids from RAP ML missing in GIS ML
        gis_no_ids = rap_table_statusla[rap_table_statusla[join_field].isin(rap_gis_no_ids)]
        gis_no_ids[gis_field] = 'No'

        ## Lot ids from RAP ML missing in GIS Portal
        gis_portal_no_ids = rap_table_statusla[rap_table_statusla[join_field].isin(rap_gis_portal_no_ids)]
        gis_portal_no_ids[gis_portal_field] = 'No'

        ## 1.4. Concatenate two tables (rbind)
        dataframes = [gis_no_ids,gis_portal_no_ids]
        table = pd.concat(dataframes)
        table = table.reset_index(drop=True)
        duplicated_ids = table.index[table.duplicated([join_field]) == True]
        table = table.drop(duplicated_ids)
        table[gis_portal_field] = 'No'

        ## 1.5. Update 'GIS_ML' and 'Env_ML'
        id = table.index[table[join_field].isin(gis_add_lot_ids)]
        table.loc[id, gis_field] = 'Yes'
        table[rap_field] = 'Yes'

        ## 1.6. Add check field
        table = rename_columns_title(table, rap_status_field, rap_status_new_field)
        table[rap_status_new_field] = pd.to_numeric(table[rap_status_new_field], errors='coerce')
        table['Need_to_Check'] = 'No?'
        id = table.index[table[rap_status_new_field].notna()]
        table.loc[id,'Need_to_Check'] = 'Yes'

        ## This table shows lot ids which are missing in either GIS ML or GIS Portal or both.
        ## Check the following lots with Envi Team: lots with status in Envi Table but not reflected in GIS ML or GIS Portal or both.
        try:
            file_name = "CHECK-" + project + "_" + "Structure_Missing_IDs.xlsx"
        except:
            file_name = "_" + "Structure_Missing_IDs.xlsx"
        
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            table.to_excel(writer, sheet_name=rap_status_field, index=False)

class CheckMissingIsfIDs(object):
    def __init__(self):
        self.label = "4.3. Check Missing ISF (NLO) IDs (Rap ML, GIS ML, and GIS Portal)"
        self.description = "Check Missing ISF (NLO) IDs (Rap ML, GIS ML, and GIS Portal)"

    def getParameterInfo(self):
        proj = arcpy.Parameter(
            displayName = "Project Extension: N2 or SC",
            name = "Project Extension: N2 or SC",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        proj.filter.type = "ValueList"
        proj.filter.list = ['N2', 'SC']
    
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        gis_table_ml = arcpy.Parameter(
            displayName = "GIS ISF ML (Excel)",
            name = "GIS ISF ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_portal_ml = arcpy.Parameter(
            displayName = "GIS ISF Portal (Excel)",
            name = "GIS ISF Portal (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_table_ml = arcpy.Parameter(
            displayName = "Rap ISF ML (Excel)",
            name = "Rap ISF ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_table_ml, gis_portal_ml, rap_table_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_table_ml = params[2].valueAsText
        gis_portal_ml = params[3].valueAsText
        rap_table_ml = params[4].valueAsText

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
        
        def toString(table, to_string_fields):
            for field in to_string_fields:
                table[field] = table[field].astype(str)
                table[field] = table[field].replace(r'\s+|^\w\s$','',regex=True)
            return table
        
        rap_table = pd.read_excel(rap_table_ml) # for checking NVS3, do not use default_na = false
        gis_table = pd.read_excel(gis_table_ml)
        gis_portal = pd.read_excel(gis_portal_ml)

        # rename City/Municipality or City => 'Municipality'
        colname_change = rap_table.columns[rap_table.columns.str.contains('^City|Municipality',regex=True)]
        rap_table = rename_columns_title(rap_table, colname_change[0], 'Municipality')

        join_field = 'StrucID'
        rap_status_field = 'StatusRC'
        rap_status_new_field = 'Rap_Status'
        package_field = 'CP'
        municipality_field = 'Municipality'
        rap_field = 'Rap_ML'
        gis_field = 'GIS_ML'
        gis_portal_field = 'GIS_Portal'
        need_to_check_field = 'Need_to_Check'

        # Convert to strings
        to_string_fields = [join_field, municipality_field]
        rap_table = toString(rap_table, to_string_fields)
        gis_table = toString(gis_table, to_string_fields)
        gis_portal = toString(gis_portal, to_string_fields)

        ## 1. StatusLA =0 -> StatusLA = empty
        id = rap_table.index[rap_table[rap_status_field] == 0]
        rap_table.loc[id, rap_status_field] = None

        ### 1.0. Keep only 'LotID', 'CP', and 'StatusLA' fields
        #### 1.0.1. RAP ML
        search_names = '|'.join([join_field, municipality_field, rap_status_field])
        bool_list = [e for e in rap_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        rap_table_statusla = rap_table.iloc[:, ind_id]

        #### 1.0.2. GIS ML
        search_names = '|'.join([join_field, municipality_field])
        bool_list = [e for e in gis_table.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_table_statusla = gis_table.iloc[:, ind_id]

        #### 1.0.3. GIS Portal
        bool_list = [e for e in gis_portal.columns.str.contains(search_names, regex=True)]
        ind_id = [i for i, val in enumerate(bool_list) if val]
        gis_portal_statusla = gis_portal.iloc[:, ind_id]

        ## 1.2. Filter
        rap_lot_ids = unique(rap_table_statusla[join_field])
        gis_lot_ids = unique(gis_table_statusla[join_field])
        gis_portal_lot_ids = unique(gis_portal_statusla[join_field])

        ### 1.3. Identify Lot IDs missing in GIS ML and GIS Portal Ids in reference to RAP ML
        rap_gis_no_ids = [e for e in rap_lot_ids if e not in gis_lot_ids]
        rap_gis_portal_no_ids = [e for e in rap_lot_ids if e not in gis_portal_lot_ids]

        ## compare rap_gis_no_ids with rap_gis_portal_no_ids
        ## Lot ids not commonly observed between these two GIS tables => 'GIS ML' = 'Yes'
        gis_add_lot_ids = [e for e in rap_gis_portal_no_ids if e not in rap_gis_no_ids]

        ## Lot ids from RAP ML missing in GIS ML
        gis_no_ids = rap_table_statusla[rap_table_statusla[join_field].isin(rap_gis_no_ids)]
        gis_no_ids[gis_field] = 'No'

        ## Lot ids from RAP ML missing in GIS Portal
        gis_portal_no_ids = rap_table_statusla[rap_table_statusla[join_field].isin(rap_gis_portal_no_ids)]
        gis_portal_no_ids[gis_portal_field] = 'No'

        ## 1.4. Concatenate two tables (rbind)
        dataframes = [gis_no_ids,gis_portal_no_ids]
        table = pd.concat(dataframes)
        table = table.reset_index(drop=True)
        duplicated_ids = table.index[table.duplicated([join_field]) == True]
        table = table.drop(duplicated_ids)
        table[gis_portal_field] = 'No'

        ## 1.5. Update 'GIS_ML' and 'Env_ML'
        id = table.index[table[join_field].isin(gis_add_lot_ids)]
        table.loc[id, gis_field] = 'Yes'
        table[rap_field] = 'Yes'

        ## 1.6. Add check field
        table = rename_columns_title(table, rap_status_field, rap_status_new_field)
        table[rap_status_new_field] = pd.to_numeric(table[rap_status_new_field], errors='coerce')
        table['Need_to_Check'] = 'No?'
        id = table.index[table[rap_status_new_field].notna()]
        table.loc[id,'Need_to_Check'] = 'Yes'

        ## This table shows lot ids which are missing in either GIS ML or GIS Portal or both.
        ## Check the following lots with Envi Team: lots with status in Envi Table but not reflected in GIS ML or GIS Portal or both.
        try:
            file_name = "CHECK-" + project + "_" + "ISF_Missing_Structure_IDs.xlsx"
        except:
            file_name = "_" + "ISF_Missing_Structure_IDs.xlsx"
        
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            table.to_excel(writer, sheet_name=rap_status_field, index=False)
