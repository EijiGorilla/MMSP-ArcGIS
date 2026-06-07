from fileinput import filename
import math

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
    
def unique_values_layer(table, field):  ##uses list comprehension
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor if row[0] is not None})
    
def non_match_elements(list_a, list_b):
    """
    Return non-matched values between two lists
    """
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

def first_letter_capital(table, column_names): # column_names are list
    for name in column_names:
        table[name] = table[name].str.title()
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
        try:
            table[field] = table[field].astype(str)
            table[field] = table[field].replace(r'\s+', '', regex=True)
        except:
            pass
    return table

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
        row = [re.sub(r'\s+','',str(e)) for e in row]
        flat_list.extend(row)
    return flat_list

def remove_empty_strings(string_list):
    return [string for string in string_list if string]

def unlist_brackets(nested_list): ## Remove nested list in a list
    return [item for sublist in nested_list for item in sublist]

#--- Fill and Remove dummy date in the first row
def first_row_fill_empty(table, fields, data, datatype):
    """
    arg: the first row is filled when empty to avoide data type inconsistency in GIS attribute table
    table: pandas dataFrame
    fields: a list of subject fields
    data: string, number, or date (e.g., 0.0, '1990-01-01')
    datatype: only two types are allowd: 'float' or 'date'
    """
    for field in fields:
        first_row = table[field].iloc[:1].item()
        if first_row is None or pd.isnull(first_row):
            if datatype == "float":
                table.loc[0, field] = data
                table[field] = pd.to_numeric(table[field], errors='coerce')
            elif datatype == "date":
                table.loc[0, field] = pd.to_datetime(data)
    return table

#--- Fill and Remove dummy date in the first row
def first_row_delete_dummy_fc(fc, fields, datatype):
    """
    Arg: Delete dummy data from the first in selected fields.
    fc: Feature Class (Layer),
    datatype: Allowed for only 'float' or 'date'
    """
    try:
        if datatype == 'float':    
            for field in fields:
                with arcpy.da.UpdateCursor(fc, [field]) as cursor:
                    for row in cursor:
                        if row[0]:
                            if row[0] == -99.0:
                                row[0] = None
                        cursor.updateRow(row)
                        break
        elif datatype == 'date':
            for field in fields:
                with arcpy.da.UpdateCursor(fc, [field]) as cursor:
                    for row in cursor:
                        if row[0]:
                            year = row[0].strftime("%Y")
                            if int(year) < 2000:
                                row[0] = None
                            else:
                                row[0] = row[0]
                        cursor.updateRow(row)
                        break
    except:
        arcpy.AddMessage(f"failed to delete dummy data in the first of selected fields..")
        arcpy.AddError('error...')

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


def merge_table_to_masterTable(input_table, target_table, id_field, rename_array, dummy_subject_fiels,  add_dummy_value=False):
    """
    Add four fields from each historical ML to reference ML: 1. 'StatusLA' (e.g., x20240101), 2. 'AffectedArea' (e.g., x20240101_TAA), 3. 'HandedOverArea' (e.g., x20240101_HOA), and 4. 'HandedOver' (e.g., x20240101_HO).
    input_table: historical ML table to merge
    target_table: reference ML table to be merged
    id_field: ID field for merging (e.g., LotID)
    rename_array: a dictionary for renaming fields in input_table (e.g., {status_field: f'x{yyyymm}', affectedArea_field: f'x{yyyymm}_TAA', handedOverArea_field: f'x{yyyymm}_HOA', handedover_field: f'x{yyyymm}_HO'})
    dummy_subject_fiels: a list of subject fields to add dummy value when the first row is empty.
    add_dummy_value: a boolean value to determine whether to add dummy value in the first row when the first row is empty.
    """

    if add_dummy_value:
        table = first_row_fill_empty(input_table, dummy_subject_fiels, -99.0, "float")
    table = input_table.rename(columns=rename_array)
    
    #--- Merge pre-processed historical ML to the latest ML
    merged_table = pd.merge(left=target_table, right=table, how='left', left_on=id_field, right_on=id_field)

    return merged_table

def preprocess_table_with_yyyymmdd(filepath, id_field, status_field):
    """
    Preprocess the table and extract yyyymmdd from the file name.
    filepath: path to the Excel file
    id_field: ID field for merging (e.g., LotID)
    status_field: status field to be renamed (e.g., StatusLA)
    dumy_subject_fiels: a list of subject fields to add dummy value when the first row is empty.

    Caution: ensure that the table's file name starts with yyyymmdd (e.g., 20240101_RAP_MasterList.xlsx) to extract yyyymmdd correctly.
    """
    yyyymmdd = os.path.basename(filepath)[:8]
    table = pd.read_excel(filepath)
    table = toString(table, [id_field])

    #--- Status = 0 => None ---#
    try:
        table.loc[table.query(f"{status_field} == 0").index, status_field] = None
    except:
        pass

    return table, yyyymmdd

def find_duplicates_ordered(arr):
    seen = set()
    duplicates = set()
    for item in arr:
        if item in seen:
            duplicates.add(item) # Use a set to avoid adding the same duplicate multiple times
        else:
            seen.add(item)
    dups = [x for x in duplicates if not math.isnan(x)]
    return list(dups)

