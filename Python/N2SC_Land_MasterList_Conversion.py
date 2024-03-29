import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import re
import string
import openpyxl

home=Path.home()

# Choose Project
Project = 'N2'

## Directory and files
gdb_dir = "C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\Pre-Construction_nscrexn2\\Pre-Construction_nscrexn2.gdb"
n2_gis_dir = "Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/01-LAR/99-MasterList/03-Compiled"
sc_gis_dir = "Dropbox/01-Railway/02-NSCR-Ex/02-SC/02-Pre-Construction/01-Environment/01-LAR/99-MasterList/03-Compiled"
rap_dir=os.path.join(home,"Dropbox/01-Railway/02-NSCR-Ex/99-MasterList_RAP_Team")

if Project == 'N2':
    gis_dir=os.path.join(home,n2_gis_dir)
else:
    gis_dir=os.path.join(home,sc_gis_dir)

last_update = '20231228'

def N2SC_Land_Update(gdb_dir, gis_dir, rap_dir, Project ,last_update):
    # Definitions
    if Project == 'N2':
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

            
    # List files
    lot_gis_files = os.listdir(gis_dir)
    lot_rap_files = os.listdir(rap_dir)

    # Read as xlsx
    queryExpGis = '^' + Project + '_Land.*_Status.xlsx$'
    queryExpRap = '^' + Project + '_Parce.*xlsx$'
    queryExpRapSC1 = '^' + Project + '1_.*Parcellary.*.xlsx'

    queryGis = [re.search(queryExpGis, i).group() for i in lot_gis_files if re.search(queryExpGis, i) is not None][0]
    queryRap = [re.search(queryExpRap, i).group() for i in lot_rap_files if re.search(queryExpRap, i) is not None][0]

    lot_rap_table = pd.read_excel(os.path.join(rap_dir, queryRap))
    lot_gis_table = pd.read_excel(os.path.join(gis_dir, queryGis))

    # Land
    backup_path = os.path.join(gis_dir, 'Backup')
    lot_gis_table.to_excel(os.path.join(backup_path,last_update + "_" + queryGis),index=False)
    
    #####################################################################################################
    # SC1
    ## Join SC1 Lot to SC
    if Project == 'SC':
        joinField = 'LotID'
        joinedFields = [joinField, 'ContSubm', 'Subcon', 'Priority1', 'Reqs']

        queryRapSC1 = [re.search(queryExpRapSC1, i).group() for i in lot_rap_files if re.search(queryExpRapSC1, i) is not None][0]
        lot_rap_table_sc1 = pd.read_excel(os.path.join(rap_dir, queryRapSC1))
        
        # Add contractors submission
        lot_rap_table_sc1['ContSubm'] = 1
        
        # Rename Municipality
        lot_rap_table_sc1 = lot_rap_table_sc1.rename(columns={'City': 'Municipality'})
        
        lot_rap_table_sc1.head()
        lot_rap_table_sc1.dtypes

        # Convert to numeric
        to_numeric_fields = 'Priority1'
        lot_rap_table_sc1[to_numeric_fields] = lot_rap_table_sc1[to_numeric_fields].replace(r'\s+|[^\w\s]', '', regex=True)
        lot_rap_table_sc1[to_numeric_fields] = pd.to_numeric(lot_rap_table_sc1[to_numeric_fields])
        
        # Conver to string with white space removal
        to_string_fields = ['LotID']
        toString(lot_rap_table_sc1, to_string_fields)
            
        # Create Priority1_1 for web mapping purpose only
        ## Unique priority values
        uniques = unique(lot_rap_table_sc1[to_numeric_fields].dropna())
        new_priority_field = 'Priority1_1'
        lot_rap_table_sc1[new_priority_field] = None
        for num in uniques:
            id = lot_rap_table_sc1.index[lot_rap_table_sc1[to_numeric_fields] == num]
            if num == 2:
                lot_rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'nd').replace('.0','')
            elif num == 3:
                lot_rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'rd').replace('.0','')
            else:
                lot_rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'st').replace('.0','')

        # Filter fields
        lot_rap_table_sc1 = lot_rap_table_sc1[joinedFields + [new_priority_field]]
        lot_rap_table = lot_rap_table.drop(joinedFields[2:], axis=1)
        
        lot_rap_table_sc1.head(10)

        # Left join
        lot_rap_table['LotID'] = lot_rap_table['LotID'].astype(str)
        lot_rap_table_sc1['LotID'] = lot_rap_table_sc1['LotID'].astype(str)
        lot_rap_table = pd.merge(left=lot_rap_table, right=lot_rap_table_sc1, how='left', left_on='LotID', right_on='LotID')
    
        # Check if any missing LotID when joined
        id = lot_rap_table.index[lot_rap_table['ContSubm'] == 1]
        lotID_sc = unique(lot_rap_table.loc[id,joinField])
        lotID_sc1 = unique(lot_rap_table_sc1[joinField])
        non_match_LotID = non_match_elements(lotID_sc, lotID_sc1)
        if (len(non_match_LotID) > 0):
            print('LotIDs do not match between SC and SC1 tables.')

        ####################################################################################################

    # Rename column names
    lot_rap_table = lot_rap_table.rename(columns={'City/Municipality': 'Municipality'})

    # Convert to numeric
    to_numeric_fields = ["TotalArea","AffectedArea","RemainingArea","HandedOverArea","HandedOver","Priority","StatusLA","MoA","PTE", 'Endorsed']
    cols = lot_rap_table.columns
    non_match_col = non_match_elements(to_numeric_fields, cols)
    [to_numeric_fields.remove(non_match_col[0]) if non_match_col else print('no need to remove field from the list for numeric conversion')]

    for field in to_numeric_fields:
       lot_rap_table[field] = lot_rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
       lot_rap_table[field] = pd.to_numeric(lot_rap_table[field])
        
    # Conver to string
    to_string_fields = ["LotID", "CP"]
    toString(lot_rap_table, to_string_fields)
    
    # Reformat CP
    lot_rap_table['CP'] = lot_rap_table['CP'].str[-2:]       
    lot_rap_table['CP'] = cp_suffix + lot_rap_table['CP']
        
    # Conver to date   
    to_date_fields = ['HandOverDate','HandedOverDate']
    for field in to_date_fields:
        lot_rap_table[field] = pd.to_datetime(lot_rap_table[field],errors='coerce').dt.date
 
    ## Convert to uppercase letters for LandUse
    match_col = match_elements(cols, 'LandUse')
    if len(match_col) > 0:
        lot_rap_table['LandUse'] = lot_rap_table['LandUse'].apply(lambda x: x.upper())
    
    # Add scale from old master list
    lot_rap_table = lot_rap_table.drop('Scale',axis=1)
    lot_gis_scale = lot_gis_table[['Scale','LotID']]
    lot_rap_table = pd.merge(left=lot_rap_table, right=lot_gis_scale, how='left', left_on='LotID', right_on='LotID')

    # Check and Fix StatusLA, HandedOverDate, HandOverDate, and HandedOverArea
    ## 1. StatusLA =0 -> StatusLA = empty
    id = lot_rap_table.index[lot_rap_table['StatusLA'] == 0]
    lot_rap_table.loc[id, 'StatusLA'] = None

    ## 2. HandedOver = 1 & !is.na(HandOverDate) -> HandedOverDate = HandOverDate
    id = lot_rap_table.index[(lot_rap_table['HandedOver'] == 1) & (lot_rap_table['HandOverDate'].notna())]
    lot_rap_table.loc[id, 'HandedOverDate'] = lot_rap_table.loc[id, 'HandOverDate']
    lot_rap_table.loc[id, 'HandOverDate'] = None

    ## 3. HandedOver = 0 & !is.na(HandedOverDate) -> HandedOverDate = empty
    id = lot_rap_table.index[(lot_rap_table['HandedOver'] == 0) & (lot_rap_table['HandedOverDate'].notna())]
    lot_rap_table.loc[id, 'HandedOverDate'] = None
    
    ## 4. if the first row is empty, temporarily add the first row for 'HandedOverDate' and 'HandOverDate'
    for field in to_date_fields:
        date_item = lot_rap_table[field].iloc[:1].item()
        if date_item is None:
            lot_rap_table.loc[0, field] = pd.to_datetime('1990-01-01')

    ## 5. is.na(HandedOverArea) -> HandedOverArea = 0
    id = lot_rap_table.index[(lot_rap_table['HandedOverArea'] == None) | (lot_rap_table['HandedOverArea'].isna())]
    lot_rap_table.loc[id, 'HandedOverArea'] = 0

    # Calculate percent handed-over
    lot_rap_table['percentHandedOver'] = round((lot_rap_table['HandedOverArea'] / lot_rap_table['AffectedArea'])*100,0)
  
    # Export
    to_excel_file = os.path.join(gis_dir, 'test_'+ queryGis)
    lot_rap_table.to_excel(to_excel_file, index=False)
    
    # Export to geodatabase table
    arcpy.conversion.ExportTable(os.path.join(to_excel_file,"Sheet1$"), os.path.join(gdb_dir, Project + "_Land_Status_TEST"))
    
