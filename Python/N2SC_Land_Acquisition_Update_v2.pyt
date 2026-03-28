from pandas.plotting import table

import arcpy
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
import re
import string


#-----------------------------------#
## Define user functions anc class ##
#-----------------------------------#
def unique(lists):
    collect = []
    unique_list = pd.Series(lists).drop_duplicates().tolist()
    for x in unique_list:
        collect.append(x)
    return(collect)

def unique_values(table, field):  ##uses list comprehension
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor if row[0] is not None})

## 3. Return non-matched values between two lists
def non_match_elements(list_a, list_b):
    non_match = []
    for i in list_a:
        if i not in list_b:
            non_match.append(i)
    return non_match

def first_letter_capital(table, column_names): # column_names are list
    for name in column_names:
        table[name] = table[name].str.title()
    return table

def rename_city_to_municipality(table, renamed_city):
    col = table.columns[table.columns.str.contains('|'.join(['City','city', 'Muni']))]
    table = table.rename(columns={str(col[0]): renamed_city})
    return table

def replace_strings_table(table, field, array):
    """
    table: pandas dataFrame
    field: field to be updated
    array: array of pattern and replacement strings (e.g., {r'3A|3B': '3a', r''...})
    """
    # for item in array:
    #     table[field] = table[field].apply(lambda x: re.sub(item, array[item], str(x)))
    for item in array:
        table[field] = table[field].str.replace(item, array[item], regex=True)
        table[field] = table[field].apply(lambda x: re.sub(item, array[item], str(x)))
    return table

def toString(table, to_string_fields):
    for field in to_string_fields:
        table[field] = table[field].astype(str)
        table[field] = table[field].replace(r'\s+', '', regex=True)
    return table

def find_duplicates_ordered(arr):
    seen = set()
    duplicates = set()
    for item in arr:
        if item in seen:
            duplicates.add(item) # Use a set to avoid adding the same duplicate multiple times
        else:
            seen.add(item)
    return list(duplicates)

def remove_underline_hyphen_from_numeric_field(table, fields_list):
    for field in fields_list:
        table[field] = table[field].replace(r'^[_-]','',regex=True)
        return table
    
def convert_lotids_to_correct_cp(table, search_field, lotids, cp_field, new_cp):
    ids= table.index[table[search_field].str.contains(rf"{lotids}",regex=True,na=False)]
    table.loc[ids, cp_field] = new_cp
    return table

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

### Check missing field between tables
def identify_missing_ids_excel(table1, table2, field1, field2):    
    ids1 = table1[field1].values
    ids2 = table2[field2].values
    noids_ids2 = [id for id in ids1 if id not in ids2]
    noids_id1 = [id for id in ids2 if id not in ids1]
    noids = noids_ids2 + noids_id1
    return noids

def identify_missing_ids_fc(ids1, ids2):
    noids_ids2 = [id for id in ids1 if id not in ids2]
    noids_id1 = [id for id in ids2 if id not in ids1]
    noids = noids_ids2 + noids_id1
    return noids

### Pier Workability
def extract_ids_for_assign_obstruction(proj, table, field, field2=None):
    if proj == 'N2':
        table = table.dropna(subset=[field]).reset_index(drop=True)
        table[field] = table[field].astype(str)
        table[field] = table[field].str.lstrip(',')
        ids_flat = flatten_extend(table[field].str.split(','))          
        ids = unique(ids_flat)
        ids = remove_empty_strings(ids)
    else:
        ids = table.index[table[field] == 1]
        ids_flat = flatten_extend(table.loc[ids, field2].str.split(","))
        ids = unique(ids_flat)
        ids = remove_empty_strings(ids)
    return ids

def summary_statistics_count_ids(proj, cp, rap_ids, gisml_ids, gisportal_ids):
    noids_rap_vs_gisml = ",".join(non_match_elements(rap_ids, gisml_ids))
    noids_rap_vs_gisportal = ",".join(non_match_elements(rap_ids, gisportal_ids))
    rap_vs_gisml = len(rap_ids) - len(gisml_ids)
    rap_vs_gisportal = len(rap_ids) - len(gisportal_ids)
    params = [cp, len(rap_ids), len(gisml_ids), len(gisportal_ids), rap_vs_gisml, rap_vs_gisportal, noids_rap_vs_gisml, noids_rap_vs_gisportal]
    columns = ['cp', 'rap', 'gis_ml', 'gis_portal', 'rap_vs_gisml', 'rap_vs_gisportal', 'noIDs_rap_vs_gisml', 'noIDs_rap_vs_gisportal']
    table = pd.DataFrame(columns=columns)
    for i in range(0, len(columns)):
        table.loc[0, columns[i]] = params[i]
    
    # Add remarks
    if len(noids_rap_vs_gisml) > 0:
        table['remark'] = f"**{noids_rap_vs_gisml} were manually assigned 'Yes' in the Obstruction field of GIS_{proj}_ML.xlsx."
    return [table, noids_rap_vs_gisml]

### Custom class for generating a summary statistics table
def summary_by_field(table, stats_type, stats_field, groupby_fields):
    count_name = 'temp'
    if stats_type == 'count':
        table = table.groupby(groupby_fields)[stats_field].count().reset_index(name=count_name).sort_values(by=groupby_fields).to_numpy()
    else:
        table = table.groupby(groupby_fields)[stats_field].sum().reset_index(name=count_name).sort_values(by=groupby_fields).to_numpy()

    arrays = {}
    for i, field in enumerate(groupby_fields + ['values1']):
        values = [f[i] for f in table]
        arrays[f"{field}"] = values
    return arrays

class summaryStatistics():
    # Make sure to use a list for groupby_field
    # The first field in groupby_fields will be a primary field for generating statistics.
    # Provide output table columns
    def __init__(self, table1, table2, stats_type, stats_field, groupby_fields):
        self.tab1 = table1
        self.tab2 = table2
        self.stat_tp = stats_type
        self.stat_fd = stats_field
        self.gpby_fds = groupby_fields

    def process_data_before_after(self):
        def calculate_summary():
            summary_tab1 = summary_by_field(self.tab1, self.stat_tp, self.stat_fd, self.gpby_fds)
            summary_tab2 = summary_by_field(self.tab2, self.stat_tp, self.stat_fd, self.gpby_fds)
            return {"table1": summary_tab1, "table2": summary_tab2}

        def calculate_differene_before_after():
            stats = calculate_summary()

            #-- Create an empty dataframe
            arcpy.AddMessage(stats)
            stats0 = stats['table1']
            stats0['values2'] = stats['table2']['values1']
            stats0['dff'] = np.array(stats0['values1']) - np.array(stats0['values2'])
            final = pd.DataFrame(stats0)

            #-- Rename columns
            final = final.rename(columns={'values1': 'Table1', 'values2': 'Table2'})
            return final
    
        s_table = calculate_differene_before_after()
        return s_table


class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [RestoreScaleForLot, JustMessage1, CompileRAPtables, UpdateLot, UpdateISF, UpdateStructure,
                      JustMessage10, AddObstructionToLotN2, AddObstructionToStructureN2, AddObstructionToLotSC, AddObstructionToStructureSC,
                      JustMessage2, UpdateLotGIS, UpdateStructureGIS,
                      JustMessage3, GenerateStatisticsBetweenTwoTables,
                      JustMessage4, CompareStringFieldExcelTables, CompareStringFieldFeatureClasses,
                      ]

