import arcpy
import pandas as pd
import os
from pathlib import Path
from datetime import date, datetime
import re
import string
import numpy as np
import time

def unique(lists):
    collect = []
    unique_list = pd.Series(lists).drop_duplicates().tolist()
    for x in unique_list:
        collect.append(x)
    return(collect)

def match_elements(list_a, list_b):
    matched = []
    for i in list_a:
        if i in list_b:
            matched.append(i)
    return matched

def toString(table, to_string_fields): # list of fields to be converted to string
    for field in to_string_fields:
        ## Need to convert string first, then apply space removal, and then convert to string again
        ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
        table[field] = table[field].astype(str)
        table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
        table[field] = table[field].astype(str)
        
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
        
    table = pd.merge(left=target_table, right=input_table, how='left', left_on=join_field, right_on=join_field)
    return table

def convert_status_to_numeric(table, dic, input_field, new_field):
    for i in range(len(dic)):
        id = table.index[table[input_field] == list(dic.keys())[i]]
        table.loc[id, new_field] = list(dic.values())[i]
        
def toNumeric(table, fields):
    for i in range(len(fields)):
        table[fields[i]] = pd.to_numeric(table[fields[i]])
        
def toString(table, to_string_fields): # list of fields to be converted to string
    for field in to_string_fields:
        ## Need to convert string first, then apply space removal, and then convert to string again
        ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
        table[field] = table[field].astype(str)
        
def toDate(table, field):
    table[field] = pd.to_datetime(table[field],format='%Y-%m-%d', errors='coerce').dt.date
    #table[field] = table[field].astype('datetime64[ns]')

def to_Date_no_hms(table, field):
    table[field] = pd.to_datetime(table[field], format='%Y-%m-%d', errors='coerce').dt.date
    table[field] = table[field].astype('datetime64[ns]')
    return table

def add_status(table, start_field, finish_field, status_field):
    table[status_field] = 1

    ## if finishdate, completed (Status = 4)
    idx = table.query(f"{finish_field}.notna()").index
    table.loc[idx, status_field] = 4

    ## if startdate & !finishdate, ongoing (Status = 2)
    idx = table.query(f"{start_field}.notna() and {finish_field}.isna()").index
    table.loc[idx, status_field] = 2
    return table

def find_duplicates_ordered(arr):
    seen = set()
    duplicates = set()
    for item in arr:
        if item in seen:
            duplicates.add(item) # Use a set to avoid adding the same duplicate multiple times
        else:
            seen.add(item)
    non_na = [x for x in list(duplicates) if x == x] # this removes nan
    return non_na

def replace_strings_table(table, field, array):
    """
    table: pandas dataFrame
    field: field to be updated
    array: array of pattern and replacement strings (e.g., {r'3A|3B': '3a', r''...})
    """
    for item in array:
        table[field] = table[field].str.replace(item, array[item], regex=True)
    return table

def replace_strings_in_dataframe(table, field, search_replace_arrays):
    """
    Replace multiple strings in a DataFrame column.
    table: pandas DataFrame
    field: column name where the replacement will occur
    search_replace_arrays: list of dictionary containing (search_string, replace_string)
    Example: {
    search_replace_arrays = {
        r'\s+': '',
        r'CPN': 'N-',
        r'[,/].*' : '' # This will remove anything after ',' or '/' in the string
    }
    """
    for search in search_replace_arrays:
        # table[field] = table[field].str.replace(search, search_replace_arrays[search], regex=True)
        table[field] = table[field].apply(lambda x: re.sub(search, search_replace_arrays[search], str(x)))
    return table

def extract_pier_numbers(pier_num_field, gist=None, civilt=None, piertrackt=None):
    if gist is not None:
        piers = gist[pier_num_field].values

    elif civilt is not None:
        #--- Update pier number for monopiles
        piers = civilt[pier_num_field].values

    elif piertrackt is not None:
        piers = piertrackt[pier_num_field].values
    return piers

def non_match_elements(list_a, list_b):
    non_match = []
    for i in list_a:
        if i not in list_b:
            non_match.append(i)
    return non_match

def summary_statistics_count_piers(cp, ids1, ids2, columns, ids3=None):
    # Primary ids = ids1
    table = pd.DataFrame(columns=columns)
    if ids3 is not None:
        noids_ids1_vs_ids2 = ",".join(non_match_elements(ids1, ids2))
        noids_ids1_vs_ids3 = ",".join(non_match_elements(ids1, ids3))
        params = [cp, len(ids1), len(ids2), len(ids3), noids_ids1_vs_ids2, noids_ids1_vs_ids3]
        for i in range(0, len(columns)):
            table.loc[0, columns[i]] = params[i]

    else:
        noids_ids1_vs_ids2 = ",".join(non_match_elements(ids1, ids2))
        params = [cp, len(ids1), len(ids2), noids_ids1_vs_ids2]
        for i in range(0, len(columns)):
            table.loc[0, columns[i]] = params[i]

    return table

def find_word_location(df, search_word):
    """
    Finds the index and column of a specific word in a Pandas DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to search.
        search_word (str): The word to search for.

    Returns:
        list: A list of dictionaries, where each dictionary represents a location
            of the word in the DataFrame. Each dictionary has 'index' and 'column' keys.
            Returns an empty list if the word is not found.
    """
    locations = []
    col_idx = {name: i for i, name in enumerate(df)}
    for col in df.columns:
        for idx, value in df[col].items():
            if isinstance(value, str) and search_word in value.title():
                locations.append({'index': idx, 'column': col, 'colidx': col_idx[col]})
            elif isinstance(value, str) and search_word in value:
                locations.append({'index': idx, 'column': col, 'colidx': col_idx[col]})       
    return locations

def preprocess_civil_table(idx,
                           file,
                           sheet_name,
                           remarks_field,
                           type_field, 
                           start_actual_field, 
                           finish_plan_field, 
                           finish_actual_field, 
                           package_field, No_field, 
                           civil_pier_field,
                           status_field,
                           ):
    x = pd.read_excel(file, sheet_name = sheet_name)
    ids = x.query(f"{remarks_field} == 'SAMPLE'").index
    x = x.iloc[ids[0] + 1:, ].reset_index(drop=True)
    # x = x.drop(ids).reset_index(drop=True)

    # Remove empty pier number
    ids = x.query(f"{civil_pier_field}.isna()").index
    x = x.drop(ids).reset_index(drop=True)
    
    # Keep columns until 'Remarks' field
    col_index = {name: i for i, name in enumerate(x.columns)}
    ids = col_index[remarks_field]
    x = x[x.columns[0:ids]]
    
    # Remove emtpy columns
    col_index = {name: i for i, name in enumerate(x.columns)}
    ids = [v for k, v in col_index.items() if k.startswith('Unnamed')]
    x = x.drop(x.columns[ids], axis=1)
    
    # Add Type
    x[type_field] = str(idx + 1)

    # Reformat date fields
    for field in [start_actual_field, finish_plan_field, finish_actual_field]:
        x = to_Date_no_hms(x, field)

    # Add Status
    x = add_status(x, start_actual_field, finish_actual_field, status_field)

    # Reformat Pier: BUEP-(x) -> BUE-P (O)
    changed_items_array = {
        r'BUEP-': 'BUE-P',
        r'^P-': 'P',
        r'^P': 'P-',
        r'^P-R': 'PR'
    }
        
    # x = replace_strings_table(x, civil_pier_field, changed_items_array)
    x = replace_strings_in_dataframe(x, civil_pier_field, changed_items_array)
    x[civil_pier_field] = x[civil_pier_field].str.upper()

    # Drop empty rows
    ## Bored Pile
    if idx == 0:
        ids = x.query(f"{package_field}.isna() or {No_field}.isna()").index
        x = x.drop(ids).reset_index(drop=True)
    # else:
    #     ids = x.query(f"{civil_pier_field}.isna()").index
    #     x = x.drop(ids).reset_index(drop=True)
    return x