def generate_check_lotid_match(input_table, target_table, id_field):
    """
    Generate lotIds and duplicated lotIds in input and target tables for checking if lotIds are matched between two tables.
    input_table: historical ML to merge.
    target_table: latest ML to be merged.
    id_field: ID field for merging (e.g., LotID)
    """
    input_ids = input_table[id_field].values
    target_ids = target_table[id_field].values
    input_dup = find_duplicates_ordered(input_ids)
    target_dup = find_duplicates_ordered(target_ids)

    return input_dup, target_dup

def export_excel(table, export_dir, file_name):
    export_file = os.path.join(export_dir, file_name)
    table.to_excel(export_file, index=False)

def rename_columns_title(table, col_names, col_indices, search_text, replace_col):
    search_col = [col for col in col_names if re.search(search_text, col)][0]
    search_col_index = col_indices[search_col]
    if re.search(search_text, col_names[search_col_index]):
        table = table.rename(columns={col_names[search_col_index]: replace_col})
    return table


def convert_columns_to_numeric(proj, table, numericFields, column_names, endorsed_field=None):
    if proj == 'N2':
        to_numeric_fields = numericFields + [endorsed_field]
    else:
        to_numeric_fields = numericFields

    # Remove non-matching fields for numeric conversion
    non_match_col = non_match_elements(to_numeric_fields, column_names)
    [to_numeric_fields.remove(non_match_col[0]) if non_match_col else arcpy.AddMessage('no need to remove field from the list for numeric conversion')]

    for field in to_numeric_fields:
        table[field] = table[field].replace(r'\s+|[^\w\s$]','',regex=True)
        table[field] = pd.to_numeric(table[field])

    return table

def preprocess_rap_table(proj,
                         table, 
                         table_type,
                         id_field,
                         cp_field, 
                         to_string_fields=None, 
                         to_numeric_fields=None, 
                         to_date_fields=None,
                         endorsed_field=None):
    """
    Process the RAP table to prepare for merging with the GIS master list. The processing includes renaming columns, converting data types, and reformatting CP values.
    proj: project extension (e.g., 'N2' or 'SC')
    table: RAP table to be processed
    table_type: type of the RAP table (e.g., 'land' or 'structure' or 'isf')
    cp_field: the field name of CP in the RAP table
    to_string_fields: a list of field names to be converted to string type
    to_numeric_fields: a list of field names to be converted to numeric type
    endorsed_field: the field name of Endorsed in the RAP table (only for land table)
    """
    col_names = table.columns
    col_indices = {name: i for i, name in enumerate(col_names)}

    #--- Rename columns of Municipality and Barangay
    for search_text, replace_col in zip(['City|Municipal', 'Bara|bara'], ["Municipality", "Barangay"]):
        table = rename_columns_title(table, col_names, col_indices, search_text, replace_col)
    
    #--- Ensure that the first letter of each word in the municipality and barangay fields is capitalized and remove space, hyphen, and underline
    for field in ["Municipality", "Barangay"]:
        table = first_letter_capital(table, [field])

    #--- Convert to string and numeric fields
    if to_string_fields:
        table = toString(table, to_string_fields)


    if to_numeric_fields:
        table = convert_columns_to_numeric(proj, table, to_numeric_fields, col_names, endorsed_field=endorsed_field)

    #--- Convert date fields if provided
    if to_date_fields:
        for field in to_date_fields:
            table[field] = pd.to_datetime(table[field], errors='coerce').dt.date

    #--- Reformat CP
    if proj == 'N2':
        table[cp_field] = table[cp_field].str.replace(r'N','N-',regex=True)
    else:
        arrays = {
            r'3A|3A|3a': '3a',
            r'3B|3B|3b': '3b',
            r'3C|3C|3c': '3c',
            r'/.*|,.*': ''
        }
        table = replace_strings_table(table, cp_field, arrays)

        if table_type == 'land':
            for ids, pkg in zip(['10155|10156|10158-5', '60136-A', '^100003$|^100004$|^100005$|^100010$'], ["S-01", "S-04", "S-06"]):
                table = convert_lotids_to_correct_cp(table, id_field, ids, cp_field, pkg)
        elif table_type == 'structure':
            table[id_field] = table[id_field].str.upper()
            table = convert_lotids_to_correct_cp(table, id_field, 'NSRP-01-08-ML046', cp_field, 'S-01')
    
    # First CP when 'N-03,N-02' (ie.N-03) 
    table[cp_field] = table[cp_field].apply(lambda x: re.sub(r',.*','',x))

    return table