class RestoreScaleForLot(object):
    def __init__(self):
        self.label = "0.0. Add Scale To GIS Excel ML for Lot (Optional)"
        self.description = "Add Scale To GIS Excel ML for Lot (Optional)"

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
            transfer_field = "Scale"

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

class CompileRAPtables(object):
    def __init__(self):
        self.label = "1.1. Compile RAP Master Lists including Historical Records (Lot)"
        self.description = "Compile RAP Master Lists including Historical Records (Lot)"

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

        rap_ml_dir = arcpy.Parameter(
            displayName = "Directory of RAP Master Lists (Latest ML in the last of the latest year folder)",
            name = "Directory of RAP Master Lists",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, rap_ml_dir]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        rap_ml_dir = params[1].valueAsText

        def N2SC_Compile_RAP_tables():
              
            lotid_field = 'LotID'
            status_field = 'StatusLA'
            renamed_city = 'Municipality'
            handedOverArea_field = 'HandedOverArea'
            handedOverDate_field = 'HandedOverDate'
            affectedArea_field = 'AffectedArea'
            totalarea_field = 'TotalArea'
            note_field = 'note'
            
            # Read and compile a list of RAP ML files from each directory:
            rap_dirs = [dir for dir in os.listdir(rap_ml_dir) if dir.startswith('20') and os.path.isdir(os.path.join(rap_ml_dir, dir))]# extract ONLY folder starting with '20..'
            rap_files_dirs = [os.path.join(rap_ml_dir, file) for file in rap_dirs] # rap_ml_dir = "'C:\\Users\\oc3512\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\02-Pre-Construction\\01-Environment\\01-LAR\\99-MasterList\\00-N2_RAP_Compiled"
            rap_files = [os.path.join(dir, file) for dir in rap_files_dirs for file in os.listdir(dir) if file.endswith('.xlsx')]
        
            # Each ML is merged with the latest ML
            yyyymm_latest = os.path.basename(rap_files[-1])[:8]
            latest_ml = pd.read_excel(rap_files[-1])
            latest_ml = remove_underline_hyphen_from_numeric_field(latest_ml, [affectedArea_field, totalarea_field])

            latest_ml = toString(latest_ml, [lotid_field])
            latest_ml['x' + yyyymm_latest] = latest_ml[status_field]
            latest_ml['x' + yyyymm_latest + '_HOA'] = latest_ml[handedOverArea_field] # HOA: Handed-Over Area
            latest_ml['x' + yyyymm_latest + '_TAA'] = latest_ml[affectedArea_field] # TAA: Total Affected Area
            latest_ml[note_field] = ""

            # compiled_ml = pd.DataFrame()
            for file in rap_files[:-1]:
                arcpy.AddMessage(f"Check input table: {file}")
                table0 = pd.read_excel(file)
                table0 = remove_underline_hyphen_from_numeric_field(table0, [affectedArea_field, totalarea_field])
                table0 = toString(table0, [lotid_field])
                yyyymm = os.path.basename(file)[:8]

                # Check if lotIds are matched with the latest ML
                input_lotids = table0[lotid_field].values
                target_lotids = latest_ml[lotid_field].values

                # Check duplicated LotID, if found, exit the loop.
                input_duplicated = find_duplicates_ordered(input_lotids)
                target_duplicated = find_duplicates_ordered(target_lotids)

                arcpy.AddMessage(f"Input duplicated: {input_duplicated}")
                arcpy.AddMessage(f"Target duplicated: {target_duplicated}")

                if (not input_duplicated) and (not target_duplicated):
                    ## when no duplication, proceed:
                    # Check LotIDs are matched between input and target tables.
                    if np.array_equal(input_lotids, target_lotids):
                        # Keep only 'LotID', 'StatusLA', 'TotalAffectedArea', 'HandedOverArea'
                        table = table0[[lotid_field, status_field, affectedArea_field, handedOverArea_field]]
                        table[lotid_field] = table[lotid_field].astype(str)

                        # Rename columns
                        table = table.rename(columns={status_field: 'x' + yyyymm, affectedArea_field: 'x' + yyyymm + '_TAA', handedOverArea_field: 'x' + yyyymm + '_HOA'})

                        # Merge to the latest
                        latest_ml = pd.merge(left=latest_ml, right=table, how='left', left_on=lotid_field, right_on=lotid_field)
                    
                    else:
                        # when lotID is not matched, there are two scenarios:
                        ## 1. Unmatched LotIDs arise from the same lot:
                        ## 1.1. The lotID was subdivided before but merged into one lot.
                        ### E.g., Input table: 003A, 003B, Target table: 003

                        ## 1.2. The lotID has been subdivided but was one lot.
                        ### E.g., Input table: 003, Target table: 003A, 003B
                        arcpy.AddMessage(input_lotids)
                        arcpy.AddMessage(target_lotids)
                        input_non_match_ids = list(np.setdiff1d(input_lotids, target_lotids))
                        target_non_match_ids = list(np.setdiff1d(target_lotids, input_lotids))

                        # Case 1: lot was subdivided in the past.
                        arcpy.AddMessage(f"Input non-match ids: {input_non_match_ids}")
                        arcpy.AddMessage(f"Target non-match ids: {target_non_match_ids}")

                        for i, lot in enumerate(target_non_match_ids):
                            # arcpy.AddMessage(f"target lot: {lot}")
                            items = [item for item in input_non_match_ids if item.startswith("".join([i for i in lot if i.isdigit()]))]
                            # arcpy.AddMessage(f"items: {items}")

                            if items:
                                id = latest_ml.query(f"{lotid_field} == '{lot}'").index
                                add_items = ','.join(np.array(items).flatten())
                                existing = latest_ml.loc[id, note_field].values[0]
                                if existing:
                                    new_items = existing + "; " + add_items + " (" + yyyymm + ")"
                                    latest_ml.loc[id, note_field] = new_items
                                else:
                                    latest_ml.loc[id, note_field] = add_items + " (" + yyyymm + ")"
                        
                        # Keep only 'LotID', 'TotalAffectedArea', 'HandedOverArea'
                        table = table0[[lotid_field, status_field, affectedArea_field, handedOverArea_field]]
                        table = table.rename(columns={status_field: 'x' + yyyymm, affectedArea_field: 'x' + yyyymm + '_TAA', handedOverArea_field: 'x' + yyyymm + '_HOA'})
                        # table = table.rename(columns={status_field: 'x' + yyyymm, lotid_field: 'x' + yyyymm + '_LOT', affectedArea_field: 'x' + yyyymm + '_TAA', handedOverArea_field: 'x' + yyyymm + '_HOA'})
                        # table[lotid_field] = table0[lotid_field]

                        arcpy.AddMessage(table.head())
                        arcpy.AddMessage(latest_ml.head())
                        latest_ml = pd.merge(left=latest_ml, right=table, how='left', left_on='LotID', right_on='LotID')

                        ## 2. Unmatched LotIDs arise from different lots:
                        ### In this case, we ignore.

                    
                    #--- 'StatusLA' = 0 => None ---#
                    cols = latest_ml.filter(regex='\\d+$', axis=1).columns
                    for col in cols:
                        idx = latest_ml.query(f"{col} == 0").index
                        if len(idx) > 0:
                            latest_ml.loc[idx, col] = None
                    idx = latest_ml.query(f"{status_field} == 0").index
                    latest_ml.loc[idx, status_field] = None

                    #--- HandedOverDate ---#
                    ## remove "-", "_"
                    latest_ml[handedOverDate_field] = latest_ml[handedOverDate_field].replace(r'^[-_]','',regex=True)

                    #--- Rename a field to 'Municipality'
                    latest_ml = rename_city_to_municipality(latest_ml, renamed_city)

                    #--- Save the compiled master list ---#
                    latest_ml[note_field] = latest_ml.pop(note_field)
                    yyyymmdd_latest = os.path.basename(rap_files[-1])[:8]
                    export_file_name = str(yyyymmdd_latest) + "_" + proj + '_Compiled_RAP_Master_List' + '.xlsx'
                    export_file_path = os.path.join(rap_ml_dir, export_file_name)
                    latest_ml.to_excel(export_file_path, index=False)
                else:
                    arcpy.AddError('There are duplicated Ids in RAP table shown above. The Process stopped. Please correct the duplicated rows.')
                    break

        N2SC_Compile_RAP_tables()

