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
        self.tools = [UpdateExcelML, UpdateGISTable, 
                      CreateWorkablePierLayer, CheckPierNumbers, 
                      UpdateWorkablePierLayer, UpdatePierPointLayer,
                      ReSortGISTable, CheckUpdatesCivilGIS]

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
        civil_ml = params[2].valueAsText
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
            cp_field = 'CP'
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
            # temp_table = pd.ExcelFile(civil_dir)
            sheet_names = ['BoredPile', 'PileCap', 'Pier', 'PierHead', 'Precast'] #temp_table.sheet_names

            # 0. Check duplicated observations in Civil Table
            dup_compile = []
            for sheet in sheet_names:
                table = pd.read_excel(civil_ml, sheet_name=sheet)

                # Civil table often misses bored pile no, in this case, drop these piers
                table[id_field] = np.nan

                # Drop rows with empty pier numbers
                idx = table.index[~table[civil_pier_field].isna()]
                table = table.loc[idx, ].reset_index(drop=True)
                table['temp'] = table[civil_pier_field].str.replace(r'[^P]','',regex=True) # Remove all letters except for 'P'
                idx = table.index[table['temp'] != 'PP']
                table = table.loc[idx, ]

                if via_type[sheet] == 1: # only for bored piles
                    # Remove the first row with 'SAMPLE' in Remarks column
                    id = table.index[table['Remarks'] == 'SAMPLE']
                    table = table.drop(id).reset_index(drop=True)
                    
                    # Delete this later
                    # x1 = table.query(f"{civil_pier_field} == 'P685'")
                    # arcpy.AddMessage(x1)

                    # Drop rows with empty 'No'
                    id = table.index[table[No_field].isnull()]
                    table = table.drop(id).reset_index(drop=True)
                    
                    # Create ID ('Pier" + '-' + 'No')
                    ## Make sure to have no hypen for P. (e.g., P684-2 (O), P-684-2 (X))
                    table[civil_pier_field] = table[civil_pier_field].apply(lambda x: x.upper())
                    table[civil_pier_field] = table[civil_pier_field].apply(lambda x: x.replace(r'P-','P'))
                    table[No_field] = table[No_field].astype(str)
                    table[id_field] = table[civil_pier_field].str.cat(table[No_field], sep = "-")
                    # idx = table.index[table[civil_pier_field] == 'P686']
                    # arcpy.AddMessage(table.loc[idx, id_field])

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
                arcpy.AddMessage("No duplicated records..Proceed.")

                ## 1. Compile civil table
                civil_table2 = pd.DataFrame()
                for sheet in sheet_names:    
                    # Read sheet for each viaduct type
                    arcpy.AddMessage(sheet)
                    civil_table = pd.read_excel(civil_ml, sheet_name=sheet)

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

                    # Drop rows with empty pier numbers
                    idx = civil_table.index[~civil_table[civil_pier_field].isna()]
                    civil_table = civil_table.loc[idx, ].reset_index(drop=True)
                    civil_table['temp'] = civil_table[civil_pier_field].str.replace(r'[^P]','',regex=True) # Remove all letters except for 'P'
                    idx = civil_table.index[civil_table['temp'] != 'PP']
                    civil_table = civil_table.loc[idx, ]

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

                    ##finish_actual exists -> Status = 4 (Completed)
                    id = civil_table.index[civil_table[finish_actual_field].notna()]
                    civil_table.loc[id,status1_field] = 4

                    ### start_actual & empty finish_actual -> 2 (under construction)
                    id = civil_table.index[(civil_table[start_actual_field].notna()) & (civil_table[finish_actual_field].isnull())]
                    civil_table.loc[id,status1_field] = 2
                    
                    ### (finish_plan < date of updat) & finish_actual is empty -> 3 (delayed)
                    id = civil_table.index[(civil_table[finish_actual_field].isnull()) & (civil_table[finish_plan_field].notna()) & (civil_table[finish_plan_field] < today)]
                    civil_table.loc[id,status1_field] = 3

                    ### else 1
                    id = civil_table.index[civil_table[status1_field].isnull()]
                    civil_table.loc[id, status1_field] = 1
                    
                    if via_type[sheet] == 1: # only for bored piles
                        # Drop rows with empty 'No'
                        id = civil_table.index[civil_table[No_field].isnull()]
                        civil_table = civil_table.drop(id).reset_index(drop=True)

                        # To string before concatenating column names
                        civil_table[No_field] = civil_table[No_field].astype(str)
                        civil_table[No_field] = civil_table[No_field].apply(lambda x: re.sub('.0','',x)) # need to remove '.0' in '3.0'
                        
                        # Concatenate: 'Pier' + "-" + 'No' + "-" + 'Type' (e.g., P684-2-2-1, P684-2-3-1)    
                        civil_table[id_field] = civil_table[civil_pier_field] + "-" + civil_table[No_field] + "-" + civil_table[type_field]
                        civil_table = civil_table.drop(columns=[No_field,type_field])
                    else:
                        civil_table[id_field] = civil_table[civil_pier_field] + "-" + civil_table[type_field]
                        civil_table = civil_table.drop(columns=type_field)

                    # Drop column name 'Segement' if present
                    try:
                         civil_table = civil_table.drop(columns="Segment")
                    except:
                        pass

                    # Re-format 'Pier' and rename
                    civil_table = rename_columns_title(civil_table,civil_pier_field,pier_field)
                    
                    # Delete 'Status' and rename 'Status1' = 'Status'
                    civil_table = civil_table.drop(columns=status_field)
                    civil_table = rename_columns_title(civil_table,status1_field,status_field)
                    civil_table[status_field] = civil_table[status_field].astype('int64')

                    # Ensure to delete empty column if present (sometimes civil_table has empty columns. In this case, python throws 'Unanamed' column)
                    empty_column = civil_table.columns[civil_table.columns.str.contains(r'^Unnamed',regex=True)]
                    civil_table = civil_table.drop(columns=empty_column)
                   
                    # Drope other fields
                    civil_table1 = civil_table.drop(columns=delete_fields)

                    # Column bind 
                    civil_table2 = pd.concat([civil_table2,civil_table1])
                    # civil_table2.to_excel(os.path.join(gis_dir, "check_civil_table2" + ".xlsx"), index=False)
                
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

                ## 2.6. Return labeling notation for PierNumber (e.g., P-0101, PR-1911)
                final_table[pier_field] = final_table[pier_field].replace(r'P','P-',regex=True)
                final_table[pier_field] = final_table[pier_field].replace(r'P-R','PR',regex=True)

                ## 2.7. Sort by uniqueID
                final_table = final_table.sort_values(by=[unique_id])

                # final_table.to_excel(os.path.join(gis_dir, "testTable1.xlsx"), index=False)

                ## Final tweak:
                ## 2.8. Status = 1 when Status is emptyc
                id = final_table.index[final_table[status_field].isnull()]
                final_table.loc[id, status_field] = 1

                ## 2.9. The 1st rows of date_fiels are empty -> enter dummy dates
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
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )
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

        # 6. Table to Excel
        # (This ensures that SC_Viaduct_ML.xlsx is always consistent with SC Viaduct GIS attribute table)
        # Reason: uniqueID is sometimes updated in the GIS attribute table
        arcpy.conversion.TableToExcel(gis_layer, os.path.join(gis_dir, 'SC_Viaduct_ML.xlsx'))
        
        # Delete the copied feature layer
        deleteTempLayers = [gis_copied, viaduct_ml]
        arcpy.Delete_management(deleteTempLayers)

