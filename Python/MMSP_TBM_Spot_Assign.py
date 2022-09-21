# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 14:38:43 2022

This code assigns tbmSpot to TBM segmented line layer

@author: oc3512
"""
import arcpy

arcpy.env.overwriteOutput = True

# Script parameters
workSpace = arcpy.GetParameterAsText(0)
inputLayer = arcpy.GetParameterAsText(1)

## collect all the line values first

with arcpy.da.SearchCursor(inputLayer, "line") as cursor:
    uniqueList = []
    for row in cursor:
        if row[0] not in uniqueList:
            uniqueList.append(row[0])

"""
['TBM6', 'TBM5', 'TBM1',
'TBM2', 'TBM3', 'TBM4', 
'05 Camp Aguinaldo to Ortigas_S', '04 Camp Aguinaldo to Anonas_S','10 Lawton to Senate_S',
'10 Lawton to Senate_N', '09 Lawton to BGC_N', '09 Lawton to BGC_S',
'07 Shaw to Kalayaan_S', '08 Kalayaan to BGC_S', '06 Shaw to Ortigas_S',
'07 Shaw to Kalayaan_N', '08 Kalayaan to BGC_N', '02 QC Ave to East Ave_S',
'01 North Ave to QC Ave_S', '05 Camp Aguinaldo to Ortigas_N', '06 Ortigas to Shaw_N',
'01 North Ave to QC Ave_N', '02 East Ave to QC Ave_N', '03 Anonas to East Ave_N',
'03 Anonas to East Ave_S', '04 Camp Aguinaldo to Anonas_N', '11 Senate to T3_S', '11 Senate to T3_N']
"""
# PO
TBM1 = []
TBM2 = []
TBM3 = []
TBM4 = []
TBM5 = []
TBM6 = []

# Remaining Section
TBM1_s = []
TBM1_n = []
TBM2_s = []
TBM2_n = []
TBM3_s = []
TBM3_n = []
TBM4_s = []
TBM4_n = []
TBM5_s = []
TBM5_n = []
TBM6_s = []
TBM6_n = []
TBM7_s = []
TBM7_n = []
TBM8_s = []
TBM8_n = []
TBM9_s = []
TBM9_n = []
TBM10_s = []
TBM10_n = []
TBM11_s = []
TBM11_n = []

# First collect segment Numbers for each TBM line where status is completed
fields = ["line","segmentno","status"]
with arcpy.da.SearchCursor(inputLayer, fields) as cursor:
    for row in cursor:
        # PO Section
        if row[0] == 'TBM1' and row[2] == 4:
            TBM1.append(row[1])
        elif row[0] == 'TBM2' and row[2] == 4:
            TBM2.append(row[1])
        elif row[0] == 'TBM3' and row[2] == 4:
            TBM3.append(row[1])
        elif row[0] == 'TBM4' and row[2] == 4:
            TBM4.append(row[1])
        elif row[0] == 'TBM5' and row[2] == 4:
            TBM5.append(row[1])
        elif row[0] == 'TBM6' and row[2] == 4:
            TBM6.append(row[1])

        # Remaining Section
        elif row[0] == '01 North Ave to QC Ave_S' and row[2] == 4:       
            TBM1_s.append(row[1])
        elif row[0] == '01 North Ave to QC Ave_N' and row[2] == 4:               
            TBM1_n.append(row[1])
        elif row[0] == '02 QC Ave to East Ave_S' and row[2] == 4:             
            TBM2_s.append(row[1])
        elif row[0] == '02 East Ave to QC Ave_N' and row[2] == 4:            
            TBM2_n.append(row[1])
        elif row[0] == '03 Anonas to East Ave_S' and row[2] == 4:
            TBM3_s.append(row[1])
        elif row[0] == '03 Anonas to East Ave_N' and row[2] == 4:
            TBM3_n.append(row[1])
        elif row[0] == '04 Camp Aguinaldo to Anonas_S' and row[2] == 4:            
            TBM4_s.append(row[1])
        elif row[0] == '04 Camp Aguinaldo to Anonas_N' and row[2] == 4:                     
            TBM4_n.append(row[1])
        elif row[0] == '05 Camp Aguinaldo to Ortigas_S' and row[2] == 4:   
            TBM5_s.append(row[1])
        elif row[0] == '05 Camp Aguinaldo to Ortigas_N' and row[2] == 4:   
            TBM5_n.append(row[1])
        elif row[0] == '06 Shaw to Ortigas_S' and row[2] == 4:          
            TBM6_s.append(row[1])
        elif row[0] == '06 Shaw to Ortigas_N' and row[2] == 4:          
            TBM6_n.append(row[1])
        elif row[0] == '07 Shaw to Kalayaan_S' and row[2] == 4:          
            TBM7_s.append(row[1])
        elif row[0] == '07 Shaw to Kalayaan_N' and row[2] == 4:          
            TBM7_n.append(row[1])
        elif row[0] == '08 Kalayaan to BGC_S' and row[2] == 4:                   
            TBM8_s.append(row[1])
        elif row[0] == '08 Kalayaan to BGC_N' and row[2] == 4:                   
            TBM8_n.append(row[1])
        elif row[0] == '09 Lawton to BGC_S' and row[2] == 4:                   
            TBM9_s.append(row[1])
        elif row[0] == '09 Lawton to BGC_N' and row[2] == 4:                   
            TBM9_n.append(row[1])
        elif row[0] == '10 Lawton to Senate_S' and row[2] == 4:                   
            TBM10_s.append(row[1])
        elif row[0] == '10 Lawton to Senate_N' and row[2] == 4:                   
            TBM10_n.append(row[1])
        elif row[0] == '11 Senate to T3_S' and row[2] == 4:                   
            TBM11_s.append(row[1])
        elif row[0] == '11 Senate to T3_N' and row[2] == 4:                   
            TBM11_n.append(row[1])


# Now fill in tbmSpot
fields1 = ["line","segmentno","tbmSpot"] 
with arcpy.da.UpdateCursor(inputLayer, fields1) as cursor:
    for row in cursor:
        try:
            # PO Section
            if row[0] == "TBM1" and row[1] == max(TBM1):
                row[2] = 1
            elif row[0] == "TBM2" and row[1] == max(TBM2):
                row[2] = 1
            elif row[0] == "TBM3" and row[1] == max(TBM3):
                row[2] = 1
            elif row[0] == "TBM4" and row[1] == max(TBM4):
                row[2] = 1
            elif row[0] == "TBM5" and row[1] == max(TBM5):
                row[2] = 1
            elif row[0] == "TBM6" and row[1] == max(TBM6):
                row[2] = 1

            # Remaining Section
        # Remaining Section
            elif row[0] == '01 North Ave to QC Ave_S' and row[1] == max(TBM1_s):       
                TBM1_s.row[2] = 1
            elif row[0] == '01 North Ave to QC Ave_N' and row[1] == max(TBM1_n):               
                TBM1_n.row[2] = 1
            elif row[0] == '02 QC Ave to East Ave_S' and row[1] == max(TBM2_s):             
                TBM2_s.row[2] = 1
            elif row[0] == '02 East Ave to QC Ave_N' and row[1] == max(TBM2_n):            
                TBM2_n.row[2] = 1
            elif row[0] == '03 Anonas to East Ave_S' and row[1] == max(TBM3_s):
                TBM3_s.row[2] = 1
            elif row[0] == '03 Anonas to East Ave_N' and row[1] == max(TBM3_n):
                TBM3_n.row[2] = 1
            elif row[0] == '04 Camp Aguinaldo to Anonas_S' and row[1] == max(TBM4_s):            
                TBM4_s.row[2] = 1
            elif row[0] == '04 Camp Aguinaldo to Anonas_N' and row[1] == max(TBM4_n):                     
                TBM4_n.row[2] = 1
            elif row[0] == '05 Camp Aguinaldo to Ortigas_S' and row[1] == max(TBM5_s):   
                TBM5_s.row[2] = 1
            elif row[0] == '05 Camp Aguinaldo to Ortigas_N' and row[1] == max(TBM5_n):   
                TBM5_n.row[2] = 1
            elif row[0] == '06 Shaw to Ortigas_S' and row[1] == max(TBM6_s):          
                TBM6_s.row[2] = 1
            elif row[0] == '06 Shaw to Ortigas_N' and row[1] == max(TBM6_n):          
                TBM6_n.row[2] = 1
            elif row[0] == '07 Shaw to Kalayaan_S' and row[1] == max(TBM7_s):          
                TBM7_s.row[2] = 1
            elif row[0] == '07 Shaw to Kalayaan_N' and row[1] == max(TBM7_n):          
                TBM7_n.row[2] = 1
            elif row[0] == '08 Kalayaan to BGC_S' and row[1] == max(TBM8_s):                   
                TBM8_s.row[2] = 1
            elif row[0] == '08 Kalayaan to BGC_N' and row[1] == max(TBM8_n):                   
                TBM8_n.row[2] = 1
            elif row[0] == '09 Lawton to BGC_S' and row[1] == max(TBM9_s):                   
                TBM9_s.row[2] = 1
            elif row[0] == '09 Lawton to BGC_N' and row[1] == max(TBM9_n):                   
                TBM9_n.row[2] = 1
            elif row[0] == '10 Lawton to Senate_S' and row[1] == max(TBM10_s):                   
                TBM10_s.row[2] = 1
            elif row[0] == '10 Lawton to Senate_N' and row[1] == max(TBM10_n):                   
                TBM10_n.row[2] = 1
            elif row[0] == '11 Senate to T3_S' and row[1] == max(TBM11_s):                   
                TBM11_s.row[2] = 1
            elif row[0] == '11 Senate to T3_N' and row[1] == max(TBM11_n):                   
                TBM11_n.row[2] = 1
            cursor.updateRow(row)
        except:
            pass
