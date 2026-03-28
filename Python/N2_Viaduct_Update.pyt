import arcpy
import pandas as pd
import os
from pathlib import Path
from datetime import date, datetime
import re
import string
import numpy as np

#----------------------------------------------#
def unique(lists):
    collect = []
    unique_list = pd.Series(lists).drop_duplicates().tolist()
    for x in unique_list:
        collect.append(x)
    return(collect)

def unique_values(table, field):  ##uses list comprehension
    with arcpy.da.SearchCursor(table, [field]) as cursor:
        return sorted({row[0] for row in cursor if row[0] is not None})

def non_match_elements(list_a, list_b):
    non_match = []
    for i in list_a:
        if i not in list_b:
            non_match.append(i)
    return non_match

def to_Date_no_hms(table, field):
    table[field] = pd.to_datetime(table[field],errors='coerce').dt.date
    return table
    #table[field] = table[field].astype('datetime64[ns]')

def rename_columns_title(table, search_names, renamed_word): # one by one
    colname_change = table.columns[table.columns.str.contains(search_names,regex=True)]
    try:
        table = table.rename(columns={str(colname_change[0]): renamed_word})
    except:
        pass
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

def add_status(table, start_field, finish_field, status_field):
    table[status_field] = 1

    ## if finishdate, completed (Status = 4)
    idx = table.query(f"{finish_field}.notna()").index
    table.loc[idx, status_field] = 4

    ## if startdate & !finishdate, ongoing (Status = 2)
    idx = table.query(f"{start_field}.notna() and {finish_field}.isna()").index
    table.loc[idx, status_field] = 2
    return table

# Check missing field between tables
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

def update_N2_CP_notation(table, field):
    table[field] = table[field].str.replace(r'\s+','',regex=True)
    table[field] = table[field].replace(r'CPN','N-',regex=True)
    #--- Fix N-01/N-02 => N-01, N-02/N-03 => N-02
    table[field] = table[field].apply(lambda x: re.sub(r'[,/].*','',x))
    return table

#--- Update pier numbers
def update_monopile_pier_numbers_civilML(table, field):
    """
    Renaming pier numbers: 'P-159' and 'P-160'
    New pier numbers: 'P-159C' and 'P-160C'

    """
    for pier in ['P-159', 'P-160']:
        idx = table.query(f"{field} == '{pier}'").index
        table.loc[idx, field] = f"{pier}C"
    return table

def extract_pier_numbers(cp, cp_field, pier_num_field, type_field=None, viat=None, civilt=None, piertrackt=None):
    if viat:
        x = pd.read_excel(viat)
        ids = x.query(f"{cp_field} == '{cp}' and {type_field} == 2").index
        piers = x.loc[ids, pier_num_field].values

    elif civilt:
        new_cols = ['PierNumber', 'CP', 'util1', 'util2', 'Others', 'Workability']
        x = pd.read_excel(civilt, skiprows=2)
        ids = x.columns[x.columns.str.contains(r'^Pier No.*|Contract P.*|^Name of Utilities|^Others|^Pile Cap Workable.*',regex=True,na=False)]
        x = x.loc[:, ids]
        for i, col in enumerate(ids):
            x = x.rename(columns={col: new_cols[i]})

        #--- Update pier number for monopiles
        x = update_monopile_pier_numbers_civilML(x, pier_num_field)

        ids = x.query(f"{cp_field} == '{cp}'").index
        piers = x.loc[ids, pier_num_field].values

    elif piertrackt:
        x = pd.read_excel(piertrackt, sheet_name=cp, skiprows=1)
        # Find nth row wheren field name 'PierNumber' begins and drop emty row.
        ids = x.iloc[:, 0].index[x.iloc[:, 0].str.contains(r'PierNumber', regex=True, na=False)]
        x = x.drop(ids).reset_index(drop=True)
        x = x.rename(columns={x.columns[0]: pier_num_field}) 
        piers = x[pier_num_field].values
    return piers

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