class CreateWorkablePierLayer(object):
    def __init__(self):
        self.label = "3. Create Pier Workable Layer (Polygon)"
        self.description = "Create Pier Workable Layer"

    def getParameterInfo(self):
        pier_workable_dir = arcpy.Parameter(
            displayName = "SC GIS Pier Tracker Masterlist Storage Directory",
            name = "SC GIS Pier Tracker Masterlist Storage Directory",
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
        new_layer = 'SC_Pier_Workable'
        arcpy.ddd.MultiPatchFootprint(temp_layer, new_layer)

        ## Delete field
        arcpy.management.DeleteField(new_layer, ['CP','PierNumber','uniqueID','Status'], "KEEP_FIELDS")

        # Add field
        new_fields = new_cols + ['Type']
        for field in new_fields:
            if field == 'Type':
                arcpy.management.AddField(new_layer, field, "TEXT", field_alias=field, field_is_nullable="NULLABLE")
            else:
                arcpy.management.AddField(new_layer, field, "SHORT", field_alias=field, field_is_nullable="NULLABLE")

        with arcpy.da.UpdateCursor(new_layer, ['Type', 'Status', 'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']) as cursor:
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

        # delete
        deleteTempLayers = [new_layer, temp_layer]
        arcpy.Delete_management(deleteTempLayers)

        # Export the latest N2 Viaduct layer to excel
        arcpy.conversion.TableToExcel(via_layer, os.path.join(workable_dir, "SC_Viaduct_MasterList.xlsx"))

        ########################################
        ##### Update SC Pier Point Layer #######
        ########################################
        try:
            temp_layer = 'temp_layer'
            arcpy.management.MakeFeatureLayer(via_layer, temp_layer, '"Type" = 2')
        
            # 'multipatch footprint'
            ## new_cols and 'Type' (sting) = 'Pile Cap'
            new_layer = 'SC_Pier_Point'
            arcpy.ddd.MultiPatchFootprint(temp_layer, new_layer)

            ## Feature to Point
            new_point_layer = 'SC_new_Pier_Point'
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

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "4. Check Pier Numbers between Civil and GIS Portal"
        self.description = "Check Pier Numbers between Civil and GIS Portal"

    def getParameterInfo(self):
        pier_tracker_dir = arcpy.Parameter(
            displayName = "Directory for Pier Tracker",
            name = "Directory for Pier Tracker",
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
            displayName = "GIS SC Viaduct ML (Excel)",
            name = "GIS SC Viaduct ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [pier_tracker_dir, civil_workable_ms, gis_viaduct_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_tracker_dir = params[0].valueAsText
        civil_workable_ms = params[1].valueAsText
        gis_viaduct_ms = params[2].valueAsText
        
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
            lot_id_field = 'LotID'
            struc_id_field = 'StrucID'

            # cps = ['S-01','S-02','S-03a','S-03b','S-03c','S-04','S-05','S-06','S-07']
            cps = ['S-01']
            compile_all = pd.DataFrame()
            for cp in cps:
                arcpy.AddMessage("Contract Package: " + cp)
                compile_t = pd.DataFrame()

                cols = ['CP',
                        'PierNumber_civil',
                        'PierNumber_gisportal',
                        'Diff_Civil_vs_GISportal',
                        'Non-matched_piers_Civil_vs_GISportal',
                        ]

                #1. Read table
                ## N2 Viaduct portal
                portal_t = pd.read_excel(gis_viaduct_ms)
                ids = portal_t.index[(portal_t[cp_field] == cp) & (portal_t[type_field] == 2)]
                portal_t = portal_t.loc[ids, [pier_num_field, unique_id_field]].reset_index(drop=True)
                gis_piers = portal_t[pier_num_field].values
                
                ## N2 Civil ML
                cp_civil_name = "(" + cp.replace('-','') + ")"
                civil_workable_t = pd.read_excel(civil_workable_ms,sheet_name=cp_civil_name)
                civil_workable_t = civil_workable_t.iloc[:,[14,19,22,23,24,25,26,27,28,30,32,34,35,48,51]]
                ids = civil_workable_t.index[civil_workable_t.iloc[:, 0].str.contains(r'^P-',regex=True,na=False)]
                civil_workable_t = civil_workable_t.loc[ids[0]:, ]
                col_names = [pier_num_field,'via_construct_status','workability',
                            'util1','util2','util3','util4','util5','ISF_pnr','land','structure','pnr_station','others',
                            lot_id_field, struc_id_field] # 'lot_id','struc_id'

                for j, col in enumerate(col_names):
                    civil_workable_t = civil_workable_t.rename(columns={civil_workable_t.columns[j]: col})


                civil_workable_t[pier_num_field] = civil_workable_t[pier_num_field].str.replace(r'\s+','',regex=True)
                idx = civil_workable_t.index[~civil_workable_t[pier_num_field].isna()]     
                civil_piers = civil_workable_t.loc[idx, pier_num_field].values
                arcpy.AddMessage(civil_piers)
                # arcpy.AddMessage(civil_piers)

                # 2. Comparing
                compile_t.loc[0, cols[0]] = cp

                ## 2.1. Civil vs GIS Portal
                compile_t.loc[0, cols[1]] = len(civil_piers)
                compile_t.loc[0, cols[2]] = len(gis_piers)
                compile_t.loc[0, cols[3]] = compile_t.loc[0, cols[1]] - compile_t.loc[0, cols[2]]
                nonmatch_piers = [e for e in civil_piers if e not in gis_piers]
                arcpy.AddMessage(nonmatch_piers)
                if len(nonmatch_piers) > 0:
                    compile_t.loc[0, cols[4]] = nonmatch_piers
                else:
                    compile_t.loc[0, cols[4]] = np.nan

                # Compile cps
                compile_all = pd.concat([compile_all, compile_t])
                compile_all = compile_all.loc[:, cols]
                arcpy.AddMessage("Table of Non-Matched Piers:")
                arcpy.AddMessage(compile_all)
            
            # Export
            compile_all.to_excel(os.path.join(pier_tracker_dir, '99-CHECK_Summary_SC_PierNumbers_Civil_vs_GISportal.xlsx'),
                                              index=False)

        Workable_Pier_Table_Update()

class UpdateWorkablePierLayer(object):
    def __init__(self):
        self.label = "5. Update Pier Workable Layer (Polygon)"
        self.description = "Update Pier Workable Layer (Polygon)"

    def getParameterInfo(self):
        gis_viaduct_dir = arcpy.Parameter(
            displayName = "Directory for Pier Workability",
            name = "Directory for Pier Workability",
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

        params = [gis_viaduct_dir, civil_workable_ms, gis_workable_layer, gis_nlo_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_via_dir = params[0].valueAsText
        civil_workable_ms = params[1].valueAsText
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
            workability_field = 'workability'
            unique_id_field = 'uniqueID'
            lot_id_field = 'LotID'
            struc_id_field = 'StrucID'


            # 1. Clean fields
            ## cps = ['S-01','S-02','S-03a','S-03b','S-03c','S-04','S-05','S-06','S-07']
            cps = ['S-01']
            for i, cp in enumerate(cps):
                cp_civil_name = "(" + cp.replace('-','') + ")"
                civil_workable_t = pd.read_excel(civil_workable_ms, sheet_name = cp_civil_name)
                civil_workable_t = civil_workable_t.iloc[:,[14,19,22,23,24,25,26,27,28,30,32,34,35,48,51]]
                ids = civil_workable_t.index[civil_workable_t.iloc[:, 0].str.contains(r'^P-',regex=True,na=False)]
                civil_workable_t = civil_workable_t.loc[ids[0]:, ]

                col_names = [pier_number_field,'via_construct_status','workability',
                            'util1','util2','util3','util4','util5','ISF_pnr','land','structure','pnr_station','others',
                            lot_id_field, struc_id_field] # 'lot_id','struc_id'

                for j, col in enumerate(col_names):
                    civil_workable_t = civil_workable_t.rename(columns={civil_workable_t.columns[j]: col})

                # create workable columns for pre-construction work
                new_cols = ['AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']
                for k, col in enumerate(new_cols):
                    civil_workable_t[col] = np.nan
                    # x[col] = x[col].astype(str)

                ## Clean column names
                # x[col_names[0]] = x[col_names[0]].replace(r'\s+|[^\w\s]','',regex=True)
                civil_workable_t[col_names[0]] = civil_workable_t[col_names[0]].replace(r'\s+','',regex=True)

                # Remove empty space
                ids = civil_workable_t.index[civil_workable_t[col_names[0]].isna()]
                civil_workable_t = civil_workable_t.drop(ids).reset_index(drop=True)

                civil_workable_t[cp_field] = cp

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
                with arcpy.da.SearchCursor(gis_workable_layer, [pier_number_field, new_cols[0]]) as cursor:
                    for row in cursor:
                        if row[1] == 2:
                            completed_piers.append(row[0])

                # from civil pier workable database
                id_workable_piers = civil_workable_t.index[civil_workable_t['workability'] == 'Workable']
                id_nonworkable_piers = civil_workable_t.index[civil_workable_t['workability'] == 'Non-workable']

                workable_piers = civil_workable_t.loc[id_workable_piers, pier_number_field].values
                nonworkable_piers = civil_workable_t.loc[id_nonworkable_piers, pier_number_field].values

                incomp_workable_piers = non_match_elements(workable_piers, completed_piers)
                incomp_nonworkable_piers = non_match_elements(nonworkable_piers, completed_piers)

                # Enter 1
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

                # Empty cell for AllWorkable = 0 (non-workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.1 LandWorkable
                # Note that when 'land' == 1, this automatically exlucdes workable and completed piers.
                ids = civil_workable_t.index[civil_workable_t['land'] == 1]

                land_nonwork_piers = civil_workable_t.loc[ids, pier_number_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[1], cp_field]) as cursor:
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
                ids = civil_workable_t.index[civil_workable_t['structure'] == 1]
                struc_nonwork_piers = civil_workable_t.loc[ids, pier_number_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[2], cp_field]) as cursor:
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
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].str.replace('\n',',')
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].replace(r'\s+','',regex=True)
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].str.upper()
                civil_workable_t[struc_id_field] = civil_workable_t[struc_id_field].replace(r'[(]PNR[)]','',regex=True)
                
                ids_nonna = civil_workable_t.index[civil_workable_t['structure'] == 1]
                c_t2 = civil_workable_t.loc[ids_nonna, ]

                ### 2.3.2. identify any NLOs falling under the identified non-workable structures
                nlo_obstruc_piers = []
                for i in c_t2.index:
                    obstruc_struc_ids = c_t2.loc[i, struc_id_field]
                    test = [e for e in gis_nlo_t[struc_id_field] if e in obstruc_struc_ids.split(',')]
                    if len(test) > 0:
                        # idenfity pier numbers with obstructing NLOs
                        nlo_obstruc_piers.append(civil_workable_t.loc[i, pier_number_field])
                
                ### 2.3.3. Enter NLOWorkable = 0 with identified pier numbers
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[3], cp_field]) as cursor:
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
                ids = civil_workable_t.index[(civil_workable_t['util1'] == 1) | 
                                            (civil_workable_t['util2'] == 1) | 
                                            (civil_workable_t['util3'] == 1) | 
                                            (civil_workable_t['util4'] == 1)| 
                                            (civil_workable_t['util5'] == 1)]
                util_obstruc_piers = civil_workable_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[4],cp_field]) as cursor:
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
                ids = civil_workable_t.index[civil_workable_t['others'] == 1]
                others_obstruc_piers = civil_workable_t.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, new_cols[5], cp_field]) as cursor:
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
                arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(gis_via_dir, "SC_Workable_Pier.xlsx"))

        Workable_Pier_Table_Update()

