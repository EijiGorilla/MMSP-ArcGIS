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
        self.label = "UpdateSCViaduct"
        self.alias = "UpdateSCViaduct"
        self.tools = [UpdateExcelML ,UpdateGISTable]

class UpdateExcelML(object):
    def __init__(self):
        self.label = "1. Update GIS Excel ML (SC Viaduct)"
        self.description = "1. Update GIS Excel ML (SC Viaduct)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "Target GIS ML Table (Excel)",
            name = "Target GIS ML Table (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "Input Civil ML Table (Excel)",
            name = "Input Civil ML Table (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        gis_backup_dir = arcpy.Parameter(
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

        params = [gis_dir, gis_ml, civil_ml, gis_backup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_ml = params[1].valueAsText
        civil_dir = params[2].valueAsText
        gis_backup_dir = params[3].valueAsText
        lastupdate = params[4].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def SC_Viaduct_Update():
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
                    table[field] = table[field].apply(lambda x: x.replace(r'/s+', ''))
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
                table[field] = pd.to_datetime(table[field],errors='coerce').dt.date
                #table[field] = table[field].astype('datetime64[ns]')

            # Main workflow
            # 1. Compile civil tables for viaduct types
            # 2. Split GIS ML tables with only respective rows from the Civil.
            # 3. Join the compiled civil table to the split GIS table using ID field (we ned ID field to join)
            # 4. Append the split GIS tables into one table (final table)
            # 5. Export the final table as a new GIS ML table.

            ## Read table
            gis_table = pd.read_excel(gis_ml, keep_default_na=False)

            ## Create backup file for GIS master list
            export_file_name = os.path.splitext(os.path.basename(gis_ml))[0]
            try:
                arcpy.AddMessage('Backup start..')
                backup_file = os.path.join(gis_backup_dir, lastupdate + "_" + export_file_name + ".xlsx")
                gis_table.to_excel(backup_file, index=False)
            except:
                pass

            ## Define field names
            unique_id = 'uniqueID'
            status_field = 'Status'
            status1_field = 'Status1'
            type_field = 'Type'
            pier_field = 'PierNumber'
            npierno_field = 'nPierNumber'
            civil_pier_field = 'Pier'
            No_field = 'No'
            start_actual_field = 'start_actual'
            finish_plan_field = 'finish_plan'
            finish_actual_field = 'finish_actual'
            id_field = 'ID'
            package_field = 'Package'
            remarks_field = 'Remarks'
            dummy_date = '1990-01-01'

            join_fields = [pier_field, status_field, start_actual_field, finish_plan_field, finish_actual_field]
            date_fields = [start_actual_field, finish_plan_field, finish_actual_field]
            delete_fields = [package_field, remarks_field]

            ## Define viaduct types
            via_type = {
                'BoredPile': 1,
                'PileCap': 2,
                'Pier': 3,
                'PierHead': 4,
                'Precast': 5,
                # 'cantilever': 6,
                # 'At-Grade': 7
                }

            today = pd.to_datetime('today') #date.today()

            ## Re-format date in gis table
            for field in date_fields:
                toDate(gis_table, field)
                
            arcpy.AddMessage("2.")
            ## choose sheet names for each viaduct
            temp_table = pd.ExcelFile(civil_dir)
            sheet_names = temp_table.sheet_names[:-1]

            # 0. Check duplicated observations in Civil Table
            dup_compile = []
            for sheet in sheet_names:
                table = pd.read_excel(civil_dir, sheet_name=sheet)

                # Civil table often misses boref pile no, in this case, drop these piers
                table[id_field] = np.nan

                if via_type[sheet] == 1: # only for bored piles
                    # Remove the first row with 'SAMPLE' in Remarks column
                    id = table.index[table['Remarks'] == 'SAMPLE']
                    table = table.drop(id)

                    # Drop rows with empty 'No'
                    id = table.index[table[No_field].isnull()]
                    table = table.drop(id)
                    
                    # Create ID ('Pier" + '-' + 'No')
                    ## Make sure to have no hypen for P. (e.g., P684-2 (O), P-684-2 (X))
                    table[civil_pier_field] = table[civil_pier_field].apply(lambda x: x.upper())
                    table[civil_pier_field] = table[civil_pier_field].apply(lambda x: x.replace(r'P-','P'))
                    table[No_field] = table[No_field].astype(str)
                    table[id_field] = table[civil_pier_field].str.cat(table[No_field], sep = "-")

                    # Check duplicated ID
                    ids = table[id_field].duplicated()
                    idx = ids.index[ids == True]
                    dup_pier = table[civil_pier_field].iloc[idx]
                    dup_len = len(dup_pier)

                    if dup_len > 0:
                        arcpy.AddMessage("Pier           Type")
                        for i in range(0, dup_len):
                            arcpy.AddMessage("{0}        {1}".format(dup_pier.iloc[i], sheet))
                else:
                    ids = table[civil_pier_field].duplicated()
                    idx = ids.index[ids == True]
                    dup_pier = table[civil_pier_field].iloc[idx]
                    dup_len = len(dup_pier)
                    
                    if dup_len > 0:
                        arcpy.AddMessage("Pier           Type")
                        for i in range(0, dup_len):
                            arcpy.AddMessage("{0}        {1}".format(dup_pier.iloc[i], sheet))
                    
                dup_compile.append(dup_len)

            dup_comp = pd.Series(dup_compile)
            dup_len = len(dup_comp.index[dup_comp > 0])

            # Continue only when there is no duplicated observations
            if dup_len == 0:
                ## 1. Compile civil table
                civil_table2 = pd.DataFrame()
                for sheet in sheet_names:    
                    # Read sheet for each viaduct type
                    arcpy.AddMessage(sheet)
                    civil_table = pd.read_excel(civil_dir, sheet_name=sheet)

                    # Remove the first row with 'SAMPLE' in Remarks column
                    id = civil_table.index[civil_table['Remarks'] == 'SAMPLE']
                    civil_table = civil_table.drop(id)

                    # Keep columns from 1st to Remarks
                    ind = [e for e in civil_table.columns.str.contains('Remarks',regex=True)].index(True)
                    civil_table = civil_table.drop(civil_table.columns[ind+1:],axis=1)

                    # To String
                    civil_table[civil_pier_field] = civil_table[civil_pier_field].astype(str)

                    # Re-format 'P-' to 'P'
                    civil_table[civil_pier_field] = civil_table[civil_pier_field].apply(lambda x: x.replace(r'P-','P'))
                    arcpy.AddMessage("5.")

                    # 1. Convert to date
                    for field in date_fields:
                        toDate(civil_table, field)
                        civil_table[field] = civil_table[field].astype('datetime64[ns]')

                    # 2. add viaduct type
                    civil_table[type_field] = via_type[sheet]
                    civil_table[type_field] = civil_table[type_field].astype(str)
                    civil_table[type_field] = civil_table[type_field].apply(lambda x: re.sub('.0','',x)) # need to remove '.0' in '3.0'
                    
                    # 3. Update and add status
                    civil_table[status1_field] = np.nan

                    # arcpy.AddMessage(civil_table) OK
                   
                    ## Status = 1:
                    ### start_actual & finish_plan are both empty -> Delete. Default status is entered with '1' in GIS ML = no need
                    #id = civil_table.index[(civil_table[start_actual_field].isnull()) & (civil_table[finish_plan_field].isnull())]
                    ### 'Status' field is empty => drop rows.
                    id = civil_table.index[(civil_table[status_field].isnull()) | (civil_table[status_field].isna())]
                    civil_table = civil_table.drop(id)

                    arcpy.AddMessage(civil_table)

                    ### start_actual is empty & finish_plan > today (construction has not started but target date is future)
                    id = civil_table.index[civil_table[start_actual_field].isnull() & (civil_table[finish_plan_field] > today)]
                    civil_table.loc[id, status1_field] = 1
                    
                    ##finish_actual exists -> Status = 4 (Completed)
                    id = civil_table.index[civil_table[finish_actual_field].notna()]
                    civil_table.loc[id,status1_field] = 4

                    ## finish_actual empty but Status = cast/Cast/casted/Casted
                    # id = civil_table.index[civil_table[finish_actual_field].isna() | civil_table[status_field].str.contains(r'cast|casted|Cast|Casted',regex=True)]
                    # civil_table.loc[id, status1_field] = 4
                    
                    ### start_actual & empty finish_actual -> 2 (under construction)
                    id = civil_table.index[(civil_table[start_actual_field].notna()) & (civil_table[finish_actual_field].isnull())]
                    civil_table.loc[id,status1_field] = 2
                    
                    ### (finish_plan < date of updat) & finish_actual is empty -> 3 (delayed)
                    id = civil_table.index[(civil_table[finish_actual_field].isnull()) & (civil_table[finish_plan_field].notna()) & (civil_table[finish_plan_field] < today)]
                    civil_table.loc[id,status1_field] = 3

                    # arcpy.AddMessage(civil_table)
                    
                    if via_type[sheet] == 1: # only for bored piles
                         # Drop rows with empty 'No'
                        id = civil_table.index[civil_table[No_field].isnull()]
                        civil_table = civil_table.drop(id)

                        # To string before concatenating column names
                        civil_table[No_field] = civil_table[No_field].astype(str)
                        civil_table[No_field] = civil_table[No_field].apply(lambda x: re.sub('.0','',x)) # need to remove '.0' in '3.0'
                        
                        # Concatenate: 'Pier' + "-" + 'No' + "-" + 'Type' (e.g., P684-2-2-1, P684-2-3-1)
                        arcpy.AddMessage("6.")
    
                        civil_table[id_field] = civil_table[civil_pier_field] + "-" + civil_table[No_field] + "-" + civil_table[type_field]
                        civil_table = civil_table.drop(columns=[No_field,type_field])
                        arcpy.AddMessage("7.")
                    else:
                        civil_table[id_field] = civil_table[civil_pier_field] + "-" + civil_table[type_field]
                        civil_table = civil_table.drop(columns=type_field)
                        arcpy.AddMessage("8.")
                        
                    # Re-format 'Pier' and rename
                    civil_table = rename_columns_title(civil_table,civil_pier_field,pier_field)
                    
                    # Delete 'Status' and rename 'Status1' = 'Status'
                    civil_table = civil_table.drop(columns=status_field)
                    civil_table = rename_columns_title(civil_table,status1_field,status_field)
                    civil_table[status_field] = civil_table[status_field].astype('int64')
                    
                    # Drope other fields
                    civil_table = civil_table.drop(columns=delete_fields)

                    # Column bind 
                    civil_table2 = pd.concat([civil_table2,civil_table])
                    civil_table2.to_excel(os.path.join(gis_dir, "check_civil_table2" + ".xlsx"), index=False)
                
                # Re-index the compiled table
                civil_table2 = civil_table2.reset_index(drop=True)
                
                ## 2. Update GIS ML table               
                ## 2.1. Get only 'ID's from the updated Civil table
                ids = civil_table2[id_field]
                
                ## 2.2. Extract rows from GIS table with respective IDs
                ### 2.2.1. Clean 'P-' to 'P-'
                gis_table[pier_field] = gis_table[pier_field].apply(lambda x: x.replace(r'P-','P'))
                gis_table2 = gis_table # copy in case
                id = gis_table2.index[gis_table2[id_field].str.contains('|'.join(ids))]
                g_table = gis_table2.iloc[id]
                
                ## 2.3.Extract rows from GIS table without respective IDs
                ### We need to remove these observations for updating from Civil table
                id = gis_table2.index[gis_table2[id_field].str.contains('|'.join(ids)) == False]
                g_table2 = gis_table2.iloc[id]
                
                ## 2.4. Join updated civil table to this extracted gis table
                ### DO not drop 'uniqueID' field
                g_table = g_table.drop(columns=join_fields)
                merged_table = pd.merge(left=g_table, right=civil_table2, how='left', left_on=id_field, right_on=id_field)
                
                ## 2.5. Append the merged table to the GIS table
                final_table = pd.concat([g_table2, merged_table], ignore_index=True)

                ## 2.6. Sort by uniqueID
                final_table = final_table.sort_values(by=[unique_id])

                ## Final tweak:
                ## 2.6. Status = 1 when Status is empty
                id = final_table.index[final_table[status_field].isnull()]
                final_table.loc[id, status_field] = 1

                ## 2.7. The 1st rows of date_fiels are empty -> enter dummy dates
                final_table = final_table.reset_index(drop=True)
                for field in date_fields:
                    date_item = final_table[field].iloc[:1].item()
                    if date_item is None or pd.isnull(date_item):
                        final_table.loc[0, field] = pd.to_datetime(dummy_date)

                    # to Date (conver to pd.to_datetime)
                    toDate(final_table, field)
                
                ## Export
                to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
                final_table.to_excel(to_excel_file, index=False)

            else:
                arcpy.AddError("Duplicated IDs were detected in Civil Team's Excel. This process stopped.")
                pass
        SC_Viaduct_Update()

class UpdateGISTable(object):
    def __init__(self):
        self.label = "2. Update GIS Attribute Table (SC Viaduct)"
        self.description = "Update SC Viaduct multipatch layer (SC Viaduct)"

    def getParameterInfo(self):
        gis_layer = arcpy.Parameter(
            displayName = "GIS Attribute Table (SC Viaduct)",
            name = "GIS Attribute Table (SC Viaduct)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        excel_table = arcpy.Parameter(
            displayName = "GIS MasterList Table (Excel)",
            name = "GIS MasterList Table (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_layer, excel_table]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        gis_layer = params[0].valueAsText
        excel_table = params[1].valueAsText

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
            arcpy.AddMessage('The following IDs do not match between ML and GIS.')
            arcpy.AddMessage('Missing LotIDs in GIS table: {}'.format(uniqueid_miss_gis))
            arcpy.AddMessage('Missing LotIDs in ML Excel table: {}'.format(uniqueid_miss_ml))
            
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

        # Delete the copied feature layer
        deleteTempLayers = [gis_copied, viaduct_ml]
        arcpy.Delete_management(deleteTempLayers)