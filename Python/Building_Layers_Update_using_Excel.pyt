import arcpy
import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import string

"""
# Instruction and Description 
This python toolbox runs the following:
### 1.0. Export building layers to excel
### 1.1. Update Master excel file
### 1.2. Update existing building layers using the master excel

"""

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateN2StationStructures"
        self.alias = "pdateN2StationStructures"
        self.tools = [ExportToExcel, UpdateGISExcel, UpdateBuildingLayer]

class ExportToExcel(object):
    def __init__(self):
        self.label = "1.0. Export Building Layers to Excel"
        self.description = "5.1. Export each building layer to excel and compile into one sheet"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Sublayers in Building Layers",
            name = "Select Sublayers in Building Layers ",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        in_fl = arcpy.Parameter(
            displayName = "Directory that stores exported excel file",
            name = "Export Directory",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )

        export_name = arcpy.Parameter(
            displayName = "Exported File Name",
            name = "Exported File Name",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        params = [in_replaced_fc, in_fl, export_name]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_replaced_fc = params[0].valueAsText
        in_fl = params[1].valueAsText
        export_name = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        inputLayers = list(in_replaced_fc.split(";"))
        arcpy.AddMessage(inputLayers)

        # 1. merge all the input layers
        mergedLayer = "mergedLayers"
        arcpy.management.Merge(inputLayers, mergedLayer,"","")

        # 3. Export to excel
        #home = Path.home()
        #path = os.path.join(home, "Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/02-Station Structure/01-Masterlist/01-Compiled")
        arcpy.conversion.TableToExcel(mergedLayer, os.path.join(in_fl, export_name + ".xlsx"))

        # 6. Delete copied files
        deletedLayers = [mergedLayer]
        arcpy.management.Delete(deletedLayers)

class UpdateGISExcel(object):
        def __init__(self):
            self.label = "1.1. Update Master Excel File"
            self.description = "1.1. Update Master Excel File for GIS"

        def getParameterInfo(self):
            gis_dir = arcpy.Parameter(
                displayName = "Directory of Master Excel File",
                name = "Directory of Master Excel File",
                datatype = "DEWorkspace",
                parameterType = "Required",
                direction = "Input"
            )

            target_ms = arcpy.Parameter(
                displayName = "Master Excel File",
                name = "Master Excel File",
                datatype = "DEFile",
                parameterType = "Required",
                direction = "Input"
            )

            input_ms = arcpy.Parameter(
                displayName = "Input Excel File",
                name = "Input Excel File",
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

            join_field = arcpy.Parameter(
                displayName = "Join Field",
                name = "Join Field",
                datatype = "Field",
                parameterType = "Required",
                direction = "Input"
            )
            join_field.parameterDependencies = [target_ms.name]

            params = [gis_dir, target_ms, input_ms, gis_bakcup_dir, lastupdate,join_field]
            return params

        def updateMessage(self, params):
            return
        
        def execute(self, params, messages):
            gis_dir = params[0].valueAsText
            target_ms = params[1].valueAsText
            input_ms = params[2].valueAsText
            gis_bakcup_dir = params[3].valueAsText
            lastupdate = params[4].valueAsText
            join_field = params[5].valueAsText

            arcpy.env.overwriteOutput = True

            def unique(lists):
                collect = []
                unique_list = pd.Series(lists).drop_duplicates().tolist()
                for x in unique_list:
                    collect.append(x)
                return(collect)
            
            def toString(table, to_string_fields): # list of fields to be converted to string
                for field in to_string_fields:
                    ## Need to convert string first, then apply space removal, and then convert to string again
                    ## If you do not apply string conversion twice, it will fail to join with the GIS attribute table
                    table[field] = table[field].astype(str)
                    table[field] = table[field].apply(lambda x: x.replace(r'\s+', ''))
                    table[field] = table[field].astype(str)

            # 1. Read excel files
            input_table = pd.read_excel(input_ms)
            target_table = pd.read_excel(target_ms)

            # 2. Create bakcup files
            export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
            to_excel_file = os.path.join(gis_bakcup_dir, lastupdate + "_" + export_file_name + ".xlsx")
            
            try:
                target_table.to_excel(to_excel_file, index=False)
                arcpy.AddMessage("The master list was successfully exported.")
            except:
                pass

            # toString join_field
            toString(target_table, [join_field])
            toString(input_table,[join_field])

            # add temp field to new table
            temp_field = 'temp'
            input_table[temp_field] = 1

            # join input_table to target table using unique id field
            input_table2 = input_table[[temp_field,join_field]]
            joined_table = pd.merge(left=target_table, right=input_table2, how='left', left_on=join_field, right_on=join_field, validate='one_to_one')

            # Delete rows with temp == 1 (i.e., deleting ObjectsIds of input_table from target_table)
            id = joined_table.index[joined_table[temp_field] != 1]
            joined_table = joined_table.iloc[id]

            # Append joined_table to input_table
            final_table = pd.concat([joined_table, input_table], ignore_index=True)

            # sort by join_field
            final_table = final_table.sort_values(by=[join_field])

            # Delete temp field
            final_table = final_table.drop(columns = temp_field)

            # Export
            # export_file_name = os.path.splitext(os.path.basename(target_ms))[0]
            # to_excel_file = os.path.join(gis_dir, export_file_name + ".xlsx")
            final_table.to_excel(target_ms, index=False)

class UpdateBuildingLayer(object):
    def __init__(self):
        self.label = "1.2. Update Building Layers using ML"
        self.description = "1.2. Update building layers using excel ML"

    def getParameterInfo(self):
        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Existing Building Layers",
            name = "Select Existing Building Layers ",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )

        in_ml = arcpy.Parameter(
            displayName = "Excel Master List",
            name = "Excel Master List",
            datatype = "GPTableView",
            parameterType = "Required",
            direction = "Input"
        )

        id_field = arcpy.Parameter(
            displayName = "Select Unique ID FIeld",
            name = "Select Unique ID FIeld",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        id_field.parameterDependencies = [in_ml.name]

        params = [in_replaced_fc, in_ml, id_field]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        in_replaced_fc = params[0].valueAsText
        in_ml = params[1].valueAsText
        id_field = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        old_buildingLayers = list(in_replaced_fc.split(";"))
        arcpy.AddMessage(old_buildingLayers)

        for layer in old_buildingLayers:
            # 1. Copy the existing building layers
            basename = os.path.basename(layer)
            output_name = basename + "_copy"
            arcpy.management.CopyFeatures(layer, output_name)
            arcpy.AddMessage(basename + " building layer is successfully copied.")
            
            # 2. Delete fields
            arcpy.DeleteField_management(output_name, [id_field], "KEEP_FIELDS")
            arcpy.AddMessage("All fields other than uniqueID were successfully deleted from " + output_name)

            # 3. Join Field
            ## 3.1. Remove uniqueID and OBJECTID from transferFiedls; otherwise, it fails
            fields = [f.name for f in arcpy.ListFields(in_ml)]
            transferFieldsRev = []
            search_words = '|'.join([id_field,'^Object'])
            
            for field in fields:
                try:
                    reg = re.search(search_words,field).group() 
                    if reg is None:
                        transferFieldsRev.append(field)
                except AttributeError:
                    reg = re.search(search_words,field)
                    if reg is None:
                        transferFieldsRev.append(field)
            arcpy.management.JoinField(output_name, id_field, in_ml, id_field, transferFieldsRev)
            arcpy.AddMessage(in_ml + " was successfully joined to " + output_name)

          #  ## 3.2. If Status = 1 and target_date < current_date, Status = 3 (delayed) [This will be done by R]
          #  codeblock = """
          #  import re
          #  def reclass(id, target, status):
          #      
          #      try:
          #          reg = re.search('\\d+',pier).group()
          #          return reg
          #      except AttributeError:
          #          reg = re.search('\\d+',pier)
          #          return reg
          #  """
            expression = "reclass(!{}!)".format(id_field, "target_date", "Status")
            #arcpy.CalculateField_management(inputFeature, field_temp, expression, "PYTHON3", codeblock)

            # 4. Truncate the existing building layer
            arcpy.TruncateTable_management(layer)
            arcpy.AddMessage("The existing building layer, " + layer + " was successfully truncated for joining.")

            # 5. Append the updated copied to the existing building layer
            arcpy.Append_management(output_name, layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("The existing building layer, " + layer + " was successfully updated.")

            # 6. Delete copied files
            arcpy.management.Delete(output_name)
