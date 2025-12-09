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
                      UpdateWorkablePierLayer, UpdatePierPointLayer, UpdateStripMapLayer,
                      ReSortGISTable, CheckUpdatesCivilGIS]

class UpdateExcelML(object):
    def __init__(self):
        self.label = "1. Update GIS Excel ML (SC Viaduct)"
        self.description = "1. Update GIS Excel ML (SC Viaduct)"

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
            displayName = "SC Viaduct Civil ML (Excel)",
            name = "SC Viaduct Civil ML (Excel)",
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
            gis_table0 = pd.read_excel(gis_ml, keep_default_na=False)

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
                    # idx = civil_table.index[~civil_table[civil_pier_field].isna()]
                    # civil_table = civil_table.loc[idx, ].reset_index(drop=True)
                    # civil_table['temp'] = civil_table[civil_pier_field].str.replace(r'[^P]','',regex=True) # Remove all letters except for 'P'
                    # idx = civil_table.index[civil_table['temp'] != 'PP']
                    # civil_table = civil_table.loc[idx, ]

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
                ### 2.2.1. Clean 'P-' to 'P'
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
                # final_table[pier_field] = final_table[pier_field].str.replace(r'P','P-',regex=True)
                # final_table[pier_field] = final_table[pier_field].str.replace(r'P-R','PR',regex=True)

                ## join back original PierNumber
                temp = gis_table0.loc[:, ['uniqueID','PierNumber']]
                final_table = pd.merge(left=final_table, right=temp, how='left', left_on=unique_id, right_on=unique_id)
                final_table = final_table.drop('PierNumber_x',axis=1)
                final_table = final_table.rename(columns={'PierNumber_y': pier_field})

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
            displayName = "SC Pier Workability Directory",
            name = "SC Pier Workability Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

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

        pier_number_layer = arcpy.Parameter(
            displayName = "SC Pier Layer (Point)",
            name = "SC Pier Layer (Point)",
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

        ####### Pier Workability Status 
        # 0 = 'Workable'
        # 1 = 'Non-workable'
        # 2 = Completed (construction)

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
        arcpy.conversion.TableToExcel(via_layer, os.path.join(workable_dir, "SC_Viaduct_ML.xlsx"))

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

class UpdateWorkablePierLayer(object):
    def __init__(self):
        self.label = "4. Update Pier Workability Tracker (Excel) & Layer (Polygon)"
        self.description = "Update Pier Workability Tracker (Excel) & Layer (Polygon)"

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

        gis_nlo_ms = arcpy.Parameter(
            displayName = "SC Structure NLO (ISF) ML (Excel)",
            name = "SC Structure NLO (ISF) ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        params = [gis_viaduct_dir, civil_workable_ms, gis_workable_layer, gis_nlo_ms]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        pier_workability_dir = params[0].valueAsText
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

            def remove_empty_strings(string_list):
                return [string for string in string_list if string]

            def unlist_brackets(nested_list):
                return [item for sublist in nested_list for item in sublist]

            def flatten_extend(matrix):
                flat_list = []
                for row in matrix:
                    row = [re.sub(r'\s+','',e) for e in row]
                    flat_list.extend(row)
                return flat_list
            
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
                for col in df.columns:
                    for idx, value in df[col].items():
                        if isinstance(value, str) and search_word in value.title():
                            locations.append({'index': idx, 'column': col})
                return locations
            
            def find_word_location2(df, search_word):
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
                for col in df.columns:
                    for idx, value in df[col].items():
                        if isinstance(value, str) and search_word in value:
                            locations.append({'index': idx, 'column': col})
                return locations

            def get_column_indices(df, column_names):
                """
                Extracts the indices of columns with matching names in a Pandas DataFrame.

                Args:
                    df (pd.DataFrame): The input DataFrame.
                    column_names (list): A list of column names to search for.

                Returns:
                    list: A list of indices of the matched columns.
                            Returns an empty list if no matching columns are found.
                """

                indices = []
                for col_name in column_names:
                    if col_name in df.columns:
                        indices.append(df.columns.get_loc(col_name))
                return indices
            
            # Read as xlsx
            # gis_via_t = pd.read_excel(gis_via_ms)
            gis_nlo_t = pd.read_excel(gis_nlo_ms)
            # civil_workable_t = pd.read_excel(civil_workable_ms,sheet_name='(S01)',skiprows=3)

            # List of fields
            cp_field = 'CP'
            type_field = 'Type'
            status_field = 'Status'
            pier_number_field = 'PierNumber'
            workability_field = 'Workability'
            unique_id_field = 'uniqueID'
            lot_id_field = 'LotID'
            struc_id_field = 'StrucID'
            utility_field = 'Utility'
            others_field = 'Others'
            land_field = 'Land'
            struc_field = 'Structure'
            land1_field = 'Land.1'
            struc1_field = 'Structure.1'
            nlo_field = 'NLO'
            remarks_field = 'Remarks'

            # 1. Clean fields
            ## cps = ['S-01','S-02','S-03a','S-03b','S-03c','S-04','S-05','S-06','S-07']
            cps = ['S-01', 'S-02', 'S-03a', 'S-03c','S-04','S-05','S-06']
            civil_t = pd.DataFrame()

            ####################################################
            # A. Update Pier Workability Tracker table #########
            ####################################################

            for i, cp in enumerate(cps):
                arcpy.AddMessage(f"Contract Package: {cp}")
                cp_civil_name = "(" + cp.replace('-','') + ")"
                civil_workable_t = pd.read_excel(civil_workable_ms, sheet_name = cp_civil_name)

                new_cols = [cp_field,
                            pier_number_field,
                            workability_field,
                            utility_field,
                            others_field,
                            land_field,
                            struc_field,
                            nlo_field,
                            land1_field,
                            struc1_field,
                        ]
                
                # Search the first column 'IFC Designation'
                loc = find_word_location(civil_workable_t,'Chainage')
                idx_chainage = loc[0]['index']
                col_chainage = loc[0]['column']

                # Search the next column 'STATUS"
                loc = find_word_location(civil_workable_t,'Status')
                idx_status = loc[0]['index']
                col_status = loc[0]['column']

                # Search the next column 'Others"
                loc = find_word_location2(civil_workable_t,'Others')
                idx_others = loc[0]['index']
                col_others = loc[0]['column']

                # Search the next column 'Remarks'
                loc = find_word_location2(civil_workable_t, '# of Lots')
                idx_lot = loc[0]['index']
                col_lot = loc[0]['column']
                print(loc)

                # Search the last column 'Structures'
                loc = find_word_location2(civil_workable_t, '# of Structures')
                idx_struc = loc[0]['index']
                col_struc = loc[0]['column']
                print(loc)

                # Extract column indices with all the searched words
                ## First identify utility columns
                sc_util_cols = [
                    {
                        'S-01': ['Meralco','Telco Line','Drainage','Canal','Waterline'],
                        'S-02': ['NGCP POLE', 'Maynilad', 'Meralco', 'ETPI'],
                        'S-03a': ['NGCP POLE', 'Maynilad', 'Meralco', 'ETPI'],
                        'S-03c': ['NGCP POLE', 'Maynilad', 'Meralco', 'ETPI'],
                        'S-04': ['NGCP POLE', 'Maynilad', 'Meralco', 'ETPI'],
                        'S-05': ['NGCP', 'ETPI', 'Maynilad', 'Meralco', 'Telco'],
                        'S-06': ['ETPI', 'Maynilad', 'Meralco / Telcom']
                    }
                ]

                util_cols = []
                for util in sc_util_cols[0][cp]:
                    if cp == 'S-05' and util == 'NGCP':
                        col = {'index': 1, 'column': 'Unnamed: 23'}
                        util_cols.append(col['column'])
                    else:
                        col = find_word_location2(civil_workable_t, util)
                        util_cols.append(col[0]['column'])

                idx_cols = get_column_indices(civil_workable_t, [col_chainage, col_status] + util_cols + [col_others, col_lot, col_struc])
                idx_cols[0] = idx_cols[0]-1 # PierNumber
                idx_cols[-2] = idx_cols[-2] + 1 # Lots
                idx_cols[-1] = idx_cols[-1] + 1 # Structures
                x = civil_workable_t.iloc[idx_status:, idx_cols].reset_index(drop=True)

                # Rename columns
                for i, util in enumerate(util_cols):
                    x = x.rename(columns={util: 'util' + str(i)})
                arcpy.AddMessage("5.ok")

                # Rename 'PierNumber', 'Workability', 'Others', 'Land.1', 'Structure.1'
                col_names = [pier_number_field, workability_field, others_field, land1_field, struc1_field]
                for i, idx in enumerate([0, 1, len(util_cols)+2, len(util_cols)+3, len(util_cols)+4]):
                    x = x.rename(columns={x.columns[idx]: col_names[i]})
                arcpy.AddMessage("6.ok")

                # Remove rows
                idx = x.index[x[pier_number_field].str.contains(r'^P-',regex=True,na=False)]
                x = x.drop(x.index[0:idx[0]]).reset_index(drop=True)
                x = x.drop(x.index[x[pier_number_field].isna()]).reset_index(drop=True)
                arcpy.AddMessage("7.ok")

                col_utils = x.columns[x.columns.str.contains(r'^util.*',regex=True)]
                # for i, util in enumerate(col_utils):
                #     idx = x.index[x[util].isna()]
                    # x.loc[idx, util] = 0
                    # x[util] = pd.to_numeric(x[util], errors='coerce').astype('int64')

                for col in col_utils:
                    x[col] = x[col].astype(str).str.replace(r'[()]', '', regex=True)
                    x[col] = x[col].replace(['N/A', 'n/a', '-', '--', '', ' ', 'NaN', 'nan', 'null', 'NULL'], np.nan)
                    
                x[col_utils] = x[col_utils].apply(pd.to_numeric, errors='coerce')
                x[utility_field] = x.loc[:, col_utils].sum(axis=1)
                idx = x.index[x[utility_field] > 0]
                x.loc[idx, utility_field] = 1
                idx = x.index[x[utility_field] == 0]
                x.loc[idx, utility_field] = np.nan

                ## 1. 'Workability' = Workable => Null
                idx = x.index[x[workability_field] == 'Workable']
                for field in [utility_field,land_field,land1_field,struc_field,struc1_field,others_field]:
                    x.loc[idx, field] = np.nan
     
                ## 2. Enter 2 for 'Completed' pier numbers
                completed_piers = []
                with arcpy.da.SearchCursor(gis_workable_layer, [pier_number_field, 'AllWorkable']) as cursor:
                    for row in cursor:
                        if row[1] == 2:
                            completed_piers.append(row[0])

                idx = x.index[x[pier_number_field].isin(completed_piers)]
                x.loc[idx, workability_field] = 'Completed'
               
                ## Delete any words other than IDs
                idx = x.index[x[land1_field].str.contains(r'^No l.*|^No s.*|^Lot.*|^lot.*',regex=True,na=False)]
                x.loc[idx, land1_field] = np.nan

                idx = x.index[~x[land1_field].isna()]
                x.loc[idx, land_field] = 1

                x[land1_field] = x[land1_field].astype(str)
                x[land1_field] = x[land1_field].str.replace(r'\n',',',regex=True)
                x[land1_field] = x[land1_field].str.replace(r';',',',regex=True)
                x[land1_field] = x[land1_field].str.replace(r';;',',',regex=True)
                x[land1_field] = x[land1_field].str.replace(r',,',',',regex=True)
                x[land1_field] = x[land1_field].str.replace(r',,,',',',regex=True)
                x[land1_field] = x[land1_field].str.replace(r',$','',regex=True)
                x[land1_field] = x[land1_field].str.replace(r'nan','',regex=True)
                x[land1_field] = x[land1_field].str.replace(r'\s+','',regex=True)
                x[land1_field] = x[land1_field].str.upper()
                x[land1_field] = x[land1_field].replace(r'[(]PNR[)]','',regex=True)
                x[land1_field] = x[land1_field].str.lstrip(',') # remove leading comma
                x[land1_field] = x[land1_field].str.rstrip(',') # remove leading comma
                arcpy.AddMessage("9.ok")

                ### Extract obstructing LotIDs
                x1 = x.dropna(subset=[land1_field]).reset_index(drop=True)
                x1[land1_field] = x1[land1_field].astype(str)
                lot_ids = flatten_extend(x1[land1_field].str.split(","))
                x_lot_ids = unique(lot_ids)
                x_lot_ids = remove_empty_strings(x_lot_ids)

                ## Delete any words other than IDs
                idx = x.index[x[struc1_field].str.contains(r'^No l.*|^No s.*|^Lot.*|^lot.*',regex=True,na=False)]
                x.loc[idx, struc1_field] = np.nan

                idx = x.index[~x[struc1_field].isna()]
                x.loc[idx, struc_field] = 1

                x[struc1_field] = x[struc1_field].astype(str)
                x[struc1_field] = x[struc1_field].str.replace(r'\n',',',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r';',',',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r';;',',',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r',,',',',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r',,,',',',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r',$','',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r'nan','',regex=True)
                x[struc1_field] = x[struc1_field].str.replace(r'\s+','',regex=True)
                x[struc1_field] = x[struc1_field].replace(r'[(]PNR[)]','',regex=True)
                x[struc1_field] = x[struc1_field].str.lstrip(',') # remove leading comma
                x[struc1_field] = x[struc1_field].str.rstrip(',') # remove leading comma

                x1 = x.dropna(subset=[struc1_field]).reset_index(drop=True)
                x1[struc1_field] = x1[struc1_field].astype(str)
                struc_ids = flatten_extend(x1[struc1_field].str.split(","))
                x_struc_ids = unique(struc_ids)
                x_struc_ids = remove_empty_strings(x_struc_ids)  

                ## Utility
                x1 = x.query(f"{utility_field} > 0").reset_index(drop=True)
                util_piers = x1[pier_number_field].values
                util_obstruc_piers = unique(util_piers)
                util_obstruc_piers = remove_empty_strings(util_obstruc_piers)

                ## Others
                x1 = x.query(f"{others_field} > 0").reset_index(drop=True)
                others_piers = x1[pier_number_field].values
                others_obstruc_piers = unique(others_piers)
                others_obstruc_piers = remove_empty_strings(others_obstruc_piers)

                ## NLO
                # Get all strucIDs from NLO master list
                nlo_piers = unique(gis_nlo_t[struc_id_field])

                # Inspect the Pier Tracker ML contains the above strucIDs
                nlo_piers_join = ("|").join(nlo_piers)
                idx = x.index[x[struc1_field].str.contains(nlo_piers_join,regex=True,na=False)]
                x.loc[idx, nlo_field] = 1
                # x.loc[x.index[x[nlo_field].isna()], nlo_field] = 0
                # x[nlo_field] = x[nlo_field].astype(int)

                # Final civil_workable_t
                x[cp_field] = cp
                x[pier_number_field] = x[pier_number_field].replace(r'\s+','',regex=True)
                x = x.loc[:, new_cols]

                # Replace empty strings with NaN
                ### else .isna() does not work 
                x = x.replace('^\s*$', np.nan, regex=True)

                ### Compile for all the packages for subsequent operation
                civil_t = pd.concat([civil_t, x]).reset_index(drop=True)

                ######################################################################################
                # B. Update Pier Workable Layer using pier tracker table (derived from Civil table) ##
                ######################################################################################

                ## 1. Workable Pile Cap
                ## Status of Workable Pier
                ### 1: Non-Workable
                ### 0: Workable (i.e, construction is incomplete)
                ### 2: Completed

                ### 1.2. Workable Pile Cap
                id_workable_piers = x.index[x[workability_field] == 'Workable']
                incomp_workable_piers = x.loc[id_workable_piers, pier_number_field].values
  
                # Enter 0
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(incomp_workable_piers) and row[7] == cp:
                            row[1] = 0
                            row[2] = 0
                            row[3] = 0
                            row[4] = 0
                            row[5] = 0
                            row[6] = 0
                        cursor.updateRow(row)

                # Empty cell for AllWorkable = 1 (non-workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'AllWorkable',cp_field]) as cursor:
                    for row in cursor:
                        # if row[1] is None and row[2] == cp:
                        if row[1] is None and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                ## 2.1 LandWorkable
                # Note that when 'land' == 1, this automatically exlucdes workable and completed piers.
                ids = x.index[x[land_field] == 1]

                land_nonwork_piers = x.loc[ids, pier_number_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, 'LandWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(land_nonwork_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'LandWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.2 StrucWorkable
                ids = x.index[x[struc_field] == 1]
                struc_nonwork_piers = x.loc[ids, pier_number_field].values
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, 'StrucWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(struc_nonwork_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'StrucWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.3 NLOWorkable
                ids = x.index[x[nlo_field] == 1]
                nlo_nonwork_piers = x.loc[ids, pier_number_field].values
                
                ### 'Non-workable' (1)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, 'NLOWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(nlo_nonwork_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)


                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'NLOWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.4. UtilWorkable
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, 'UtilWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(util_obstruc_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'UtilWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp:
                            row[1] = 0
                        cursor.updateRow(row)

                ## 2.5. OthersWorkable 
                ids = x.index[x[others_field] == 1]
                others_obstruc_piers = x.loc[ids, pier_number_field]
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, 'OthersWorkable', cp_field]) as cursor:
                    for row in cursor:
                        if row[0] in tuple(others_obstruc_piers) and row[2] == cp:
                            row[1] = 1
                        cursor.updateRow(row)

                # Empty cell = 0 (workable)
                with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field,'OthersWorkable',cp_field]) as cursor:
                    for row in cursor:
                        if row[1] is None and row[2] == cp: # if row[1] is None and row[2] == cp: # 

                            row[1] = 0
                        cursor.updateRow(row)

                ## Export this layer to excel
                #arcpy.conversion.TableToExcel(gis_workable_layer, os.path.join(pier_workability_dir, "SC_Pier_Workability_GIS_Portal.xlsx"))

                ## Final tweak
                ### When 'AllWorkable' = 2, the other fields ('LandWorkable', 'StrucWorkable', 'NLOWorkable', 'UtilWorkable', 'OthersWorkable') must be 2.
                ### We need this process, as the construction of some pile caps is completed, but these piers are sometimes entered with obstructing IDs in the Civil Team's table.
                with arcpy.da.UpdateCursor(gis_workable_layer, ['Type', 'Status', 'AllWorkable','LandWorkable','StrucWorkable','NLOWorkable', 'UtilWorkable', 'OthersWorkable']) as cursor:
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

            ##################### Identify incosistent data entry ###############################
            ## Add case of errors to Remarks field;
            ## 1. Completed and Workable piers have obstructions (in Utility, Land, Structure, Others, Land.1, Structure.1)
            ## 2. Non-workable piers have empty cells in Utility, Land, Structure, Others, Land.1, Structure.1.
            ## 3. Piers with obstructing Land (1) or Structure (1) do not have any IDs in Land.1 or Structure.1 field.
            ## 4. Piers with obstructing Lot or Structure IDs in Land.1 or Structure.1 field do not have '1' in Land or Structure field.
            civil_t[remarks_field] = np.nan
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

            obstruc_fields_notna = ((~civil_t[utility_field].isna()) |
                                    (~civil_t[land_field].isna()) |
                                    (~civil_t[struc_field].isna()) |
                                    (~civil_t[others_field].isna()) |
                                    (~civil_t[land1_field].isna()) |
                                    (~civil_t[struc1_field].isna()))
            
            obstruc_fields_na = ((civil_t[utility_field].isna()) &
                        (civil_t[land_field].isna()) &
                        (civil_t[struc_field].isna()) &
                        (civil_t[others_field].isna()) &
                        (civil_t[land1_field].isna()) &
                        (civil_t[struc1_field].isna()))

            ### Case 1:
            idx = civil_t.index[((civil_t[workability_field] == 'Completed') | (civil_t[workability_field] == 'Workable')) & 
                                    obstruc_fields_notna]
            civil_t.loc[idx, remarks_field] = error_descriptions[0]['case1']

            ### Case 2:
            idx = civil_t.index[(civil_t[workability_field] == 'Non-workable') &
                                    obstruc_fields_na]
            civil_t.loc[idx, remarks_field] = error_descriptions[0]['case2']

            ### Case 3:
            idx = civil_t.index[((civil_t[workability_field] == 'Non-workable') & (civil_t[land_field] == 1)) &
                                    (civil_t[land1_field].isna())]
            civil_t.loc[idx, remarks_field] = error_descriptions[0]['case3']

            ### Case 4:
            idx = civil_t.index[((civil_t[workability_field] == 'Non-workable') & (civil_t[struc_field] == 1)) &
                                    (civil_t[struc1_field].isna())]
            civil_t.loc[idx, remarks_field] = error_descriptions[0]['case4']

            ### Case 5:
            idx = civil_t.index[((civil_t[workability_field] == 'Non-workable') & (~civil_t[land1_field].isna())) &
                                    (civil_t[land_field].isna())]
            civil_t.loc[idx, remarks_field] = error_descriptions[0]['case5']

            ### Case 6:
            idx = civil_t.index[((civil_t[workability_field] == 'Non-workable') & (~civil_t[struc1_field].isna())) &
                                    (civil_t[struc_field].isna())]
            civil_t.loc[idx, remarks_field] = error_descriptions[0]['case6']

            ## Final Tweak
            ### When 'AllWorkable' = 2, the other fields ('LandWorkable', 'StrucWorkable', 'NLOWorkable', 'UtilWorkable', 'OthersWorkable') must be 2.
            ### We need this process, as the construction of some pile caps is completed, but these piers are sometimes entered with obstructing IDs in the Civil Team's table.
            idx = civil_t.index[(civil_t[workability_field] == "Completed") & ((civil_t[land_field] == 1) | (civil_t[struc_field] == 1) | (civil_t[utility_field] == 1) | (civil_t[nlo_field] == 1) | (civil_t[others_field] == 1))]
            civil_t.loc[idx, land_field] = np.nan
            civil_t.loc[idx, land1_field] = np.nan
            civil_t.loc[idx, struc_field] = np.nan
            civil_t.loc[idx, struc1_field] = np.nan
            civil_t.loc[idx, utility_field] = np.nan
            civil_t.loc[idx, nlo_field] = np.nan
            civil_t.loc[idx, others_field] = np.nan

            civil_t.to_excel(os.path.join(pier_workability_dir, "SC_Pier_Workability_Tracker.xlsx"), index=False)

            ## Update Pier Workable Layer for 'Remarks'
            idx = civil_t.index[~civil_t[remarks_field].isna()]
            remarks_piers = civil_t.loc[idx, pier_number_field].values
            remarks_text = civil_t.loc[idx, remarks_field].values
            with arcpy.da.UpdateCursor(gis_workable_layer, [pier_number_field, remarks_field]) as cursor:
                for row in cursor:
                    if row[0] in tuple(remarks_piers):
                        # Find index of the subject pier numbers in a list (remarks_piers)
                        idx2 = [index for index, value in enumerate(remarks_piers) if value == row[0]][0]

                        # Use this index to extract the corresponding remarks
                        row[1] = remarks_text[idx2]
                    cursor.updateRow(row)
                        
        Workable_Pier_Table_Update()