def gis_attribute_table_update(gis_dir,
                               target_layer,
                               input_table,
                               join_field,
                               export_file_name,
                               check_box,
                               date_fields=None):
    """
    Update GIS attribute table by joining with Excel table and export to Excel file. It also checks matching of uniqueID between GIS and Excel tables before joining, and gives messages if there are mismatches. If date_fields are provided, it will remove dummy dates (before year 2000) from the GIS attribute table after joining.
    gis_dir: directory for exporting Excel file
    target_layer: GIS feature layer to be updated
    input_table: Feature Table to join with GIS attribute table (Not excel file)
    join_field: field name for joining GIS and Excel tables (e.g., uniqueID)
    export_file_name: file name for exported Excel file (without extension)
    (optional) date_fields: list of date field names to check for dummy dates (e.g., ['start_actual', 'finish_plan', 'finish_actual'])
    """
    layer_copy = "layer_copy"
    arcpy.management.CopyFeatures(target_layer, layer_copy)

    #--- Keep only uniquID
    arcpy.management.DeleteField(layer_copy, [join_field], "KEEP_FIELDS")

    #--- Check matching
    id_copy = unique_values_layer(layer_copy, join_field)
    id_ml = unique_values_layer(input_table, join_field)

    id_miss_gis = [e for e in id_copy if e not in id_ml]
    id_miss_ml = [e for e in id_ml if e not in id_copy]

    if id_miss_ml or id_miss_gis:
        arcpy.AddMessage('The following IDs do not match between ML and GIS.')
        arcpy.AddMessage('Missing IDs in GIS Excel table: {}'.format(id_miss_gis))
        arcpy.AddMessage('Missing IDs in GIS Attribute Table: {}'.format(id_miss_ml))
    
    #--- Join fields
    transfer_fields = [f.name for f in arcpy.ListFields(input_table) if f.name not in ('ObjectID', 'OBJECTID', join_field)]
    arcpy.management.JoinField(layer_copy, join_field, input_table, join_field, transfer_fields)

    #-----------------------------------------------------#
    #       Add missing fields if check_box is True       #
    #-----------------------------------------------------#
    if check_box:
        exclude_fields = ['ObjectID',
                          'OBJECTID',
                          'Shape_Length',
                          'Shape_Area',
                          'Shape.STArea()',
                          'Shape.STLength()',
                          'GlobalID',
                          'created_user',
                          'created_date',
                          'last_edited_user',
                          'last_edited_date',
                          'temp_',
                          'temp'
                        ]
        fields_target = [f.name for f in arcpy.ListFields(target_layer) if f.name not in tuple(exclude_fields)]
        fields_input = [f.name for f in arcpy.ListFields(input_table) if f.name not in tuple(exclude_fields)]
        fields_add = [item for item in fields_input if item not in fields_target]
        arcpy.AddMessage(f"Missing fields in target feature layer: {fields_add}")

        to_dataTypes = {
                        'String': 'TEXT',
                        'Integer': 'SHORT',
                        'SmallInteger': 'SHORT',
                        'Double': 'DOUBLE',
                        'Date': 'DATE',
                    }

        #--- Add fields to target feature
        if fields_add:
            for field in fields_add:
                arcpy.AddMessage(f"Adding missing field: {field}")
                org_type = arcpy.ListFields(input_table, field)[0].type

                if org_type != 'Geometry':
                    arcpy.management.AddField(target_layer,
                                            field,
                                            to_dataTypes[org_type],
                                            "","","",
                                            field,
                                            "NULLABLE")


    #--- Remove dummy date from GIS attribute table if any
    if date_fields:
        first_row_delete_dummy_fc(layer_copy, date_fields, datatype='date')

    #--- Trucnate
    arcpy.management.TruncateTable(target_layer)

    #--- Append
    arcpy.management.Append(layer_copy, target_layer, schema_type = 'NO_TEST')

    #--- Table to Excel
    arcpy.conversion.TableToExcel(target_layer, f"{os.path.join(gis_dir, export_file_name)}.xlsx")
    
    #--- Delete the copied feature layer
    deleteTempLayers = [layer_copy]
    arcpy.management.Delete(deleteTempLayers)
        
#-----------------------#
#    Pier Workability   #
#-----------------------#
def extract_ids_for_assign_obstruction(table, field, field2=None):
    ids = table.index[(table[field] == 1) & (table[field2].notna())]
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

def add_obstruction(table, id_field, obstField, search_ids):
    """
    Add obstruction to a excel table: 'Yes' or 'No'
    table: excel mater list table (land or structure ML)
    field: obstruction field
    id_field: LotID or structureID
    """
    table[obstField] = np.nan
    table[obstField] = table[obstField].astype(str)
    table.loc[:, obstField] = 'No'

    indices = table.query(f"{id_field}.isin({search_ids})").index
    IDs = table.loc[indices, id_field].values
    table.loc[indices, obstField] = 'Yes'
    
    return table, IDs

def extract_obstructing_ids(table, id_field, search_ids):
    """
    Extract obstructing IDs
    table: excel master list table in pandas
    id_field: ID field
    search_ids: search IDs
    """
    idx = table.query(f"{id_field}.isin({search_ids})").index
    IDs = table.loc[idx, id_field].values

    return IDs