N2SC_Land_Update(gis_dir, rap_dir, Project ,last_update, gdb_dir)


######################################################################################################
######################################################################################################
######################################################################################################

def N2SC_Structure_Update(gdb_dir, gis_dir, rap_dir, Project ,last_update):
    # Definitions
    if Project == 'N2':
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

            
    # List files
    gis_files = os.listdir(gis_dir)
    rap_files = os.listdir(rap_dir)

    # Read as xlsx
    queryExpGis = '^' + Project + '_Structure.*xlsx$'
    queryExpRap = '^' + Project + '_Structure.*masterlist.*xlsx$'
    queryExpRapSC1 = '^' + Project + '1_.*Structure.*.xlsx'

    queryGis = [re.search(queryExpGis, i).group() for i in gis_files if re.search(queryExpGis, i) is not None][0]
    queryRap = [re.search(queryExpRap, i).group() for i in rap_files if re.search(queryExpRap, i) is not None][0]

    rap_table = pd.read_excel(os.path.join(rap_dir, queryRap))
    gis_table = pd.read_excel(os.path.join(gis_dir, queryGis))

    # Land
    backup_path = os.path.join(gis_dir, 'Backup')
    gis_table.to_excel(os.path.join(backup_path,last_update + "_" + queryGis),index=False)
    
    #####################################################################################################
    # SC1
    ## Join SC1 Lot to SC
    if Project == 'SC':
        joinField = 'LotID'
        joinedFields = [joinField, 'ContSubm', 'Subcon', 'Priority1', 'Reqs']

        queryRapSC1 = [re.search(queryExpRapSC1, i).group() for i in lot_rap_files if re.search(queryExpRapSC1, i) is not None][0]
        lot_rap_table_sc1 = pd.read_excel(os.path.join(rap_dir, queryRapSC1))
        
        # Add contractors submission
        lot_rap_table_sc1['ContSubm'] = 1
        
        # Rename Municipality
        lot_rap_table_sc1 = lot_rap_table_sc1.rename(columns={'City': 'Municipality'})
        
        lot_rap_table_sc1.head()
        lot_rap_table_sc1.dtypes

        # Convert to numeric
        to_numeric_fields = 'Priority1'
        lot_rap_table_sc1[to_numeric_fields] = lot_rap_table_sc1[to_numeric_fields].replace(r'\s+|[^\w\s]', '', regex=True)
        lot_rap_table_sc1[to_numeric_fields] = pd.to_numeric(lot_rap_table_sc1[to_numeric_fields])
        
        # Conver to string with white space removal
        to_string_fields = ['LotID']
        toString(lot_rap_table_sc1, to_string_fields)
            
        # Create Priority1_1 for web mapping purpose only
        ## Unique priority values
        uniques = unique(lot_rap_table_sc1[to_numeric_fields].dropna())
        new_priority_field = 'Priority1_1'
        lot_rap_table_sc1[new_priority_field] = None
        for num in uniques:
            id = lot_rap_table_sc1.index[lot_rap_table_sc1[to_numeric_fields] == num]
            if num == 2:
                lot_rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'nd').replace('.0','')
            elif num == 3:
                lot_rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'rd').replace('.0','')
            else:
                lot_rap_table_sc1.loc[id, new_priority_field] = (str(num) + 'st').replace('.0','')

        # Filter fields
        lot_rap_table_sc1 = lot_rap_table_sc1[joinedFields + [new_priority_field]]
        lot_rap_table = lot_rap_table.drop(joinedFields[2:], axis=1)
        
        lot_rap_table_sc1.head(10)

        # Left join
        lot_rap_table['LotID'] = lot_rap_table['LotID'].astype(str)
        lot_rap_table_sc1['LotID'] = lot_rap_table_sc1['LotID'].astype(str)
        lot_rap_table = pd.merge(left=lot_rap_table, right=lot_rap_table_sc1, how='left', left_on='LotID', right_on='LotID')
    
        # Check if any missing LotID when joined
        id = lot_rap_table.index[lot_rap_table['ContSubm'] == 1]
        lotID_sc = unique(lot_rap_table.loc[id,joinField])
        lotID_sc1 = unique(lot_rap_table_sc1[joinField])
        non_match_LotID = non_match_elements(lotID_sc, lotID_sc1)
        if (len(non_match_LotID) > 0):
            print('LotIDs do not match between SC and SC1 tables.')

        ####################################################################################################

    # Rename column names
    colname_change = rap_table.columns[rap_table.columns.str.contains('Muni', 'City')]  
    rap_table = rap_table.rename(columns={colname_change[0]: 'Municipality'})

    # Convert to numeric
    to_numeric_fields = ["TotalArea","AffectedArea","RemainingArea","HandOver","StatusStruc","Status","MoA","PTE", "Occupancy"]
    cols = rap_table.columns
    non_match_col = non_match_elements(to_numeric_fields, cols)
    [to_numeric_fields.remove(non_match_col[0]) if non_match_col else print('no need to remove field from the list for numeric conversion')]

    for field in to_numeric_fields:
       rap_table[field] = rap_table[field].replace(r'\s+|[^\w\s]', '', regex=True)
       rap_table[field] = pd.to_numeric(rap_table[field])
        
    # Conver to string
    to_string_fields = ["StrucID", "CP", "StructureUse"]
    toString(rap_table, to_string_fields)
    
    # Reformat CP
    lot_rap_table['CP'] = lot_rap_table['CP'].str[-2:]    
    lot_rap_table['CP'] = cp_suffix + lot_rap_table['CP']
 
    ## Convert to uppercase letters for StructureUse
    uppercase_field = 'StructureUse'
    match_col = match_elements(cols, uppercase_field)
    if len(match_col) > 0:
        rap_table[uppercase_field] = rap_table[uppercase_field].apply(lambda x: x.upper())

    # Check and Fix StatusLA, HandedOverDate, HandOverDate, and HandedOverArea
    ## 1. StatusLA =0 -> StatusLA = empty
    id = lot_rap_table.index[lot_rap_table['StatusLA'] == 0]
    lot_rap_table.loc[id, 'StatusLA'] = None

    ## 2. HandedOver = 1 & !is.na(HandOverDate) -> HandedOverDate = HandOverDate
    id = lot_rap_table.index[(lot_rap_table['HandedOver'] == 1) & (lot_rap_table['HandOverDate'].notna())]
    lot_rap_table.loc[id, 'HandedOverDate'] = lot_rap_table.loc[id, 'HandOverDate']
    lot_rap_table.loc[id, 'HandOverDate'] = None

    ## 3. HandedOver = 0 & !is.na(HandedOverDate) -> HandedOverDate = empty
    id = lot_rap_table.index[(lot_rap_table['HandedOver'] == 0) & (lot_rap_table['HandedOverDate'].notna())]
    lot_rap_table.loc[id, 'HandedOverDate'] = None
    
    ## 4. if the first row is empty, temporarily add the first row for 'HandedOverDate' and 'HandOverDate'
    for field in to_date_fields:
        date_item = lot_rap_table[field].iloc[:1].item()
        if date_item is None:
            lot_rap_table.loc[0, field] = pd.to_datetime('1990-01-01')

    ## 5. is.na(HandedOverArea) -> HandedOverArea = 0
    id = lot_rap_table.index[(lot_rap_table['HandedOverArea'] == None) | (lot_rap_table['HandedOverArea'].isna())]
    lot_rap_table.loc[id, 'HandedOverArea'] = 0

    # Calculate percent handed-over
    lot_rap_table['percentHandedOver'] = round((lot_rap_table['HandedOverArea'] / lot_rap_table['AffectedArea'])*100,0)
  
    # Export
    to_excel_file = os.path.join(gis_dir, 'test_'+ queryGis)
    lot_rap_table.to_excel(to_excel_file, index=False)
    
    # Export to geodatabase table
    arcpy.conversion.ExportTable(os.path.join(to_excel_file,"Sheet1$"), os.path.join(gdb_dir, Project + "_Land_Status_TEST"))