class CheckPierNumbers(object):
    def __init__(self):
        self.label = "5. Check Pier Numbers between Civil and GIS Portal"
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

            # List of fields
            cp_field = 'CP'
            type_field = 'Type'
            pier_num_field = 'PierNumber'
            unique_id_field = 'uniqueID'
            pier_num_field_c = 'Pier No. (P)'
            lot_id_field = 'LotID'
            struc_id_field = 'StrucID'

            cps = ['S-01','S-02','S-03a','S-03c','S-04','S-05','S-06']
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
                # arcpy.AddMessage(f"GIS_Portal_Piers: {gis_piers}")
                
                ## SC Civil ML
                pier_workable_t = pd.read_excel(pier_tracker_ms)
                pier_t = pier_workable_t.query(f"{cp_field} == '{cp}'").reset_index(drop=True)
                civil_piers = pier_t[pier_num_field].values
                # arcpy.AddMessage(f"Civill_Piers: {civil_piers}")

                # 2. Comparing
                compile_t.loc[0, cols[0]] = cp

                ## 2.1. Civil vs GIS Portal
                compile_t.loc[0, cols[1]] = len(civil_piers)
                compile_t.loc[0, cols[2]] = len(gis_piers)
                compile_t.loc[0, cols[3]] = compile_t.loc[0, cols[1]] - compile_t.loc[0, cols[2]]
                nonmatch_piers = [e for e in civil_piers if e not in gis_piers]
                # [e for e in gis_piers if e not in civil_piers]
                # nonmatch_piers_all = [e for innerList in nonmatch_piers for e in innerList]

                arcpy.AddMessage(f"Non-matched piers: {nonmatch_piers}")
                compile_t.loc[0, cols[4]] = np.nan
                if len(nonmatch_piers) > 0:
                    compile_t.loc[0, cols[4]] = ",".join(nonmatch_piers)
                
                # Compile cps
                compile_all = pd.concat([compile_all, compile_t])
                compile_all = compile_all.loc[:, cols]
                arcpy.AddMessage("Table of Non-Matched Piers:")
                arcpy.AddMessage(compile_all)
            
            # Export
            compile_all.to_excel(os.path.join(pier_tracker_dir, '99-CHECK_SC_PierNumbers_Civil_vs_GISportal.xlsx'),
                                              index=False)

        Workable_Pier_Table_Update()

