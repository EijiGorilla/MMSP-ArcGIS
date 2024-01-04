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
        self.tools = [UpdateLot, UpdateISF, UpdateStructure, UpdateBarangay, UpdatePier, UpdateFGDB, UpdateSDE, UpdateUsingMasterList]

class UpdateLot(object):
    def __init__(self):
        self.label = "1.0. Update Excel Master List (Lot)"
        self.description = "Update Excel Master List (Lot)"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

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

        gis_bakcup_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Backup Directory",
            name = "GIS Masterlist Backup Directory",
            datatype = "DEWorkspace",
            parameterType = "Optional",
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
            displayName = "RAP SC1 Land Status ML for SC",
            name = "RAP SC1 Land Status for SC",
            datatype = "DEFile",
            parameterType = "Optional",
            direction = "Input"
        )

        lastupdate = arcpy.Parameter(
            displayName = "Date of last update (yyyymmdd) e.g., 20240101 for backup",
            name = "Date of last update (yyyymmdd) e.g., 20240101",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [ws, proj, gis_dir, gis_bakcup_dir, gis_lot_ms, rap_lot_ms, rap_lot_sc1_ms, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        ws = params[0].valueAsText
        proj = params[1].valueAsText
        gis_dir = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        gis_lot_ms = params[4].valueAsText
        rap_lot_ms = params[5].valueAsText
        rap_lot_sc1_ms = params[6].valueAsText
        lastupdate = params[7].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def N2SC_Land_Update():
            # Definitions
            if proj == 'N2':
                cp_suffix = 'N-'
            else:
                cp_suffix = 'S-'
            
            ## 1. Remove leading and trailing space for object columns
            def whitespace_removal(dataframe):
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
            
            ## 4. Return matched elements
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

            def rename_columns_title(table, search_names, renamed_word): # search_names are list, renamed_word is a string
                colname_change = table.columns[table.columns.str.contains('|'.join(search_names))]
                table = table.rename(columns={str(colname_change[0]): renamed_word})

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].apply(lambda x: x.title())
            
            rap_table = pd.read_excel(rap_lot_ms)
            gis_table = pd.read_excel(gis_lot_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Land_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Land_Status'))

            # Common query and definitions
            joinField = 'LotID'
            search_names_city = ['City/Municipality', 'City', 'Munici']
            renamed_city = 'Municipality'

           # SC1
            ## Join SC1 Lot to SC
            if proj == 'SC':
                try:
                    joinedFields = [joinField, 'ContSubm', 'Subcon', 'Priority1', 'Reqs']

                    rap_table_sc1 = pd.read_excel(rap_lot_sc1_ms)
                    
                    # Add contractors submission
                    rap_table_sc1['ContSubm'] = 1
                    
                    # Rename Municipality
                    colname_change = rap_table.columns[rap_table.columns.str.contains('|'.join(search_names_city))]
                    rap_table = rap_table.rename(columns={str(colname_change[0]): renamed_city})

                    colname_change = rap_table_sc1.columns[rap_table_sc1.columns.str.contains('|'.join(search_names_city))]
                    rap_table_sc1 = rap_table_sc1.rename(columns={str(colname_change[0]): renamed_city})

                    first_letter_capital(rap_table, [renamed_city])
                    first_letter_capital(rap_table, [renamed_city])

                    # Convert to numeric
                    to_numeric_fields = 'Priority1'
                    rap_table_sc1[to_numeric_fields] = rap_table_sc1[to_numeric_fields].replace(r'\s+|[^\w\s]', '', regex=True)
                    rap_table_sc1[to_numeric_fields] = pd.to_numeric(rap_table_sc1[to_numeric_fields])
                        
                    # Create Priority1_1 for web mapping purpose only
                    ## Unique priority values
                    uniques = unique(rap_table_sc1[to_numeric_fields].dropna())
                    new_priority_field = 'Priority1_1'
                    rap_table_sc1[new_priority_field] = None
                    for num in uniques:
                        id = rap_table_sc1.index[rap_table_sc1[to_numeric_fields] == num]
                        if num == 2:
                            rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'nd').replace('.0','')
                        elif num == 3:
                            rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'rd').replace('.0','')
                        else:
                            rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'st').replace('.0','')

                    # Filter fields
                    rap_table_sc1 = rap_table_sc1[joinedFields + [new_priority_field]]
                    rap_table = rap_table.drop(joinedFields[2:], axis=1)

                    # Left join
                    rap_table[joinField] = rap_table[joinField].astype(str)
                    rap_table_sc1[joinField] = rap_table_sc1[joinField].astype(str)
                    rap_table = pd.merge(left=rap_table, right=rap_table_sc1, how='left', left_on=joinField, right_on=joinField)

                    # Check if any missing LotID when joined
                    id = rap_table.index[rap_table['ContSubm'] == 1]
                    lotID_sc = unique(rap_table.loc[id,joinField])
                    lotID_sc1 = unique(rap_table_sc1[joinField])
                    non_match_LotID = non_match_elements(lotID_sc, lotID_sc1)
                    if (len(non_match_LotID) > 0):
                        print('LotIDs do not match between SC and SC1 tables.')

                except Exception:
                    arcpy.AddMessage('You did not select {0} master list for updating contractors submission status.'.format('SC1_Land_Status '))

            # Rename City for Municipality
            try:
                colname_change = rap_table.columns[rap_table.columns.str.contains('|'.join(search_names_city))]
                rap_table = rap_table.rename(columns={str(colname_change[0]): renamed_city})
            except:
                pass

            first_letter_capital(rap_table, [renamed_city])
            
            # Convert to numeric
            numeric_fields_common = ["TotalArea","AffectedArea","RemainingArea","HandedOverArea","HandedOver","Priority","StatusLA","MoA","PTE"]
            if proj == 'N2':
                to_numeric_fields = numeric_fields_common + ['Endorsed']
            else:
                to_numeric_fields = numeric_fields_common
            
            cols = rap_table.columns
            non_match_col = non_match_elements(to_numeric_fields, cols)
            [to_numeric_fields.remove(non_match_col[0]) if non_match_col else arcpy.AddMessage('no need to remove field from the list for numeric conversion')]

            for field in to_numeric_fields:
                rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
                rap_table[field] = pd.to_numeric(rap_table[field])
                
            # Conver to string
            to_string_fields = ["LotID", "CP"]
            toString(rap_table, to_string_fields)

            # Reformat CP
            if proj == 'N2':
                rap_table['CP'] = rap_table['CP'].str[-2:]       
                rap_table['CP'] = cp_suffix + rap_table['CP']
                
            # Conver to date   
            to_date_fields = ['HandOverDate','HandedOverDate']
            for field in to_date_fields:
                rap_table[field] = pd.to_datetime(rap_table[field],errors='coerce').dt.date
        
            ## Convert to uppercase letters for LandUse
            match_col = match_elements(cols, 'LandUse')
            if len(match_col) > 0:
                rap_table['LandUse'] = rap_table['LandUse'].apply(lambda x: x.upper())  

            # Add scale from old master list
            rap_table = rap_table.drop('Scale',axis=1)
            lot_gis_scale = gis_table[['Scale','LotID']]
            rap_table = pd.merge(left=rap_table, right=lot_gis_scale, how='left', left_on='LotID', right_on='LotID')

            # Check and Fix StatusLA, HandedOverDate, HandOverDate, and HandedOverArea
            ## 1. StatusLA =0 -> StatusLA = empty
            id = rap_table.index[rap_table['StatusLA'] == 0]
            rap_table.loc[id, 'StatusLA'] = None

            ## 2. HandedOver = 1 & !is.na(HandOverDate) -> HandedOverDate = HandOverDate
            id = rap_table.index[(rap_table['HandedOver'] == 1) & (rap_table['HandOverDate'].notna())]
            rap_table.loc[id, 'HandedOverDate'] = rap_table.loc[id, 'HandOverDate']
            rap_table.loc[id, 'HandOverDate'] = None

            ## 3. HandedOver = 0 & !is.na(HandedOverDate) -> HandedOverDate = empty
            id = rap_table.index[(rap_table['HandedOver'] == 0) & (rap_table['HandedOverDate'].notna())]
            rap_table.loc[id, 'HandedOverDate'] = None

           ## 4. if the first row is empty, temporarily add the first row for 'HandedOverDate' and 'HandOverDate'
            for field in to_date_fields:
                date_item = rap_table[field].iloc[:1].item()
                if date_item is None or pd.isnull(date_item):
                    rap_table.loc[0, field] = pd.to_datetime('1990-01-01')

            ## 5. is.na(HandedOverArea) -> HandedOverArea = 0
            id = rap_table.index[(rap_table['HandedOverArea'] == None) | (rap_table['HandedOverArea'].isna())]
            rap_table.loc[id, 'HandedOverArea'] = 0

            # Calculate percent handed-over
            rap_table['percentHandedOver'] = round((rap_table['HandedOverArea'] / rap_table['AffectedArea'])*100,0)
        
            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_lot_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

            arcpy.AddMessage("The master list was successfully exported.")

            ########################
            # ### Remove temporary date added
            # for field in to_date_fields:
            #     with arcpy.da.UpdateCursor(copyLot, [field]) as cursor:
            #         for row in cursor:
            #             if row[0]:
            #                 year = row[0].strftime("%Y")
            #                 if int(year) < 2000:
            #                     row[0] = None
            #                 else:
            #                     row[0] = row[0]
            #             cursor.updateRow(row)

            # ## Remove temporary date from the feature layer and master list excel table
            # for field in to_date_fields:
            #     field = 'HandedOverDate'
            #     id = rap_table.index[rap_table[field] == pd.to_datetime('1990-01-01')]
            #     rap_table.loc[id, field] = None
            # rap_table.to_excel(to_excel_file, index=False)

        N2SC_Land_Update()