class UpdateLot(object):
    def __init__(self):
        self.label = "1.2. Update Excel Master List (Lot)"
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
            displayName = "GIS Land Status ML (Excel) - only for joining scale",
            name = "GIS Land Status ML (Excel) only for joining scale",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_lot_ms = arcpy.Parameter(
            displayName = "RAP Land Status ML Compiled (Excel)",
            name = "RAP Land Status ML (Excel)",
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

        params = [proj, gis_dir, gis_lot_ms, rap_lot_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_lot_ms = params[2].valueAsText
        rap_lot_ms = params[3].valueAsText
        gis_bakcup_dir = params[4].valueAsText
        lastupdate = params[5].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def N2SC_Land_Update():

            # Join Field & Define all fields
            joinField = 'LotID'
            package_field = 'CP'
            land_use_field = 'LandUse'
            endorsed_field = 'Endorsed'
            total_area_field = 'TotalArea'
            affected_area_field = 'AffectedArea'
            remaining_area_field = 'RemainingArea'
            handedover_area_field = 'HandedOverArea'
            handedover_field = 'HandedOver'
            handover_date_field = 'HandOverDate'
            handedover_date_field = 'HandedOverDate'
            percent_handedover_area_field = 'percentHandedOver'
            priority_field = 'Priority'
            statusla_field = 'StatusLA'
            moa_field = 'MoA'
            pte_field = 'PTE'
            scale_field = 'Scale'
            renamed_city = 'Municipality'

            # Define numeric and string fields
            numeric_fields_common = [total_area_field, affected_area_field, remaining_area_field, handedover_area_field, handedover_field, priority_field, statusla_field, moa_field, pte_field]
            to_string_fields = [joinField, package_field]

            # Import excel files
            rap_table_origin = pd.read_excel(rap_lot_ms)
            rap_table = pd.read_excel(rap_lot_ms)
            gis_table = pd.read_excel(gis_lot_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Land_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Land_Status'))

            # Check duplicated LotID
            duplicated_Ids = rap_table[rap_table.duplicated([joinField]) == True][joinField]

            if len(duplicated_Ids) == 0:
                ## Create column indices
                column_names = rap_table.columns
                city_field = [field for field in column_names if re.search('City|Municipal', field)][0]
                column_indices = {name: i for i, name in enumerate(column_names)}

                ## Rename Municipality
                if proj == 'N2':
                    municipal_col_index = column_indices[city_field]
                    to_numeric_fields = numeric_fields_common + [endorsed_field]
                else:
                    municipal_col_index = column_indices[city_field]
                    to_numeric_fields = numeric_fields_common

                rap_table = rap_table.rename(columns={column_names[municipal_col_index]: renamed_city})
                rap_table_origin = rap_table_origin.rename(columns={column_names[municipal_col_index]: renamed_city})
                non_match_col = non_match_elements(to_numeric_fields, column_names)
                [to_numeric_fields.remove(non_match_col[0]) if non_match_col else arcpy.AddMessage('no need to remove field from the list for numeric conversion')]

                ## Convert to numeric 
                for field in to_numeric_fields:
                    # you need to keep [] a set of characters in regex; otherwise, error.
                    rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s$]','',regex=True)
                    rap_table[field] = pd.to_numeric(rap_table[field])

                    rap_table_origin[field] = rap_table_origin[field].replace(r'\s+|[^\w\s$]','',regex=True)
                    rap_table_origin[field] = pd.to_numeric(rap_table_origin[field])
                    
                ## Conver to string
                rap_table = toString(rap_table, to_string_fields)
                rap_table_origin = toString(rap_table_origin, to_string_fields)
                gis_table[joinField] = gis_table[joinField].astype(str)

                ## Reformat CP
                if proj == 'N2':
                    rap_table[package_field] = rap_table[package_field].str.replace(r'N','N-',regex=True)
                else:
                    arrays = {
                        r'3A|3A|3a': '3a',
                        r'3B|3B|3b': '3b',
                        r'3C|3C|3c': '3c',
                        r'/.*|,.*': ''
                    }
                    rap_table = replace_strings_table(rap_table, package_field, arrays)

                    rap_table = convert_lotids_to_correct_cp(rap_table, joinField, '10155|10156|10158-5', package_field, "S-01")
                    rap_table = convert_lotids_to_correct_cp(rap_table, joinField, '60136-A', package_field, "S-04")
                    rap_table = convert_lotids_to_correct_cp(rap_table, joinField, '^100003$|^100004$|^100005$|^100010$', package_field, "S-06")
                
                #--- Get the first CP (e.g., N-03,N-02 => N-03)
                rap_table[package_field] = rap_table[package_field].apply(lambda x: re.sub(r',.*','',x))
                
                # Convert to date   
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
                rap_table = pd.merge(left=rap_table, right=lot_gis_scale, how='left', left_on=joinField, right_on=joinField, validate="one_to_one")

                # Fix StatusLA
                ## StatusLA =0 -> StatusLA = empty
                rap_table.loc[rap_table.query(f'{statusla_field} == 0').index, statusla_field] = None

                ## 4. if the first row is empty, temporarily add the first row for 'HandedOverDate' and 'HandOverDate'
                for field in to_date_fields:
                    date_item = rap_table[field].iloc[:1].item()
                    if date_item is None or pd.isnull(date_item):
                        rap_table.loc[0, field] = pd.to_datetime('1990-01-01')

                ## 5. is.na(HandedOverArea) -> HandedOverArea = 0
                rap_table.loc[rap_table.query(f'{handedover_area_field}.isna() or {handedover_area_field}.isna()').index, handedover_area_field] = 0

                #--- Calculate percent handed-over
                rap_table[percent_handedover_area_field] = round((rap_table[handedover_area_field] / rap_table[affected_area_field])*100,0)

                #---
                
                # Export
                export_file_name = os.path.splitext(os.path.basename(gis_lot_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                rap_table.to_excel(to_excel_file, index=False)

                arcpy.AddMessage("The master list was successfully exported.")

                #*****************************************************************************************
                # Create summary statistics between rap_table and updated GIS table to confirm matching #
                #*****************************************************************************************
                arrays = {
                        r'3A|3A|3a': '3a',
                        r'3B|3B|3b': '3b',
                        r'3C|3C|3c': '3c',
                        r'/.*|,.*': ''
                    }
                rap_table_origin = replace_strings_table(rap_table_origin, package_field, arrays)
                
                ## Count of statusLA by municipality
                s_statusla = summaryStatistics(rap_table_origin, rap_table, "count", statusla_field, [renamed_city, statusla_field])
                statusla_stats = s_statusla.process_data_before_after()

                ## Count of handed-over lots
                s_handedover = summaryStatistics(rap_table_origin, rap_table, "count", handedover_field, [renamed_city, handedover_field])
                handedover_stats = s_handedover.process_data_before_after()

                ## Total affected area by Municipality
                s_affectedarea = summaryStatistics(rap_table_origin, rap_table, "sum", affected_area_field, [renamed_city])
                affectedarea_stats = s_affectedarea.process_data_before_after()

                ### 3.0. Export summary statistics table
                file_name_stats = 'CHECK-' + proj + '_LA_Summary_Statistics_Rap_and_GIS_ML.xlsx'
                to_excel_file0 = os.path.join(gis_dir, file_name_stats)

                with pd.ExcelWriter(to_excel_file0) as writer:
                    statusla_stats.to_excel(writer, sheet_name=statusla_field, index=False)
                    statusla_stats.to_excel(writer, sheet_name=statusla_field, index=False)
                    handedover_stats.to_excel(writer, sheet_name=handedover_field, index=False)
                    affectedarea_stats.to_excel(writer, sheet_name=affected_area_field, index=False)

            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids in RAP table shown above. The Process stopped. Please correct the duplicated rows.')
                pass

        N2SC_Land_Update()

class UpdateISF(object):
    def __init__(self):
        self.label = "1.3. Update Excel Master List (ISF)"
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

        def N2SC_ISF_Update():
            rap_table_stats = pd.read_excel(rap_isf_ms)
            rap_table = pd.read_excel(rap_isf_ms)
            gis_table = pd.read_excel(gis_isf_ms)

            # Field definitions
            municipality_field = 'Municipality'
            barangay_field = 'Barangay'
            structure_id_field = 'StrucID'
            nlo_status_field = 'StatusRC'
            package_field = 'CP'

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_" + "ISF_Relocation_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format('ISF_Relocation_Status'))
            
            # Rename 'City' to Municipality
            try:
                rap_table = rename_city_to_municipality(rap_table, municipality_field)
                rap_table = first_letter_capital(rap_table, [municipality_field])

                # For Summary Stats
                rap_table = rename_city_to_municipality(rap_table, municipality_field)
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
            to_string_fields = [municipality_field, barangay_field, structure_id_field, package_field]
            for field in to_string_fields:
                rap_table[field] = rap_table[field].astype(str)
                rap_table_stats[field] = rap_table_stats[field].astype(str)

            # Re-format CP
            arrays = {
                        r'3A|3A|3a': '3a',
                        r'3B|3B|3b': '3b',
                        r'3C|3C|3c': '3c',
                        r'/.*|,.*': ''
                    }
            rap_table = replace_strings_table(rap_table, package_field, arrays)
            rap_table_stats = replace_strings_table(rap_table_stats, package_field, arrays)

            ## If Projec is N2
            if proj == 'N2':
                rap_table[package_field] = rap_table[package_field].replace(r'N', 'N-',regex=True)
                rap_table_stats[package_field] = rap_table_stats[package_field].replace(r'N', 'N-',regex=True)

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

            #*****************************************************************************************
            # Create summary statistics between rap_table and updated GIS table to confirm matching #
            #*****************************************************************************************
            ## Conver StatusRC = 0 -> NA          
            id = rap_table_stats.index[rap_table_stats[nlo_status_field] == 0]
            rap_table_stats.loc[id, nlo_status_field] = np.nan

            s_statusla = summaryStatistics(rap_table_stats, rap_table, "count", nlo_status_field, [municipality_field, nlo_status_field])
            statusla_stats = s_statusla.process_data_before_after()

            ### Export summary statistics table
            file_name_stats = 'CHECK-' + proj + '_ISF_Summary_Statistics_Rap_and_GIS_ML.xlsx'
            to_excel_file0 = os.path.join(gis_dir, file_name_stats)

            statusla_stats.to_excel(to_excel_file0, index=False)

        N2SC_ISF_Update()

class UpdateStructure(object):
    def __init__(self):
        self.label = "1.4. Update Excel Master List (Structure)"
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
            handover_field = 'HandOver'
            structure_status_field = 'StatusStruc'
            structure_use_field = 'StructureUse'
            family_number_field = 'FamilyNumber'

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
                        joinedFields = [joinField, sc1_contsubm, sc1_subcon, sc1_basic_plan]
                        rap_table_sc1 = pd.read_excel(rap_struc_sc1_ms)
                        rap_table_sc1[sc1_contsubm] = 1

                        # Conver to string with white space removal and uppercase
                        to_string_fields = [joinField]
                        toString(rap_table_sc1, to_string_fields)

                        rap_table[joinField] = rap_table[joinField].apply(lambda x: x.upper())
                        rap_table_sc1[joinField] = rap_table_sc1[joinField].apply(lambda x: x.upper())

                        # Filter fields
                        rap_table_sc1 = rap_table_sc1[joinedFields]
                        rap_table = rap_table.drop(joinedFields[2:], axis=1)
        
                        # Left join
                        rap_table[joinField] = rap_table[joinField].astype(str)
                        rap_table_sc1[joinField] = rap_table_sc1[joinField].astype(str)
                        rap_table = pd.merge(left=rap_table, right=rap_table_sc1, how='left', left_on=joinField, right_on=joinField)

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
                rap_table_stats = rap_table_stats.rename(columns={str(colname_change[0]): municipality_field})
                rap_table_stats = first_letter_capital(rap_table_stats, [municipality_field])

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
                    arrays = {
                        r'3A|3A|3a': '3a',
                        r'3B|3B|3b': '3b',
                        r'3C|3C|3c': '3c',
                        r'/.*|,.*': ''
                    }
                    rap_table = replace_strings_table(rap_table, cp_field, arrays)
                    rap_table_stats = replace_strings_table(rap_table_stats, cp_field, arrays)

                    # Conver the following LotIDs to S-01
                    rap_table = convert_lotids_to_correct_cp(rap_table, joinField, 'NSRP-01-08-ML046', cp_field, "S-01")

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
                toString(rap_relo_table, [joinField])
                rap_relo_table[family_number_field] = 0
                df = rap_relo_table.groupby(joinField).count()[[family_number_field]]
                rap_table = pd.merge(left=rap_table, right=df, how='left', left_on=joinField, right_on=joinField)
            
                # Export
                export_file_name = os.path.splitext(os.path.basename(gis_struc_ms))[0]
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                rap_table.to_excel(to_excel_file, index=False)

                arcpy.AddMessage("The {} master list for structure was successfully exported.".format(proj))

                ##############################################################################
                # Create summary statistics between original rap_table and updated rap_table
                ### StatusLA = 0 -> NA          
                id = rap_table_stats.index[rap_table_stats[structure_status_field] == 0]
                rap_table_stats.loc[id, structure_status_field] = np.nan

                ## Count status for each municipality
                s_statusla = summaryStatistics(rap_table_stats, rap_table, "count", structure_status_field, [municipality_field, structure_status_field])
                status_stats = s_statusla.process_data_before_after()

                ## Count handedover structures for each municipality
                s_handedover = summaryStatistics(rap_table_stats, rap_table, "count", handover_field, [municipality_field, handover_field])
                handedover_stats = s_handedover.process_data_before_after()
 
                ## Export summary statistics table
                file_name_stats = 'CHECK-' + proj + '_Structure_Summary_Statistics_Rap_and_GIS_ML.xlsx'
                to_excel_file0 = os.path.join(gis_dir, file_name_stats)

                with pd.ExcelWriter(to_excel_file0) as writer:
                    status_stats.to_excel(writer, sheet_name=structure_status_field, index=False)
                    handedover_stats.to_excel(writer, sheet_name=handover_field, index=False)

            else:
                arcpy.AddMessage(duplicated_Ids)
                arcpy.AddError('There are duplicated Ids in Envi table shown above. The Process stopped. Please correct the duplicated rows.')
                pass

        N2SC_Structure_Update()

class JustMessage10(object):
    def __init__(self):
        self.label = "4.0 ----- Update Land & Structure for Workable Pier -----"
        self.description = "Update Excel Master List"

class AddObstructionToLotN2(object):
    def __init__(self):
        self.label = "4.1 (N2) Add Obstruction to Excel Master List (Lot)"
        self.description = "(N2) Add Obstruction to Excel Master List (Lot)"

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
    
        gis_rap_dir = arcpy.Parameter(
            displayName = "N2 GIS Directory for RAP",
            name = "N2 GIS Directory for RAP",
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
            displayName = "N2 Pier Workable Tracker (Excel compiled with RAP and Civil)",
            name = "N2 Pier Workability Tracker (Excel compiled with RAP and Civil)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, gis_rap_dir, gis_lot_ms, gis_lot_portal, gis_via_dir, pier_workable_tracker]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_rap_dir = params[1].valueAsText
        gis_lot_ms = params[2].valueAsText
        gis_lot_portal = params[3].valueAsText
        gis_via_dir = params[4].valueAsText
        pier_workable_tracker = params[5].valueAsText

        arcpy.env.overwriteOutput = True

        def Obstruction_Land_ML_Update():                      
            # Define field names
            cp_field = 'CP'
            land1_field = 'Land.1'
            obstruc_field = 'Obstruction'
            lot_id_field = 'LotID'

            # Read as xlsx
            gis_lot_table = pd.read_excel(gis_lot_ms)
            gis_lot_portal_t = pd.read_excel(gis_lot_portal)

            # to string
            gis_lot_table[lot_id_field] = gis_lot_table[lot_id_field].astype(str)
            gis_lot_portal_t[lot_id_field] = gis_lot_portal_t[lot_id_field].astype(str)


            # 0. Reset 'Obstruction' to 'No' first
            gis_lot_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_land = pd.DataFrame()
            sum_lot_compile = pd.DataFrame()

            cps = ['N-01','N-02','N-03']
            for cp in cps:
                gis_lot_t = gis_lot_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                pier_wtracker_t = pd.read_excel(pier_workable_tracker, sheet_name=cp)

                #--------------------------------------------------------------#
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                #--------------------------------------------------------------#
                ## Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps are obstructed by the same lots or structures.

                ## Land
                x_lot_ids = extract_ids_for_assign_obstruction(proj, pier_wtracker_t, land1_field)

                ### Add these obstructing LotIDs to GIS Structure master list
                # First, reset 'obstruction' field
                gis_lot_t[obstruc_field] = np.nan
                gis_lot_t.loc[:, obstruc_field] = 'No'

                ids = gis_lot_t.query(f"{lot_id_field}.isin({x_lot_ids})").index
                y_lot_ids = gis_lot_t.loc[ids, lot_id_field].values
                gis_lot_t.loc[ids, obstruc_field] = 'Yes'

                # Extract obstructing LotIDs from the GIS Attribute table (GIS_portal)
                idcp = gis_lot_portal_t.query(f"{cp_field} == '{cp}'").index
                ids_portal = gis_lot_portal_t.loc[idcp, ].index[gis_lot_portal_t.loc[idcp, lot_id_field].isin(x_lot_ids)]
                y_lot_portal_ids = gis_lot_portal_t.loc[ids_portal, lot_id_field].values

                ## compile for cps
                compile_land = pd.concat([compile_land, gis_lot_t])

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, x_lot_ids, y_lot_ids, y_lot_portal_ids)
                sum_lot_compile = pd.concat([sum_lot_compile, summary_table[0]], ignore_index=False)

            #--------------------------------------------------------------#
            ##  Overwrite existing GIS_Lot_ML with summary statistics      ##
            #--------------------------------------------------------------#
            # Add missing CPs (N-04 & N-05) to the compiled table
            compile_cps = unique(compile_land[cp_field])
            gis_cps = unique(gis_lot_table[cp_field])
 
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            gis_lot_misst = gis_lot_table.query(f"{cp_field} in {miss_cp}")
            gis_lot_misst[obstruc_field] = 'No'
            compile_land = pd.concat([compile_land, gis_lot_misst]).reset_index(drop=True)

            # Manually Assign non-matched lot ids (overlapping CPs and piers) to 'Yes' in the Obstruction field
            # non_matched_lot_ids = flatten_extend(non_matched_lot_ids)

            arcpy.AddMessage(f"The following non-matched LotIDs were assigned to 'Yes' in the Obstruction field separately due to the associated overlapping piers and cps")
            arcpy.AddMessage(str(summary_table[1])) # pd.Series removes nested list

            ids = compile_land.index[compile_land[lot_id_field].isin(tuple(summary_table[1]))]
            compile_land.loc[ids, obstruc_field] = 'Yes'

            # Export updated GIS Lot ML with obstruction field
            compile_land.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_lot_ms)), index=False)

            ## Export summary table
            sum_lot_compile.to_excel(os.path.join(gis_via_dir, '99-N2_Non-Matched_Obstruction_for_Land_RAP_vs_GIS.xlsx'), sheet_name='Land', index=False)

        Obstruction_Land_ML_Update()