#--- Custom class for generating a summary statistics table ---#
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
        self.label = "UpdateSCViaduct"
        self.alias = "UpdateSCViaduct"
        self.tools = [JustMessage1,
                      CompileViaductMasterList,
                      UpdateExcelML, UpdateGISTable,
                      JustMessage2, CreateWorkablePierLayer,
                      UpdatePierWorkableTrackerML, CheckPierNumbers,
                      UpdatePierWorkablePolygonLayer, UpdatePierPointLayer, UpdateStripMapLayer,
                      ReSortGISTable,
                      JustMessage3,
                      GenerateStatisticsBetweenTwoTables,
                      ViaductBIMUpdateMessage,
                      CreateBIMtoGeodatabase, CreateBuildingLayers, AppendBatchesBIM, AddFieldsToBuildingLayerStation, EditBuildingLayerStation, DomainSettingStationStructure]

class JustMessage1(object):
    def __init__(self):
        self.label = "2.0.----- Update SC Viaduct -----"
        self.description = "Update Viaduct using Multipatch & Excel"

class CompileViaductMasterList(object):
    def __init__(self):
        self.label = "2.1. Compile Civil ML Tables (SC Viaduct)"
        self.description = "Compile Civil ML Tables (SC Viaduct)"

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

        via_dir = arcpy.Parameter(
            displayName = "SC Viaduct Output Directory",
            name = "SC Viaduct Output Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "SC Viaduct Civil Master List (Excel)",
            name = "SC Viaduct Civil Master List",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [proj, via_dir, civil_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        via_dir = params[1].valueAsText
        civil_ml = params[2].valueAsText

        def N2_Compile_viaduct_tables():
            cp_field = 'CP'
            status_field = 'Status'
            type_field = 'Type'
            pierno_field = 'PierNumber'
            pileno_field = 'PileNo'
            pierno_id = 'PierId'
            civil_pier_field = 'Pier'

            # Columns in Civil ML
            No_field = 'No'
            start_actual_field = 'start_actual'
            finish_plan_field = 'finish_plan'
            finish_actual_field = 'finish_actual'
            package_field = 'Package'
            remarks_field = 'Remarks'
            segment_field = 'Segment'

            viaduct_types = ['BoredPile', 'PileCap', 'Pier', 'PierHead', 'Precast']

            rename_cols = {
                civil_pier_field: pierno_field,
                package_field: cp_field,
                No_field: pileno_field,
            }

            comp_table = pd.DataFrame()
            for i, type in enumerate(viaduct_types):
                x = preprocess_civil_table(i,
                   civil_ml,
                   type,
                   remarks_field,
                   type_field, 
                   start_actual_field, 
                   finish_plan_field, 
                   finish_actual_field, 
                   package_field, No_field, 
                   civil_pier_field,
                   status_field,
                   )
                #--- Bored Pile ---#
                if i == 0:                    
                    # Fix pile no
                    x[No_field] = x[No_field].astype(str).str.replace('.0','')
                
                    # Crete pileId
                    x[pierno_id] = x[civil_pier_field] + "-" + x[No_field] + "-" + x[type_field]

                    # Compile
                    comp_table = pd.concat([comp_table, x])

                #--- Other components ---#
                else:
                    # Crete pileId
                    x[pierno_id] = x[civil_pier_field] + "-" + x[type_field]
                
                    # Compile
                    comp_table = pd.concat([comp_table, x])

            #--- Conver type_field to integer ---#
            comp_table[type_field] = comp_table[type_field].astype('int64')

            #--- Check duplication
            duplicated_ids = find_duplicates_ordered(comp_table[pierno_id].values)

            if duplicated_ids:
                arcpy.AddMessage(f"Duplicated PierIds were found: {duplicated_ids}")
                arcpy.AddError("Please check Civil's master list table.")
            else:
                #--- Rename columns ---#
                col_index = {name: i for i, name in enumerate(comp_table.columns)}
                comp_table = comp_table.drop(comp_table.columns[col_index[segment_field]], axis=1)

                for col in rename_cols:
                    comp_table = comp_table.rename(columns={str(col): rename_cols[col]})

                #--- Re-format BUEP (x) -> BUE-P (O), SCTP (x) -> SCT-P (O)
                arrays = {
                    r'^BUEP': 'BUE-P',
                    r'^SCTP': 'SCT-P',
                    r'^P--': 'P-'
                }
                comp_table = replace_strings_in_dataframe(comp_table, pierno_field, arrays)

                #--- Fix CP notation
                arrays = {
                    r'^1$': 'S-01',
                    r'^2$': 'S-02',
                    r'^4$': 'S-04',
                    r'^5$': 'S-05',
                    r'^6$': 'S-06',
                    r'^3a$': 'S-03a',
                    r'^3c$': 'S-03c',
                    r'^S02$': r'S-02',
                    r'^S03A$': r'S-03a',
                    r'^S04$': r'S-04',
                    r'^S05$': r'S-05',
                    r'^S06$': r'S-06',
                }
                comp_table = replace_strings_in_dataframe(comp_table, cp_field, arrays)

                #--- Remove Pier Number with 'ES..'
                ids = comp_table[comp_table[pierno_field].str.contains(r'^ES.*', regex=True, na=False)].index
                comp_table = comp_table.drop(ids).reset_index(drop=True)

                excel_file = proj + "_Viaduct_Civil_ML_compiled.xlsx"
                comp_table.to_excel(os.path.join(via_dir, excel_file), index=False)

        N2_Compile_viaduct_tables()

class UpdateExcelML(object):
    def __init__(self):
        self.label = "2.2. Update GIS Excel ML (SC Viaduct)"
        self.description = "2. Update GIS Excel ML (SC Viaduct)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "SC Viaduct Directory",
            name = "SC Viaduct Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "SC Viaducut GIS ML (Excel)",
            name = "SC Viaducut GIS ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "SC Viaduct Civil ML Compiled (Excel)",
            name = "SC Viaduct Civil ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_dir, gis_ml, civil_ml]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_ml = params[1].valueAsText
        civil_ml = params[2].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def SC_Viaduct_Update():
            status_field = 'Status'
            pierno_id = 'PierId'
            start_actual_field = 'start_actual'
            finish_plan_field = 'finish_plan'
            finish_actual_field = 'finish_actual'
            dummy_date = '1990-01-01'
            dates_fields = [start_actual_field, finish_plan_field, finish_actual_field]

            gis_t = pd.read_excel(gis_ml, keep_default_na=False)
            civil_t = pd.read_excel(civil_ml)

            #--- Compare PierIds between Civil and GIS ML
            ids = civil_t.query(f"{status_field} == 4 or {status_field} == 2").index
            civil_piers = civil_t.loc[ids, pierno_id].values
            ids = gis_t.query(f"{pierno_id}.isin({tuple(civil_piers)})").index
            gis_piers = gis_t.loc[ids, pierno_id].values

            notin_civil = [f for f in gis_piers if f not in civil_piers]
            notin_gis = [f for f in civil_piers if f not in gis_piers]

            if notin_civil or notin_gis:
                arcpy.AddMessagey("PierIds are not matched between GIS and Civil master list tables.")
                arcpy.AddMessage(f"Not in Civil ML: {notin_civil}")
                arcpy.AddMessage(f"Not in GIS ML: {notin_gis}")

            #--- Update Status
            else:
                #--- Update Status ---#
                gis_t[status_field] = 1

                # Completed (status=4) and ongoing(status=2)
                for status in (2, 4):
                    civil_piers = civil_t.loc[civil_t.query(f"{status_field} == {status}").index, pierno_id].values
                    ids = gis_t.query(f"{pierno_id}.isin({tuple(civil_piers)})").index
                    gis_t.loc[ids, status_field] = status

                #--- Add dummy dates when the first of date fields are empty
                for field in dates_fields:
                    gis_t = to_Date_no_hms(gis_t, field)
                    date_item = gis_t[field].iloc[:1].item()
                    if date_item is None or pd.isnull(date_item):
                        gis_t.loc[0, field] = pd.to_datetime(dummy_date, format='%Y-%m-%d', errors='coerce')

                #--- Export ---#
                gis_t.to_excel(os.path.join(gis_dir, "SC_Viaduct_ML_new.xlsx"), index=False)
                    
        SC_Viaduct_Update()

class UpdateGISTable(object):
    def __init__(self):
        self.label = "2.3. Update GIS Attribute Table (SC Viaduct)"
        self.description = "Update SC Viaduct multipatch layer (SC Viaduct)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "SC Viaduct Directory",
            name = "SC Viaduct Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        gis_layer = arcpy.Parameter(
            displayName = "SC Viaduct Layer (Multipatch)",
            name = "SC Viaduct Layer (Multipatch)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        excel_table = arcpy.Parameter(
            displayName = "SC Viaduct ML (Feature Table)",
            name = "SC Viaduct ML (Feature Table)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_dir, gis_layer, excel_table]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_layer = params[1].valueAsText
        excel_table = params[2].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        arcpy.AddMessage('Updating SC Viaduct layer has started..')

        # For Removing dummy dates if any specified in the first tool
        start_actual_field = 'start_actual'
        finish_plan_field = 'finish_plan'
        finish_actual_field = 'finish_actual'
        date_fields = [start_actual_field, finish_plan_field, finish_actual_field]

        uniqueID = 'uniqueID'

        # 1. Copy Original Feature Layers
        copied_name = 'tempLayer'               
        gis_copied = arcpy.CopyFeatures_management(gis_layer, copied_name)
            
        arcpy.AddMessage("Stage 1: Copy feature layer was success")
                
        # 2. Delete Field
        gis_fields = [f.name for f in arcpy.ListFields(gis_copied)]
            
        ## 2.1. Identify fields to be dropped
        gis_drop_fields_check = [e for e in gis_fields if e not in (uniqueID,'Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
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
        viaduct_ml = arcpy.conversion.ExportTable(excel_table, 'viaduct_ml')

        # Check if LotID match between ML and GIS
        uniqueid_gis = unique_values(gis_copied, uniqueID)
        uniqueid_ml = unique_values(viaduct_ml, uniqueID)
        
        uniqueid_miss_gis = [e for e in uniqueid_gis if e not in uniqueid_ml]
        uniqueid_miss_ml = [e for e in uniqueid_ml if e not in uniqueid_gis]

        if uniqueid_miss_ml or uniqueid_miss_gis:
            arcpy.AddMessage('The following uniqueIDs do not match between ML and GIS.')
            
        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        viaduct_ml_fields = [f.name for f in arcpy.ListFields(viaduct_ml)]
        viaduct_ml_transfer_fields = [e for e in viaduct_ml_fields if e not in ('LotId', uniqueID,'OBJECTID')]
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in ('LotId', uniqueID)]))                      
        viaduct_ml_join_field =' '.join(map(str, [f for f in viaduct_ml_fields if f in ('LotId', uniqueID)]))
            
        ## 3.4 Join
        arcpy.JoinField_management(in_data=gis_copied, in_field=gis_join_field, join_table=viaduct_ml, join_field=viaduct_ml_join_field, fields=viaduct_ml_transfer_fields)

        ## 3.5. Remove dummy date from GIS attribute table if any
        try:
            for field in date_fields:
                with arcpy.da.UpdateCursor(gis_copied, [field]) as cursor:
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

        # 4. Trucnate
        arcpy.TruncateTable_management(gis_layer)

        # 5. Append
        arcpy.Append_management(gis_copied, gis_layer, schema_type = 'NO_TEST')

        # 6. Table to Excel
        # (This ensures that SC_Viaduct_ML.xlsx is always consistent with SC Viaduct GIS attribute table)
        # Reason: uniqueID is sometimes updated in the GIS attribute table
        arcpy.conversion.TableToExcel(gis_layer, os.path.join(gis_dir, 'SC_Viaduct_Portal.xlsx'))
        
        # Delete the copied feature layer
        deleteTempLayers = [gis_copied, viaduct_ml]
        arcpy.Delete_management(deleteTempLayers)

class JustMessage2(object):
    def __init__(self):
        self.label = "3.0.----- Update SC Pier Workability -----"
        self.description = "Update Viaduct using Multipatch & Excel"

class CreateWorkablePierLayer(object):
    def __init__(self):
        self.label = "3.1. Create Pier Workable Layer (Polygon)"
        self.description = "Create Pier Workable Layer"

    def getParameterInfo(self):
        # Input Feature Layers
        workable_pier_layer = arcpy.Parameter(
            displayName = "SC Pier Workability Layer (Polygon)",
            name = "SC Pier Workability Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        via_layer = arcpy.Parameter(
            displayName = "SC Viaduct Layer (Multipatch)",
            name = "SC Viaduct Layer (Multipatch)",
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

        new_fields = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']

        #--- Pier Workability Status ---#
        # 0 = 'Workable'
        # 1 = 'Non-workable'
        # 2 = Completed (construction)

        # Extract pile cap only (Type = 2)
        temp_layer = 'temp_layer'
        type2_exression = f"{type_field} = 2"
        # '"Type" = 2'
        arcpy.management.MakeFeatureLayer(via_layer, temp_layer, type2_exression)

        # 'multipatch footprint'
        new_layer = 'SC_Pier_Workable'
        arcpy.ddd.MultiPatchFootprint(temp_layer, new_layer)

        #--- Keep fields
        arcpy.management.DeleteField(new_layer, [cp_field, pier_number_field, unique_id_field, status_field, type_field], "KEEP_FIELDS")

        # Add field
        for field in new_fields:
            arcpy.management.AddField(new_layer, field, "SHORT", field_alias=field, field_is_nullable="NULLABLE")

        with arcpy.da.UpdateCursor(new_layer, [type_field, status_field, 'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']) as cursor:
            # 0: Non-workable, 1: Workable, 2: Completed
            for row in cursor:
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

class UpdatePierWorkableTrackerML(object):
    def __init__(self):
        self.label = "3.2. Update Pier Workability Tracker (Excel)"
        self.description = "Update Pier Workability Tracker (Excel)"

    def getParameterInfo(self):
        gis_viaduct_dir = arcpy.Parameter(
            displayName = "SC Pier Workability Directory",
            name = "SC Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_workable_ms = arcpy.Parameter(
            displayName = "SC Pier Workability Civil ML (Excel)",
            name = "SC Pier Workability Civil ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_workable_layer = arcpy.Parameter(
            displayName = "SC Pier Workability Layer (Polygon)",
            name = "SC Pier Workability Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_viaduct_dir, civil_workable_ms, gis_workable_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_workability_dir = params[0].valueAsText
        civil_workable_ms = params[1].valueAsText
        gis_workable_layer = params[2].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Workable_Pier_Table_Update():
            cp_field = 'CP'
            status_field = 'Status'
            pier_number_field = 'PierNumber'
            workability_field = 'Workability'
            utility_field = 'Utility'
            others_field = 'Others'
            land_field = 'Land'
            struc_field = 'Structure'
            land1_field = 'Land.1'
            struc1_field = 'Structure.1'
            nlo_field = 'NLO'
            remarks_field = 'Remarks'

            #--- Get a correct sheetname
            xls = pd.ExcelFile(civil_workable_ms)
            # sheet_name = [f for f in xls.sheet_names if f.startswith('Summary')][0]
            civil_t = pd.read_excel(civil_workable_ms, sheet_name="SUMMARY BREAKDOWN (B271 only)")

            columns = [cp_field, 
                       pier_number_field, 
                       workability_field, 
                       utility_field, 
                       others_field, 
                       land_field, 
                       struc_field,
                       nlo_field, 
                       land1_field, 
                       struc1_field,
                       remarks_field]
            
            cols = find_word_location(civil_t, "Workability")[1]
            civil_t = civil_t.iloc[:, np.r_[0,1,cols['colidx']:21]].loc[2:, ].reset_index(drop=True)
            civil_t.columns = columns

            #--- Reformat Obstruction ids for land and structure (with NLO) ---#
            arrays = {
                    r'\n': ',',
                    r';': ',',
                    r';;': ',',
                    r',,': ',',
                    r',,,': ',',
                    r',$': '',
                    r'^,': '',
                    r'nan': '',
                    r'\s+': '',
                    r'^[,./]': '',
                    r'[,./]$': ''
                    }
            
            for field in [land1_field, struc1_field]:
                civil_t = replace_strings_in_dataframe(civil_t, field, arrays)
                ids = civil_t.index[civil_t[field] == '']
                civil_t.loc[ids, field] = np.nan

            #--- Update 'Workability' field ---#
            # 'Workability' = Completed
            layer_piers = [k[0] for k in arcpy.da.SearchCursor(gis_workable_layer, [pier_number_field, 'AllWorkable']) if k[1] == 2]
            idx = civil_t.index[civil_t[pier_number_field].isin(layer_piers)]
            civil_piers = civil_t.loc[idx, pier_number_field].values

            notin_civil = [f for f in layer_piers if f not in civil_piers]
            notin_layer = [f for f in civil_piers if f not in layer_piers]

            if notin_civil or notin_layer:
                arcpy.AddMessage("There are unmatching pier numbers.. between Pier Workability Polygon and Civil Tracker ML")
            else:
                civil_t.loc[idx, workability_field] = 'Completed'

            #--- Add 'Status' ---#
            civil_t[status_field] = 1
            civil_t.loc[idx, status_field] = 4

            #---- Keep only pier numbers starting with 'P' and 'BUE'
            ids = civil_t[civil_t[pier_number_field].str.contains(r'^P|^BUE', regex=True, na=False)].index
            civil_t = civil_t.loc[ids, ]

            #--------------------------------------------------------#
            #                 Identify Discrepancies                 #
            #--------------------------------------------------------#
            # Add case of errors to Remarks field;
            # 1. Completed and Workable piers have obstructions (in Utility, Land, Structure, Others, Land.1, Structure.1)
            # 2. Non-workable piers have empty cells in Utility, Land, Structure, Others, Land.1, Structure.1.
            # 3. Piers with obstructing Land (1) or Structure (1) do not have any IDs in Land.1 or Structure.1 field.
            # 4. Piers with obstructing Lot or Structure IDs in Land.1 or Structure.1 field do not have '1' in Land or Structure field.

            civil_t[remarks_field] = np.nan
            error_descriptions =   {
                    # 'case1': 'Workable or completed piers should not have obstructions in one or more columns.',
                    'case2': 'Non-workable piers should have at least one obstruction in columns.',
                    'case3': 'This pier is missing obstructing LotIDs.',
                    'case4': 'This pier is missing obstructing StructureIDs.',
                    'case5': 'This pier is missing obstruction in Land',
                    'case6': 'This pier is missing obstruction in Structure'
                    }
            
            query_str = {
                'case2': ("(`{}` == 'Non-workable') & "
                        "`{}`.isna() & `{}`.isna() & `{}`.isna() & "
                        "`{}`.isna() & `{}`.isna() & `{}`.isna()"
                        ).format(workability_field, utility_field, land_field, struc_field, others_field, land1_field, struc1_field),
                'case3': ("`{}` == 'Non-workable' & `{}` == 1 & `{}`.isna()").format(workability_field, land_field, land1_field),
                'case4': ("`{}` == 'Non-workable' & `{}` == 1 & `{}`.isna()").format(workability_field, struc_field, struc1_field),
                'case5': ("`{}` == 'Non-workable' & `{}` == 1 & ~`{}`.isna()").format(workability_field, land1_field, land_field),
                'case6': ("`{}` == 'Non-workable' & `{}` == 1 & ~`{}`.isna()").format(workability_field, struc1_field, struc_field)
            }

            for error in error_descriptions:
                ids = civil_t.query(query_str[error]).index
                civil_t.loc[ids, remarks_field] = error_descriptions[error]

            #--- Export ---#
            excel_file = os.path.join(pier_workability_dir, "SC_Pier_Workability_Tracker.xlsx")
            civil_t.to_excel(excel_file, index=False)
                        
        Workable_Pier_Table_Update()

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "3.3. Check Pier Numbers between Civil and GIS Portal"
        self.description = "Check Pier Numbers between Civil and GIS Portal"

    def getParameterInfo(self):
        pier_tracker_dir = arcpy.Parameter(
            displayName = "SC Pier Workability Directory",
            name = "SC Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "SC Pier Workability Tracker (Excel)",
            name = "SC Civil Pier Workability Tracker (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_viaduct_ms = arcpy.Parameter(
            displayName = "SC Viaduct ML (Excel)",
            name = "SC Viaduct ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_tracker_dir, pier_workable_tracker_ms, gis_viaduct_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_tracker_dir = params[0].valueAsText
        pier_tracker_ms = params[1].valueAsText
        gis_viaduct_ms = params[2].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Workable_Pier_Table_Update():
            # List of fields
            type_field = 'Type'
            pier_num_field = 'PierNumber'
            cp_field = 'CP'

            gis_t = pd.read_excel(gis_viaduct_ms)
            tracker_t = pd.read_excel(pier_tracker_ms)

            compile_table = pd.DataFrame()

            for cp in ['S-01', 'S-02', 'S-03a', 'S-03c', 'S-04', 'S-05', 'S-06']:
                gist = gis_t.query(f"{cp_field} == '{cp}' & {type_field} == 2").reset_index(drop=True)
                trackert = tracker_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                
                gis_piers = extract_pier_numbers(pier_num_field, gist, None, None)
                tracker_piers = extract_pier_numbers(pier_num_field, None, None, trackert)

                columns = ['cp',
                            'gis',
                            'tracker',
                            'non-matched piers (gis-tracker)',
                            ]
                
                table = summary_statistics_count_piers(cp, gis_piers, tracker_piers, columns, None)

                # Compile cps
                compile_table = pd.concat([compile_table, table])
            
            # Export
            compile_table.to_excel(os.path.join(pier_tracker_dir, '99-CHECK_Summary_SC_PierNumbers_GIS_ML_vs_pierTracker.xlsx'),
                                              index=False)


        Workable_Pier_Table_Update()

class UpdatePierWorkablePolygonLayer(object):
    def __init__(self):
        self.label = "3.4. Update Pier Workable Layer (Polygon)"
        self.description = "Update Pier Workable Layer (Polygon)"

    def getParameterInfo(self):               
        pier_workable_tracker_ms = arcpy.Parameter(
            displayName = "SC Pier Workability Tracker ML (Excel)",
            name = "SC Pier Workability Tracker ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_workable_layer = arcpy.Parameter(
            displayName = "SC Pier Workability Layer (Polygon)",
            name = "SC Pier Workability Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_workable_tracker_ms, gis_workable_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_tracker_ms = params[0].valueAsText
        gis_workable_layer = params[1].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Workable_Pier_Table_Update():            
            # List of fields
            cp_field = 'CP'
            type_field = 'Type'
            status_field = 'Status'
            pier_number_field = 'PierNumber'
            workability_field = 'Workability'
            land_obstruc_field = 'Land'
            struc_obstruc_field = 'Structure'
            others_obstruc_field = 'Others'
            lot_obstrucid_field = 'Land.1'
            struc_obstrucid_field = 'Structure.1'
            utility_obstruc_field = 'Utility'
            nlo_obstruc_field = 'NLO'
            remarks_field = 'Remarks'

            x = pd.read_excel(pier_tracker_ms)

            #----------------------------------------------------#
            #  Update Pier Workable Layer using Civil table      #
            #----------------------------------------------------#

            # Workable Pile Cap
            ## 1: Non-Workable
            ## 0: Workable (i.e, construction is incomplete)
            ## 2: Completed

            workable_cols = ['AllWorkable',
                    'LandWorkable',
                    'StrucWorkable',
                    'NLOWorkable', 
                    'UtilWorkable', 
                    'OthersWorkable'
                    ]
            
            obstruction_cols = [workability_field, 
                    land_obstruc_field, 
                    struc_obstruc_field,
                    nlo_obstruc_field,
                    utility_obstruc_field,
                    others_obstruc_field
                    ]

           # --- Update fields to 'Workable' for incomplete pile caps ---#
            id_workable_piers = x.query(f"{workability_field} == 'Workable'").index
            incomp_workable_piers = x.loc[id_workable_piers, pier_number_field].values

            with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']) as cursor:
                for row in cursor:
                    if row[0] in tuple(incomp_workable_piers):
                        row[1] = 0
                        row[2] = 0
                        row[3] = 0
                        row[4] = 0
                        row[5] = 0
                        row[6] = 0
                    cursor.updateRow(row)

            #--- Update fields to 'Non-workable' ---#
            for i, col in enumerate(workable_cols):
                if col == workable_cols[0]:
                    ids = x.query(f"{workability_field} == 'Non-workable'").index
                    nonworkable_piers = x.loc[ids, pier_number_field].values
                    with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, col]) as cursor:
                        for row in cursor:
                            if row[0] in tuple(nonworkable_piers):
                                row[1] = 1
                            cursor.updateRow(row)
                else:
                    ids = x.query(f"{obstruction_cols[i]} == 1").index
                    nonworkable_piers = x.loc[ids, pier_number_field].values
                    with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[i]]) as cursor:
                        for row in cursor:
                            if row[0] in tuple(nonworkable_piers):
                                row[1] = 1
                            cursor.updateRow(row)

            #--- Update fields to 'Workable for empty pile caps' ---#
            # Until here, all the empty cells in workable fields are for workable pile caps.
            # But only when 'AllWorkabile' is not None.
            for col in workable_cols[1:]:
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[0], col]) as cursor:
                    for row in cursor:
                        if row[1] is not None:
                            if row[2] is None:
                                row[2] = 0
                        cursor.updateRow(row)

            #--- Completed pile cap => 2 (completed). 
            with arcpy.da.UpdateCursor(gis_workable_layer, [status_field, 'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']) as cursor:
                # 0: Non-workable, 1: Workable, 2: Completed
                for row in cursor:
                    if row[0] == 4:
                        row[1] = 2
                        row[2] = 2
                        row[3] = 2
                        row[4] = 2
                        row[5] = 2
                        row[6] = 2
                    cursor.updateRow(row)

            ## Export this layer to excel
            #arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(pier_workability_dir, "SC_Pier_Workability_GIS_Portal.xlsx"))

            #--------------------------------------------------------#
            #       Update Pier Workable Layer for 'Remarks'         #
            #--------------------------------------------------------#
            idx = x.query(f"{remarks_field}.notna()").index
            remarks_piers = x.loc[idx, pier_number_field].values
            remarks_text = x.loc[idx, remarks_field].values
            with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, remarks_field]) as cursor:
                for row in cursor:
                    if row[0] in tuple(remarks_piers):
                        idx2 = [index for index, value in enumerate(remarks_piers) if value == row[0]][0]
                        row[1] = remarks_text[idx2]
                    cursor.updateRow(row)

            ## Export this layer to excel
            # arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(gis_dir, "SC_Pier_Workability_Portal.xlsx"))

        Workable_Pier_Table_Update()