def reformat_obstructon_fields(table, field):
    table[field] = table[field].astype(str)
    table[field] = table[field].str.replace(r'\n',',',regex=True)
    table[field] = table[field].str.replace(r';',',',regex=True)
    table[field] = table[field].str.replace(r';;',',',regex=True)
    table[field] = table[field].str.replace(r',,',',',regex=True)
    table[field] = table[field].str.replace(r',,,',',',regex=True)
    table[field] = table[field].str.replace(r',$','',regex=True)
    table[field] = table[field].str.replace(r'nan','',regex=True)
    table[field] = table[field].str.replace(r'\s+','',regex=True)
    table[field] = table[field].str.lstrip(',') # remove leading comma
    table[field] = table[field].str.rstrip(',') # remove leading comma
    return table

def convert_to_nan(table, ids, fields):
    for field in fields:
        table.loc[ids, field] = np.nan
    return table

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
        self.label = "UpdateN2Viaduct"
        self.alias = "UpdateN2Viaduct"
        self.tools = [JustMessage2,
                      CompileViaductMasterList,
                      UpdateGISExcelML,
                      UpdateGISTable,
                      JustMessage3,
                      CreateWorkablePierLayer,
                      CheckPierNumbers,
                      UpdatePierWorkableTrackerML,
                      UpdatePierWorkablePolygonLayer,
                      UpdatePierPointLayer,
                      UpdateStripMapLayer,
                      JustMessage4,
                      CompareStringFieldExcelTables,
                      CompareStringFieldFeatureClasses,
                      JustMessage5,
                      GenerateStatisticsBetweenTwoTables,
                      ReSortGISTable]

class JustMessage2(object):
    def __init__(self):
        self.label = "2.0. ----- Update N2 Viaduct -----"
        self.description = "Update N2 Viaduct (Just message)"

class CompileViaductMasterList(object):
    def __init__(self):
        self.label = "2.1. Compile Civil ML Tables (N2 Viaduct)"
        self.description = "Compile Civil ML Tables (N2 Viaduct)"

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
            displayName = "N2 Viaduct Directory",
            name = "Output Directory for N2 Viaduct",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "Civil Master List Table (Excel)",
            name = "Civil Master List Table",
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
            cp_field = "CP"
            pierno_id = 'PierId'
            pierno_field = 'PierNo'
            pileno_field = 'PileNo'
            status_field = 'Status'
            type_field = 'Type'
            startdate_field = 'Start'
            finishdate_field = 'Finish'
            viaduct_types = ['BoredPile', 'PileCap', 'PierColumn', 'PierHead', 'Precast']

            compile_table = pd.DataFrame(columns=[cp_field, type_field, pierno_field, pileno_field, status_field, startdate_field, finishdate_field])
            
            for i, type in enumerate(viaduct_types):
                x = pd.read_excel(civil_ml, sheet_name = type)

                #--- Bored Pile ---#
                if i == 0:
                    x[type_field] = str(i + 1)

                    # Multiple piles
                    ids = x.query(f"{pileno_field}.notna()").index
                    x.loc[ids, pierno_id] = x.loc[ids, pierno_field] + "-" + x.loc[ids, pileno_field] + "-" + x.loc[ids, type_field]

                    # Mono Pile (P-159, P-160)
                    ids = x.query(f"{pileno_field}.isna()").index 
                    x.loc[ids, pierno_id] = x.loc[ids, pierno_field] + "-" + x.loc[ids, type_field]

                    # Add 'Status'
                    x = add_status(x, startdate_field, finishdate_field, status_field)
                    compile_table = pd.concat([compile_table, x])

                else:
                    x[type_field] = str(i + 1)
                    x[pierno_id] = x[pierno_field] + "-" + x[type_field]
                    x = add_status(x, startdate_field, finishdate_field, status_field)
                    compile_table = pd.concat([compile_table, x])

            #--- Conver type_field to integer ---#
            compile_table[type_field] = compile_table[type_field].astype('int64')

            #--- Check duplication
            duplicated_ids = find_duplicates_ordered(compile_table[pierno_id].values)

            if len(duplicated_ids) > 0:
                arcpy.AddMessage(f"Duplicated Pier IDs: {duplicated_ids}")
                arcpy.AddError("There are duplicated IDs. Please check.")
            else:
                # Export to excel
                excel_file = proj + "_Viaduct_ML_Civil_compiled.xlsx"
                compile_table.to_excel(os.path.join(via_dir, excel_file), index=False)

        N2_Compile_viaduct_tables()