class AddObstructionToStructureN2(object):
    def __init__(self):
        self.label = "4.2. (N2) Add Obstruction to Excel Master List (Structure/NLO)"
        self.description = "(N2) Add Obstruction to Excel Master List (Structure/NLO)"

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
    
        gis_rap_dir = arcpy.Parameter(
            displayName = "N2 GIS Directory",
            name = "N2 GIS Directory",
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

        params = [proj, gis_rap_dir, gis_struc_ms, gis_struc_portal, gis_nlo_ms ,gis_via_dir, pier_workable_tracker]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_rap_dir = params[1].valueAsText
        gis_struc_ms = params[2].valueAsText
        gis_struc_portal = params[3].valueAsText
        gis_nlo_ms = params[4].valueAsText
        gis_via_dir = params[5].valueAsText
        pier_workable_tracker = params[6].valueAsText

        arcpy.env.overwriteOutput = True

        def Obstruction_Structure_ML_Update():                       
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

            # 1. Clean fields
            compile_struc = pd.DataFrame()
            compile_nlo = pd.DataFrame()
            sum_struc_compile = pd.DataFrame()
            cps = ['N-01','N-02','N-03']

            for cp in cps:
                gis_struc_t = gis_struc_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                gis_nlo_t = gis_nlo_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                pier_wtracker_t = pd.read_excel(pier_workable_tracker, sheet_name=cp)

                #--------------------------------------------------------------#
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                #--------------------------------------------------------------#
                ## Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps are obstructed by the same lots or structures.

                x_struc_ids = extract_ids_for_assign_obstruction(proj, pier_wtracker_t, struc1_field)

                ### Add these obstructing StrucIDs to GIS Structure master list
                #### First, reset 'obstruction' field
                gis_struc_t[obstruc_field] = np.nan
                gis_struc_t.loc[:, obstruc_field] = 'No'

                ids = gis_struc_t.query(f"{struc_id_field}.isin({x_struc_ids})").index
                y_struc_ids = gis_struc_t.loc[ids, struc_id_field].values
                gis_struc_t.loc[ids, obstruc_field] = 'Yes'

                # #### Extract obstructing LotIDs from the GIS Attribute table (GIS_portal)
                idcp = gis_struc_portal_t.query(f"{cp_field} == '{cp}'").index
                ids_portal = gis_struc_portal_t.loc[idcp, ].query(f"{struc_id_field}.isin({x_struc_ids})").index
                # ids_portal = gis_struc_portal_t.loc[idcp, ].index[gis_struc_portal_t.loc[idcp, struc_id_field].isin(x_struc_ids)]
                y_struc_portal_ids = gis_struc_portal_t.loc[ids_portal, struc_id_field].values

                ### 2. NLO
                #### Add these obstructing StrucIDs to GIS ISF master list
                #### Note that regardless of NLO' status, all the NLOs falling under obstructing structures must be visualized.
                gis_nlo_t[obstruc_field] = np.nan
                gis_nlo_t.loc[:, obstruc_field] = 'No'

                ids = gis_nlo_t.query(f"{struc_id_field}.isin({x_struc_ids})").index
                gis_nlo_t.loc[ids, obstruc_field] = 'Yes'

                ### 3. Check obstructing StrucIDS between NLO and Structure GIS master list
                ids = gis_struc_t.query(f"{obstruc_field} == 'Yes'").index
                gis_struc_ids = gis_struc_t.loc[ids, struc_id_field].values

                ids = gis_nlo_t.query(f"{obstruc_field} == 'Yes'").index
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

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, x_struc_ids, y_struc_ids, y_struc_portal_ids)
                sum_struc_compile = pd.concat([sum_struc_compile, summary_table[0]], ignore_index=False)

            noids_rap_vs_gisml = pd.Series(summary_table[1])    

            #-----------------------------------------------------------------#
            ##  Overwrite existing GIS_Structure_ML with summary statistics  ##
            #-----------------------------------------------------------------#
            # Structure
            arcpy.AddMessage('Structure')

            ## Add missing CPs to compiled table
            compile_cps = unique(compile_struc[cp_field])
            gis_cps = unique(gis_struc_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            gis_struc_misst = gis_struc_table.query(f"{cp_field} in {miss_cp}")
            gis_struc_misst[obstruc_field] = 'No'
            compile_struc = pd.concat([compile_struc, gis_struc_misst])

            #####
            arcpy.AddMessage(f"The following non-matched StrucIDs were assigned to 'Yes' in the Obstruction field separately due to the associated overlapping piers and cps")
            arcpy.AddMessage(str(noids_rap_vs_gisml))
            ids = compile_struc.query(f"{struc_id_field}.isin({tuple(noids_rap_vs_gisml)})").index
            compile_struc.loc[ids, obstruc_field] = 'Yes'
            compile_struc.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_struc_ms)), index=False) ## gis_struc
           
            # NLO
            arcpy.AddMessage('NLO')

            ## Add missing CPs to compiled table
            compile_cps = unique(compile_nlo[cp_field])
            gis_cps = unique(gis_nlo_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            gis_nlo_misst = gis_nlo_table.query(f"{cp_field} in {miss_cp}")
            gis_nlo_misst[obstruc_field] = 'No'
            compile_nlo = pd.concat([compile_nlo, gis_nlo_misst])

            #####
            arcpy.AddMessage(f"The following non-matched StrucIDs were assigned to 'Yes' in the Obstruction field separately due to the associated overlapping piers and cps")
            arcpy.AddMessage(str(noids_rap_vs_gisml))
            ids = compile_nlo.query(f"{struc_id_field}.isin({tuple(summary_table[1])})").index
            compile_nlo.loc[ids, obstruc_field] = 'Yes'
            compile_nlo.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_nlo_ms)), index=False) ## gis_isf

            ## Export summary statistics in one excel sheet
            sum_struc_compile.to_excel(os.path.join(gis_via_dir, '99-N2_Non-Matched_Obstruction_for_Structure_RAP_vs_GIS.xlsx'), sheet_name='Structure', index=False)

        Obstruction_Structure_ML_Update()

