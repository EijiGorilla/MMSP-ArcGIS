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
        self.tools = [UpdateLot, UpdateISF, UpdateStructure, UpdateBarangay, UpdatePier,
                      UpdateLotGIS, UpdateStructureGIS, UpdatePierGIS, UpdateBarangayGIS]

class UpdateLot(object):
    def __init__(self):
        self.label = "1.0. Update Excel Master List (Lot)"
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
                        arcpy.AddMessage('LotIDs do not match between SC and SC1 tables.')

                except Exception:
                    arcpy.AddMessage('You did not select {0} master list for updating contractors submission status.'.format('SC1_Land_Status '))

            # Rename City for Municipality and upper case letter for the first letter
            try:
                colname_change = rap_table.columns[rap_table.columns.str.contains('|'.join(search_names_city))]
                rap_table = rap_table.rename(columns={str(colname_change[0]): renamed_city})
            except:
                pass

            first_letter_capital(rap_table, [renamed_city])
            # first_letter_capital(rap_table, ['Barangay'])
            
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
            if proj == 'N2':
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
        # ws = arcpy.Parameter(
        #     displayName = "Workspace",
        #     name = "workspace",
        #     datatype = "DEWorkspace",
        #     parameterType = "Required",
        #     direction = "Input"
        # )

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
                gis_table.to_excel(os.path.join(gis_bakcup_dir, lastupdate + "_" + proj + "_Structure_Status.xlsx"), index=False)
            except Exception:
                arcpy.AddMessage('You did not choose to create a backup file of {0} master list.'.format(proj + '_Structure_Status'))
            
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
            rap_relo_table.head()
            toString(rap_relo_table, [joinField])
            rap_relo_table['FamilyNumber'] = 0
            df = rap_relo_table.groupby(joinField).count()[['FamilyNumber']]
            rap_table = pd.merge(left=rap_table, right=df, how='left', left_on=joinField, right_on=joinField)
            
            # MoA is 'No Need to Acquire' -> StatusStruc is null: What is THIS?
            # id = rap_table.index[rap_table['MoA'] == 4 & (rap_table[status_field] >= 1)]
            # rap_table.loc[id, status_field] = None
        
            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_struc_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

        N2SC_Structure_Update()

class UpdateBarangay(object):
    def __init__(self):
        self.label = "1.3. Update Excel Master List (SC1 Barangay )"
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

            # Remove 'Barangay'
            rap_table = rap_table.replace(regex="^Barangay", value="")
            whitespace_removal(rap_table)

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

        params = [proj, gis_dir, gis_pier_ms, rap_pier_ms, gis_bakcup_dir, lastupdate]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        proj = params[0].valueAsText
        gis_dir = params[1].valueAsText
        gis_pier_ms = params[2].valueAsText
        rap_pier_ms = params[3].valueAsText
        gis_bakcup_dir = params[4].valueAsText
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

            # Reformat date
            rap_table['AccessDate'] = pd.to_datetime(rap_table['AccessDate'],errors='coerce').dt.date

            # Make sure no space
            toString(rap_table, ['Municipality', 'PIER', 'CP'])

            # CP to upper case
            rap_table['CP'] = rap_table['CP'].apply(lambda x: x.upper())  

            # Reformat CP
            if proj == 'N2':
                rap_table['CP'] = rap_table['CP'].str[-2:]       
                rap_table['CP'] = cp_suffix + rap_table['CP']

            # check match between RAP and GIS
            try:
                pier_rap = unique(rap_table['PIER'])
                pier_gis = unique(gis_table['PIER'])

                non_match_piers = non_match_elements(pier_rap, pier_gis)
                if (len(non_match_piers) > 0):
                    arcpy.AddMessage('Pier Numbers do not match between GIS excel ML and RAP excel ML.')
                    arcpy.AddMessage(non_match_piers)
                else:
                    arcpy.AddMessage('Pier Numbers match between Excel ML and GIS table.')
            except:
                pass

            # Change the following pier numbers
            piers_change = ['P-2152-A', 'P-2153-A', 'P-2206-A']
            for old_pier in piers_change:
                new_pier = old_pier.replace(r'-A','A')
                rap_table['PIER'].replace(old_pier, new_pier, inplace=True)

            # Export
            export_file_name = os.path.splitext(os.path.basename(gis_pier_ms))[0]
            to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            rap_table.to_excel(to_excel_file, index=False)

        N2SC_Pier_Update()

