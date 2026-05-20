import arcpy
import os

"""
# INSTRUCTION and DESCRIPTION
This python toolbox is used to convert Sentinel-1 C type GRD VV and VH polarized images to
ARD (Analysis Ready Detection) for visualization and analysis.

Please note that ARD is intended for visual analysis only? (still under confirmation)

* Make sure to download Orbit file and DEM before hand using Spyder in Anaconda.
* 'Download Orbit File' geoprocessing tool always fails due to unexpected error in ArcGIS Pro.
* The workaround is to download orbit file using Anaconda.

# 'Download Orbit File' geoprocessing tool always fails due to unexpected error
# One workaround is to open Anaconda,
# 1. run 'pip install sentineleof' in Powershell Prompt
# 2. Open Spyder
# 3. run the following using specified dates:
# reference: https://github.com/scottstanie/sentineleof

from eof.download import download_eofs
download_eofs(['20170805', '20170829'], ['S1A', 'S1A'])

Please make sure to follow steps below:
1. Download Orbit File
2. Apply Orbit Correction
3. Remove Thermal Noise
4. Radiometric Calibration
5. Radiometric terrain flattening
6. Despeckle
7. Geometric terrain correction
8. Convert SAR units

Reference: https://pro.arcgis.com/en/pro-app/3.0/help/analysis/image-analyst/analysis-ready-sentinel-1-grd-data-generation.htm

Then run 'Create Color Composite'
The purpose of running 'Create Color Composite' is to improve visualization for analysis.
Note that if imagery is decibel (which usually is), you need to specify RGB as follow:
Red: VV, Green: VH, Blue: VV-VH

if imagery is linear,
Red: VV, Green: VH, Blue: VV/VH
"""

class Toolbox(object):
    def __init__(self):
        self.label = "SARGRDtoARD"
        self.alias = "SARGRDtoARD"
        self.tools = [CreateARD, CreateColorComposite]

class CreateARD(object):
    def __init__(self):
        self.label = "1.Run conversion workflows"
        self.description = "Run 7 steps to convert GRD to ARD"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace (choose folder where SAR images are stored)",
            name = "workspace (choose folder where SAR images are stored)",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_radar = arcpy.Parameter(
            displayName = "Select input radar (manifest.safe)",
            name = "Select input radar (manifest.safe)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input" 
        )

        orbit_file = arcpy.Parameter(
            displayName = "Select corresponding orbit file (EOF)",
            name = "Select corresponding orbit file (EOF)",
            datatype = "DEFile",
            parameterType = "Required",
            direction = "Input" 
        )
        orbit_file.filter.list = ['EOF']

        output_folder = arcpy.Parameter(
            displayName = "Choose directory to store output",
            name = "Choose directory to store output",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )       

        in_dem = arcpy.Parameter(
            displayName = "Select DEM (digital elemation model)",
            name = "Select DEM (digital elemation model)",
            datatype = "GPRasterLayer",
            parameterType = "Required",
            direction = "Input" 
        )

        in_polarization = arcpy.Parameter(
            displayName = "Enter polarization (VV;VH)",
            name = "Enter polarization (VV;VH)",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input" 
        )

        params = [ws, in_radar, orbit_file, output_folder, in_dem, in_polarization]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        ws = params[0].valueAsText
        in_radar = params[1].valueAsText
        orbit_file = params[2].valueAsText
        out_folder = params[3].valueAsText
        in_dem = params[4].valueAsText
        polarization = params[5].valueAsText

        arcpy.env.workspace = ws
        arcpy.env.extent = "MINOF"
        #arcpy.env.overwriteOutput = True

        # 1. Apply Orbit Correction
        IW_manifest = arcpy.ia.ApplyOrbitCorrection(in_radar, orbit_file)

        arcpy.AddMessage("Orbit Correction is successfully done.")

        # 2. Remove Thermal Noise
        out_radar = os.path.join(out_folder, "IW_manifest_TNR.crf")
        outRadar = arcpy.ia.RemoveThermalNoise(IW_manifest, polarization)

        arcpy.AddMessage("Removal of thermal noise is successfully done.")

        # 3. Radiometric Calibration
        out_radar = os.path.join(out_folder, "IW_manifest_CalB0.crf")
        outRadar = arcpy.ia.ApplyRadiometricCalibration(outRadar, polarization, "BETA_NOUGHT")
        outRadar.save(out_radar)

        arcpy.AddMessage("Radiometric calibration is successfully done.")

        # 4. Radiometric terrain flattening
        out_radar = os.path.join(out_folder, "IW_manifest_CalB0_RTFG0.crf")
        outRadar = arcpy.ia.ApplyRadiometricTerrainFlattening(outRadar, in_dem, "GEOID", polarization, "GAMMA_NOUGHT")
        outRadar.save(out_radar)

        arcpy.AddMessage("Radiometric terrain flattening is successfully done.")

        # 5. Despeckle
        out_radar = os.path.join(out_folder, "IW_manifest_CalB0_RTFG0_Dspk.crf")
        outRadar = arcpy.ia.Despeckle(outRadar, polarization, "REFINED_LEE")
        outRadar.save(out_radar)

        arcpy.AddMessage("Despeckling is successfully done.")

        # 6. Geometric Terrain Calibration
        out_radar = os.path.join(out_folder, "IW_manifest_CalB0_RTFG0_Dspk_GTC.crf")
        geoid_correction = "GEOID"
        outRadar = arcpy.ia.ApplyGeometricTerrainCorrection(outRadar, polarization, in_dem, geoid_correction)
        outRadar.save(out_radar)

        arcpy.AddMessage("Geometric terrain calibration is successfully done.")

        # 7. Convert SAR Units to Decibels
        out_radar = os.path.join(out_folder, "IW_manifest_CalB0_RTFG0_Dspk_GTC_dB.crf")
        conversion_type = "LINEAR_TO_DB"
        outRadar = arcpy.ia.ConvertSARUnits(outRadar, conversion_type)
        outRadar.save(out_radar)

        arcpy.AddMessage("Units converstion to decibels is successfully done.")


class CreateColorComposite(object):
    def __init__(self):
        self.label = "2.Create Color Composite"
        self.description = "Use both VV and VH for improved visualization and analysis"

    def getParameterInfo(self):
        ws = arcpy.Parameter(
            displayName = "Workspace",
            name = "workspace",
            datatype = "DEWorkspace",
            parameterType = "Required",
            direction = "Input"
        )

        in_radar = arcpy.Parameter(
            displayName = "Select input radar ('IW_manifest_CalB0_RTFG0_Dspk_GTC_dB.crf')",
            name = "Select input radar ('IW_manifest_CalB0_RTFG0_Dspk_GTC_dB.crf')",
            datatype = "GPRasterLayer",
            parameterType = "Required",
            direction = "Input" 
        )

        output_folder = arcpy.Parameter(
            displayName = "Choose directory to store output",
            name = "Choose directory to store output",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )       

        params = [ws, in_radar, output_folder]
        return params
    
    def updateMessage(self, params):
        return
    
    def execute(self, params, messages):
        ws = params[0].valueAsText
        in_radar = params[1].valueAsText
        out_folder = params[2].valueAsText

        arcpy.env.workspace = ws

        out_radar = os.path.join(out_folder, "IW_manifest_CalB0_RTFG0_Dspk_GTC_dB_RGB.crf")
        method = "BAND_IDS"
        redExp = "B1" #VV
        greenExp = "B2" # VH
        blueExp = "B1-B2"

        arcpy.management.CreateColorComposite(in_radar, out_radar, method, redExp, greenExp, blueExp)