class AddObstructionToLotSC(object):
    def __init__(self):
        self.label = "4.3. (SC) Add Obstruction to Excel Master List (Lot)"
        self.description = "(SC) Add Obstruction to Excel Master List (Lot)"

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
    
        gis_rap_dir = arcpy.Parameter(
            displayName = "SC GIS Directory",
            name = "SC GIS Directory",
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

        params = [proj, gis_rap_dir, gis_lot_ms, gis_lot_portal, gis_via_dir, pier_workable_tracker_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_rap_dir = params[1].valueAsText
        gis_lot_ms = params[2].valueAsText
        gis_lot_portal = params[3].valueAsText
        gis_via_dir = params[4].valueAsText
        pier_tracker_ms = params[5].valueAsText

        arcpy.env.overwriteOutput = True

        def Obstruction_Land_ML_Update():
            # List of fields
            obstruc_field = 'Obstruction' ## ('Yes' or 'No')
            lot_id_field = 'LotID'
            cp_field = 'CP'
            land_obstruc_field = 'Land'
            land_obstrucid_field = 'Land.1'

            # Read as xlsx
            gis_lot_table = pd.read_excel(gis_lot_ms)
            gis_lot_portal_t = pd.read_excel(gis_lot_portal)

            # 0. Reset 'Obstruction' to 'No' first
            gis_lot_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_land = pd.DataFrame()
            sum_lot_compile = pd.DataFrame()

            cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
            for cp in cps:
                gis_lot_t = gis_lot_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                pier_workable_t = pd.read_excel(pier_tracker_ms)
                pier_t = pier_workable_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                #--------------------------------------------------------------#
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                #--------------------------------------------------------------#
                # Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps
                # are obstructed by the same lots or structures.

                # Land
                x_lot_ids = extract_ids_for_assign_obstruction(proj, pier_t, land_obstruc_field, land_obstrucid_field)
                arcpy.AddMessage(x_lot_ids)

                ## Add these obstructing LotIDs to GIS Structure master list
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

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, x_lot_ids, y_lot_ids, y_lot_portal_ids)
                sum_lot_compile = pd.concat([sum_lot_compile, summary_table[0]], ignore_index=False)

            #--------------------------------------------------------------#
            ##  Overwrite existing GIS_Lot_ML with summary statistics      ##
            #--------------------------------------------------------------#
            compile_cps = unique(compile_land[cp_field])
            gis_cps = unique(gis_lot_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            arcpy.AddMessage(miss_cp)
            if len(miss_cp) > 0:
                gis_lot_misst = gis_lot_table.query(f"{cp_field} in {miss_cp}")
                compile_land = pd.concat([compile_land, gis_lot_misst])
            compile_land.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_lot_ms)), index=False) ## gis_land
 
            ## Export summary table
            sum_lot_compile.to_excel(os.path.join(gis_via_dir, '99-SC_Pier_Workable_Obstruction_Land_summaryStats.xlsx'), sheet_name='Land', index=False)

        Obstruction_Land_ML_Update()