class UpdateGISExcelML(object):
    def __init__(self):
        self.label = "2.2. Update GIS Excel ML (N2 Viaduct)"
        self.description = "1. Update GIS Excel ML (N2 Viaduct)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "N2 Viaduct Directory",
            name = "N2 Viaduct Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "N2 Viaducut GIS ML (Excel)",
            name = "N2 Viaducut GIS ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "N2 Viaduct Civil ML (Excel)",
            name = "N2 Viaduct Civil ML (Excel)",
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

        def N2_Viaduct_Update():
            pierno_id = 'PierId'
            pierno_field = 'PierNumber'
            pileno_field = 'PileNo'
            status_field = 'Status'
            type_field = 'Type'
            startdate_field = 'Start'
            finishdate_field = 'Finish'
            update_fields = [status_field, startdate_field, finishdate_field]
            dummy_date = '1990-01-01'

            x = pd.read_excel(gis_ml)
            y = pd.read_excel(civil_ml)

            x[type_field] = x[type_field].astype(int)
            x[type_field] = x[type_field].astype(str)
            x[pierno_id] = np.nan

            for i in range(0, 5):
                if i == 0:
                    # Multiple piles
                    idx = x.query(f"{type_field} == '{i+1}' and {pileno_field}.notna() ").index
                    x.loc[idx, pierno_id] = x.loc[idx, pierno_field] + "-" + x.loc[idx, pileno_field] + "-" + x.loc[idx, type_field]

                    # Mono pile
                    idx = x.query(f"{type_field} == '{i+1}' and {pileno_field}.isna()").index
                    x.loc[idx, pierno_id] = x.loc[idx, pierno_field] + "-" + x.loc[idx, type_field]

                else:
                    idx = x.query(f"{type_field} == '{i+1}'").index
                    x.loc[idx, pierno_id] = x.loc[idx, pierno_field] + "-" + x.loc[idx, type_field]

            # x.to_excel(os.path.join(gis_dir, "N2_Viaduct_MasterList_with_pierID.xlsx"), index=False)
           
            #--- Check duplicated pier ids
            idx = x.query(f"{pierno_id}.notna()").index
            gis_piers = x.loc[idx, pierno_id].values
            duplicated_ids = find_duplicates_ordered(x[pierno_id].values)

            if len(duplicated_ids) > 0:
                arcpy.AddMessage(f"Duplicated Pier IDs: {duplicated_ids}")
                arcpy.AddError("There are duplicated IDs. Please check.")
            else:
                #--- Check unmatched pier ids between gis and civil
                civil_piers = y[pierno_id].values
                no_gis_piers = [f for f in civil_piers if f not in gis_piers and f == f]
                no_civil_piers = [f for f in gis_piers if f not in civil_piers and f == f]
                if len(no_gis_piers) > 0 or len(no_civil_piers) > 0:
                    arcpy.AddMessage(f"There are unmatched Pier IDs: {no_gis_piers + no_civil_piers}")
                    arcpy.AddError(f"Please check..")

                else:
                    arcpy.AddMessage(no_civil_piers)
                    arcpy.AddMessage(no_gis_piers)

                    #--- Filter out: type = 0 or 6
                    x = x.query(f"{pierno_id}.notna()").reset_index(drop=True)
                    x[type_field] = x[type_field].astype(int)
                    x = x.drop(columns=update_fields)

                    #--- Keep update fields ---#
                    y = y[[pierno_id] + update_fields]

                    arcpy.AddMessage(f"total rows for x: {len(x)}")
                    arcpy.AddMessage(f"total rows for y: {len(y)}")
                     
                    #--- Join civil ML to GIS ML ---#
                    xy = pd.merge(left=x, right=y, how='left', left_on=pierno_id, right_on=pierno_id, validate="one_to_one")

                    #--- start and finish date ---#
                    xy = xy.reset_index(drop=True)
                    for field in [startdate_field, finishdate_field]:
                        date_item = xy[field].iloc[:1].item()
                        if date_item is None or pd.isnull(date_item):
                            xy.loc[0, field] = pd.to_datetime(dummy_date)
                        xy = to_Date_no_hms(xy, field)

                    #--- Export ---#
                    xy.to_excel(os.path.join(gis_dir, "N2_Viaduct_GIS_ML_new.xlsx"), index=False)
                               
        N2_Viaduct_Update()