class UpdatePierPointLayer(object):
    def __init__(self):
        self.label = "6. Update Pier Layer (Point)"
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

class UpdateStripMapLayer(object):
    def __init__(self):
        self.label = "7. Update Strip Map Layer (Polygon)"
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

        workability_field_stripmap = 'Workability'

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
            ## 3.0. Empty all rows in 'Workability' field in strip map layer
            with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                for row in cursor:
                    if row[0] in ('Workable', 'Non-Workable', 'Completed'):
                        row[0] = None
                    cursor.updateRow(row)

            ## 3.1. Select pier point layer for each status in 'AllWorkable' field
            ### First, select rows with non-workable piers
            where_clause = "AllWorkable = 1"
            arcpy.management.SelectLayerByAttribute(pier_point_layer, 'NEW_SELECTION', where_clause)
            arcpy.management.SelectLayerByLocation(strip_map_layer, 'CONTAINS', pier_point_layer)
            with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                for row in cursor:
                    row[0] = "Non-Workable"
                    cursor.updateRow(row)

            ### Second, select rows with completed piers
            where_clause = "AllWorkable = 2"
            where_clause_stripmap = "Workability is null"
            arcpy.management.SelectLayerByAttribute(pier_point_layer, 'NEW_SELECTION', where_clause)
            arcpy.management.SelectLayerByAttribute(strip_map_layer, 'NEW_SELECTION', where_clause_stripmap)
            arcpy.management.SelectLayerByLocation(strip_map_layer, 'CONTAINS', pier_point_layer)
            with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                for row in cursor:
                    if row[0] == None:
                        row[0] = "Completed"
                    cursor.updateRow(row)

            ### Finally, select rows with workable piers
            where_clause = "AllWorkable = 0"
            where_clause_stripmap = "Workability is null"
            arcpy.management.SelectLayerByAttribute(pier_point_layer, 'NEW_SELECTION', where_clause)
            arcpy.management.SelectLayerByAttribute(strip_map_layer, 'NEW_SELECTION', where_clause_stripmap)
            arcpy.management.SelectLayerByLocation(strip_map_layer, 'CONTAINS', pier_point_layer)
            with arcpy.da.UpdateCursor(strip_map_layer, [workability_field_stripmap]) as cursor:
                for row in cursor:
                    if row[0] == None:
                        row[0] = "Workable"
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