class UpdatePierPointLayer(object):
    def __init__(self):
        self.label = "6. Update Pier Layer (Point)"
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
            new_point_layer = 'SC_new_Pier_Point'
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

class ReSortGISTable(object):
    def __init__(self):
        self.label = "(Optional) Re-Sort GIS Attribute Table (SC Viaduct)"
        self.description = "(Optional) Re-Sort GIS Attribute Table (SC Viaduct)"

    def getParameterInfo(self):
        gis_layer = arcpy.Parameter(
            displayName = "GIS Attribute Table (SC Viaduct)",
            name = "GIS Attribute Table (SC Viaduct)",
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
                                pier_s = re.search(r"^BUE-P.*[SN]?$|^SCT.*[SN]?$|^PR.*[SN]?$|^P.*[SN]?$|^MT.*[SN]?$|^STR.*[SN]?$|^DAT.*[SN]?$",str(row[0])).group()
                            except AttributeError:
                                pier_s = re.search(r"^BUE-P.*[SN]?$|^SCT.*[SN]?$|^PR.*[SN]?$|^P.*[SN]?$P|^MT.*[SN]?$|^STR.*[SN]?$|^DAT.*[SN]?$",str(row[0]))
                            
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

class CheckUpdatesCivilGIS(object):
    def __init__(self):
        self.label = "7. Check Update between Civil and GIS Maser List (SC Viaduct)"
        self.description = "Check Update between Civil and GIS Maser List (SC Viaduct)"

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


        params = [gis_dir, gis_ml, civil_ml]
        return params
    
    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_ml = params[1].valueAsText
        civil_ml = params[2].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        civil_table = pd.ExcelFile(os.path.join(gis_dir,civil_ml))
        sheet_names = ['BoredPile', 'PileCap', 'Pier', 'PierHead', 'Precast']

########################
        # idx = table.index[~table[civil_pier_field].isna()]
        # table = table.loc[idx, ].reset_index(drop=True)
        # table['temp'] = table[civil_pier_field].str.replace(r'[^P]','',regex=True) # Remove all letters except for 'P'
        # idx = table.index[table['temp'] != 'PP']
        # table = table.loc[idx, ]
###############################################
        # 1. GIS ML: Count for completed viaduct components
        y = pd.read_excel(os.path.join(gis_dir,gis_ml))

        type_field = 'Type'
        status_field = 'Status'
        cp_field = 'CP'
        count_field = 'count'

        ## query
        gis_t = y.query(f"{status_field} == 4")
        gis_sum = gis_t.groupby([cp_field,type_field,status_field])[status_field].count().reset_index(name=count_field)
        
        # 2. Civil ML: Count for completed viaduct components
        cp_name = {
            "1": "S-01",
            "2": "S-02",
            "3a": "S-03a",
            "3b": "S-03b",
            "3c": "S-03c",
            "4": "S-04",
            "5": "S-05",
            "6": "S-06",
        }

        pier_field = 'Pier'
        finish_actual_field = 'finish_actual'
        cp_field_civil = 'Package'
        id_field = 'ID'
        no_field = 'No'

        civil_sum = pd.DataFrame({cp_field:[],type_field:[],status_field:[],'count':[]} )

        for i, sheet in enumerate(sheet_names):
            x = pd.read_excel(os.path.join(gis_dir,civil_ml),sheet_name=sheet)
            idx = x.index[~x[pier_field].isna()]
            x = x.loc[idx, ].reset_index(drop=True)
            x['temp'] = x[pier_field].str.replace(r'[^P]','',regex=True) # Remove all letters except for 'P'
            idx = x.index[x['temp'] != 'PP']
            x = x.loc[idx, ]
            
            if i == 0:
                x = x.loc[1:,[pier_field,no_field,cp_field_civil,finish_actual_field]]
            else:
                x = x.loc[1:,[pier_field,cp_field_civil,finish_actual_field]]
            
            # "---------------------------------------------------------------------------------------"
            # 1. Summary statistics:
            # Re-formata 'Package'
            x[cp_field_civil] = x[cp_field_civil].astype(str)
            x[cp_field_civil] = x[cp_field_civil].replace(r'/s+','',regex=True)
            
            # Remove 'S' or 'S0'
            x[cp_field_civil] = x[cp_field_civil].replace(r'S|S0|0|.0','',regex=True)
            x = x.query(f"{finish_actual_field}.notna()").reset_index(drop=True)
            x[status_field] = 4
            x[type_field] = i + 1
            
            x = x.assign(CP=x.Package.map(cp_name))
            x_sum = x.groupby([cp_field,type_field,status_field])[status_field].count().reset_index(name='count')
            civil_sum = civil_sum._append(x_sum,ignore_index=True)
            
            # "-----------------------------------------------------------------------------------------
            # 2. Non-Matched Piers
            if i == 0:
                x[no_field] = x[no_field].astype(str)
                x[id_field] = x[pier_field] + "-" + x[no_field] + "-1"
            else:
                x[id_field] = x[pier_field] + "-" + str(i+1)
            
            ## Delete unnecessary columns
            drop_columns = x.columns[x.columns.str.contains(r'^Unname',regex=True,na=False)]
            x = x.drop(columns=drop_columns)
            
            ## Get pier ID
            civil_id = x.loc[:,'ID'].values.tolist()
            
            # 2. GIS ML
            ## Filter
            gis_fil = y.query(f"{status_field} == 4 & {type_field} == {i+1}")

            # Get pier ID
            gis_id = gis_fil.loc[:,'ID'].values.tolist()
            
            # 3. Non-matched pier
            non_matched_piers = [e for e in civil_id if e not in gis_id]
            arcpy.AddMessage(f"For {sheet_names[i]}, there are {len(civil_id)} completed cases in Civil ML. Your GIS master list has the following missing piers: {non_matched_piers}")

            # Merge
            count_name_civil = 'Civil'
            count_name_gis = 'GIS'
            merged_t = pd.merge(left=civil_sum,right=gis_sum,how='left',left_on=[cp_field,type_field],right_on=[cp_field,type_field])
            merged_t = merged_t.rename(columns={'count_x':count_name_civil,'count_y':count_name_gis})
            merged_t['Difference'] = merged_t[count_name_civil] - merged_t[count_name_gis]
            merged_t = merged_t.drop(columns=['Status_x','Status_y'])
        arcpy.AddMessage(merged_t)




        