def add_obstruction_and_extract_ids(
        target_table, 
        target_portal_table, 
        input_table,
        id_field, 
        obs_field, 
        obs_type_field, 
        obs_type1_field):
    """
    Add Obstruction ('Yes' or 'No') to GIS master list and extract obstructing IDs from both GIS master list and GIS portal table.
    proj: project extension (e.g., 'N2' or 'SC')
    target_table: GIS master list table to be updated with obstruction (land or structure ML)
    target_portal_table: GIS portal table to be checked for extracting obstructing IDs (GIS attribute table)
    input_table: RAP table to be checked for extracting obstructing IDs (land or structure RAP table)
    id_field: ID field (e.g., LotID or StrucID)
    obs_field: obstruction field to be added in the target_table (e.g., 'Obstruction')
    obs_type_field: obstruction type field in the input_table (e.g., 'Land')
    obs_type1_field: field containing obstructing IDs associated with id_field (e.g., 'Land1')
    """
    #--- pier workability tracker
    tracker_obs_ids = extract_ids_for_assign_obstruction(input_table, obs_type_field, obs_type1_field)

    #--- Add obstructing IDs to target table & return extracted IDs from GIS master list
    gis_table, gis_obs_ids = add_obstruction(target_table, id_field, obs_field, tracker_obs_ids)

    #--- Return obstructing IDs from GIS Portal table
    gis_portal_obs_ids = extract_obstructing_ids(target_portal_table, id_field, tracker_obs_ids)

    return gis_table, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids

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
            handedover_field = 'HandedOver'
            handedOverArea_field = 'HandedOverArea'
            handedOverDate_field = 'HandedOverDate'
            affectedArea_field = 'AffectedArea'
            note_field = 'note'

            keep_fields = [lotid_field, status_field, affectedArea_field, handedOverArea_field, handedover_field]
            hist_fields = [affectedArea_field, handedOverArea_field, handedover_field]
            
            # Read and compile a list of RAP ML files from each directory:
            rap_dirs = [dir for dir in os.listdir(rap_ml_dir) if dir.startswith('20') and os.path.isdir(os.path.join(rap_ml_dir, dir))]# extract ONLY folder starting with '20..'
            rap_files_dirs = [os.path.join(rap_ml_dir, file) for file in rap_dirs] # rap_ml_dir = "'C:\\Users\\oc3512\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\02-Pre-Construction\\01-Environment\\01-LAR\\99-MasterList\\00-N2_RAP_Compiled"
            rap_files = [os.path.join(dir, file) for dir in rap_files_dirs for file in os.listdir(dir) if file.endswith('.xlsx')]
        
            # Each ML is merged with the latest ML            
            ref_t, yyyymmdd_ref = preprocess_table_with_yyyymmdd(rap_files[-1], lotid_field, status_field)
            ref_t = remove_underline_hyphen_from_numeric_field(ref_t, hist_fields)
            ref_t[note_field] = ""

            # Get column names and index
            col_names = ref_t.columns
            col_indices = {name: i for i, name in enumerate(col_names)}
            
            for file in rap_files:
                arcpy.AddMessage(f"Check input table: {os.path.basename(file)}")
                t0, yyyymmdd = preprocess_table_with_yyyymmdd(file, lotid_field, status_field)
                t0 = remove_underline_hyphen_from_numeric_field(t0, hist_fields)
       
                # Check if lotIds are matched with the latest ML                  
                input_dup, target_dup = generate_check_lotid_match(t0, ref_t, lotid_field)

                if (not input_dup) and (not target_dup):
                    rename_array = {
                        status_field: f'x{yyyymmdd}',
                        affectedArea_field: f'x{yyyymmdd}_TAA',
                        handedOverArea_field: f'x{yyyymmdd}_HOA',
                        handedover_field: f'x{yyyymmdd}_HO'
                    }
                    
                    # Keep only 'LotID', 'StatusLA', 'AffectedArea', 'HandedOverArea', 'HandedOver'
                    t1 = t0[keep_fields]
                    ref_t = merge_table_to_masterTable(t1,
                                                       ref_t,
                                                       lotid_field,
                                                       rename_array,
                                                       hist_fields,
                                                       add_dummy_value=True)

                    #--- HandedOverDate ---#
                    # remove "-", "_"
                    ref_t[handedOverDate_field] = ref_t[handedOverDate_field].replace(r'^[-_]','',regex=True)

                    #--- Rename a field to 'Municipality'                    
                    ref_t = rename_columns_title(ref_t, col_names, col_indices, 'City|Municipal', renamed_city)

                    #--- Save the compiled master list ---#
                    ref_t[note_field] = ref_t.pop(note_field)

                    arcpy.AddMessage(ref_t.columns.tolist())

                else:
                    arcpy.AddMessage(f"Input duplicated: {input_dup}")
                    arcpy.AddMessage(f"Target duplicated: {target_dup}")
                    arcpy.AddError('There are duplicated Ids in RAP table shown above. The Process stopped. Please correct the duplicated rows.')
                    break

            #--- export the compiled master list ---#
            filename = f"{str(yyyymmdd_ref)}_{proj}_Compiled_RAP_MasterList.xlsx"
            export_excel(ref_t, rap_ml_dir, filename)

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

            # Define numeric and string fields
            numeric_fields_common = [total_area_field, affected_area_field, remaining_area_field, handedover_area_field, handedover_field, priority_field, statusla_field, moa_field, pte_field]
            to_string_fields = [joinField, package_field]
            to_date_fields = [handover_date_field, handedover_date_field]

            # Import excel files
            rap_table = pd.read_excel(rap_lot_ms)
            gis_table = pd.read_excel(gis_lot_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Land_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Land_Status'))

            #--- Check duplicated LotID
            duplicated_Ids = rap_table[rap_table.duplicated([joinField]) == True][joinField]

            if len(duplicated_Ids) == 0:
                #-- preprocess the RAP table
                rap_table = preprocess_rap_table(proj, 
                                                 rap_table, 
                                                 'land',
                                                 joinField,
                                                 package_field, 
                                                 to_string_fields,
                                                 numeric_fields_common, 
                                                 to_date_fields=to_date_fields, 
                                                 endorsed_field=endorsed_field)

                #--- Convert to uppercase letters for LandUse
                if proj == 'N2':
                    try:
                        rap_table = first_letter_capital(rap_table, [land_use_field])
                        # [] is a set of caracters, so this removes hypen or underline along with space
                        rap_table[land_use_field] = rap_table[land_use_field].replace(r'\s+|[^\w\s$]','',regex=True)
                    except:
                        pass

                #--- Add scale from old master list
                rap_table = rap_table.drop(scale_field,axis=1)
                lot_gis_scale = gis_table[[scale_field, joinField]]
                rap_table = pd.merge(left=rap_table, right=lot_gis_scale, how='left', left_on=joinField, right_on=joinField, validate="one_to_one")

                #--- Add dummy dates for date fields with empty values in the first row
                rap_table = first_row_fill_empty(rap_table, to_date_fields, '1990-01-01', 'date')

                #--- Replace NaN values in HandedOverArea with 0
                rap_table.loc[rap_table.query(f'{handedover_area_field}.isna() or {handedover_area_field}.isna()').index, handedover_area_field] = 0

                #--- Calculate percent handed-over
                rap_table[percent_handedover_area_field] = round((rap_table[handedover_area_field] / rap_table[affected_area_field])*100,0)
                
                # Export (updated rap_table => updated GIS master list)
                export_file_name = f"{os.path.splitext(os.path.basename(gis_lot_ms))[0]}.xlsx"
                export_excel(rap_table, gis_dir, export_file_name)
    
                arcpy.AddMessage("The master list was successfully exported.")

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
            displayName = "GIS ISF Relocation Status ML (Excel) - only for backup",
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
            rap_table = pd.read_excel(rap_isf_ms)
            gis_table = pd.read_excel(gis_isf_ms)

            # Field definitions
            structure_id_field = 'StrucID'
            nlo_status_field = 'StatusRC'
            package_field = 'CP'

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_" + "ISF_Relocation_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format('ISF_Relocation_Status'))
            
            rap_table = preprocess_rap_table(proj, 
                                    rap_table, 
                                    'structure',
                                    structure_id_field,
                                    package_field, 
                                    to_string_fields=[structure_id_field, package_field],
                                    to_numeric_fields=[nlo_status_field, "TypeRC", "HandOver"], 
                                    to_date_fields=None, 
                                    endorsed_field=None)
            
            # Export
            export_file_name = f"{os.path.splitext(os.path.basename(gis_isf_ms))[0]}.xlsx"
            export_excel(rap_table, gis_dir, export_file_name)

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
            displayName = "GIS Structure Status ML (Excel) - only for backup",
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
                  rap_struc_ms, rap_relo_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_struc_ms = params[2].valueAsText
        rap_struc_ms = params[3].valueAsText
        rap_relo_ms = params[4].valueAsText
        gis_bakcup_dir = params[5].valueAsText
        lastupdate = params[6].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True
  
        #--------------------------------------#
        #    Update Excel Master List Tables   #
        #--------------------------------------#
        rap_table = pd.read_excel(rap_struc_ms)
        rap_relo_table = pd.read_excel(rap_relo_ms)
        gis_table = pd.read_excel(gis_struc_ms)

        # Join Field
        joinField = 'StrucID'
        cp_field = 'CP'
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
            #-- preprocess the RAP table
            rap_table = preprocess_rap_table(proj, 
                                                rap_table, 
                                                'structure',
                                                joinField,
                                                cp_field, 
                                                to_string_fields=[joinField, cp_field, structure_use_field],
                                                to_numeric_fields=None, 
                                                to_date_fields=None, 
                                                endorsed_field=None)

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
            export_file_name = f"{os.path.splitext(os.path.basename(gis_struc_ms))[0]}.xlsx"
            export_excel(rap_table, gis_dir, export_file_name)

            arcpy.AddMessage("The {} master list for structure was successfully exported.".format(proj))

        else:
            arcpy.AddMessage(duplicated_Ids)
            arcpy.AddError('There are duplicated Ids in Envi table shown above. The Process stopped. Please correct the duplicated rows.')
            pass

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
                   
        # Define field names
        cp_field = 'CP'
        land1_field = 'Land.1'
        obstruc_field = 'Obstruction'
        lot_id_field = 'LotID'

        # Read as xlsx
        gis_lot_table = pd.read_excel(gis_lot_ms)
        gis_lot_portal_t = pd.read_excel(gis_lot_portal)
        pier_wtracker = pd.read_excel(pier_workable_tracker)

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
            qe = f"{cp_field} == '{cp}'"
            gis_t = gis_lot_table.query(qe).reset_index(drop=True)
            pier_t = pier_wtracker.query(qe).reset_index(drop=True)
            gis_portal_t = gis_lot_portal_t.query(qe).reset_index(drop=True)
            
            #--------------------------------------------------------------#
            ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
            #--------------------------------------------------------------#
            gis_t, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids = add_obstruction_and_extract_ids( 
                                                                                                gis_t, 
                                                                                                gis_portal_t, 
                                                                                                pier_t,
                                                                                                lot_id_field, 
                                                                                                obstruc_field,
                                                                                                "Land",
                                                                                                land1_field,
                                                                                                )
                    
            compile_land = pd.concat([compile_land, gis_t])

            #--------------------------------------------------------------#
            ##                    Summary Statistics                      ##
            #--------------------------------------------------------------#
            summary_table = summary_statistics_count_ids(proj, cp, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids)
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
            struc_obstruc_field = 'Structure'
            struc_obstrucid_field = 'Structure.1'
            obstruc_field = 'Obstruction'
            struc_id_field = 'StrucID'

            # Read as xlsx
            gis_struc_table = pd.read_excel(gis_struc_ms)
            gis_struc_portal_t = pd.read_excel(gis_struc_portal)
            gis_nlo_table = pd.read_excel(gis_nlo_ms)
            pier_wtracker = pd.read_excel(pier_workable_tracker)

            # 0. Reset 'Obstruction' to 'No' first
            gis_struc_table.loc[:, obstruc_field] = np.nan
            gis_nlo_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_struc = pd.DataFrame()
            compile_nlo = pd.DataFrame()
            sum_struc_compile = pd.DataFrame()
            cps = ['N-01','N-02','N-03']

            for cp in cps:
                qe = f"{cp_field} == '{cp}'"
                gis_t = gis_struc_table.query(qe).reset_index(drop=True)
                gis_nlo_t = gis_nlo_table.query(qe).reset_index(drop=True)
                pier_t = pier_wtracker.query(qe).reset_index(drop=True)
                gis_portal_t = gis_struc_portal_t.query(qe).reset_index(drop=True)

                #--------------------------------------------------------------#
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                #--------------------------------------------------------------#
                #--- Structure
                gis_t, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids = add_obstruction_and_extract_ids(
                                                                                                    gis_t, 
                                                                                                    gis_portal_t, 
                                                                                                    pier_t,
                                                                                                    struc_id_field, 
                                                                                                    obstruc_field,
                                                                                                    struc_obstruc_field,
                                                                                                    struc_obstrucid_field)

                #--- 2. NLO
                # Add these obstructing StrucIDs to GIS ISF master list
                # Note that regardless of NLO' status, all the NLOs falling under obstructing structures must be visualized.
                gis_nlo_t, _ = add_obstruction(gis_nlo_t, struc_id_field, obstruc_field, tracker_obs_ids)
 
                # Check obstructing StrucIDS between NLO and Structure GIS master list
                ids = gis_t.query(f"{obstruc_field} == 'Yes'").index
                gis_struc_ids = gis_t.loc[ids, struc_id_field].values

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
                compile_struc = pd.concat([compile_struc, gis_t])
                compile_nlo = pd.concat([compile_nlo, gis_nlo_t])

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids)
                sum_struc_compile = pd.concat([sum_struc_compile, summary_table[0]], ignore_index=False)

            noids_rap_vs_gisml = pd.Series(summary_table[1])    

            #-----------------------------------------------------------------#
            ##  Overwrite existing GIS_Structure_ML with summary statistics  ##
            #-----------------------------------------------------------------#
            # Structure
            arcpy.AddMessage('Structure')

            ## Add missing CPs to compiled table
            miss_cp = tuple(non_match_elements(unique(gis_struc_table[cp_field]), unique(compile_struc[cp_field])))
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
            miss_cp = tuple(non_match_elements(unique(gis_nlo_table[cp_field]), unique(compile_nlo[cp_field])))
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
            gis_lot_portal_table = pd.read_excel(gis_lot_portal)
            pier_wtracker = pd.read_excel(pier_tracker_ms)

            # 0. Reset 'Obstruction' to 'No' first
            gis_lot_table.loc[:, obstruc_field] = np.nan

            # 1. Clean fields
            compile_land = pd.DataFrame()
            sum_lot_compile = pd.DataFrame()

            cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
            for cp in cps:
                qe = f"{cp_field} == '{cp}'"
                gis_t = gis_lot_table.query(qe).reset_index(drop=True)
                pier_t = pier_wtracker.query(qe).reset_index(drop=True)
                gis_portal_t = gis_lot_portal_table.query(qe).reset_index(drop=True)
                
                #--------------------------------------------------------------#
                ## B. Identify Obstruction (Yes' or 'No') to GIS master list ###
                #--------------------------------------------------------------#
                gis_t, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids = add_obstruction_and_extract_ids( 
                                                                                                    gis_t, 
                                                                                                    gis_portal_t, 
                                                                                                    pier_t,
                                                                                                    lot_id_field, 
                                                                                                    obstruc_field,
                                                                                                    land_obstruc_field,
                                                                                                    land_obstrucid_field)
                compile_land = pd.concat([compile_land, gis_t])

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids)
                sum_lot_compile = pd.concat([sum_lot_compile, summary_table[0]], ignore_index=False)

            #--------------------------------------------------------------#
            ##  Overwrite existing GIS_Lot_ML with summary statistics      ##
            #--------------------------------------------------------------#
            miss_cp = tuple(non_match_elements(unique(gis_lot_table[cp_field]), unique(compile_land[cp_field])))

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
            pier_wtracker = pd.read_excel(pier_tracker_ms)

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
                qe = f"{cp_field} == '{cp}'"
                gis_t = gis_struc_table.query(qe).reset_index(drop=True)
                gis_nlo_t = gis_nlo_table.query(qe).reset_index(drop=True)
                pier_t = pier_wtracker.query(qe).reset_index(drop=True)
                gis_portal_t = gis_struc_portal_t.query(qe).reset_index(drop=True)
   
                #--------------------------------------------------------------#
                ##  Identify Obstruction (Yes' or 'No') to GIS master list    ##
                #--------------------------------------------------------------#
                #--- Structure
                gis_t, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids = add_obstruction_and_extract_ids(
                                                                                                    gis_t, 
                                                                                                    gis_portal_t, 
                                                                                                    pier_t,
                                                                                                    struc_id_field, 
                                                                                                    obstruc_field,
                                                                                                    struc_obstruc_field,
                                                                                                    struc_obstrucid_field)

                #--- NLO
                # Add these obstructing StrucIDs to GIS ISF master list
                # Note that regardless of NLO' status, all the NLOs falling under obstructing structures must be visualized.
                gis_nlo_t, _ = add_obstruction(gis_nlo_t, struc_id_field, obstruc_field, tracker_obs_ids)
             
                #--- Compare obstructing StrucIDS between NLO and Structure GIS master list
                ids = gis_nlo_t.index[gis_nlo_t[obstruc_field] == 'Yes']
                gis_nlo_ids = unique(gis_nlo_t.loc[ids, struc_id_field])    
                unmatched_struc_ids = non_match_elements(gis_nlo_ids, gis_obs_ids)

                arcpy.AddMessage(f"{cp}: any obstructing StrucIDs in the NLO missing from structure ML?")
                if len(unmatched_struc_ids) > 0:
                    arcpy.AddMessage(unmatched_struc_ids)
                    arcpy.AddMessage("---------------------------------------------------------------------------------------")
                else:
                    arcpy.AddMessage('No, everything is fine.')
                    arcpy.AddMessage("---------------------------------------------------------------------------------------")

                ## Compile for cps
                compile_struc = pd.concat([compile_struc, gis_t])
                compile_nlo = pd.concat([compile_nlo, gis_nlo_t])

                #--------------------------------------------------------------#
                ##                    Summary Statistics                      ##
                #--------------------------------------------------------------#
                summary_table = summary_statistics_count_ids(proj, cp, tracker_obs_ids, gis_obs_ids, gis_portal_obs_ids)
                sum_struc_compile = pd.concat([sum_struc_compile, summary_table[0]], ignore_index=False)

            #-----------------------------------------------------------------#
            ##  Overwrite existing GIS_Structure_ML with summary statistics  ##
            #-----------------------------------------------------------------#
           
            # Structure
            ## Add missing CPs to compiled table
            miss_cp = tuple(non_match_elements(unique(gis_struc_table[cp_field]), unique(compile_struc[cp_field])))
            if len(miss_cp) > 0:
                gis_struc_misst = gis_struc_table.query(f"{cp_field} in {miss_cp}")
                compile_struc = pd.concat([compile_struc, gis_struc_misst])

            compile_struc.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_struc_ms)), index=False) ## gis_struc
           
            # NLO
            miss_cp = tuple(non_match_elements(unique(gis_nlo_table[cp_field]), unique(compile_nlo[cp_field])))
            if len(miss_cp) > 0:
                gis_nlo_misst = gis_nlo_table.query(f"{cp_field} in {miss_cp}")
                compile_nlo = pd.concat([compile_nlo, gis_nlo_misst])
           
            compile_nlo.to_excel(os.path.join(gis_rap_dir, os.path.basename(gis_nlo_ms)), index=False) ## gis_isf

            # Export summary statistics table
            sum_struc_compile.to_excel(os.path.join(gis_via_dir, '99-SC_Workable_Pier_obstructing_structure_summaryStats.xlsx'), sheet_name='Land', index=False)

        Obstruction_Structure_ML_Update()