class UpdatePierPointLayer(object):
    def __init__(self):
        self.label = "3.5. Update Pier Layer (Point)"
        self.description = "Update Pier Layer (Point)"

    def getParameterInfo(self):
        pier_point_layer = arcpy.Parameter(
            displayName = "SC Pier Layer (Point)",
            name = "SC Pier Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        pier_workable_layer = arcpy.Parameter(
            displayName = "SC Pier Workability Layer (Polygon)",
            name = "SC Pier Workability Layer (Polygon)",
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
        # viaduct_layer = params[2].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Pier_Point_Layer_Update():
            new_point_layer = 'SC_new_Pier_Point'
            arcpy.management.FeatureToPoint(pier_workable_layer, new_point_layer)

            #--- Truncate an existing pier point layer
            arcpy.management.TruncateTable(pier_point_layer)

            #--- Append new point layer to the old one
            arcpy.management.Append(new_point_layer, pier_point_layer, schema_type = 'NO_TEST')
 
        Pier_Point_Layer_Update()

class UpdateStripMapLayer(object):
    def __init__(self):
        self.label = "3.6. Update Strip Map Layer (Polygon)"
        self.description = "Update Strip Map Layer (Polygon)"

    def getParameterInfo(self):
        pier_point_layer = arcpy.Parameter(
            displayName = "SC Pier Layer (Point)",
            name = "SC Pier Layer (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        strip_map_layer = arcpy.Parameter(
            displayName = "SC Strip Map Layer (Polygon)",
            name = "SC Strip Map Layer (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        cp_breakline_layer = arcpy.Parameter(
            displayName = "SC CP Breakline Layer (Line)",
            name = "SC CP Breakline Layer (Line)",
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
            pier_point_layer = params[0].valueAsText
            strip_map_layer = params[1].valueAsText
            cpbreak_layer = params[2].valueAsText
            
            arcpy.env.overwriteOutput = True
            #arcpy.env.addOutputsToMap = True
            workability_field_stripmap = 'Workability'

            #--- Empty all rows in 'Workability' field in strip map layer
            with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                for row in cursor:
                    if row[0] in ('Workable', 'Non-Workable', 'Completed'):
                        row[0] = None
                    cursor.updateRow(row)

            #--- Update 'Workability' field ---#
            strip_map_where_clause = {
                0: "Workability is null",
                1: None,
                2: "Workability is null"
            }

            workability_staus = {
                0: "Workable",
                1: "Non-Workable",
                2: "Completed"
            }

            for i in (1, 2, 0):
                where_clause = f"AllWorkable = {i}"
                where_clause_stripmap = strip_map_where_clause[i]

                if i == 1:
                    arcpy.management.SelectLayerByAttribute(pier_point_layer, 'NEW_SELECTION', where_clause)
                    arcpy.management.SelectLayerByLocation(strip_map_layer, 'CONTAINS', pier_point_layer, where_clause_stripmap)
                    with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                        for row in cursor:
                            row[0] = workability_staus[i]
                            cursor.updateRow(row)
                else:
                    arcpy.management.SelectLayerByAttribute(pier_point_layer, 'NEW_SELECTION', where_clause)
                    arcpy.management.SelectLayerByAttribute(strip_map_layer, 'NEW_SELECTION', where_clause_stripmap)
                    arcpy.management.SelectLayerByLocation(strip_map_layer, 'CONTAINS', pier_point_layer)

                    with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                        for row in cursor:
                            if row[0] == None:
                                row[0] = workability_staus[i]
                            cursor.updateRow(row)

            ### Add second 'CP' for strip polygons overlapping with two CPs.
            #### Used to accommodate two different CPs when selected in the smart map
            cp_field = 'CP_End'
            cp2_field = 'GroupId'
            where_clause = f"{cp_field} <> 'S-06'"

            # First enter null 'GroupId' field
            with arcpy.da.UpdateCursor(strip_map_layer, [cp2_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[0] = None
                    cursor.updateRow(row)
                    
            # Select rows

            arcpy.management.SelectLayerByAttribute(cpbreak_layer, 'NEW_SELECTION', where_clause)
            arcpy.management.SelectLayerByLocation(strip_map_layer, 'INTERSECT', cpbreak_layer)

            # Enter the second CP to 'GroupId' field
            ## The second CP is always +1 from the previous
            with arcpy.da.UpdateCursor(strip_map_layer, ['CP',cp2_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        if row[0] == 'S-01':
                            row[1] = 'S-02'
                        if row[0] == 'S-02':
                            row[1] = 'S-03a'
                        elif row[0] == 'S-03a':
                            row[1] = 'S-03b'
                        elif row[0] == 'S-03b':
                            row[1] = 'S-03c'
                        elif row[0] == 'S-03c':
                            row[1] = 'S-04'
                        elif row[0] == 'S-04':
                            row[1] = 'S-05'
                        elif row[0] == 'S-05':
                            row[1] = 'S-06'
                    cursor.updateRow(row)

        Strip_Map_Layer_Update()

class ReSortGISTable(object):
    def __init__(self):
        self.label = "(Optional) Re-Sort GIS Attribute Table (SC Viaduct)"
        self.description = "(Optional) Re-Sort GIS Attribute Table (SC Viaduct)"

    def getParameterInfo(self):
        gis_layer = arcpy.Parameter(
            displayName = "SC Viaduct Layer (File Geodatabase)",
            name = "SC Viaduct Layer (File Geodatabase)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        excel_export_dir = arcpy.Parameter(
            displayName = "New MasterList Export Directory",
            name = "New MasterList Export Directory",
            datatype = "DEWorkspace",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [gis_layer, excel_export_dir]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        layer = params[0].valueAsText
        excel_export_dir = params[1].valueAsText

        # Define fields
        cp_field = 'CP'
        pier_number_field = 'PierNumber'
        new_field = 'temp_pier'
        uniqueID_field = 'uniqueID'
        type_field = 'Type'

        # 0.5. If 'CP' and 'Type' fields contain empty rows, exit and stop process
        cp_list = [row[0] for row in arcpy.da.SearchCursor(layer, ["CP"])]
        type_list = [row[0] for row in arcpy.da.SearchCursor(layer, ["Type"])]
        unique_value_list = list(cp_list+type_list)
        unique_final = set(unique_value_list)
        arcpy.AddMessage(unique_final)
        # final_list = pd.Series(unique_final)
        empty_list = [i for i, val in enumerate(unique_final) if val is None]

        if len(empty_list) == 0:
            # 1. Add temporary field for sorting
            fields = [e.name for e in arcpy.ListFields(layer)]
            temp_field = [f for f in fields if f == new_field]
            if not temp_field:
                arcpy.management.AddField(layer, new_field, "TEXT", field_alias=new_field, field_is_nullable="NULLABLE")
        
            # 2.
            try:
                with arcpy.da.UpdateCursor(layer, [pier_number_field, new_field]) as cursor:
                    for row in cursor:
                        if row[0]:
                            pier_n = re.sub("\D+","",row[0])
                            try:
                                pier_s = re.search(r"^BUE-P.*[SN]?$|^SCT.*[SN]?$|^PR.*[SN]?$|^P.*[SN]?$|^MT.*[SN]?$|^STR.*[SN]?$|^DAT.*[SN]?$|^DEP.*[SN]?$",str(row[0])).group()
                            except AttributeError:
                                pier_s = re.search(r"^BUE-P.*[SN]?$|^SCT.*[SN]?$|^PR.*[SN]?$|^P.*[SN]?$P|^MT.*[SN]?$|^STR.*[SN]?$|^DAT.*[SN]?$|^DEP.*[SN]?$",str(row[0]))
                            
                            # when PierNumber has N or S suffix, we need to account for this.
                            digit = re.sub('\D+','',pier_s)
                            
                            if int(pier_n) > 0 and int(pier_n) < 10: # 0 - 9
                                if not digit:
                                    row[1] = pier_s + "00" + pier_n
                                else:
                                    # 'P1S' -> 'P001S'
                                    str_digit = str(digit)
                                    row[1] = re.sub(str_digit, "00"+str_digit, pier_s)
                                    
                            elif int(pier_n) >= 10 and int(pier_n) < 100:
                                if not digit:
                                    row[1] = pier_s + "0" + pier_n
                                else:
                                    # 'P99S' -> 'P099S'
                                    str_digit = str(digit)
                                    row[1] = re.sub(str_digit, "0"+str_digit, pier_s)
                            else:
                                if not digit:
                                    row[1] = pier_s + pier_n
                                else:
                                    # 'P100N' -. 'P100N'
                                    row[1] = pier_s
                            cursor.updateRow(row)
                        else:
                            row[0] = None

                # 3. Sort
                ## Sort by CP, temp, and type
                layer_sorted = "SC_viaduct_sorted"
                sort_fields = [[cp_field,"ASCENDING"],[new_field,"ASCENDING"],[type_field,"ASCENDING"]]
                arcpy.Sort_management(layer, layer_sorted, sort_fields)

                # 4. Re-enter 'uniqueID'
                with arcpy.da.UpdateCursor(layer_sorted, [uniqueID_field]) as cursor:
                    rec = 0
                    for row in cursor:
                        rec = rec + 1
                        row[0] = rec
                        cursor.updateRow(row)

                # 5. Delete temporary field
                arcpy.management.DeleteField(layer_sorted, [new_field], "DELETE_FIELDS")

                # 6. Truncate and append the original GIS attribute table
                arcpy.TruncateTable_management(layer)
                arcpy.management.Append(layer_sorted, layer, schema_type = 'NO_TEST')

                # 7. Export to excel as a new master-list
                to_excel_file = os.path.join(excel_export_dir, "SC_Viaduct_ML_new.xlsx")
                arcpy.conversion.TableToExcel(layer_sorted, to_excel_file)

                # 8. Delete sorted layer
                arcpy.management.Delete(layer_sorted)
            
            except Exception:
                arcpy.AddMessage('This failed. Please check your code')
                arcpy.AddError('This failed. Please check your code')
        else:
            arcpy.AddMessage('This failed. Please check your code')
            arcpy.AddError('This failed. Please check your code')

class JustMessage3(object):
    def __init__(self):
        self.label = "(Optional) ----- Optional Tools  -----"
        self.description = "Optional Tools"

class GenerateStatisticsBetweenTwoTables(object):
    def __init__(self):
        self.label = "(Optional) Comparing Statistics between Two Tables"
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

class ViaductBIMUpdateMessage(object):
    def __init__(self):
        self.label = "A-0.----- Update Viaduct using BIM models -----"
        self.description = "Update Viaduct using BIM models"

class CreateBIMtoGeodatabase(object):
    def __init__(self):
        self.label = "A-1. Create BIM To Geodatabase using revit files"
        self.description = "Create BIM To Geodatabase using revit files"

    def getParameterInfo(self):
        fgdb_dir = arcpy.Parameter(
            displayName = "File Geodatabase",
            name = "File Geodatabase",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        input_revit = arcpy.Parameter(
            displayName = "Input BIM Workspace (revit files)",
            name = "Input BIM Workspace (revit files)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        export_name = arcpy.Parameter(
            displayName = "Display Name of Feature Dataset",
            name = "Display Name of Feature Dataset",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [fgdb_dir, input_revit, export_name]
        return params

    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        fgdb_dir = params[0].valueAsText
        input_revit = params[1].valueAsText
        export_name = params[2].valueAsText

        arcpy.env.gpuId = None 
        arcpy.env.overwriteOutput = True

        revit_tables = list(input_revit.split(';'))
        
        revit_files = [os.path.basename(e) for e in revit_tables]
        arcpy.AddMessage(revit_files)

        # 1. BIM to Geodatabase
        spatial_reference = "PRS_1992_Philippines_Zone_III"
        arcpy.conversion.BIMFileToGeodatabase(revit_tables, fgdb_dir, export_name, spatial_reference, "", False)
        
        arcpy.AddMessage("BIM To Geodatabase was successful.")


        #----------------------------------------------------------------------------------#
        # spatial_reference = "PRS_1992_Philippines_Zone_III"
        # revit_files = list(input_revit.split(';'))

        # for i, revit_file in enumerate(revit_files):
        #     arcpy.AddMessage(f"Process {revit_file}")
        #     start_time = time.time()
        #     try:                
        #         # Run the BIM File To Geodatabase tool
        #         arcpy.conversion.BIMFileToGeodatabase(revit_file, fgdb_dir, export_name, spatial_reference)
        #         arcpy.AddMessage(f"Successfully processed {os.path.basename(revit_file)}")

        #         if i == 0:
        #             target_feature_classes = arcpy.ListFeatureClasses(feature_dataset=export_name)
        #         else:
        #             # Append each feature class1,2... to the first feature class0
        #             input_feature_classes = arcpy.ListFeatureClasses(feature_dataset=export_name)
        #             input_feature_classes_filtered = [e for e in input_feature_classes if e.endswith(('_1','_2','_3','_4','_5'))]
        #             # arcpy.AddMessage(f"All the appending layers: {input_feature_classes_filtered}")

        #             for target_feature_class in target_feature_classes:
        #                 arcpy.AddMessage(f"Target_Feature_Class: {target_feature_class}")

        #                 input_feature_class_append = [e for e in input_feature_classes_filtered if target_feature_class in e]
        #                 arcpy.AddMessage(f"Appending layer: {input_feature_class_append}")

        #                 schemaType = "NO_TEST"
        #                 fieldMappings = ""
        #                 subtype = ""
        #                 arcpy.management.Append(input_feature_class_append, target_feature_class, schemaType, fieldMappings, subtype)
        #                 arcpy.management.Delete(input_feature_class_append)
                    
        #                 arcpy.AddMessage(f"Successfully appended {os.path.basename(revit_file)}")
                    
                
        #         end_time = time.time()
        #         arcpy.AddMessage(f"Processing time: {((end_time - start_time)/60)} minutes.(start time: {start_time})")
            
        #     except:
        #         arcpy.AddError(f"Error processing {os.path.basename(revit_file)}")
        #         pass

class AppendBatchesBIM(object):
    def __init__(self):
        self.label = "A-2. (Optional) Append Input Geodatabases to Target Geodatabase"
        self.description = "(Optional) Append Input Geodatabases to Target Geodatabase"

    def getParameterInfo(self):
        fgdb_dir = arcpy.Parameter(
            displayName = "File Geodatabase",
            name = "File Geodatabase",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        target_feature_dataset = arcpy.Parameter(
            displayName = "Feature Dataset (Target)",
            name = "Feature Dataset (Target)",
            datatype = "DEFeatureDataset",
            parameterType = "Required",
            direction = "Input"
        )

        input_fd = arcpy.Parameter(
            displayName = "Feature Dataset (Input)",
            name = "Feature Dataset (Input)",
            datatype = "DEFeatureDataset",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )


        params = [fgdb_dir, target_feature_dataset, input_fd]
        return params

    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        fgdb_dir = params[0].valueAsText
        target_feature_dataset = params[1].valueAsText
        input_fd = params[2].valueAsText

        arcpy.env.gpuId = None 
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = fgdb_dir

        # Get target layers in target FD
        target_feature_dataset_name = os.path.basename(target_feature_dataset)
        target_feature_classes = arcpy.ListFeatureClasses(feature_dataset=target_feature_dataset_name)
        input_feature_datasets = list(input_fd.split(';'))

        try:
            for feature_dataset in input_feature_datasets:
                input_feature_dataset_name = Path(feature_dataset).name.replace("'","")
                arcpy.AddMessage(f"--------- Input Feature Dataset: {input_feature_dataset_name} -----------")
                arcpy.AddMessage("\n")

                input_feature_classes = arcpy.ListFeatureClasses(feature_dataset=input_feature_dataset_name)
                input_features = [re.sub(f"_{input_feature_dataset_name}", "", e) for e in input_feature_classes]    

                for target_feature_class in target_feature_classes:
                    ## Remove feature datase name from the target feaure class
                    target_feature = re.sub(f"_{target_feature_dataset_name}", "", target_feature_class)
                    # arcpy.AddMessage(f"Target_Feature_Class: {target_feature}")

                    # input_feature_class_append = [e for e in input_features if e.startswith(target_feature)]
                    input_feature_class_match= [e for e in input_features if re.fullmatch(target_feature, e)]
                    input_feature_class_append = [f"{e}_{input_feature_dataset_name}" for e in input_feature_class_match] # Back to the original name
                    
                    if len(input_feature_class_match) > 1:
                        arcpy.AddMessage(f"!!! {target_feature} was not appended because there are more than one appending layers: {input_feature_class_append}.")
                    elif len(input_feature_class_match) == 0:
                        arcpy.AddMessage(f"{target_feature} does not have any corresponding input layers..")
                        # arcpy.AddMessage(f"Appending layer: {input_feature_class_append}")
                    else:
                        schemaType = "NO_TEST"
                        fieldMappings = ""
                        subtype = ""
                        arcpy.management.Append(input_feature_class_append, target_feature_class, schemaType, fieldMappings, subtype)
                        arcpy.AddMessage(f"Successfully appended {input_feature_class_append}")
                        
                        # Delete input feature dataset, only when append is successful.
                        # arcpy.management.Delete(feature_dataset)

        except:
            # arcpy.AddError(f"Error processing {feature_dataset}")
            arcpy.AddError(f"Error processing {feature_dataset}")
            pass

class CreateBuildingLayers(object):
    def __init__(self):
        self.label = "A-3. (Message ONLY) Make Building Layers using Feature Dataset"
        self.description = "Make Building Layers using Feature Dataset"

class AddFieldsToBuildingLayerStation(object):          
    def __init__(self):
        self.label = "A-4. Add Fields to New Viaduct Layers"
        self.description = "Add Fields to New Viaduct Layers"

    def getParameterInfo(self):
        cp_update = arcpy.Parameter(
            displayName = "Target Contract Package",
            name = "Target Contract Package",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            # multiValue = True
        )
        cp_update.filter.type = "ValueList"
        cp_update.filter.list = [
            "S-01",
            "S-02",
            "S-03a",
            "S-03b",
            "S-03c",
            "S-04",
            "S-05",
            "S-06"
        ]
    
        input_layers = arcpy.Parameter(
            displayName = "Select Sublayers Layers (e.g., StructuralColumns)",
            name = "Select Sublayers", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [cp_update, input_layers]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        cp_update = params[0].valueAsText
        input_layers = params[1].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(input_layers.split(";"))

        # 1. Add fields
        add_fields = ['Types', 'CP', 'Status', 'PierNumber', 'nPierNumber']

        arcpy.AddMessage("Add Fields start...")
        for layer in layers:
            for field in add_fields:
                if field in ('CP', 'PierNumber', 'nPierNumber'):
                    arcpy.management.AddField(layer, field, "TEXT", "", "", "", field, "NULLABLE", "")
                else:
                    arcpy.management.AddField(layer, field, "SHORT", "", "", "", field, "NULLABLE", "")

        # 2. Initial set for Status
        arcpy.AddMessage("Convert 'Status' = 1.")
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['Status']) as cursor:
                for row in cursor:
                    row[0] = 1
                    cursor.updateRow(row)

        # 3. Types of categories
        if cp_update == 'S-01':
            for layer in layers:
                if os.path.basename(layer) == 'Decks':
                    with arcpy.da.UpdateCursor(layer, ['t00__Description', 'Types']) as cursor:
                        for row in cursor:
                            if row[0] is not None:
                                row[1] = 5
                            else:
                                row[1] = 0
                            cursor.updateRow(row)

                elif os.path.basename(layer) == 'StructuralFoundation':
                    with arcpy.da.UpdateCursor(layer, ['t00__Description', 'Types', 'Category']) as cursor:
                        for row in cursor:
                            if row[0] is not None:
                                if ('Bored Pile' in row[0]) or ('Bore Pile' in row[0]):
                                    row[1] = 1
                                elif 'Pilecap' in row[0]:
                                    row[1] = 2
                                else:
                                    row[1] = 0
                            else:
                                row[1] = 0
                            cursor.updateRow(row)

                elif os.path.basename(layer) == 'Piers':
                    with arcpy.da.UpdateCursor(layer, ['Types', 'Family', 'Category', 'FamilyType']) as cursor:
                        for row in cursor:
                            if (row[1] is not None) or (row[2] is not None):
                                if 'Pier Head' in row[1]:
                                    row[0] = 4
                                elif 'Pier' in row[1]:
                                    row[0] = 3
                                elif ('Pier Walls' in row[2]) and ('Noise Barrier' in row[3]):
                                    row[0] = 8
                                else:
                                    row[0] = 0
                            else:
                                row[0] = 0
                            cursor.updateRow(row)
                else:
                    with arcpy.da.UpdateCursor(layer, ['Types']) as cursor:
                        for row in cursor:
                            row[0] = 0
                            cursor.updateRow(row)

        elif cp_update == 'S-06':
            for layer in layers:
                arcpy.AddMessage(layer)
                if os.path.basename(layer) == 'Bearings':
                    with arcpy.da.UpdateCursor(layer, ['Types']) as cursor:
                        for row in cursor:
                            row[0] = 0
                            cursor.updateRow(row)
                else:
                    with arcpy.da.UpdateCursor(layer, ['t00__Description', 'Category', 'Types']) as cursor:
                        for row in cursor:
                            if row[0] is not None:
                                if 'Bored Pile' in row[0]:
                                    row[2] = 1
                                elif 'Pile Cap' in row[0]:
                                    row[2] = 2
                                elif ('Pier Column' in row[0]) or ('Pier Colum' in row[0]):
                                    row[2] = 3
                                elif 'Pier Head' in row[0]:
                                    row[2] = 4
                                elif ('Viaduct' in row[0]) or ('BR' in row[0]):
                                    row[2] = 5
                                elif ('At Grade' in row[0]) or ('Abutment' in row[0]):
                                    row[2] = 7
                                else:
                                    row[2] = 0
                            elif row[1] is not None:
                                if 'Pier Wall' in row[1]:
                                    row[2] = 8
                                else:
                                    row[2] = 0
                            else:
                                row[2] = 0
                            cursor.updateRow(row)

        # 4. CP
        for layer in layers:
            with arcpy.da.UpdateCursor(layer, ['DocName', 'CP']) as cursor:
                for row in cursor:

                    try:
                        cp_all = re.search(r'[S]0\d+?[abcABC]|[S]0\d+',row[0]).group()
                    except AttributeError:
                        cp_all = re.search(r'[S]0\d+?[abcABC]|[S]0\d+',row[0])
                    cp_name = re.sub(r'0','-0',str(cp_all))

                    cp_name = re.sub('A','a',cp_name)
                    cp_name = re.sub('B','b',cp_name)
                    cp_name = re.sub('C','c',cp_name)

                    row[1] = cp_name
                    cursor.updateRow(row)

class EditBuildingLayerStation(object):
    def __init__(self):
        self.label = "A-5 Update Viaduct Layers"
        self.description = "Update Viaduct Layers"

    def getParameterInfo(self):
        cp_update = arcpy.Parameter(
            displayName = "Target Contract Package",
            name = "Target Contract Package",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input",
            # multiValue = True
        )
        cp_update.filter.type = "ValueList"
        cp_update.filter.list = [
            "S-01",
            "S-02",
            "S-03a",
            "S-03b",
            "S-03c",
            "S-04",
            "S-05",
            "S-06"
        ]

        delete_fc = arcpy.Parameter(
            displayName = "Target Building Sublayers (To Be Updated)",
            name = "Target Building Sublayers (To Be Updated)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        new_fc = arcpy.Parameter(
            displayName = "Input Building Sublayers (New)",
            name = "Input Building Sublayers (New)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        params = [cp_update, delete_fc, new_fc]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        cp_update = params[0].valueAsText
        delete_bim = params[1].valueAsText
        new_bim = params[2].valueAsText

        arcpy.env.gpuId = None 
        arcpy.env.overwriteOutput = True

        def unique(lists):
            collect = []
            unique_list = pd.Series(lists).drop_duplicates().tolist()
            for x in unique_list:
                collect.append(x)
            return(collect)
        
        def are_all_items_included(sublist, mainlist):
            """
            Checks if all items in 'sublist' are present in 'mainlist'.

            Args:
                sublist: The list of items to check for inclusion.
                mainlist: The list to check against.

            Returns:
                True if all items in sublist are in mainlist, False otherwise.
            """
            return set(sublist).issubset(set(mainlist))

        # define fields
        status_field = 'Status'

        del_layers = list(delete_bim.split(";"))
        new_layers = list(new_bim.split(";"))
        # new_cps = list(cp_update.split(";"))

        arcpy.AddMessage(F"cps: {cp_update}")

        # Convert station names to station domain numbers
        # cp_selected = tuple([cp for cp in new_cps])

        # 1. Check names are matched between deleted layers and new layers
        del_basenames = []
        new_basenames = []

        for layer in del_layers:
            del_basenames.append(os.path.basename(layer))

        for layer in new_layers:
            new_basenames.append(os.path.basename(layer))

        arcpy.AddMessage(f"deleted layer names: {sorted(del_basenames)}")
        arcpy.AddMessage(f"new layer names: {sorted(new_basenames)}")

        # 2. Add and Delete
        if sorted(del_basenames) == sorted(new_basenames):
            arcpy.AddMessage('Sublayer names are all matched.')
    
            for target_layer in del_layers:
                del_basename = os.path.basename(target_layer)

                # 1. Add new layer
                new_layers_series = pd.Series(new_layers)
                id = new_layers_series.index[new_layers_series.str.contains(del_basename,regex=True)][0]
                new_layer = new_layers[id]
                arcpy.AddMessage(del_basename + "; " + new_layer)

                # Check if the same contract package is shared between target layer and new layer
                target_cp_list = unique([e[0] for e in [cp for cp in  arcpy.da.SearchCursor(target_layer, ["CP"])]])
                new_cp_list = unique([e[0] for e in [cp for cp in  arcpy.da.SearchCursor(new_layer, ["CP"])]])

                arcpy.AddMessage(f"Target layer CPs: {target_cp_list}")
                arcpy.AddMessage(f"New layer CPs: {new_cp_list}")

                # Check if all selected CPs are included in both target layer and new layer
                if are_all_items_included([cp_update], target_cp_list) and are_all_items_included([cp_update], new_cp_list):
                    arcpy.AddMessage("Both target layer and new layer have the selected CP(s), so proceed.")

                    # 2. Update 'Status' field in new_layer using 'xx_Status or xx_status' field from Revit
                    # empty cell (null): 1. To be Constructed, 
                    # 'Ongoing': 2. Ongoing
                    # 'Completed': 4. Completed
                    # 2. Extract fields
                    bim_fields = [e.name for e in arcpy.ListFields(new_layer)]

                    ## 3. Search field name excluding 'Project_'
                    try:
                        bim_status_field = [re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e).group() for e in bim_fields if re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e) is not None]
                    except AttributeError:
                        bim_status_field = [re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e) for e in bim_fields if re.search(r'^(?!.*Project)(.*?)_Status$|(?!.*Project)(.*?)_status$', e) is not None]

                    arcpy.AddMessage(f"The name of status field in BIM models: {bim_status_field}")

                    # 4. Update 'Status' field in new_layer
                    if len(bim_status_field) == 1: # Update only When status field exists in the BIM model (input)
                        if cp_update == 'S-01':
                            with arcpy.da.UpdateCursor(new_layer, [bim_status_field, status_field]) as cursor:
                                for row in cursor:
                                    if row[0] == 'Ongoing':
                                        row[1] = 2
                                    elif row[0] == 'Completed':
                                        row[1] = 4
                                    elif row[0] is None:
                                        row[1] = 1
                                    cursor.updateRow(row)
                        
                        elif cp_update == 'S-06':
                            with arcpy.da.UpdateCursor(new_layer, [bim_status_field, status_field]) as cursor:
                                for row in cursor:
                                    if row[0] == 'In-Progress':
                                        row[1] = 1
                                    elif row[0] == 'Complete':
                                        row[1] = 4
                                    elif row[0] is None:
                                        row[1] = 1
                                    cursor.updateRow(row)

                    # 5. Replace target layer with new observations
                    # Select layer by attribute
                    # if len(cp_selected) == 1:
                    #     where_clause = "CP = '{}'".format(cp_selected[0])
                    # else:
                    #     where_clause = "CP IN {}".format(cp_selected)

                    # arcpy.AddMessage(where_clause)

                    # 5. Replace target layer with new observations
                    ### Note if multiple revit models exist, We cannot just replace
                    ### all the rows in the target layer with inputs. 
                    ### We need to identify rows to be updated using DocName in the input (new) layer.
                    docNumbers = []
                    with arcpy.da.SearchCursor(new_layer, ["DocName"]) as cursor:
                        for row in cursor:
                            if row[0]:
                                docNumbers.append(row[0])

                    ## Get a unique list of docnames
                    docNumberUnique = unique(docNumbers)

                    numbers = tuple([e for e in docNumberUnique])
                    docName_field = 'DocName'

                    if (len(docNumberUnique) == 1):
                        where_clause = f"{docName_field} = '{numbers[0]}'"
                    else:
                        where_clause = f"{docName_field} IN {numbers}"

                    arcpy.management.SelectLayerByAttribute(target_layer, 'SUBSET_SELECTION',where_clause)

                    # Truncate
                    arcpy.management.DeleteRows(target_layer)

                    # Append
                    arcpy.management.Append(new_layer, target_layer, schema_type = 'NO_TEST', expression = where_clause)

                else:
                    arcpy.AddError("Either the target layer or input layer does not have the selected CP(s)Please check layers.")
                    pass

        else:
            arcpy.AddError("Matching Errors.. Select corresponding building sublayers for input and target.")
            pass

class DomainSettingStationStructure(object):
    def __init__(self):
        self.label = "A-6. Apply Domain to Fields (applicable only for enterprise geodatabase)"
        self.description = "Apply Domain to Fields"

    def getParameterInfo(self):
        gis_layers = arcpy.Parameter(
            displayName = "Building Layers (e.g., StructuralColumns)",
            name = "Building Layers (e.g., StructuralColumns)", 
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        domain_field = arcpy.Parameter(
            displayName = "Domain Field Name",
            name = "Domain Field Name", 
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        domain_field.filter.type = "ValueList"
        domain_field.filter.list = ['Types','Status']

        params = [gis_layers, domain_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        gis_layers = params[0].valueAsText
        domain_field = params[1].valueAsText
        arcpy.env.overwriteOutput = True

        layers = list(gis_layers.split(";"))

        # Domain settings
        domainList = ['ViaductType', 'ViaductStatus']

        for layer in layers:
            if domain_field == 'Status':
                arcpy.AssignDomainToField_management(layer, "Status", domainList[1])
            elif domain_field == 'Types':
                arcpy.AssignDomainToField_management(layer, "Types", domainList[0])