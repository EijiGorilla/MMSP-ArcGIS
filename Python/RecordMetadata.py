# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 10:59:04 2020

@author: oc3512

This python script adds Metadata to target feature layer(s)
Please note that this script only works in built-in Python console of ArcGIS Pro
Using a standalone python script via Toolboxes will fail to execute this command.
"""

import arcpy
import os
from arcpy import metadata as md

inputFeatures = # Copy and paste in python console and drag and drop target layer(s)

# Add metadata
for layer in inputFeatures:
    new_md = md.Metadata()
    basename = os.path.basename(layer)
    #t1 = basename.split("nscrexbasedata.BASEUSER.",1)[1]
    t1 = basename
    t1 = t1.replace("X_ref_","") # remove bracket
    new_md.title = "{}".format(t1)
    #new_md.tags = 'Parcellary, NSCR-Ex, SC, Land Acquisition'
    new_md.tags = 'Trees, Compensation, MMSP'
    new_md.summary = 'This feature layer is used to monitoring trees for compensation. Data Source: Morimoto (July 29th, 2020. OCG mail).'
    tgt_item_md = md.Metadata(layer)
    if not tgt_item_md.isReadOnly:
        tgt_item_md.copy(new_md)
        tgt_item_md.save()