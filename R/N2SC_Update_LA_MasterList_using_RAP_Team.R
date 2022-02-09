tool_exec=function(in_params,out_params){

# This R code reads all excel master list tables provided by the RAP Team
# Note that the RAP Team uses OneDrive to store all the exce tables
# Source URL: https://ocggcrconsurtium-my.sharepoint.com/personal/w_caras-rap_gcr-consortium_com/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Fw%5Fcaras%2Drap%5Fgcr%2Dconsortium%5Fcom%2FDocuments%2FSmart%20Map%20Database)

# For now, as I cannot access the URL using R code.
# 1. Download and copy all excel sheets from the source URL to your local folder
# 2. Read GIS master list
# 3. Read and import source masterl list from RAP Team's OneDrive in this R interface.
# 4. Check and edit the source excel master list tables if necessary
# 5. Update GIS excel master list tables using the downloaded source excel master list tables

library(openxlsx)
library(dplyr)
library(stringr)
library(fs)

#
  
#wd = in_params[[1]] # Working directory
#previous_date = in_params[[2]] # just string. 2022-01-26
#result = out_params[[1]]
previous_date = "2022-01-17" 
new_date = "2022-01-25"


# 1. Make sure that all the excel files are downloaded from the RAP Team's OneDrive in the following working directory;----
path = path_home()


# Parameter setting
wd_rap = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/99-MasterList_RAP_Team")
wd_gis_sc = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/02-SC/02-Pre-Construction/01-Environment/01-LAR/99-MasterList/03-Compiled")
wd_gis_n2 = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/01-LAR/99-MasterList/03-Compiled")

# 2. Read GIS masterlist;-----
## 2.1. N2 GIS master list:----
n2_lot = file.path(wd_gis_n2,"N2_Land_Status.xlsx")
n2_struc = file.path(wd_gis_n2,"N2_Structure_Status.xlsx")
n2_isf = file.path(wd_gis_n2, "N2_ISF_Relocation.xlsx")

print("Good up to this point")

n2_lot_gis = read.xlsx(n2_lot)
n2_struc_gis = read.xlsx(n2_struc)
n2_isf_gis = read.xlsx(n2_isf)


## 2.2. SC GIS master list:----
sc_lot = file.path(wd_gis_sc,"SC_Land_Status.xlsx")
sc_struc = file.path(wd_gis_sc,"SC_Structure_Status.xlsx")
sc_isf = file.path(wd_gis_sc, "SC_ISF_Relocation.xlsx")
sc1_barang = file.path(wd_gis_sc, "SC1_Barangay_Status.xlsx")


sc_lot_gis = read.xlsx(sc_lot)
sc_struc_gis = read.xlsx(sc_struc)
sc_isf_gis = read.xlsx(sc_isf)
sc1_barang_gis = read.xlsx(sc1_barang)

# 3. Read tables from the RAP Team's OneDrive
## 3.1. N2:----
n2_lot1 = file.path(wd_rap, "N2_Parcellary_masterlist_compiled.xlsx")
n2_struc1 = file.path(wd_rap, "N2_Structure_masterlist_compiled.xlsx")
n2_isf1 = file.path(wd_rap, "N2_Structure_Relocation_compiled.xlsx")

n2_lot_rap = read.xlsx(n2_lot1)
n2_struc_rap = read.xlsx(n2_struc1)
n2_isf_rap = read.xlsx(n2_isf1)

## 3.2. SC:----
### 3.2.1. SC:----
sc_lot1 = file.path(wd_rap, "SC_Parcellary_masterlist_compiled.xlsx")
sc_struc1 = file.path(wd_rap, "SC_Structure_masterlist_compiled.xlsx")
# sc_isf1 = file.path(wd_rap, "SC_Structure_Relocation_compiled.xlsx")

sc_lot_rap = read.xlsx(sc_lot1)
sc_struc_rap = read.xlsx(sc_struc1)


### 3.2.2. SC1 (Contractors' Submission):----
sc1_lot = file.path(wd_rap, "SC1_Parcellary_masterlist_compiled.xlsx")
sc1_struc = file.path(wd_rap, "SC1_Structure_masterlist_compiled.xlsx")
sc1_barang = file.path(wd_rap, "SC1_Brgy_masterlist_compiled.xlsx")

sc1_lot_rap = read.xlsx(sc1_lot)
sc1_struc_rap = read.xlsx(sc1_struc)
sc1_barang_rap = read.xlsx(sc1_barang)

sc1_lot_rap$ContSubm = 1 # we need to define this to filter by lot based on Contractors submission
sc1_struc_rap$ContSubm = 1


# 4. Check and edit the source excel master list tables if necessary:----
## 4.1. Edit column names "Mucnicipality"
## Municipality or Barangay
colNames = colnames(n2_lot_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(n2_lot_rap)[id] = "Municipality"

colNames = colnames(n2_struc_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(n2_struc_rap)[id] = "Municipality"

colNames = colnames(n2_isf_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(n2_isf_rap)[id] = "Municipality"

colNames = colnames(sc_lot_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(sc_lot_rap)[id] = "Municipality"

colNames = colnames(sc_struc_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(sc_struc_rap)[id] = "Municipality"

## LandUse for LOT
### 1: Agricultural
### 2: Agricultural & Commercial
### 3. Agricultural / Residential
### 4. Commercial
### 5. Industrial
### 6. Irrigation
### 7. Residential
### 8. Road
### 9. Road Lot
### 10. Special Exempt
head(n2_lot_rap)
unique(n2_lot_rap$LandUse)

id1 = which(str_detect(n2_lot_rap$LandUse,"^AGRICULTURAL$|^Agricultural$|^agricultural$"))
id2 = which(str_detect(n2_lot_rap$LandUse, "^AGRI.*CIAL$|^Agri.*cial$"))
id3 = which(str_detect(n2_lot_rap$LandUse, "^AGRI.*TIAL$|^Agri.*tial$"))
id4 = which(str_detect(n2_lot_rap$LandUse, "^COM|^Com"))
id5 = which(str_detect(n2_lot_rap$LandUse, "^INDUS|^Indus"))
id6 = which(str_detect(n2_lot_rap$LandUse, "^IRRIG|^Irrig"))
id7 = which(str_detect(n2_lot_rap$LandUse, "^RESID|^Resid"))
id8 = which(str_detect(n2_lot_rap$LandUse, "^ROAD$|^Road$"))
id9 = which(str_detect(n2_lot_rap$LandUse, "^ROAD.*LOT$|^ROAD.*Lot$"))
id10 = which(str_detect(n2_lot_rap$LandUse, "^SPECIAL.*MPT$|^Special.*mpt$"))


n2_lot_rap$LandUse[id1] = 1
n2_lot_rap$LandUse[id2] = 2
n2_lot_rap$LandUse[id3] = 3
n2_lot_rap$LandUse[id4] = 4
n2_lot_rap$LandUse[id5] = 5
n2_lot_rap$LandUse[id6] = 6
n2_lot_rap$LandUse[id7] = 7
n2_lot_rap$LandUse[id8] = 8
n2_lot_rap$LandUse[id9] = 9
n2_lot_rap$LandUse[id10] = 10

n2_lot_rap$LandUse = as.numeric(n2_lot_rap$LandUse)
## StrucUse for Structure
### 1: Agricultural
### 2: Agricultural & Commercial
### 3. Agricultural / Residential
### 4. Commercial
### 5. Industrial
### 6. Irrigation
### 7. Residential
### 8. Road
### 9. Road Lot
### 10. Special Exempt

unique(n2_struc_rap$StructureUse)
id1 = which(str_detect(n2_struc_rap$StructureUse,"^RESID|^Resid"))
id2 = which(str_detect(n2_struc_rap$StructureUse, "^COM|^Com"))
id3 = which(str_detect(n2_struc_rap$StructureUse, "^RESID.*CIAL$|^Resid.*cial$"))
id4 = which(str_detect(n2_struc_rap$StructureUse, "^ASSOCI|^Associ"))
id5 = which(str_detect(n2_struc_rap$StructureUse, "^INDUST|^Indust"))
id6 = which(str_detect(n2_struc_rap$StructureUse, "^INSTI|^InSTI"))
id7 = which(str_detect(n2_struc_rap$StructureUse, "^INSTI.*NITY$|^Insti.*nity$"))
id8 = which(str_detect(n2_struc_rap$StructureUse, "^OTHER|^Other"))


n2_struc_rap$StructureUse[id1] = 1
n2_struc_rap$StructureUse[id2] = 2
n2_struc_rap$StructureUse[id3] = 3
n2_struc_rap$StructureUse[id4] = 4
n2_struc_rap$StructureUse[id5] = 5
n2_struc_rap$StructureUse[id6] = 6
n2_struc_rap$StructureUse[id7] = 7
n2_struc_rap$StructureUse[id8] = 8

n2_struc_rap$StructureUse = as.numeric(n2_struc_rap$StructureUse)

## Contractor's Submission 
colNames = colnames(sc1_lot_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(sc1_lot_rap)[id] = "Municipality"

colNames = colnames(sc1_struc_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(sc1_struc_rap)[id] = "Municipality"

colNames = colnames(sc1_barang_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(sc1_barang_rap)[id] = "Municipality"

colNames = colnames(sc1_barang_rap)
id = which(str_detect(colNames,"^Bgy|^bgy|^Barang|^barang"))
colnames(sc1_barang_rap)[id] = "Barangay"

## Priority (convert to numeric)
n2_lot_rap$Priority = as.numeric(n2_lot_rap$Priority)
sc_lot_rap$Priority = as.numeric(sc_lot_rap$Priority)
sc_lot_rap$Priority = as.numeric(sc_lot_rap$Priority)
sc1_lot_rap$Priority1 = as.numeric(sc1_lot_rap$Priority1)

## Remove redundant space for uqniue ID: LotID, StrucID, barangay
n2_lot_rap$LotID[] = gsub("[[:space:]]","",n2_lot_rap$LotID)
n2_struc_rap$StrucID[] = gsub("[[:space:]]","",n2_struc_rap$StrucID)
n2_isf_rap$StrucID[] = gsub("[[:space:]]","",n2_isf_rap$StrucID)

sc_lot_rap$LotID[] = gsub("[[:space:]]","",sc_lot_rap$LotID)
sc_struc_rap$StrucID[] = gsub("[[:space:]]","",sc_struc_rap$StrucID)

sc1_lot_rap$LotID[] = gsub("[[:space:]]","",sc1_lot_rap$LotID)
sc1_struc_rap$StrucID[] = gsub("[[:space:]]","",sc1_struc_rap$StrucID)

sc1_barang_rap$Barangay[] = gsub("^Barangay","",sc1_barang_rap$Barangay)
sc1_barang_rap$Barangay[] = gsub("^\\s|\\s$","",sc1_barang_rap$Barangay)

sc1_barang_rap$Subcon[] = gsub("^\\s|\\s$","",sc1_barang_rap$Subcon)


### 4.2. Join SC Land to SC1 Land, SC1 Structure to SC structure in the RAP Teams+----
####### SC Lot
id = which(str_detect(colnames(sc1_lot_rap),"LotID|Subcon|Priority1|Reqs|ContSubm"))
y = sc1_lot_rap[,id]
xy = left_join(sc_lot_rap,y,by="LotID")
sc_lot_rap = xy

## Check if there are any missing LotID between SC Lot and joined table (i.e., xy)
sc1_lot_iid = y$LotID
sc_lot_iid = xy$LotID[which(xy$ContSubm==1)]

if(length(sc1_lot_iid)!= length(sc_lot_iid)){
  ## Identify LotID missing in sc_lot_rap
  sc1_lot_iid[!sc1_lot_iid %in% sc_lot_iid]
  
  ## Identify LotID missing in sc1_lot_rap
  sc_lot_iid[!sc_lot_iid %in% sc1_lot_iid]
} else {
  print("LotIDs match between sc_lot_rap and sc1_lot_rap")
}


####### SC Structure
id = which(str_detect(colnames(sc1_struc_rap),"StrucID|Subcon|BasicPlan|ContSubm"))
y = sc1_struc_rap[,id]
xy = left_join(sc_struc_rap,y,by="StrucID")
sc_struc_rap = xy

## Check if there are any missing StrucID between SC struc and joined table (i.e., xy)
sc1_struc_iid = y$StrucID
sc_struc_iid = xy$StrucID[which(xy$ContSubm==1)]

if(length(sc1_struc_iid)!= length(sc_struc_iid)){
  ## Identify LotID missing in sc_struc_rap
  sc1_struc_iid[!sc1_struc_iid %in% sc_struc_iid]
  
  ## Identify LotID missing in sc1_struc_rap
  sc_struc_iid[!sc_struc_iid %in% sc1_struc_iid]
} else {
  print("StrucIDs match between sc_struc_rap and sc1_struc_rap")
}

## In the subsequent sections, No Need to Consider "sc1_lot", "sc1_struc"

# 5. Update GIS excel master list tables using the downloaded source excel master list tables;-----
## 5.1. Create backup files first;----
backup_dir_n2 = file.path(wd_gis_n2,"Backup")
backup_dir_sc = file.path(wd_gis_sc,"Backup")

# N2 Land, N2 Structure
#
SC1_Barangay_fileName = "SC1_Barangay_Status.xlsx"
backupF = function(){
  write.xlsx(n2_lot_gis, file.path(backup_dir_n2,paste(gsub("-","",previous_date),"_",basename(n2_lot),sep="")))
  write.xlsx(n2_struc_gis, file.path(backup_dir_n2,paste(gsub("-","",previous_date),"_",basename(n2_struc),sep="")))
  write.xlsx(n2_isf_gis, file.path(backup_dir_n2,paste(gsub("-","",previous_date),"_",basename(n2_isf),sep="")))
  
  # SC Land, SC Structure. SC Barangay
  write.xlsx(sc_lot_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_lot),sep="")))
  write.xlsx(sc_struc_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_struc),sep="")))
  write.xlsx(sc_isf_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_isf),sep="")))
  
  # barangay
  write.xlsx(sc1_barang_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",SC1_Barangay_fileName,sep="")))
}

tryCatch(backupF(),
         error = function(e)
           print("You can't calculate the log of a character"))

## 5.2. Add "SCale" from old master list to the new master list from the RAP Team
## N2 Lot
n2_lot_rap = n2_lot_rap[,-which(colnames(n2_lot_rap)=="Scale")]
y = n2_lot_gis[,c("LotID","Scale")]
n2_lot_rap = left_join(n2_lot_rap,y,by="LotID")

## SC Lot
sc_lot_rap = sc_lot_rap[,-which(colnames(sc_lot_rap)=="Scale")]
y = sc_lot_gis[,c("LotID","Scale")]
sc_lot_rap = left_join(sc_lot_rap,y,by="LotID")


## Final Export
## Basically, we will overwrite the RAP Team's excel master list tables that are edited in this code.
## and the GIS master list table are replaced with the edited tables (i.e., overwrite)

### N2
write.xlsx(n2_lot_rap,file.path(wd_gis_n2,basename(n2_lot)),overwrite=TRUE)
write.xlsx(n2_struc_rap,file.path(wd_gis_n2,basename(n2_struc)),overwrite=TRUE)
write.xlsx(n2_isf_rap,file.path(wd_gis_n2,basename(n2_isf)),overwrite=TRUE)

### SC
write.xlsx(sc_lot_rap,file.path(wd_gis_sc,basename(sc_lot)),overwrite=TRUE)
write.xlsx(sc_struc_rap,file.path(wd_gis_sc,basename(sc_struc)),overwrite=TRUE)
#write.xlsx(sc_isf_rap,file.path(wd_gis_sc,basename(sc_isf)))
write.xlsx(sc1_barang_rap,file.path(wd_gis_sc,SC1_Barangay_fileName),overwrite=TRUE)


# Output
#arc.write(result, sc1_barang_rap, overwrite = TRUE)
#return(out_params)


}