class UpdateISF(object):
    def __init__(self):
        self.label = "1.1. Update Excel Master List (ISF)"
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

        gis_bakcup_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Backup Directory",
            name = "GIS Masterlist Backup Directory",
            datatype = "DEWorkspace",
            parameterType = "Optional",
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

        lastupdate = arcpy.Parameter(
            displayName = "Date of last update (yyyymmdd) e.g., 20240101 for backup",
            name = "Date of last update (yyyymmdd) e.g., 20240101",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_bakcup_dir, gis_isf_ms, rap_isf_ms, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_bakcup_dir = params[2].valueAsText
        gis_isf_ms = params[3].valueAsText
        rap_isf_ms = params[4].valueAsText
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
            
            ## 4. Return matched elements
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

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].apply(lambda x: x.title())
            
            ####################################################
            # Update Excel Master List Tables
            ####################################################
            if proj == 'N2':
                cp_suffix = 'N-'
            else:
                cp_suffix = 'S-'
        
            rap_table = pd.read_excel(rap_isf_ms)
            gis_table = pd.read_excel(gis_isf_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + proj + "_" + "ISF_Relocation_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format('ISF_Relocation_Status'))
            
            # Rename 'City' to Municipality
            renamed_city = 'Municipality'
            try:
                renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['City','city', 'Muni']))]
                rap_table = rap_table.rename(columns={str(renamed_col[0]): renamed_city})
                first_letter_capital(rap_table, [renamed_city])
            except:
                pass

            # Rename Barangay
            renamed_brgy = 'Barangay'
            try:
                renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['Bara','bara']))]
                rap_table = rap_table.rename(columns={str(renamed_col[0]): renamed_brgy})
                #first_letter_capital(rap_table, [renamed_brgy])
            except:
                pass

            # Make sure no space
            toString(rap_table, ['Municipality', 'Barangay', 'StrucID', 'CP'])

            # Reformat CP
            if proj == 'N2':
                rap_table['CP'] = rap_table['CP'].str[-2:]       
                rap_table['CP'] = cp_suffix + rap_table['CP']

            # Convert to numeric
            to_numeric_fields = ["StatusRC", "TypeRC", "HandOver"]
            cols = rap_table.columns
            non_match_col = non_match_elements(to_numeric_fields, cols)
            [to_numeric_fields.remove(non_match_col[0]) if non_match_col else print('no need to remove field from the list for numeric conversion')]

            for field in to_numeric_fields:
                rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
                rap_table[field] = pd.to_numeric(rap_table[field])

            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_isf_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

        N2SC_ISF_Update()