class UpdateGISTable(object):
    def __init__(self):
        self.label = "2.3. Update GIS Attribute Table (N2 Viaduct)"
        self.description = "Update SC Viaduct multipatch layer (N2 Viaduct)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "N2 Viaduct Directory",
            name = "N2 Viaduct Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
        gis_layer = arcpy.Parameter(
            displayName = "N2 Viaduct Layer (Multipatch)",
            name = "N2 Viaduct Layer (Multipatch)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        excel_table = arcpy.Parameter(
            displayName = "N2 Viaduct ML (Feature Table)",
            name = "N2 Viaduct ML (Feature Table)",
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


        arcpy.AddMessage('Updating SC Viaduct layer has started..')

        # For Removing dummy dates if any specified in the first tool
        startdate_field = 'Start'
        finishdate_field = 'Finish'
        date_fields = [startdate_field, finishdate_field]

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
            arcpy.AddMessage('The following IDs do not match between ML and GIS.')
            arcpy.AddMessage('Missing uniqueID in GIS table: {}'.format(uniqueid_miss_gis))
            arcpy.AddMessage('Missing uniqueID in ML Excel table: {}'.format(uniqueid_miss_ml))
            
        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        viaduct_ml_fields = [f.name for f in arcpy.ListFields(viaduct_ml)]
        viaduct_ml_transfer_fields = [e for e in viaduct_ml_fields if e not in (uniqueID,'OBJECTID')]
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in ('uniqueId', uniqueID)]))                      
        viaduct_ml_join_field =' '.join(map(str, [f for f in viaduct_ml_fields if f in ('uniqueId', uniqueID)]))
            
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
        arcpy.conversion.TableToExcel(gis_layer, os.path.join(gis_dir, 'N2_Viaduct_GIS_Portal.xlsx'))
        
        # Delete the copied feature layer
        deleteTempLayers = [gis_copied, viaduct_ml]
        arcpy.Delete_management(deleteTempLayers)

class JustMessage3(object):
    def __init__(self):
        self.label = "3.0. ----- Update Pier Workability -----"
        self.description = "Update Pier Workability (Just message)"

class CreateWorkablePierLayer(object):
    def __init__(self):
        self.label = "3.1. Create Pier Workable Layer (Polygon)"
        self.description = "Create Pier Workable Layer"

    def getParameterInfo(self):
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

        params = [workable_pier_layer, via_layer]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workable_pier_layer = params[0].valueAsText
        via_layer = params[1].valueAsText

        arcpy.env.overwriteOutput = True
        
        # Define fields
        status_field = 'Status'
        cp_field = 'CP'
        pier_number_field = 'PierNumber'
        unique_id_field = 'uniqueID'
        type_field = 'Type'

        new_fields = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']

        #--- Keep Type = 2 and only 'CP', 'PierNumber', and 'uniqueID'
        pilecaps_layer = 'pilecaps_layer'
        arcpy.management.MakeFeatureLayer(via_layer, pilecaps_layer, '"Type" = 2')

        # Use pier head for monopiles: P-159C, P-159NB/SB, P-160C, P-160NB/SB        
        monopile_query = f"({pier_number_field} LIKE '%P-159%' OR {pier_number_field} LIKE '%P-160%') AND {type_field} = 4"
        monopile_layer = 'monopile_layer'
        arcpy.management.MakeFeatureLayer(via_layer, monopile_layer, monopile_query)

        #-- Add monopile pier head
        temp_layer = 'temp_layer'
        arcpy.management.Merge([pilecaps_layer, monopile_layer], temp_layer)

        #--- 'multipatch footprint'
        new_layer = 'N2_Pier_Workable'
        arcpy.ddd.MultiPatchFootprint(temp_layer, new_layer)

        #--- Keep fields
        arcpy.management.DeleteField(new_layer, [cp_field, pier_number_field, unique_id_field, status_field, type_field], "KEEP_FIELDS")

        # Add field
        for field in new_fields:
            arcpy.management.AddField(new_layer, field, "SHORT", field_alias=field, field_is_nullable="NULLABLE")

        # Status = 4 => 'Workable' = 2 (completed). 
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

        ## Delete field
        # arcpy.management.DeleteField(new_layer, ['CP','PierNumber','uniqueID','Status'], "KEEP_FIELDS")
        
        # delete
        deleteTempLayers = [new_layer, temp_layer]
        arcpy.Delete_management(deleteTempLayers)

