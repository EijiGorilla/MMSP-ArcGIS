import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "UpdateLandAcquisition"
        self.alias = "UpdateLandAcquisition"
        self.tools = [UpdateFGDB, UpdateSDE, UpdateUsingMasterList]

class UpdateFGDB(object):
    def __init__(self):
        self.label = "Update File Geodatabase"
        self.description = "Update feature layers in file geodatabase for land, structure, and ISF of N2/SC"

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

        # 1. Copy
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
            MasterListN2Pier = arcpy.TableToTable_conversion(mlPier, workspace, 'MasterListN2Pier')
            
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

        #######################################################################################
        #######################################################################################
            
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
        MasterListLot = arcpy.TableToTable_conversion(mlLot, workspace, 'MasterListLot')
        MasterListStruc = arcpy.TableToTable_conversion(mlStruct, workspace, 'MasterListStruc')
            
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
        MasterListISF = arcpy.TableToTable_conversion(mlISF, workspace, 'MasterListISF')

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
        sr = arcpy.SpatialReference(32651)
        outLayerISF = arcpy.management.XYTableToPoint(MasterListISF, out_feature_class, xCoords, yCoords, zCoords, sr)


        ### Delete 'POINT_X', 'POINT_Y', 'POINT_Z'; otherwise, it gives error for the next batch
        dropXYZ = [xCoords, yCoords, zCoords]
        arcpy.DeleteField_management(outLayerISF, dropXYZ)

        ## 2-2.4. Add Domain
        
        ## 2-2.5. Truncate original ISF point FL
        arcpy.TruncateTable_management(inISF)

        ## 2-2.6. Append to the Original ISF
        arcpy.Append_management(outLayerISF, inISF, schema_type = 'NO_TEST')

        ###########################################################################
        ##### STAGE 3: Convert 0 to Null ######
        ###########################################################################
        paid = "Paid"
        handOver = "HandOver"
        moa = "MoA"
        relocated = "Relocated"
        status = "Status"
        pte = "PTE"
        #barang = "Barangay"

        varFieldLA = [paid, handOver, moa, pte]
        varFieldStruc = [paid, handOver, moa, status, pte]
        varFieldOccup= [paid, moa, status]
        varFieldISF = [paid, relocated]
        #varFieldBarang = [barang]
        
        codeblock = """
        def reclass(status):
            if status == None:
                return None
            elif status == 0:
                return None
            else:
                return status"""
            
        #Apply to four layers: 'Status for LA', 'Status of Structure', 'Status of Relocation (occupany)', and
        # 'Status for Relocation (ISF)'

        ## 1. Status for LA
        for field in varFieldLA:
            arcpy.AddMessage(field)
            expression = "reclass(!{}!)".format(field)
                
            # Execute CalculateField
            arcpy.CalculateField_management(inLot, field, expression, "PYTHON3", codeblock)
            
            ## 2. Status for Structure
        for field in varFieldStruc:
            arcpy.AddMessage(field)
            expression = "reclass(!{}!)".format(field)
                
            # Execute CalculateField
            arcpy.CalculateField_management(inStruc, field, expression, "PYTHON3", codeblock)
        ## 2. Status for Relocation (Occupancy)
        for field in varFieldOccup: 
            arcpy.AddMessage(field)
            expression = "reclass(!{}!)".format(field)
                
            # Execute CalculateField
            arcpy.CalculateField_management(inOccup, field, expression, "PYTHON3", codeblock)
            
            ## 3. Status for Relocation (ISF)
        for field in varFieldISF:
            arcpy.AddMessage(field)
            expression = "reclass(!{}!)".format(field)
            
            # Execute CalculateField
            arcpy.CalculateField_management(inISF, field, expression, "PYTHON3", codeblock)    

        """
            ## 4. Status for Barangay
        for field in varFieldBarang:
            arcpy.AddMessage(field)
            expression = "reclass(!{}!)".format(field)
                
            # Execute CalculateField
            arcpy.CalculateField_management(inputLayerBarangOrigin, field, expression, "PYTHON3", codeblock)  
        """

        # Delete the copied feature layer
        deleteTempLayers = [copyLot, copyStruc, pointStruc, outLayerISF, MasterListLot, MasterListStruc, MasterListISF]
        arcpy.Delete_management(deleteTempLayers)

class UpdateSDE(object):
    def __init__(self):
        self.label = "Update Enterprise Geodatabase"
        self.description = "Update feature layers in enterprise geodatabase for land, structure, and ISF of N2/SC"

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
        self.label = "Update Feature Layer using Excel Master List"
        self.description = "Update any type of feature layers using excel master list table"

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
        MasterList = arcpy.TableToTable_conversion(ml, workspace, 'MasterList')

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