class UpdateStructure(object):
    def __init__(self):
        self.label = "1.2. Update Excel Master List (Structure)"
        self.description = "Update Excel Master List (Structure)"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

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

        gis_bakcup_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Backup Directory",
            name = "GIS Masterlist Backup Directory",
            datatype = "DEWorkspace",
            parameterType = "Optional",
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
            displayName = "RAP Structure Relocation Status ML (Excel)",
            name = "RAP Structure Relocation Status ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        lastupdate = arcpy.Parameter(
            displayName = "Date of last update (yyyymmdd) e.g., 20240101 for backup",
            name = "Date of last update (yyyymmdd) e.g., 20240101",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [ws, proj, gis_dir, gis_bakcup_dir, gis_struc_ms,
                  rap_struc_ms, rap_struc_sc1_ms, rap_relo_ms, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        ws = params[0].valueAsText
        proj = params[1].valueAsText
        gis_dir = params[2].valueAsText
        gis_bakcup_dir = params[3].valueAsText
        gis_struc_ms = params[4].valueAsText
        rap_struc_ms = params[5].valueAsText
        rap_struc_sc1_ms = params[6].valueAsText
        rap_relo_ms = params[7].valueAsText
        lastupdate = params[8].valueAsText

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
            
            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].apply(lambda x: x.title())
            
            ####################################################
            # Update Excel Master List Tables
            ####################################################
            rap_table = pd.read_excel(rap_struc_ms)
            rap_relo_table = pd.read_excel(rap_relo_ms)
            gis_table = pd.read_excel(gis_struc_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Land_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Land_Status'))
            
            # Common query and definitions
            joinField = 'StrucID'
            search_names_city = ['City/Municipality', 'City', 'Munici']
            renamed_city = 'Municipality'

            # SC
            if proj == 'SC':
                try:
                    arcpy.AddMessage("ok0")
                    joinedFields = [joinField, 'ContSubm', 'Subcon', 'BasicPlan']

                    arcpy.AddMessage("ok00")
                    rap_table_sc1 = pd.read_excel(rap_struc_sc1_ms)
                    
                    arcpy.AddMessage("ok1")
                    # Add contractors submission
                    rap_table_sc1['ContSubm'] = 1

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
                    id = rap_table.index[rap_table['ContSubm'] == 1]
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
            rap_table = rap_table.rename(columns={str(colname_change[0]): renamed_city})
                    
            first_letter_capital(rap_table, [renamed_city])

            # Convert to numeric
            to_numeric_fields = ["TotalArea","AffectedArea","RemainingArea","HandOver","StatusStruc","Status","MoA","PTE", "Occupancy"]
            cols = rap_table.columns
            non_match_col = non_match_elements(to_numeric_fields, cols)
            [to_numeric_fields.remove(non_match_col[0]) if non_match_col else print('no need to remove field from the list for numeric conversion')]

            for field in to_numeric_fields:
                rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
                rap_table[field] = pd.to_numeric(rap_table[field])
                
            # Conver to string
            common_fields = ["StrucID", "CP"]
            if proj == 'N2':
                to_string_fields = common_fields + ["StructureUse"]
            else:
                to_string_fields = common_fields
            toString(rap_table, to_string_fields)
            
            # Reformat CP
            rap_table['CP'] = rap_table['CP'].str[-2:]    
            rap_table['CP'] = cp_suffix + rap_table['CP']
        
            ## Convert to uppercase letters for StructureUse and StrucID
            try:
                uppercase_field = 'StructureUse'
                match_col = match_elements(cols, uppercase_field)
                if len(match_col) > 0:
                    rap_table[uppercase_field] = rap_table[uppercase_field].apply(lambda x: x.upper())
            except:
                 pass
            
            rap_table[joinField] = rap_table[joinField].apply(lambda x: x.upper())

            # Check and Fix StatusLA, HandedOverDate, HandOverDate, and HandedOverArea
            ## 1. StatusStruc =0 -> StatusStruc = empty
            status_field = 'StatusStruc'
            id = rap_table.index[rap_table[status_field] == 0]
            rap_table.loc[id, status_field] = None
            
            # Join the number of families to table
            rap_relo_table.dtypes
            rap_relo_table.head()
            toString(rap_relo_table, [joinField])
            rap_relo_table['FamilyNumber'] = 0
            df = rap_relo_table.groupby(joinField).count()[['FamilyNumber']]
            rap_table = pd.merge(left=rap_table, right=df, how='left', left_on=joinField, right_on=joinField)
            
            # MoA is 'No Need to Acquire' -> StatusStruc is null
            id = rap_table.index[(rap_table['MoA'] == 4) & (rap_table[status_field] >= 1)]
            rap_table.loc[id, status_field] = None
        
            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_struc_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

        N2SC_Structure_Update()

class UpdateBarangay(object):
    def __init__(self):
        self.label = "1.3. Update Barangay Excel Master List (SC1)"
        self.description = "Update Barangay Excel Master List (SC1)"

    def getParameterInfo(self):
        gis_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Storage Directory",
            name = "GIS master-list directory",
            datatype = "DEWorkspace",
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

        lastupdate = arcpy.Parameter(
            displayName = "Date of last update (yyyymmdd) e.g., 20240101 for backup",
            name = "Date of last update (yyyymmdd) e.g., 20240101",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [gis_dir, gis_bakcup_dir, gis_barangay_ms, rap_barangay_ms, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        gis_dir = params[0].valueAsText
        gis_bakcup_dir = params[1].valueAsText
        gis_barangay_ms = params[2].valueAsText
        rap_barangay_ms = params[3].valueAsText
        lastupdate = params[4].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True

        def SC1_Barangay_Update():
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
            
            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].apply(lambda x: x.title())
            
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
            first_letter_capital(rap_table, [renamed_city])

            # Rename Barangay
            renamed_brgy = 'Barangay'
            renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['Bgy','bgy']))]
            rap_table = rap_table.rename(columns={str(renamed_col[0]): renamed_brgy})
            first_letter_capital(rap_table, [renamed_brgy])

            # Make sure no space
            toString(rap_table, ['Municipality', 'Barangay', 'Subcon'])

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

