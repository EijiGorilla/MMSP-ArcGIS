from pathlib import Path
import sys

from arcgis.gis import GIS, Item
from arcgis.features import FeatureLayerCollection
from arcgis.mapping import WebMap
from datetime import datetime
import arcpy
import os
import pandas as pd
import numpy as np
from arcgis.features.managers import FeatureLayerManager
from arcgis import features
from arcgis import geometry
from copy import deepcopy

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateHostedFeatureLayer"
        self.alias = "UpdateHostedFeatureLayer"
        self.tools = [UpdateHosted]

class UpdateHosted(object):
    def __init__(self):
        self.label = "Update Hosted Feature Layer using Excel"
        self.description = "Update Hosted Feature Layer using Excel"

    def getParameterInfo(self):
        url_agol = arcpy.Parameter(
            displayName = "ArcGIS Online URL (e.g., https://mmsp.maps.arcgis.com)",
            name = "ArcGIS Online URL (e.g., https://mmsp.maps.arcgis.com)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
                
        username_agol = arcpy.Parameter(
            displayName = "Username (AGOL)",
            name = "Username (AGOL)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        passw_agol = arcpy.Parameter(
            displayName = "Password (AGOL)",
            name = "Password (AGOL)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        itemid_agol = arcpy.Parameter(
            displayName = "Target Hosted Feature Layer (Enter item id from AGOL)",
            name = "Target Hosted Feature Layer (Enter item id from AGOL)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )

        input_table_excel = arcpy.Parameter(
            displayName = "Input Table (Excel)",
            name = "Join GIS Land Status Table (GIS Feature Layer)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input"
        )

        join_field = arcpy.Parameter(
            displayName = "Join Field (Common Field Name)",
            name = "Join Field (Common Field Name)",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input"
        )
        join_field.parameterDependencies = [input_table_excel.name]

        transfer_fields = arcpy.Parameter(
            displayName = "Two Transfer Fields: (ONLY two fields in this order: Status and date fields) from Input Table",
            name = "Two Transfer Fields: (ONLY two fields in this order: Status and date fields) from Input Table",
            datatype = "Field",
            parameterType = "Required",
            direction = "Input",
            multiValue = True
        )
        transfer_fields.parameterDependencies = [input_table_excel.name]

        params = [url_agol, username_agol, passw_agol, itemid_agol, input_table_excel, join_field, transfer_fields]
        return params

    def updateMessages(self, params):
        return
    
    def execute(self, params, messages):
        url_agol = params[0].valueAsText
        username_agol = params[1].valueAsText
        passw_agol = params[2].valueAsText
        itemid_agol = params[3].valueAsText
        input_table_excel = params[4].valueAsText
        join_field = params[5].valueAsText
        transfer_fields = params[6].valueAsText

        def match_elements(list_a, list_b):
            matched = []
            for i in list_a:
                if i in list_b:
                    matched.append(i)
            return matched

        arcpy.env.overwriteOutput = True

        # 1. Log in 
        gis = GIS(url_agol, username_agol, passw_agol)

        # 2. Read target hosted feature layer
        fsItemId = itemid_agol # Choose associated feature layer for scene layer
        featureLayer = gis.content.get(fsItemId)
        target_layer = featureLayer.layers[0]

        ## querying without any conditions returns all the features
        target_fset = target_layer.query()
        target_fset.sdf.head()

        ## first get all features
        all_target_features = target_fset.features
        all_target_features[0]

        # 3. Read input table
        input_table = pd.read_excel(input_table_excel)
        input_table.head()

        # 4. Update Hosted Feature Layer
        for_update = []
        uniqueIDs = [f for f in input_table[join_field]]

        # Ensure that join field and transfer fields you entered match 
        t_fields = list(transfer_fields.split(";"))
        input_fields = [f for f in input_table.columns]
        
        match_field_join = match_elements(input_fields, [join_field])
        match_field_transfer = match_elements(input_fields, t_fields)

        if len(match_field_join) > 0 and len(match_field_transfer) == len(t_fields):
            for unique_id in uniqueIDs:
                # Status for target
                original_feature = [f for f in all_target_features if f.attributes[join_field] == unique_id][0]
                to_be_updated = deepcopy(original_feature)

                # get the status for input and target layers
                ## Input 
                id = input_table.index[input_table[join_field] == unique_id]

                # if input fields are null, we can simply skip
                try: # Both status and targets
                    status_input = input_table[t_fields[0]].loc[id].iloc[0]
                    enddate_input = pd.to_datetime(input_table[t_fields[1]].loc[id].iloc[0]).date()
 
                    ## Target
                    status_target = original_feature.attributes[t_fields[0]]
                    objectid_target = original_feature.attributes['OBJECTID']
                    
                    timestamp = original_feature.attributes[t_fields[1]] / 1000
                    enddate_target = datetime.fromtimestamp(timestamp).date()

                    ## If input and target does not match in status and end_date, append to for_update list
                    if status_input != status_target or enddate_input != enddate_target:
                        to_be_updated = {
                            'attributes': {
                                'OBJECTID': objectid_target,
                                t_fields[0] : status_input,
                                t_fields[1] : enddate_input
                            }
                        }
                        for_update.append(to_be_updated)
                        arcpy.AddMessage("UniqueID: {}, to_be_updated: {}".format(unique_id, to_be_updated))
                except:
                    pass

            # Update target hosted feature layer
            if len(for_update) == 0:
                arcpy.AddMessage('No need to update target feature layer')
            else:
                target_layer.edit_features(updates=for_update)
        else:
            arcpy.AddMessage("Either join field or transfer fields you endered cannot be found in your excel sheets.")
            arcpy.AddMessage("Operation stopped.")
            pass
                