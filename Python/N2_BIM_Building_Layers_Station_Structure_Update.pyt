import arcpy
import os
import re
from pathlib import Path

"""
# Instruction and Description 
This Python toolbox is used to update the construction progress on N2 station structures using P6ID
The intention is to use the planned construction dates in P6 DB for the construction monitoring.

Note that we cannot use BIM revit models directly to update existing building layers, as we need to
manually add planned construction dates from P6 DB.

## Note that you do not need to export building layers to excel if excel ML keeps up-to-date information.

## A. Update target dates from P6 Database
## This R code update construction target dates from P6 database
## file name: 'N2_Viaduct_Station_Structure_P6_tableConversion.R'
1. Update the excel ML using R code (This must be done separately from python)


## B. Update Building Layers for N2 station structures
1. Copy the building layer
2. Keep field 'objectId'
3. Join the updated excel ML to the copied using 'objectId' (? or 'P6ID'?)
4. Trucate the original building layer
5. Append the copied to the original building layer
6. Reapt 1 to 6 for each building layer

## C. Update construction progress manually based on Civil Team's information
1. Manually update in SDE

## D. Export updated building layers to excel ML (only when you manually edited building layers)
### note that we are manually updating constructin progress in SDE, so we need to replace old excel ML with the updated one
1. Table to Excel for each building layer
2. Compile all the excel sheets into a single sheet

## E. Delete 'created_user', 'created"date', 'last_edited_user', and 'last_edited_date' from the exported excel ML

"""

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateN2StationStructures"
        self.alias = "pdateN2StationStructures"
        self.tools = [JustMessage, UpdateBuildingLayer, JustMessage2, ExportToExcel]

class JustMessage(object):
    def __init__(self):
        self.label = "1. (JUST MESSAGE): Update Target Dates in Excel ML using R code"
        self.description = "Run R code to update the excel ML with target construction dates"

class UpdateBuildingLayer(object):
    def __init__(self):
        self.label = "2. Update Building Layers in SDE using ML"
        self.description = "Update building layers using excel ML derived from P6 DB"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

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

        params = [ws, in_replaced_fc, in_ml]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_replaced_fc = params[1].valueAsText
        in_ml = params[2].valueAsText

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
            keepField = 'uniqueID'
            arcpy.DeleteField_management(output_name, [keepField], "KEEP_FIELDS")
            arcpy.AddMessage("All fields other than uniqueID were successfully deleted from " + output_name)

            # 3. Join Field
            ## 3.1. Remove uniqueID and OBJECTID from transferFiedls; otherwise, it fails
            fields = [f.name for f in arcpy.ListFields(in_ml)]
            transferFieldsRev = []
            for field in fields:
                try:
                    reg = re.search("uniqueID|^Object",field).group() 
                    if reg is None:
                        transferFieldsRev.append(field)
                except AttributeError:
                    reg = re.search("uniqueID|^Object",field)
                    if reg is None:
                        transferFieldsRev.append(field)
            arcpy.management.JoinField(output_name, keepField, in_ml, keepField, transferFieldsRev)
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
            expression = "reclass(!{}!)".format("uniqueID", "target_date", "Status")
            #arcpy.CalculateField_management(inputFeature, field_temp, expression, "PYTHON3", codeblock)

            # 4. Truncate the existing building layer
            arcpy.TruncateTable_management(layer)
            arcpy.AddMessage("The existing building layer, " + layer + " was successfully truncated for joining.")

            # 5. Append the updated copied to the existing building layer
            arcpy.Append_management(output_name, layer, schema_type = 'NO_TEST')
            arcpy.AddMessage("The existing building layer, " + layer + " was successfully updated.")

            # 6. Delete copied files
            arcpy.management.Delete(output_name)

class JustMessage2(object):
    def __init__(self):
        self.label = "3. (JUST MESSAGE): Update SDE manually, if necessary"
        self.description = "Manually update SDE only when necessary."

class ExportToExcel(object):
    def __init__(self):
        self.label = "4. Export Building Layers in SDE to Excel, if necessary"
        self.description = "Export each building layer to excel and compile into one sheet"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_replaced_fc = arcpy.Parameter(
            displayName = "Select Existing Building Layers",
            name = "Select Existing Building Layers ",
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

        params = [ws, in_replaced_fc, in_fl]
        return params

    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        workspace = params[0].valueAsText
        in_replaced_fc = params[1].valueAsText
        in_fl = params[2].valueAsText

        arcpy.env.overwriteOutput = True

        inputLayers = list(in_replaced_fc.split(";"))
        arcpy.AddMessage(inputLayers)

        # 1. merge all the input layers
        mergedLayer = "mergedLayers"
        arcpy.management.Merge(inputLayers, mergedLayer,"","")

        # 2. Sort by uniqueID
        sortedLayer = "sorted_mergedLayers"
        arcpy.Sort_management(mergedLayer, sortedLayer, [["uniqueID", "ASCENDING"]])

        # 3. Export to excel
        #home = Path.home()
        #path = os.path.join(home, "Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/02-Station Structure/01-Masterlist/01-Compiled")
        arcpy.conversion.TableToExcel(sortedLayer, os.path.join(in_fl, "N2_Station_Structure_P6ID_SDE.xlsx"))

        # 6. Delete copied files
        deletedLayers = [mergedLayer, sortedLayer]
        arcpy.management.Delete(deletedLayers)