class AddObstructionToStructureSC(object):
    def __init__(self):
        self.label = "4.4. (SC) Add Obstruction to Excel Master List (Structure & NLO)"
        self.description = "(SC) Add Obstruction to Excel Master List (Structure & NLO)"

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

        gis_rap_dir = arcpy.Parameter(
            displayName = "SC GIS Directory",
            name = "SC GIS Directory",
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

        params = [proj, gis_rap_dir, gis_struc_ms, gis_struc_portal, gis_nlo_ms, gis_via_dir, pier_workable_tracker_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_rap_dir = params[1].valueAsText
        gis_struc_ms = params[2].valueAsText
        gis_struc_portal = params[3].valueAsText
        gis_nlo_ms = params[4].valueAsText
        gis_via_dir = params[5].valueAsText
        pier_tracker_ms = params[6].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Obstruction_Structure_ML_Update():
            # Read as xlsx
            gis_struc_table = pd.read_excel(gis_struc_ms)
            gis_struc_portal_t = pd.read_excel(gis_struc_portal)
            gis_nlo_table = pd.read_excel(gis_nlo_ms)

            # List of fields
            obstruc_field = 'Obstruction' ## ('Yes' or 'No')
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
      
            cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
            for i, cp in enumerate(cps):
                gis_struc_t = gis_struc_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                gis_nlo_t = gis_nlo_table.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                pier_workable_t = pd.read_excel(pier_tracker_ms)
                pier_t = pier_workable_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)

                #--------------------------------------------------------------#
                ##  Identify Obstruction (Yes' or 'No') to GIS master list    ##
                #--------------------------------------------------------------#
                # Note that Civil table may have duplicated LotIDs or Structure IDs, as some pile caps
                # are obstructed by the same lots or structures.

                # Structure and ISF
                x_struc_ids = extract_ids_for_assign_obstruction(proj, pier_t, struc_obstruc_field, struc_obstrucid_field)

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

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, x_struc_ids, y_struc_ids, y_struc_portal_ids)
                sum_struc_compile = pd.concat([sum_struc_compile, summary_table[0]], ignore_index=False)

            #-----------------------------------------------------------------#
            ##  Overwrite existing GIS_Structure_ML with summary statistics  ##
            #-----------------------------------------------------------------#
           
            # Structure
            ## Add missing CPs to compiled table
            compile_cps = unique(compile_struc[cp_field])
            gis_cps = unique(gis_struc_table[cp_field])
            miss_cp = tuple(non_match_elements(gis_cps, compile_cps))
            if len(miss_cp) > 0:
                gis_struc_misst = gis_struc_table.query(f"{cp_field} in {miss_cp}")
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
        self.label = "5.0. ----- Update GIS Layers -----"
        self.description = "Update Excel Master List"