class CheckUpdatesCivilGIS(object):
    def __init__(self):
        self.label = "(Optional) Check Update between Civil and GIS Maser List (SC Viaduct)"
        self.description = "(Optional) Check Update between Civil and GIS Maser List (SC Viaduct)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "SC Viaduct Directory",
            name = "SC Viaduct Directory",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        gis_ml = arcpy.Parameter(
            displayName = "SC Viaduct GIS ML (Excel)",
            name = "SC Viaduct GIS ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        civil_ml = arcpy.Parameter(
            displayName = "SC Viaduct Civil ML (Excel)",
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

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        civil_table = pd.ExcelFile(os.path.join(gis_dir,civil_ml))
        sheet_names = ['BoredPile', 'PileCap', 'Pier', 'PierHead', 'Precast']

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

            ## Delete unnecessary columns
            drop_columns = x.columns[x.columns.str.contains(r'^Unname',regex=True,na=False)]
            x = x.drop(columns=drop_columns)

            if i == 0: # for Bored Pile
                x = x.loc[1:,[pier_field,no_field,cp_field_civil,finish_actual_field]]
            else:
                x = x.loc[1:,[pier_field,cp_field_civil,finish_actual_field]]

            ## Delete rows with empty pier field
            idx = x.index[x[pier_field].isna()]
            x = x.drop(idx).reset_index(drop=True)

            ## Delete rows with ES
            ids = x.index[x[pier_field].str.contains(r'^ES', regex=True, na=False)]
            x = x.drop(ids).reset_index(drop=True)

            # "---------------------------------------------------------------------------------------"
            # 1. Summary statistics:
            # Re-formata 'Package'
            x[cp_field_civil] = x[cp_field_civil].astype(str)
            x[cp_field_civil] = x[cp_field_civil].replace(r'/s+','',regex=True)

            # Remove 'S' or 'S0'
            x[cp_field_civil] = x[cp_field_civil].replace(r'S|S0|0|.0','',regex=True)

            ## Keep only completed ones
            x = x.query(f"{finish_actual_field}.notna()").reset_index(drop=True)
            x[status_field] = 4
            x[type_field] = i + 1

            x = x.assign(CP=x.Package.map(cp_name))
            x_sum = x.groupby([cp_field,type_field,status_field])[status_field].count().reset_index(name='count')
            civil_sum = civil_sum._append(x_sum,ignore_index=True)
                
            # Create 'ID'
            # Bored Piles
            if i == 0: 
                x[no_field] = x[no_field].astype(str)
                x[no_field] = x[no_field].apply(lambda x: re.sub(r'.0', '', x))
                x[id_field] = x[pier_field] + "-" + x[no_field] + "-1"
            else:
                x[id_field] = x[pier_field] + "-" + str(i+1)
                x[id_field] = x[id_field].apply(lambda x: re.sub(r'P-', 'P', x))

            ## 2.2. Get pier ID
            civil_id = x[id_field].values          

            # 3. GIS ML
            ## Filter
            gis_fil = y.query(f"{status_field} == 4 & {type_field} == {i+1}").reset_index(drop=True)
            gis_id = gis_fil[id_field].values
   
            # 3. Non-matched pier
            non_matched_piers1 = [e for e in civil_id if e not in gis_id]
            non_matched_piers2 = [e for e in gis_id if e not in civil_id]
            non_matched_piers_all = non_matched_piers1 + non_matched_piers2
            arcpy.AddMessage(f"For {sheet_names[i]}, There are {len(non_matched_piers_all)} cases where the follwing completed piers do not match between Civil  and GIS ML: {non_matched_piers_all}")

            # Merge
            count_name_civil = 'Civil'
            count_name_gis = 'GIS'
            merged_t = pd.merge(left=civil_sum,right=gis_sum,how='left',left_on=[cp_field,type_field],right_on=[cp_field,type_field])
            merged_t = merged_t.rename(columns={'count_x':count_name_civil,'count_y':count_name_gis})
            merged_t['Difference'] = merged_t[count_name_civil] - merged_t[count_name_gis]
            erged_t = merged_t.drop(columns=['Status_x','Status_y'])

            ## Add remakrs for duplicated IDs in GIS ML
            merged_t['Remarks'] = np.nan
            idx = merged_t.index[merged_t['Difference'] < 0]
            if len(idx) > 0: # potentially duplicated IDs in the GIS table
                ids = gis_fil[id_field].duplicated()
                idx = ids.index[ids == True]
                duplicated_ids = gis_fil.loc[idx, id_field].values
                merged_t[idx, 'Remarks'] = duplicated_ids
        arcpy.AddMessage(merged_t)




        