class UpdatePierWorkableTrackerML(object):
    def __init__(self):
        self.label = "3.2. Update GIS Pier Workable Tracker ML (Excel)"
        self.description = "Update GIS Pier Workable Tracker ML (Excel)"

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
            displayName = "N2 Civil Pier Workability ML (Excel)",
            name = "N2 Civil Pier Workability ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_obstruction_ms = arcpy.Parameter(
            displayName = "N2 RAP Pier Workability Tracker (Excel)",
            name = "N2 RAP Pier Workability Tracker (Excel)",
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

        params = [pier_workablet_dir, viaduct_ms, civil_workable_ms, rap_obstruction_ms, gis_nlo_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_workablet_dir = params[0].valueAsText
        viaduct_ms = params[1].valueAsText
        civil_table = params[2].valueAsText
        rap_obst_table = params[3].valueAsText
        gis_nlo_ms = params[4].valueAsText

        def Workable_Pier_Tracker_Update():            
            # Define field names
            cp_field = 'CP'
            type_field = 'Type'
            status_field = 'Status'
            pier_num_field = 'PierNumber'
            workability_field = 'Workability'
            land_field = 'Land'
            land1_field = 'Land.1'
            struc_field = 'Structure'
            struc1_field = 'Structure.1'
            others_field = 'Others'
            util_obstruc_field = 'Utility'
            remarks_field = 'Remarks'
            struc_id_field = 'StrucID'
            nlo_obstruc_field = 'NLO'

            #--------------------------------------------------------#
            #             Clean Civil Team's Tracker ML              #
            #--------------------------------------------------------#
            # Workability field:
            ## 0: Workable
            ## 1: Non-workable
            ## 2: Completed

            workable_status = {
                'Yes': 'Workable',
                'No': 'Non-workable',
                'Partial': 'Non-workable'
            }

            civil_t = pd.read_excel(civil_table, skiprows=2)
            via_t = pd.read_excel(viaduct_ms)
            gis_nlo_t = pd.read_excel(gis_nlo_ms)
            
            new_cols = ['PierNumber', 'CP', 'util1', 'util2', 'Others', 'Workability']
            
            #----------------------#
            # --- Clean fields --- #
            #----------------------#
            ids = civil_t.columns[civil_t.columns.str.contains(r'^Pier No.*|Contract P.*|^Name of Utilities|^Others|^OTHERS|^Pile Cap Workable.*',regex=True,na=False)]
            civil_t = civil_t.loc[:, ids]
            for i, col in enumerate(ids):
                civil_t = civil_t.rename(columns={col: new_cols[i]})
                
            #--- change CP notation           
            civil_t = update_N2_CP_notation(civil_t, new_cols[1])

            #--- Update 'Workability' field ---#
            civil_t[new_cols[5]] = civil_t[new_cols[5]].str.title()
            for status in ['Yes', 'No', 'Partial']:
                ids = civil_t.query(f"{new_cols[5]} == '{status}'").index
                civil_t.loc[ids, new_cols[5]] = workable_status[status]

            idx_workable = civil_t.index[civil_t[workability_field] == 'Workable']

            #--- Update 'Utility' field ---#
            ids = civil_t.query(f"{new_cols[2]}.notna() or {new_cols[3]}.notna()").index
            civil_t.loc[ids, util_obstruc_field] = 1
            civil_t = civil_t.drop([new_cols[2], new_cols[3]], axis=1)

            ## When workable, 'Utility' field => empty
            civil_t.loc[idx_workable, util_obstruc_field] = np.nan

            #--- Update 'Others' ---#
            ids = civil_t.query(f"~{new_cols[4]}.isna()").index
            civil_t.loc[ids, new_cols[4]] = 1

            #--------------------------------------------------------#
            #              Clean RAP Team's Tracker                  #
            #--------------------------------------------------------#
            # Add obstructing Lot and structure IDs to pier workable tracker ML
            final_table = pd.DataFrame()
            cps = ['N-01', 'N-02', 'N-03']
            for cp in cps:
                rap_t = pd.read_excel(rap_obst_table, skiprows = 1, sheet_name = cp)
                rap_t = rap_t.loc[:, [pier_num_field,
                                    land_field,
                                    struc_field,
                                    land1_field,
                                    struc1_field]]
                
                # Land1                
                rap_t = reformat_obstructon_fields(rap_t, land1_field)
                ids = rap_t.index[rap_t[land1_field] == '']
                rap_t.loc[ids, land1_field] = np.nan

                # struc1
                rap_t = reformat_obstructon_fields(rap_t, struc1_field)               
                ids = rap_t.index[rap_t[struc1_field] == '']
                rap_t.loc[ids, struc1_field] = np.nan

                # NLO
                ## Enter NLO using obstructing structure IDs
                gis_nlo_t_filter = gis_nlo_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                nlo_piers = unique(gis_nlo_t_filter[struc_id_field])

                # Inspect the Pier Tracker ML contains the above strucIDs
                nlo_piers_join = ("|").join(nlo_piers)
                idx = rap_t.index[rap_t[struc1_field].str.contains(nlo_piers_join,regex=True,na=False)]
                rap_t[nlo_obstruc_field] = np.nan
                rap_t.loc[idx, nlo_obstruc_field] = 1

                # Filter civil tracker
                c_t = civil_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                merged = pd.merge(left=c_t, right=rap_t, how='left', on=pier_num_field)
                final_table = pd.concat([final_table, merged])
            
            final_table = final_table.reset_index(drop=True)

            #--------------------------------------------------------#
            #           Finalize Pier Workable Tracker ML            #
            #--------------------------------------------------------#
            #--- Monopile (no pile cap) to Completed => P-159C, P-159NB/SB, P-160C, P-160NB/SB ---#
            # P-159 => P-159C
            # P-160 => P-160C
            # This code must be executed before adding 'Completed' pile cap.
            final_table = update_monopile_pier_numbers_civilML(final_table, pier_num_field)

            mono_piles = ["P-159C", "P-159NB", "P-159SB", "P-160C", "P-160NB", "P-160SB"]
            ids = final_table.query(f"{pier_num_field}.isin({mono_piles})").index
            final_table.loc[ids, workability_field] = "Workable"

            # Add status_field
            final_table[status_field] = 1

            # Update 'Workability'
            ## 'Workability' = Completed
            ids = via_t.query(f"{status_field} == 4 and {type_field} == 2").index
            comp_piers = list(via_t.loc[ids, pier_num_field])
            ids = final_table.query(f"{pier_num_field}.isin({comp_piers})").index
            final_table.loc[ids, workability_field] = 'Completed'
            final_table.loc[ids, status_field] = 4

            ## 'Workability' = 'Completed', the other fields = np.nan
            ids = final_table.query(f"{workability_field} == 'Completed' and ({land_field} == 1 or {struc_field} == 1 or {util_obstruc_field} == 1 or {nlo_obstruc_field} == 1 or {others_field} == 1 )").index            
            final_table = convert_to_nan(final_table, ids, [land_field, land1_field, struc_field, struc1_field, util_obstruc_field, nlo_obstruc_field, others_field])

            ## 'Workability', the other fields = np.nan
            ids = final_table.query(f"{workability_field} == 'Workable' and ({land_field} == 1 or {struc_field} == 1 or {util_obstruc_field} == 1 or {nlo_obstruc_field} == 1 or {others_field} == 1 )").index
            final_table = convert_to_nan(final_table, ids, [land_field, land1_field, struc_field, struc1_field, util_obstruc_field, nlo_obstruc_field, others_field])

            #--------------------------------------------------------#
            #                 Identify Discrepancies                 #
            #--------------------------------------------------------#
            # Add case of errors to Remarks field;
            # 1. Completed and Workable piers have obstructions (in Utility, Land, Structure, Others, Land.1, Structure.1)
            # 2. Non-workable piers have empty cells in Utility, Land, Structure, Others, Land.1, Structure.1.
            # 3. Piers with obstructing Land (1) or Structure (1) do not have any IDs in Land.1 or Structure.1 field.
            # 4. Piers with obstructing Lot or Structure IDs in Land.1 or Structure.1 field do not have '1' in Land or Structure field.

            final_table[remarks_field] = np.nan
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
                        ).format(workability_field, util_obstruc_field, land_field, struc_field, others_field, land1_field, struc1_field),
                'case3': ("`{}` == 'Non-workable' & `{}` == 1 & `{}`.isna()").format(workability_field, land_field, land1_field),
                'case4': ("`{}` == 'Non-workable' & `{}` == 1 & `{}`.isna()").format(workability_field, struc_field, struc1_field),
                'case5': ("`{}` == 'Non-workable' & `{}` == 1 & ~`{}`.isna()").format(workability_field, land1_field, land_field),
                'case6': ("`{}` == 'Non-workable' & `{}` == 1 & ~`{}`.isna()").format(workability_field, struc1_field, struc_field)
            }

            for error in error_descriptions:
                ids = final_table.query(query_str[error]).index
                final_table.loc[ids, remarks_field] = error_descriptions[error]

            # Export as a new tracker
            to_excel_file0 = os.path.join(pier_workablet_dir, "N2_Pier_Workability_Tracker.xlsx")
            with pd.ExcelWriter(to_excel_file0) as writer:
                final_table.query(f"{cp_field} == 'N-01'").reset_index(drop=True).to_excel(writer, sheet_name='N-01', index=False)
                final_table.query(f"{cp_field} == 'N-02'").reset_index(drop=True).to_excel(writer, sheet_name='N-02', index=False)
                final_table.query(f"{cp_field} == 'N-03'").reset_index(drop=True).to_excel(writer, sheet_name='N-03', index=False)

        Workable_Pier_Tracker_Update()

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "3.3. Check Pier Numbers between Civil, GIS Portal, and RAP ML"
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
            displayName = "N2 Pier Workability Tracker (Excel)",
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

            # List of fields
            cp_field = 'CP'
            type_field = 'Type'
            pier_num_field = 'PierNumber'
            cps = ['N-01','N-02','N-03']

            compile_table = pd.DataFrame()

            #--- Preprocess Civil ML 
            # must run this first for cp notations like N-01/N-02
            new_cols = ['PierNumber', 'CP', 'util1', 'util2', 'Others', 'Workability']           
            x = pd.read_excel(civil_workable_ms, skiprows=2)
            ids = x.columns[x.columns.str.contains(r'^Pier No.*|Contract P.*|^Name of Utilities|^Others|^Pile Cap Workable.*',regex=True,na=False)]
            x = x.loc[:, ids]
            for i, col in enumerate(ids):
                x = x.rename(columns={col: new_cols[i]})

            #--- Update pier number for monopiles
            x = update_monopile_pier_numbers_civilML(x, pier_num_field)

            for cp in cps:
                arcpy.AddMessage("Contract Package: " + cp)
  
                #--- Get pier numbers ---#
                gis_piers = extract_pier_numbers(cp, cp_field, pier_num_field, type_field, gis_viaduct_ms, None, None)
                tracker_piers = extract_pier_numbers(cp, cp_field, pier_num_field, None, None, None, gis_pier_tracker_ms)
                civil_piers = x.loc[x.query(f"{cp_field} == '{cp}'").index, pier_num_field].values
                
                columns = ['cp',
                           'civil',
                            'gis',
                            'tracker',
                            'non-matched piers (civil-gis)',
                            'non-matched piers (civil-tracker)'
                            ]
                
                table = summary_statistics_count_piers(cp, civil_piers, gis_piers, columns, tracker_piers)
 
                # Compile cps
                compile_table = pd.concat([compile_table, table])
            
            # Export
            compile_table.to_excel(os.path.join(pier_tracker_dir, '99-CHECK_Summary_N2_PierNumbers_Civil_vs_GISportal_vs_pierTracker.xlsx'),
                                              index=False)

        Workable_Pier_Table_Update()