class UpdateLotGIS(object):
    def __init__(self):
        self.label = "5.1. Update GIS Attribute Table (Lot) - Stop Service & Disconnect"
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
            displayName = "Land Feature Layer in SDE (Polygon)",
            name = "Land Feature Layer in SDE (Polygon)",
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
        target_feature = params[2].valueAsText
        mlLot = params[3].valueAsText

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

        ## Copy feature layer 
        copy_feature = 'copy_feature'
        arcpy.management.CopyFeatures(target_feature, copy_feature)

        # Join fields to attribute table
        # 2. Delete Field
        gis_fields = [f.name for f in arcpy.ListFields(copy_feature)]
            
        ## 2.1. Identify fields to be dropped
        gis_drop_fields_check = [e for e in gis_fields if e not in ('LotId', 'LotID','created_user', 'created_date', 'last_edited_user', 'last_edited_date', 'Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
        ## 2.2. Extract existing fields
        arcpy.AddMessage("Stage 1: Extract existing fields was success")
            
        ## 2.3. Check if there are fields to be dropped
        gis_drop_fields = [f for f in gis_fields if f in tuple(gis_drop_fields_check)]
            
        arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")
        arcpy.AddMessage(gis_drop_fields)
            
        ## 2.4 Drop
        if len(gis_drop_fields) == 0:
            arcpy.AddMessage("There is no field that can be dropped from the feature layer")
        else:
            arcpy.management.DeleteField(copy_feature, gis_drop_fields)


        # arcpy.AddMessage("Deleted Fields from Polygon: ", [e.name for e in arcpy.ListFields(target_feature)])     
        arcpy.AddMessage("Stage 1: Dropping Fields was success")
        arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

        # 3. Join Field
        ## 3.1. Convert Excel tables to feature table
        lot_ml = arcpy.conversion.ExportTable(mlLot, 'lot_ml')

        # Check if LotID match between ML and GIS
        lotid_field = 'LotID'
        lotid_gis = unique_values(copy_feature, lotid_field)
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

        # arcpy.AddMessage("Transfer Fields: ", lot_ml_transfer_fields)
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in ('LotId', lotid_field)]))                      
        lot_ml_join_field =' '.join(map(str, [f for f in lot_ml_fields if f in ('LotId', lotid_field)]))
            
        ## 3.4 Join fields 
        arcpy.management.JoinField(in_data=copy_feature, in_field=gis_join_field, join_table=lot_ml, join_field=lot_ml_join_field, fields=lot_ml_transfer_fields)

        ## 3.5. Truncate SDE
        arcpy.management.TruncateTable(target_feature)

        # ## 3.6. Append copy_feature to target feature
        arcpy.management.Append(copy_feature, target_feature, schema_type = 'NO_TEST')

        # ## 3.7 Join missing fields in copy_feature to target feature
        ### Unmatched fields
        target_fields = [f.name for f in arcpy.ListFields(target_feature)]
        miss_fields = [item for item in gis_fields if item not in target_fields]

        ## 3.8. Join missing_fields to target feature
        arcpy.management.JoinField(in_data=target_feature, in_field=gis_join_field, join_table=copy_feature, join_field=gis_join_field, fields=miss_fields)

        ## 3.9. Check all the fields are matched between copy_feature and target_feature
        new_target_fields = [f.name for f in arcpy.ListFields(target_feature)]
        missing_fields = [item for item in gis_fields if item not in target_fields]
        arcpy.AddMessage(f"Missing LotIDs: {missing_fields}")

        # # Export
        file_name = project + "_" + "GIS_Land_Portal.xlsx"
        arcpy.conversion.TableToExcel(target_feature, os.path.join(gis_dir, file_name))

class UpdateStructureGIS(object):
    def __init__(self):
        self.label = "5.3. Update GIS Attribute Tables (Structures/Occupancy/ISF Relocation)"
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

class JustMessage3(object):
    def __init__(self):
        self.label = "7.0. ----- Calculate Statistics between Two Tables (Optional)  -----"
        self.description = "Calculate Statistics between Two Tables (Optional)"