class UpdatePier(object):
    def __init__(self):
        self.label = "1.4. Update Excel Master List (Pier)"
        self.description = "Update Excel Master List (Pier)"

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

        gis_bakcup_dir = arcpy.Parameter(
            displayName = "GIS Masterlist Backup Directory",
            name = "GIS Masterlist Backup Directory",
            datatype = "DEWorkspace",
            parameterType = "Optional",
            direction = "Input"
        )

        gis_pier_ms = arcpy.Parameter(
            displayName = "GIS Pier Number List ML (Excel)",
            name = "GIS Pier Number List ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        rap_pier_ms = arcpy.Parameter(
            displayName = "RAP Pier Number List ML (Excel)",
            name = "RAP Pier Number List ML (Excel)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        lastupdate = arcpy.Parameter(
            displayName = "Date of last update (yyyymmdd) e.g., 20240101 for backup",
            name = "Date of last update (yyyymmdd) e.g., 20240101",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [proj, gis_dir, gis_bakcup_dir, gis_pier_ms, rap_pier_ms, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_bakcup_dir = params[2].valueAsText
        gis_pier_ms = params[3].valueAsText
        rap_pier_ms = params[4].valueAsText
        lastupdate = params[5].valueAsText

        arcpy.env.overwriteOutput = True
        #arcpy.env.addOutputsToMap = True
        def N2SC_Pier_Update():
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
            
            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)

            def first_letter_capital(table, column_names): # column_names are list
                for name in column_names:
                    table[name] = table[name].apply(lambda x: x.title())
            
            ####################################################
            # Update Excel Master List Tables
            ####################################################
            if proj == 'N2':
                cp_suffix = 'N-'
            else:
                cp_suffix = 'S-'
        
            rap_table = pd.read_excel(rap_pier_ms)
            gis_table = pd.read_excel(gis_pier_ms)

            # Create backup files
            try:
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + proj + "_" + "Pier_Land.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format('Pier_Land Table'))
            
            # Rename 'City' to Municipality
            renamed_city = 'Municipality'
            try:
                renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['City','city', 'Muni']))]
                rap_table = rap_table.rename(columns={str(renamed_col[0]): renamed_city})
                first_letter_capital(rap_table, [renamed_city])
            except:
                pass       
            
            # Convert Pier column name to upper case
            try:
                renamed_col = rap_table.columns[rap_table.columns.str.contains('|'.join(['pier','Pier', 'PIER']))]
                rap_table = rap_table.rename(columns={str(renamed_col[0]): "PIER"})
            except:
                pass

            # Make sure no space
            toString(rap_table, ['Municipality', 'PIER', 'CP'])

            # CP to upper case
            rap_table['CP'] = rap_table['CP'].apply(lambda x: x.upper())  

            # Reformat CP
            if proj == 'N2':
                rap_table['CP'] = rap_table['CP'].str[-2:]       
                rap_table['CP'] = cp_suffix + rap_table['CP']

            # check match between RAP and GIS
            pier_rap = unique(rap_table['PIER'])
            pier_gis = unique(gis_table['PIER'])
            non_match_piers = non_match_elements(pier_rap, pier_gis)
            if (len(non_match_piers) > 0):
                print('Pier Numbers do not match between GIS excel ML and RAP excel ML.')

            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_pier_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

        N2SC_Pier_Update()