class JustMessage2(object):
    def __init__(self):
        self.label = "5.0. ----- Update GIS Layers -----"
        self.description = "Update Excel Master List"

class UpdateLotGIS(object):
    def __init__(self):
        self.label = "5.1. Update GIS Attribute Table (Lot) - Disconnect SDE"
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

        check_box = arcpy.Parameter(
            displayName="Add Missing Fields to Target Feature Layer",
            name="Add Missing Fields to Target Feature Layer",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
       )

        params = [proj, gis_dir, in_lot, ml_lot, check_box]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        project = params[0].valueAsText
        gis_dir = params[1].valueAsText
        target_feature = params[2].valueAsText
        mlLot = params[3].valueAsText
        check_box = params[4].valueAsText

        arcpy.env.overwriteOutput = True

        join_field = "LotID"

        gis_attribute_table_update(gis_dir,
                                target_feature,
                                mlLot,
                                join_field,
                                f"{project}_GIS_Land_Portal",
                                check_box,
                                date_fields=None)

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

        check_box = arcpy.Parameter(
            displayName="Add Missing Fields to Target Feature Layer",
            name="Add Missing Fields to Target Feature Layer",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
       )

        params = [proj, gis_dir, in_structure, in_occupancy, in_isf, ml_structure, ml_isf, check_box]
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
        check_box = params[7].valueAsText

        arcpy.env.overwriteOutput = True

        # 1. Copy Original Feature Layers
        join_field = 'StrucID'
        Struc_Temp = 'Struc_Temp'

        # if there are duplicated observations in Portal and exit
        struc_ids_list = [f[0] for f in arcpy.da.SearchCursor(inStruc, [join_field])]
        duplicated_ids = find_duplicates_ordered(struc_ids_list)
        if duplicated_ids:
            arcpy.AddMessage('The following Struc IDs are duplicated in the GIS attribute table:')
            arcpy.AddMessage(duplicated_ids)
            arcpy.AddError('There are duplicated StrucIDs in the GIS attribute table. The process stops. Please fix this first.')

        else:
            #---------------------------------------------------------#
            #         STAGE 1: Update Existing Structure Layer        #
            #---------------------------------------------------------#
            gis_attribute_table_update(gis_dir,
                            inStruc,
                            mlStruct,
                            'StrucID',
                            f"{project}_GIS_Structure_Portal",
                            check_box,
                            date_fields=None)

            #---------------------------------------------------------------------------------#
            #         STAGE 2: Update Existing Structure (Occupancy) & Structure (ISF)        #
            #---------------------------------------------------------------------------------#      
            # STAGE: 2-1. Create Structure (point) for Occupany
            ## Feature to Point for Occupany
            outFeatureClassPointStruc = 'Struc_pt_occupancy_temp'
            pointStruc = arcpy.management.FeatureToPoint(inStruc, outFeatureClassPointStruc, "CENTROID")
            
            ## Add XY Coordinates
            arcpy.management.AddXY(pointStruc)
            
            ## Truncate original point structure layer (Occupancy)
            arcpy.management.TruncateTable(inOccup)

            ## Append to the original FL
            arcpy.management.Append(pointStruc, inOccup, schema_type = 'NO_TEST')

            # Create and Update ISF Feture Layer
            ## Convert ISF (Relocation excel) to Feature table
            MasterListISF = arcpy.conversion.ExportTable(mlISF, 'MasterListISF')

            # Join
            xCoords = "POINT_X"
            yCoords = "POINT_Y"
            zCoords = "POINT_Z"

            # Join only 'POINT_X' and 'POINT_Y' in the 'inputLayerOccupOrigin' to 'MasterListISF'
            arcpy.management.JoinField(in_data=MasterListISF, in_field=join_field, join_table=inOccup, join_field=join_field, fields=[xCoords, yCoords, zCoords])

            # XY Table to Points (FL)
            out_feature_class = "Status_for_Relocation_ISF_temp"
            sr = arcpy.SpatialReference(3123)
            outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords, zCoords, sr)

            # Delete 'POINT_X', 'POINT_Y', 'POINT_Z'; otherwise, it gives error for the next batch
            dropXYZ = [xCoords, yCoords, zCoords]
            arcpy.management.DeleteField(outLayerISF, dropXYZ)
            
            # Check if StrucIDs match between ISF excel ML and GIS point feature layer
            arcpy.AddMessage(".\n")
            try:
                check_field_match(outLayerISF, MasterListISF, join_field)
            except:
                pass

            # Truncate original ISF point FL
            arcpy.management.TruncateTable(inISF)

            # Append to the Original ISF
            arcpy.management.Append(outLayerISF, inISF, schema_type = 'NO_TEST')

            # Delete the copied feature layer
            deleteTempLayers = [Struc_Temp, pointStruc, outLayerISF, MasterListISF] 
            arcpy.management.Delete(deleteTempLayers)

            #----------------------------------------------------#
            #       Export updated GIS Layers to Excel Sheet     #
            #----------------------------------------------------#
            # NLO
            file_name_nlo = project + "_" + "GIS_ISF_Portal.xlsx"
            arcpy.conversion.TableToExcel(inISF, os.path.join(gis_dir, file_name_nlo))

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