class UpdateLotGIS(object):
    def __init__(self):
        self.label = "2.1. Update GIS Attribute Table (Lot)"
        self.description = "Update feature layer for land acquisition"

    def getParameterInfo(self):
        # Input Feature Layers
        in_lot = arcpy.Parameter(
            displayName = "GIS Lot Status (Polygon)",
            name = "GIS Lot Status (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        # Input Excel master list tables
        ml_lot = arcpy.Parameter(
            displayName = "Excel MasterList (Lot)",
            name = "Excel MasterList (Lot)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_lot, ml_lot]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inLot = params[0].valueAsText
        mlLot = params[1].valueAsText

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

        except:
            pass

class UpdateStructureGIS(object):
    def __init__(self):
        self.label = "2.2. Update GIS Attribute Tables (Structures/Occupancy/ISF Relocation)"
        self.description = "Update feature layers for structures including occupany and ISF Relocation"

    def getParameterInfo(self):
        in_structure = arcpy.Parameter(
            displayName = "GIS Structure Status (Polygon)",
            name = "GIS Structure Status (Polygon)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_occupancy = arcpy.Parameter(
            displayName = "GIS Structure Occupancy (Point)",
            name = "GIS Structure Occupancy (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        in_isf = arcpy.Parameter(
            displayName = "GIS ISF Relocation (Point)",
            name = "GIS ISF Relocation (Point)",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        ml_structure = arcpy.Parameter(
            displayName = "Excel MasterList (Structure)",
            name = "Structure_ML (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        ml_isf = arcpy.Parameter(
            displayName = "Excel MasterList (ISF Relocation)",
            name = "ISF_Relocation_ML (Excel)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_structure, in_occupancy, in_isf, ml_structure, ml_isf]
        return params

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inStruc = params[0].valueAsText
        inOccup = params[1].valueAsText
        inISF = params[2].valueAsText
        mlStruct = params[3].valueAsText
        mlISF = params[4].valueAsText

        def unique_values(table, field):  ##uses list comprehension
            with arcpy.da.SearchCursor(table, [field]) as cursor:
                return sorted({row[0] for row in cursor if row[0] is not None})

        arcpy.env.overwriteOutput = True

        # 1. Copy Original Feature Layers
        copied_name = 'Struc_Temp'
        gis_copied = arcpy.CopyFeatures_management(inStruc, copied_name)
            
        arcpy.AddMessage("Stage 1: Copy feature layer was success")
                
        # 2. Delete Field
        gis_fields = [f.name for f in arcpy.ListFields(gis_copied)]
            
        ## 2.1. Identify fields to be dropped
        gis_drop_fields_check = [e for e in gis_fields if e not in ('StrucID', 'strucID','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
                        
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
        struc_ml = arcpy.conversion.ExportTable(mlStruct, 'structure_ml')

        # Check if StrucID match between ML and GIS
        strucid_field = 'StrucID'
        strucid_gis = unique_values(gis_copied, strucid_field)
        strucid_ml = unique_values(struc_ml, strucid_field)
        
        strucid_miss_gis = [e for e in strucid_gis if e not in strucid_ml]
        strucid_miss_ml = [e for e in strucid_ml if e not in strucid_gis]

        if strucid_miss_ml or strucid_miss_gis:
            arcpy.AddMessage('The following Structure IDs do not match between ML and GIS.')
            arcpy.AddMessage('Missing StrucIDs in GIS table: {}'.format(strucid_miss_gis))
            arcpy.AddMessage('Missing StrucIDs in ML Excel table: {}'.format(strucid_miss_ml))
            
        ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
        struc_ml_fields = [f.name for f in arcpy.ListFields(struc_ml)]
        struc_ml_transfer_fields = [e for e in struc_ml_fields if e not in (strucid_field, 'strucID','OBJECTID')]
            
        ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
        gis_join_field = ' '.join(map(str, [f for f in gis_fields if f in (strucid_field, 'strucID')]))
        struc_ml_join_field = ' '.join(map(str, [f for f in struc_ml_fields if f in (strucid_field, 'strucID')]))
            
        ## 3.4 Join
        arcpy.JoinField_management(in_data=gis_copied, in_field=gis_join_field, join_table=struc_ml, join_field=struc_ml_join_field, fields=struc_ml_transfer_fields)

        # 4. Trucnate
        arcpy.TruncateTable_management(inStruc)

        # 5. Append
        arcpy.Append_management(gis_copied, inStruc, schema_type = 'NO_TEST')

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
        deleteTempLayers = [gis_copied, pointStruc, outLayerISF, MasterListISF]
        arcpy.Delete_management(deleteTempLayers)

class UpdatePierGIS(object):
    def __init__(self):
        self.label = "2.3. Update GIS Attribute Tables (Pier Number)"
        self.description = "Update feature layers for pier number"

    def getParameterInfo(self):
        in_pier = arcpy.Parameter(
            displayName = "GIS Pier Number (Point)",
            name = "GIS Pier Number",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input"
        )

        ml_pier = arcpy.Parameter(
            displayName = "Excel MasterList (Pier No.)",
            name = "Excel MasterList (Pier No.)",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_pier, ml_pier]
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
            arcpy.AddMessage('Updating Pier No. list has started..')
            pier_copied_name = 'N2_Pier_test'
            pier_copied_gis = arcpy.CopyFeatures_management(inPier, pier_copied_name)
            
            # 2. Delete fields: 'Municipality' and 'AccessDate'
            pier_gis_fields = [f.name for f in arcpy.ListFields(pier_copied_gis)]
            
            ## 2.1. Fields to be dropped
            pier_drop_fields = [e for e in pier_gis_fields if e not in ('PIER','CP','Shape','Shape_Length','Shape_Area','Shape.STArea()','Shape.STLength()','OBJECTID','GlobalID')]
            
            ## 2.3. Check if there are fields to be dropped
            pier_drop_fields_check = [f for f in pier_gis_fields if f in tuple(pier_drop_fields)]
            
            ## 2.4 Drop
            if len(pier_drop_fields_check) == 0:
                arcpy.AddMessage("There is no field that can be dropped from the feature layer")
            else:
                arcpy.DeleteField_management(pier_copied_gis, pier_drop_fields_check)

            # 3. Join Field
            ## 3.1. Convert Excel tables to feature table
            ##MasterListN2Pier = arcpy.TableToTable_conversion(mlPier, workspace, 'MasterListN2Pier')
            pier_ml_table = arcpy.conversion.ExportTable(mlPier, 'pier_ml_table')

            # Check if pier numbers match between ML and GIS
            pier_field = 'PIER'
            piers_gis = unique_values(pier_copied_gis, pier_field)
            piers_ml = unique_values(pier_ml_table, pier_field)
            
            piers_miss_gis = [e for e in piers_gis if e not in piers_ml] # missing in gis
            piers_miss_ml = [e for e in piers_ml if e not in piers_gis] # missing in ML

            if piers_miss_ml or piers_miss_gis:
                arcpy.AddMessage('The following pier numbers do not match between ML and GIS.')
                arcpy.AddMessage('Missing Pier Numbers in GIS table: {}'.format(piers_miss_gis))
                arcpy.AddMessage('Missing Pier Numbers in ML Excel table: {}'.format(piers_miss_ml))
            
            ## 3.2. Get Join Field from MasterList gdb table: Gain all fields except 'Id'
            pier_ml_fields = [f.name for f in arcpy.ListFields(pier_ml_table)]
            transfer_fields = [e for e in pier_ml_fields if e not in ('PIER', 'Pier','OBJECTID')]
            
            ## 3.3. Extract a Field from MasterList and Feature Layer to be used to join two tables
            gis_join_field = ' '.join(map(str, [f for f in pier_gis_fields if f in ('PIER', 'Pier')]))
            ml_join_field =' '.join(map(str, [f for f in pier_ml_fields if f in ('PIER', 'Pier')]))
            
            ## 3.4 Join
            arcpy.JoinField_management(in_data=pier_copied_gis, in_field=gis_join_field, join_table=pier_ml_table, join_field=ml_join_field, fields=transfer_fields)
            
            # 4. Trucnate
            arcpy.TruncateTable_management(inPier)
            
            # 5. Append
            arcpy.Append_management(pier_copied_gis, inPier, schema_type = 'NO_TEST')
            
        except:
            pass

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
            
        except:
            pass