class UpdateFGDB(object):
    def __init__(self):
        self.label = "2. Update GIS Attribute Tables"
        self.description = "Update feature layers for land, structure, and ISF of N2/SC"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Feature Layers
        in_lot = arcpy.Parameter(
            displayName = "Status of Lot (Polygon)",
            name = "Status of Lot (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_structure = arcpy.Parameter(
            displayName = "Status of Structure (Polygon)",
            name = "Status of Structure (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_occupancy = arcpy.Parameter(
            displayName = "Status of Occupancy (Point)",
            name = "Status of Occupancy (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_isf = arcpy.Parameter(
            displayName = "Status of ISF (Point)",
            name = "Status of ISF (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_pier = arcpy.Parameter(
            displayName = "Status of Pier (Point)",
            name = "Status of Pier (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        # Input Excel master list tables
        ml_lot = arcpy.Parameter(
            displayName = "Lot_ML (Excel)",
            name = "Lot_ML (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        ml_structure = arcpy.Parameter(
            displayName = "Structure_ML (Excel)",
            name = "Structure_ML (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        ml_isf = arcpy.Parameter(
            displayName = "ISF_Relocation_ML (Excel)",
            name = "ISF_Relocation_ML (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        ml_pier = arcpy.Parameter(
            displayName = "Pier_ML (Excel)",
            name = "Pier_ML (Excel)",
            datatype = "GPTableView",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [ws, in_lot, in_structure, in_occupancy, in_isf, in_pier,
                  ml_lot, ml_structure, ml_isf, ml_pier]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        inLot = params[1].valueAsText
        inStruc = params[2].valueAsText
        inOccup = params[3].valueAsText
        inISF = params[4].valueAsText
        inPier = params[5].valueAsText
        mlLot = params[6].valueAsText
        mlStruct = params[7].valueAsText
        mlISF = params[8].valueAsText
        mlPier = params[9].valueAsText

        arcpy.env.overwriteOutput = True

        # 1. For Pier
        try:
            copyNameN2Pier = 'N2_Pier_test'
            copyN2Pier = arcpy.CopyFeatures_management(inPier, copyNameN2Pier)
            
            # 2. Delete fields: 'Municipality' and 'AccessDate'
            fieldNameN2Pier = [f.name for f in arcpy.ListFields(copyN2Pier)]
            
            ## 2.1. Fields to be dropped
            dropFieldN2Pier = [e for e in fieldNameN2Pier if e not in ('PIER','CP','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
            ## 2.2 Extract existing fields
            inFieldN2Pier = [f.name for f in arcpy.ListFields(copyN2Pier)]
            
            ## 2.3. Check if there are fields to be dropped
            finalDropFieldN2Pier = [f for f in inFieldN2Pier if f in tuple(dropFieldN2Pier)]
            
            ## 2.4 Drop
            if len(finalDropFieldN2Pier) == 0:
                arcpy.AddMessage("There is no field that can be dropped from the feature layer")
            else:
                arcpy.DeleteField_management(copyN2Pier, finalDropFieldN2Pier)
                
            # 3. Join Field
            ## 3.1. Convert Excel tables to feature table
            ##MasterListN2Pier = arcpy.TableToTable_conversion(mlPier, workspace, 'MasterListN2Pier')
            MasterListN2Pier = arcpy.conversion.ExportTable(mlPier, 'MasterListN2Pier')
            
            ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
            inputFieldN2Pier = [f.name for f in arcpy.ListFields(MasterListN2Pier)]
            joinFieldN2Pier = [e for e in inputFieldN2Pier if e not in ('PIER', 'Pier','OBJECTID')]
            
            ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
            tN2Pier = [f.name for f in arcpy.ListFields(copyN2Pier)]
            in_fieldN2Pier = ' '.join(map(str, [f for f in tN2Pier if f in ('PIER', 'Pier')]))
            
            uN2Pier = [f.name for f in arcpy.ListFields(MasterListN2Pier)]
            join_fieldN2Pier=' '.join(map(str, [f for f in uN2Pier if f in ('PIER', 'Pier')]))
            
            ## 3.4 Join
            arcpy.JoinField_management(in_data=copyN2Pier, in_field=in_fieldN2Pier, join_table=MasterListN2Pier, join_field=join_fieldN2Pier, fields=joinFieldN2Pier)
            
            # 4. Trucnate
            arcpy.TruncateTable_management(inPier)
            
            # 5. Append
            arcpy.Append_management(copyN2Pier, inPier, schema_type = 'NO_TEST')
            
        except:
            pass

        ## For Record: Original code below
        # 1. Copy Original Feature Layers
            
        copyNameLot = 'LA_Temp'
        copyNameStruc = 'Struc_Temp'
            
        copyLot = arcpy.CopyFeatures_management(inLot, copyNameLot)
        copyStruc = arcpy.CopyFeatures_management(inStruc, copyNameStruc)
            
        #copyLot = arcpy.CopyFeatures_management(inputLayerLot, copyNameLot)
        #copyStruc = arcpy.CopyFeatures_management(inputLayerStruc, copyNameStruc)
            
        arcpy.AddMessage("Stage 1: Copy feature layer was success")
                
        # 2. Delete Field
        fieldNameLot = [f.name for f in arcpy.ListFields(copyLot)]
        fieldNameStruc = [f.name for f in arcpy.ListFields(copyStruc)]
            
        ## 2.1. Identify fields to be dropped
        dropFieldLot = [e for e in fieldNameLot if e not in ('LotId', 'LotID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
        dropFieldStruc = [e for e in fieldNameStruc if e not in ('StrucID', 'strucID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
        ## 2.2. Extract existing fields
        inFieldLot = [f.name for f in arcpy.ListFields(copyLot)]
        inFieldStruc = [f.name for f in arcpy.ListFields(copyStruc)]
            
        arcpy.AddMessage("Stage 1: Extract existing fields was success")
            
        ## 2.3. Check if there are fields to be dropped
        finalDropFieldLot = [f for f in inFieldLot if f in tuple(dropFieldLot)]
        finalDropFieldStruc = [f for f in inFieldStruc if f in tuple(dropFieldStruc)]
            
        arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")
            
        ## 2.4 Drop
        if len(finalDropFieldLot) == 0:
            arcpy.AddMessage("There is no field that can be dropped from the feature layer")
        else:
            arcpy.DeleteField_management(copyLot, finalDropFieldLot)
                
        if len(finalDropFieldStruc) == 0:
            arcpy.AddMessage("There is no field that can be dropped from the feature layer")
        else:
            arcpy.DeleteField_management(copyStruc, finalDropFieldStruc)
                
        arcpy.AddMessage("Stage 1: Dropping Fields was success")
        arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

        # 3. Join Field
        ## 3.1. Convert Excel tables to feature table
        MasterListLot = arcpy.conversion.ExportTable(mlLot, 'MasterListLot')
        MasterListStruc = arcpy.conversion.ExportTable(mlStruct, 'MasterListStruc')
            
        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        inputFieldLot = [f.name for f in arcpy.ListFields(MasterListLot)]
        inputFieldStruc = [f.name for f in arcpy.ListFields(MasterListStruc)]
            
        joinFieldLot = [e for e in inputFieldLot if e not in ('LotId', 'LotID','OBJECTID')]
        joinFieldStruc = [e for e in inputFieldStruc if e not in ('StrucID', 'strucID','OBJECTID')]
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        tLot = [f.name for f in arcpy.ListFields(copyLot)]
        tStruc = [f.name for f in arcpy.ListFields(copyStruc)]
            
        in_fieldLot = ' '.join(map(str, [f for f in tLot if f in ('LotId', 'LotID')]))
        in_fieldStruc = ' '.join(map(str, [f for f in tStruc if f in ('StrucID', 'strucID')]))
            
        uLot = [f.name for f in arcpy.ListFields(MasterListLot)]
        uStruc = [f.name for f in arcpy.ListFields(MasterListStruc)]
            
        join_fieldLot=' '.join(map(str, [f for f in uLot if f in ('LotId', 'LotID')]))
        join_fieldStruc = ' '.join(map(str, [f for f in uStruc if f in ('StrucID', 'strucID')]))
            
        ## 3.4 Join
        arcpy.JoinField_management(in_data=copyLot, in_field=in_fieldLot, join_table=MasterListLot, join_field=join_fieldLot, fields=joinFieldLot)
        arcpy.JoinField_management(in_data=copyStruc, in_field=in_fieldStruc, join_table=MasterListStruc, join_field=join_fieldStruc, fields=joinFieldStruc)

        # 4. Trucnate
        arcpy.TruncateTable_management(inLot)
        arcpy.TruncateTable_management(inStruc)

        # 5. Append
        arcpy.Append_management(copyLot, inLot, schema_type = 'NO_TEST')
        arcpy.Append_management(copyStruc, inStruc, schema_type = 'NO_TEST')

        ##########################################################################
        ##### STAGE 2: Update Existing Structure (Occupancy) & Structure (ISF) ######
        ###########################################################################
        ## Copy original feature layer
        
        
        # STAGE: 2-1. Create Structure (point) for Occupany
        ## 2-1.1. Feature to Point for Occupany
        outFeatureClassPointStruc = 'Structure_point_occupancy_temp'
        pointStruc = arcpy.FeatureToPoint_management(inStruc, outFeatureClassPointStruc, "CENTROID")
        
        ## 2-1.2. Add XY Coordinates
        arcpy.AddXY_management(pointStruc)
        
        ## 2-1.3. Truncate original point structure layer (Occupancy)
        arcpy.TruncateTable_management(inOccup)

        ## 2-1.4. Append to the original FL
        arcpy.Append_management(pointStruc, inOccup, schema_type = 'NO_TEST')

        # STAGE: 2-2. Create and Update ISF Feture Layer
        ## 2-2.1. Convert ISF (Relocation excel) to Feature table
        ##MasterListISF = arcpy.TableToTable_conversion(mlISF, workspace, 'MasterListISF')
        MasterListISF = arcpy.conversion.ExportTable(mlISF, 'MasterListISF')

        ## 2-2.2. Get Join Field from MasterList gdb table: Gain all fields except 'StrucId'
        inputFieldISF = [f.name for f in arcpy.ListFields(MasterListISF)]
        joinFieldISF = [e for e in inputFieldISF if e not in ('StrucId', 'strucID','OBJECTID')]

        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        tISF = [f.name for f in arcpy.ListFields(inOccup)] # Note 'inputLayerOccupOrigin' must be used, not ISF
        in_fieldISF= ' '.join(map(str, [f for f in tISF if f in ('StrucID','strucID')]))

        uISF = [f.name for f in arcpy.ListFields(MasterListISF)]
        join_fieldISF = ' '.join(map(str, [f for f in uISF if f in ('StrucID', 'strucID')]))

        ## Join
        xCoords = "POINT_X"
        yCoords = "POINT_Y"
        zCoords = "POINT_Z"

        # Join only 'POINT_X' and 'POINT_Y' in the 'inputLayerOccupOrigin' to 'MasterListISF'
        arcpy.JoinField_management(in_data=MasterListISF, in_field=join_fieldISF, join_table=inOccup, join_field=in_fieldISF, fields=[xCoords, yCoords, zCoords])

        ## 2-2.3. XY Table to Points (FL)
        out_feature_class = "Status_for_Relocation_ISF_temp"
        sr = arcpy.SpatialReference(3123)
        outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords, zCoords, sr)

        ### Delete 'POINT_X', 'POINT_Y', 'POINT_Z'; otherwise, it gives error for the next batch
        dropXYZ = [xCoords, yCoords, zCoords]
        arcpy.DeleteField_management(outLayerISF, dropXYZ)

        ## 2-2.4. Add Domain
        
        ## 2-2.5. Truncate original ISF point FL
        arcpy.TruncateTable_management(inISF)

        ## 2-2.6. Append to the Original ISF
        arcpy.Append_management(outLayerISF, inISF, schema_type = 'NO_TEST')

        # Delete the copied feature layer
        deleteTempLayers = [copyLot, copyStruc, pointStruc, outLayerISF, MasterListISF]
        arcpy.Delete_management(deleteTempLayers)

class UpdateSDE(object):
    def __init__(self):
        self.label = "Update Enterprise Geodatabase from File Geodatabase (Run if necessary)"
        self.description = "Update feature layers in enterprise geodatabase for land, structure, and ISF of N2/SC"
        # self.alias = 'test'

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        lot_fgdb = arcpy.Parameter(
            displayName = "Status of Lot in file geodatabase",
            name = "Status of Lot in file geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        struc_fgdb = arcpy.Parameter(
            displayName = "Status of Structure in file geodatabase",
            name = "Status of Structure in file geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        occup_fgdb = arcpy.Parameter(
            displayName = "Occupancy of structures (point) in file geodatabase",
            name = "Occupancy of structures (point) in file geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        isf_fgdb = arcpy.Parameter(
            displayName = "ISF Relocation of structures (point) in file geodatabase",
            name = "ISF Relocation of structures (point) in file geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        barang_fgdb = arcpy.Parameter(
            displayName = "Barangay in file geodatabase",
            name = "Barangay in file geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        pier_fgdb = arcpy.Parameter(
            displayName = "Pier in file geodatabase",
            name = "Pier in file geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        lot_sde = arcpy.Parameter(
            displayName = "Status of Lot in enterprise geodatabase",
            name = "Status of Lot in enterprise geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        struc_sde = arcpy.Parameter(
            displayName = "Status of Structure in enterprise geodatabase",
            name = "Status of Structure in enterprise geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        occup_sde = arcpy.Parameter(
            displayName = "Occupancy of structures (point) in enterprise geodatabase",
            name = "Occupancy of structures (point) in enterprise geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        isf_sde = arcpy.Parameter(
            displayName = "ISF Relocation of structures (point) in enterprise geodatabase",
            name = "ISF Relocation of structures (point) in enterprise geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        barang_sde = arcpy.Parameter(
            displayName = "Barangay in enterprise geodatabase",
            name = "Barangay in enterprise geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        pier_sde = arcpy.Parameter(
            displayName = "Pier in enterprise geodatabase",
            name = "Pier in enterprise geodatabase",
            datatype = "GPFeatureLayer",
            parameterType = "Optional",
            direction = "Input"
        )

        params = [ws, lot_fgdb, struc_fgdb, occup_fgdb, isf_fgdb, barang_fgdb, pier_fgdb,
                  lot_sde, struc_sde, occup_sde ,isf_sde, barang_sde, pier_sde]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        lot_fgdb = params[1].valueAsText
        struc_fgdb = params[2].valueAsText
        occup_fgdb = params[3].valueAsText
        isf_fgdb = params[4].valueAsText
        barang_fgdb = params[5].valueAsText
        pier_fgdb = params[6].valueAsText
        lot_sde = params[7].valueAsText
        struc_sde = params[8].valueAsText
        occup_sde = params[9].valueAsText
        isf_sde = params[10].valueAsText
        barang_sde = params[11].valueAsText
        pier_sde = params[12].valueAsText

        arcpy.env.overwriteOutput = True

        # Copy each layer in PRS92, Truncate, and append
        layerList_fgdb = list()
        layerList_sde = list()

        layerList_fgdb.append(lot_fgdb)
        layerList_fgdb.append(struc_fgdb)
        layerList_fgdb.append(occup_fgdb)
        layerList_fgdb.append(isf_fgdb)
        #layerList_fgdb.append(barang_fgdb)

        layerList_sde.append(lot_sde)
        layerList_sde.append(struc_sde)
        layerList_sde.append(occup_sde)
        layerList_sde.append(isf_sde)
        #layerList_sde.append(barang_sde)

        # Delete empty elements (i.e., if some layers are not selected, we need to vacate this element)
        layerList_fgdb = [s for s in layerList_fgdb if s != '']
        layerList_sde = [s for s in layerList_sde if s != '']

        arcpy.AddMessage("Layer List of FGDB: " + str(layerList_fgdb))
        arcpy.AddMessage("Layer List of SDE: " + str(layerList_sde))

        for layer in layerList_fgdb:
            #arcpy.AddMessage("Layer to be added: " + str(layer))
            
            try:
                # Copy to transform WGS84 to PRS92
                copied = "copied_layer"
                copyL = arcpy.CopyFeatures_management(layer, copied)
                
                arcpy.AddMessage("Copy to CS tranformation for PRS92: Success")
                
                # Truncate and append
                if layer == layerList_fgdb[0]:
                    arcpy.TruncateTable_management(lot_sde)
                    arcpy.Append_management(copyL, lot_sde, schema_type = 'NO_TEST')
                    
                elif layer == layerList_fgdb[1]:
                    arcpy.TruncateTable_management(struc_sde)
                    arcpy.Append_management(copyL, struc_sde, schema_type = 'NO_TEST')
                    
                elif layer == layerList_fgdb[2]:
                    arcpy.TruncateTable_management(occup_sde)
                    arcpy.Append_management(copyL, occup_sde, schema_type = 'NO_TEST')
                    
                elif layer == layerList_fgdb[3]:
                    arcpy.TruncateTable_management(isf_sde)
                    arcpy.Append_management(copyL, isf_sde, schema_type = 'NO_TEST')
                
                elif layer == layerList_fgdb[4]:
                    arcpy.TruncateTable_management(barang_sde)
                    arcpy.Append_management(copyL, barang_sde, schema_type = 'NO_TEST')
                    
                    arcpy.AddMessage("Truncate and Append is Success")
                    
            except:
                pass
            
            # Delete
        arcpy.Delete_management(copyL)
        arcpy.AddMessage("Delete copied layer is Success")


        # We need to run Barangay independently from others.
        try:
            copied = "copied_layer"
            copyB = arcpy.CopyFeatures_management(barang_fgdb, copied)
                
            arcpy.AddMessage("Barangay Layer: Copy to CS tranformation for PRS92: Success")
            
            # Truncate and append
            arcpy.TruncateTable_management(barang_sde)
            arcpy.Append_management(copyB, barang_sde, schema_type = 'NO_TEST')
            
            arcpy.AddMessage("Barangay Layer:Truncate and Append is Success")
            arcpy.Delete_management(copyB)
            
        except:
            pass

        arcpy.AddMessage("Delete copied layer is Success")

        # We need to run pier independently from others.
        try:
            copied = "copied_layer"
            copyP = arcpy.CopyFeatures_management(pier_fgdb, copied)
                
            arcpy.AddMessage("Pier Layer: Copy to CS tranformation for PRS92: Success")
            
            # Truncate and append
            arcpy.TruncateTable_management(pier_sde)
            arcpy.Append_management(copyP, pier_sde, schema_type = 'NO_TEST')
            
            arcpy.AddMessage("Pier Layer:Truncate and Append is Success")
            arcpy.Delete_management(copyP)
            
        except:
            pass

        arcpy.AddMessage("Delete copied layer is Success")

class UpdateUsingMasterList(object):
    def __init__(self):
        self.label = "Update Feature Layer using Excel Master List (Run case-by-case)"
        self.description = "Update any type of feature layers using excel master list table."

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_fc = arcpy.Parameter(
            displayName = "Input Feature Layer",
            name = "Input Feature Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        ml = arcpy.Parameter(
            displayName = "Excel Master List",
            name = "Excel Master List",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        jField = arcpy.Parameter(
            displayName = "Join Field",
            name = "Join Field",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"            
        )
        jField.parameterDependencies = [in_fc.name]

        params = [ws, in_fc, ml, jField]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_fc = params[1].valueAsText
        ml = params[2].valueAsText
        joinField = params[3].valueAsText

        arcpy.env.overwriteOutput = True

        # 1. Copy feature layer
        copyLayer = 'copiedLayer'

        copiedL = arcpy.CopyFeatures_management(in_fc, copyLayer)

        # 2. Delete Field
        fieldNames= [f.name for f in arcpy.ListFields(copiedL)]

        ## 2.1. Identify fields to be droppeds
        baseField = ['Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','OBJECTID_1','GlobalID']
        fieldsKeep = tuple([joinField]) + tuple(baseField)

        dropField = [e for e in fieldNames if e not in fieldsKeep]

        ## 2.2. Extract existing fields
        inField = [f.name for f in arcpy.ListFields(copiedL)]

        arcpy.AddMessage("Stage 1: Extract existing fields was success")

        ## 2.3. Check if there are fields to be dropped
        finalDropField = [f for f in inField if f in tuple(dropField)]

        arcpy.AddMessage("Stage 1: Checking for Fields to be dropped was success")

        ## 2.4 Drop
        if len(finalDropField) == 0:
            arcpy.AddMessage("There is no field that can be dropped from the feature layer")
        else:
            arcpy.DeleteField_management(copiedL, finalDropField)
            
        arcpy.AddMessage("Stage 1: Dropping Fields was success")
        arcpy.AddMessage("Section 2 of Stage 1 was successfully implemented")

        # 3. Join Field
        ## 3.1. Convert Excel tables to feature table
        ##MasterList = arcpy.TableToTable_conversion(ml, workspace, 'MasterList')
        MasterList = arcpy.conversion.ExportTable(ml, 'MasterList')

        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        inputField = [f.name for f in arcpy.ListFields(MasterList)]

        toBeJoinedField = tuple([joinField]) + tuple(['OBJECTID'])
        joiningField = [e for e in inputField if e not in toBeJoinedField]

        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        tLot = [f.name for f in arcpy.ListFields(copiedL)]

        in_field = ' '.join(map(str, [f for f in tLot if f in tuple([joinField])]))
        uLot = [f.name for f in arcpy.ListFields(MasterList)]

        join_field=' '.join(map(str, [f for f in uLot if f in tuple([joinField])]))

        ## 3.4 Join
        arcpy.JoinField_management(in_data=copiedL, in_field=in_field, join_table=MasterList, join_field=join_field, fields=joiningField)

        # 4. Trucnate
        arcpy.TruncateTable_management(in_fc)

        # 5. Append
        arcpy.Append_management(copiedL, in_fc, schema_type = 'NO_TEST')

        # Delete the copied feature layer
        deleteTempLayers = [copiedL, MasterList]
        arcpy.Delete_management(deleteTempLayers)