class UpdatePierWorkablePolygonLayer(object):
    def __init__(self):
        self.label = "3.4. Update Pier Workable Layer (Polygon)"
        self.description = "Update Pier Workable Layer (Polygon)"

    def getParameterInfo(self):
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

            # 1. Clean fields
            cps = ['N-01','N-02','N-03']
            for cp in cps:
                pier_tracker_t = pd.read_excel(pier_tracker_ms, sheet_name = cp)
                idx = pier_tracker_t.iloc[:, 0].index[pier_tracker_t.iloc[:, 0].str.contains(r'PierNumber',regex=True,na=False)]
                pier_tracker_t = pier_tracker_t.drop(idx).reset_index(drop=True)

                # to string
                pier_tracker_t[lot_obstrucid_field] = pier_tracker_t[lot_obstrucid_field].astype(str)
                pier_tracker_t[struc_obstrucid_field] = pier_tracker_t[struc_obstrucid_field].astype(str)

                # create workable columns for pre-construction work
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
                
                #--------------------------------------------------------#
                #     Update Pier Workable Layer using Civil table       #
                #--------------------------------------------------------#
                # Status of Workable Pier
                ## 1: Non-Workable
                ## 0: Workable
                ## 2: Completed

                # --- Update 'AllWorkalble' to Completed
                completed_piers = []
                with arcpy.da.SearchCursor(gis_workable_layer, [pier_number_field, workable_cols[0]]) as cursor:
                    for row in cursor:
                        if row[1] == 2:
                            completed_piers.append(row[0])

                # --- Update fields to 'Workable' for incomplete pile caps ---#
                id_workable_piers = pier_tracker_t.index[pier_tracker_t[workability_field] == 'Workable']
                workable_piers = pier_tracker_t.loc[id_workable_piers, pier_number_field].values

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

                #--- Update fields to 'Non-workable' ---#
                for i, col in enumerate(workable_cols):
                    if col == workable_cols[0]:
                        ids = pier_tracker_t.index[pier_tracker_t[workability_field] == 'Non-workable']
                        nonworkable_piers = pier_tracker_t.loc[ids, pier_number_field].values
                        with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, col, cp_field]) as cursor:
                            for row in cursor:
                                if row[0] in tuple(nonworkable_piers) and row[2] == cp:
                                    row[1] = 1
                                cursor.updateRow(row)
                    else:
                        ids = pier_tracker_t.query(f"{obstruction_cols[i]} == 1").index
                        nonworkable_piers = pier_tracker_t.loc[ids, pier_number_field].values

                        with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, workable_cols[i], cp_field]) as cursor:
                            for row in cursor:
                                if row[0] in tuple(nonworkable_piers) and row[2] == cp:
                                    row[1] = 1
                                cursor.updateRow(row)

                #--- Update fields to 'Workable for empty pile caps' ---#
                for col in workable_cols[1:]:
                    with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, col, cp_field]) as cursor:
                        for row in cursor:
                            if row[1] is None and row[2] == cp:
                                row[1] = 0
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

                #--------------------------------------------------------#
                #       Update Pier Workable Layer for 'Remarks'         #
                #--------------------------------------------------------#
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