class GenerateStatisticsBetweenTwoTables(object):
    def __init__(self):
        self.label = "7.1. Comparing Statistics between Two Tables"
        self.description = "Comparing Statistics between Two Tables"

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

        table1 = arcpy.Parameter(
            displayName = "Table 1 (Excel)",
            name = "Table 1 (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        table2 = arcpy.Parameter(
            displayName = "Table 2 (Excel)",
            name = "Table 2 (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        groupby_fields = arcpy.Parameter(
            displayName = "Group-by Fields",
            name = "Group-by Fields",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = True,
        )

        stats_field = arcpy.Parameter(
            displayName = "Statistics Field",
            name = "Statistics Field",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            multiValue = True,
        )

        stats_type = arcpy.Parameter(
            displayName = "Statistics Type",
            name = "Statistics Type",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
        )
        stats_type.filter.type = "ValueList"
        stats_type.filter.list = ['count', 'sum']

        params = [proj, gis_dir, table1, table2, groupby_fields, stats_field, stats_type]
        return params
    
    def updateParameters(self, params):
        if params[2].value and not params[4].altered:
            excel_path = params[2].valueAsText
            tab = pd.read_excel(excel_path)
            # tab = tab.select_dtypes(include=['object'])
            params[4].filter.list = list(tab.columns)

        if params[2].value and not params[5].altered:
            excel_path = params[2].valueAsText
            tab = pd.read_excel(excel_path)
            # tab = tab.select_dtypes(include=['object'])
            params[5].filter.list = list(tab.columns)      

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        table1 = params[2].valueAsText
        table2 = params[3].valueAsText
        groupby_fields = params[4].valueAsText
        stats_field = params[5].valueAsText
        stats_type = params[6].valueAsText

        # Read table
        tab1 = pd.read_excel(table1)
        tab2 = pd.read_excel(table2)

        groupby_fields = list(groupby_fields.split(';'))
        stats_field = list(stats_field.split(';'))

        compile_list = []
        for field in stats_field:
            summary = summaryStatistics(tab1, tab2, stats_type, field, groupby_fields)
            stats_summary = summary.process_data_before_after()
            compile_list.append(stats_summary)

        # Export the updated GIS portal to excel sheet for checking lot IDs
        tab1_name = re.sub(r'.xlsx|.xls', "", os.path.basename(table1))
        tab2_name = re.sub(r'.xlsx|.xls', "", os.path.basename(table2))

        file_name = f"CHECK-{stats_field}_{tab1_name}_and_{tab2_name}.xlsx"
            
        to_excel_file = os.path.join(gis_dir, file_name)
        with pd.ExcelWriter(to_excel_file) as writer:
            for i, stats in enumerate(compile_list):
                stats.to_excel(writer, sheet_name=stats_field[i], index=False)

class JustMessage4(object):
    def __init__(self):
        self.label = "6.0. ----- Identify Unmatched Unique Values (Optional) -----"
        self.description = "Identify Unmatched Unique Values"

class CompareStringFieldExcelTables(object):
    def __init__(self):
        self.label = "6.1. Compare Unique Values In String Field (Excel Tables)"
        self.description = "Compare Unique Values In String Field (Excel Tables)"

    def getParameterInfo(self):
        table1 = arcpy.Parameter(
            displayName = "Table 1 (Excel)",
            name = "Table 1 (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )
      
        field1 = arcpy.Parameter(
            displayName = "String Field for Table 1",
            name = "String Field for Table 1",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        table2 = arcpy.Parameter(
            displayName = "Table 2 (Excel)",
            name = "Table 2 (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        field2 = arcpy.Parameter(
            displayName = "String Field for Table 2",
            name = "String Field for Table 2",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        table3 = arcpy.Parameter(
            displayName = "Table 3 (Excel)",
            name = "Table 3 (Excel)",
            datatype = "DEFile",
            parameterType = "Optional",
            direction = "Input"
        )

        field3 = arcpy.Parameter(
            displayName = "String Field for Table 3",
            name = "String Field for Table 3",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [table1, field1, table2, field2, table3, field3]
        return params
    
    def updateParameters(self, params):
        if params[0].value and not params[1].altered:
            excel_path = params[0].valueAsText
            tab = pd.read_excel(excel_path)
            tab = tab.select_dtypes(include=['object'])
            params[1].filter.list = list(tab.columns)

        if params[2].value and not params[3].altered:
            excel_path = params[2].valueAsText
            tab = pd.read_excel(excel_path)
            tab = tab.select_dtypes(include=['object'])
            params[3].filter.list = list(tab.columns)

        if params[4].value and not params[5].altered:
            excel_path = params[4].valueAsText
            tab = pd.read_excel(excel_path)
            tab = tab.select_dtypes(include=['object'])
            params[5].filter.list = list(tab.columns)           
        

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        table1 = params[0].valueAsText
        field1 = params[1].valueAsText
        table2 = params[2].valueAsText
        field2 = params[3].valueAsText
        table3 = params[4].valueAsText
        field3 = params[5].valueAsText

        if table3 and field3:
            table1 = pd.read_excel(table1) # for checking NVS3, do not use default_na = false
            table2 = pd.read_excel(table2)
            table3 = pd.read_excel(table3)

            table1[field1] = table1[field1].astype(str)
            table2[field2] = table2[field2].astype(str)
            table3[field3] = table3[field3].astype(str)

            table1_vs_table2 = identify_missing_ids_excel(table1, table2, field1, field2)
            table3_vs_table1 = identify_missing_ids_excel(table1, table3 ,field1, field3)
            table2_vs_table3 = identify_missing_ids_excel(table2, table3, field2, field3)

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table1 vs Table2: {table1_vs_table2}")

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table3 vs Table1: {table3_vs_table1}")

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table2 vs Table3: {table2_vs_table3}")

        else:
            table1 = pd.read_excel(table1) # for checking NVS3, do not use default_na = false
            table2 = pd.read_excel(table2)
            table1[field1] = table1[field1].astype(str)
            table2[field2] = table2[field2].astype(str)
    
            table1_vs_table2 = identify_missing_ids_excel(table1, table2, field1, field2)

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table1 vs Table2: {table1_vs_table2}")

class CompareStringFieldFeatureClasses(object):
    def __init__(self):
        self.label = "6.2. Compare Unique Values In String Field (Feature Class)"
        self.description = "Compare Unique Values In String Field (Feature Class)"

    def getParameterInfo(self):
        table1 = arcpy.Parameter(
            displayName = "Feature Class 1",
            name = "Feature Class 1",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        field1 = arcpy.Parameter(
            displayName = "String Field for Feature Class 1",
            name = "String Field for Feature Class 1",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        field1.parameterDependencies = [table1.name]

        table2 = arcpy.Parameter(
            displayName = "Feature Class 2",
            name = "Feature Class 2",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        field2 = arcpy.Parameter(
            displayName = "String Field for Feature Class 2",
            name = "String Field for Feature Class 2",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        field2.parameterDependencies = [table2.name]

        table3 = arcpy.Parameter(
            displayName = "Feature Class 3",
            name = "Feature Class 3",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        field3 = arcpy.Parameter(
            displayName = "String Field for Feature Class 3",
            name = "String Field for Feature Class 3",
            datatype = "Field",
            parameterType = "Optional",
            direction = "Input"
        )
        field3.parameterDependencies = [table3.name]

        params = [table1, field1, table2, field2, table3, field3]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        table1 = params[0].valueAsText
        field1 = params[1].valueAsText
        table2 = params[2].valueAsText
        field2 = params[3].valueAsText
        table3 = params[4].valueAsText
        field3 = params[5].valueAsText

        if table3 and field3:
            values1 = [f for f in arcpy.da.SearchCursor(table1, [field1]) if f]
            values2 = [f for f in arcpy.da.SearchCursor(table2, [field2]) if f]
            values3 = [f for f in arcpy.da.SearchCursor(table3, [field3]) if f]

            table1_vs_table2 = identify_missing_ids_fc(values1, values2)
            table3_vs_table1 = identify_missing_ids_fc(values1, values3)
            table2_vs_table3 = identify_missing_ids_fc(values2, values3)

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table1 vs Table2: {table1_vs_table2}")

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table3 vs Table1: {table3_vs_table1}")

            arcpy.AddMessage("----------- Output -----------")
            arcpy.AddMessage(f"Table2 vs Table3: {table2_vs_table3}")

        else:
            values1 = [f for f in arcpy.da.SearchCursor(table1, [field1]) if f]
            values2 = [f for f in arcpy.da.SearchCursor(table2, [field2]) if f]
    
            table1_vs_table2 = identify_missing_ids_fc(values1, values2)
            arcpy.AddMessage(f"Table1 vs Table2: {table1_vs_table2}")

