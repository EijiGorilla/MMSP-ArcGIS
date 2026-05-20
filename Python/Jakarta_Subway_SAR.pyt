import arcpy
import os
import re
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import string

class Toolbox(object):
    def __init__(self):
        self.label = "CreateFishnet3D"
        self.alias = "CreateFishnet3D"
        self.tools = [Fishnet3DLineTool]

class Fishnet3DLineTool(object):
    def __init__(self):
        self.label = "Create Fishnet 3D Line"
        self.description = "Creates a 3D fishnet line feature class based on specified parameters."

    def getParameterInfo(self):
        fishnet_polygon_layer = arcpy.Parameter(
            displayName = "Fishnet polygon
            name = "SAR Points Layer",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input",
        )