class UpdatePierPointLayer(object):
    def __init__(self):
        self.label = "3.5. Update Pier Layer (Point)"
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
        # viaduct_layer = params[2].valueAsText
        
        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def Pier_Point_Layer_Update():
            
            unique_id_field = 'uniqueID'
            new_point_layer = 'N2_new_Pier_Point'
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
        workability_field_stripmap = 'Workability'

        def Strip_Map_Layer_Update():
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

            #--- Update 2nd CP field for overlapping polygons ---#
            #*** Accommodate two different CPs when selected in the smart map
            cp2_field = 'GroupId'

            # First enter null 'GroupId' field
            with arcpy.da.UpdateCursor(strip_map_layer, [cp2_field]) as cursor:
                for row in cursor:
                    if row[0]:
                        row[0] = None
                    cursor.updateRow(row)
                    
            # Select rows
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

class JustMessage5(object):
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
 
class ReSortGISTable(object):
    def __init__(self):
        self.label = "8.0. (Optional) Re-Sort N2 Viaduct Attribute Table"
        self.description = "(Optional) Re-Sort N2 Viaduct Attribute Table"

    def getParameterInfo(self):
        gis_layer = arcpy.Parameter(
            displayName = "N2 Viaduct Layer (File Geodatabase)",
            name = "N2 Viaduct Layer (File Geodatabase)",
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
                layer_sorted = "N2_viaduct_sorted"
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
                to_excel_file = os.path.join(excel_export_dir, "N2_Viaduct_GIS_Portal.xlsx")
                arcpy.conversion.TableToExcel(layer_sorted, to_excel_file)

                # 8. Delete sorted layer
                arcpy.management.Delete(layer_sorted)
            
            except Exception:
                arcpy.AddMessage('This failed. Please check your code')
                arcpy.AddError('This failed. Please check your code')
        else:
            arcpy.AddMessage('This failed. Please check your code')
            arcpy.AddError('This failed. Please check your code')
