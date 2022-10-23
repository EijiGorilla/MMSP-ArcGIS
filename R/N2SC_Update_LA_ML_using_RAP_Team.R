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
library(lubridate)

#
  
#rapFolder = in_params[[1]] # Directory where you saved master list excel tables from the RAP Team 
#previous_date = in_params[[2]] # just string. 2022-01-26
#result = out_params[[1]]
previous_date = "2022-08-30"
new_date = "2022-10-03"


# 1. Make sure that all the excel files are downloaded from the RAP Team's OneDrive in the following working directory;----
path = path_home()


# Parameter setting
wd_rap = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/99-MasterList_RAP_Team")
wd_gis_sc = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/02-SC/02-Pre-Construction/01-Environment/01-LAR/99-MasterList/03-Compiled")
wd_gis_n2 = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/01-LAR/99-MasterList/03-Compiled")


# List Files
rap_files = list.files(wd_rap)
gis_n2_files = list.files(wd_gis_n2)
gis_sc_files = list.files(wd_gis_sc)

# 2. Read GIS masterlist;-----
## 2.1. N2 GIS master list:----
n2_lot = file.path(wd_gis_n2,gis_n2_files[which(str_detect(gis_n2_files,"Land.*_Status.*xlsx$"))])
n2_struc = file.path(wd_gis_n2,gis_n2_files[which(str_detect(gis_n2_files,"Structure.*xlsx$"))])
n2_isf = file.path(wd_gis_n2,gis_n2_files[which(str_detect(gis_n2_files,"ISF.*xlsx$"))])
n2_pier = file.path(wd_gis_n2,gis_n2_files[which(str_detect(gis_n2_files,"Pier.*_Land.xlsx$"))])

print("Good up to this point")

n2_lot_gis = read.xlsx(n2_lot)
n2_struc_gis = read.xlsx(n2_struc)
n2_isf_gis = read.xlsx(n2_isf)
n2_pier_gis = read.xlsx(n2_pier)

## 2.2. SC GIS master list:----

sc_lot = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Land.*_Status.*xlsx$"))])
sc_struc = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Structure.*xlsx$"))])
sc_isf = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"ISF.*xlsx$"))])
sc_pier = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Pier.*_Land.xlsx$"))])
sc1_barang = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Barangay.*xlsx$"))])


sc_lot_gis = read.xlsx(sc_lot)
sc_struc_gis = read.xlsx(sc_struc)
sc_isf_gis = read.xlsx(sc_isf)
sc_pier_gis = read.xlsx(sc_pier)
sc1_barang_gis = read.xlsx(sc1_barang)

# 3. Read tables from the RAP Team's OneDrive
## 3.1. N2:----

n2_lot1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^N2.*Parcellary.*.xlsx"))])
n2_struc1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^N2.*Structure.*masterlist.*xlsx"))])
n2_isf1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^N2.*Relocation.*.xlsx"))])
n2_pier1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^N2.*Pier.*.xlsx"))])

n2_lot_rap = read.xlsx(n2_lot1)
n2_struc_rap = read.xlsx(n2_struc1)
n2_isf_rap = read.xlsx(n2_isf1)
n2_pier_rap = read.xlsx(n2_pier1)

# HandOver = 1 to StatusLA
n2_lot_rap$HandOver = as.numeric(n2_lot_rap$HandOver)
id = which(n2_lot_rap$HandOver == 1)
n2_lot_rap$StatusLA[id] = 0


## 3.2. SC:----
### 3.2.1. SC:----
sc_lot1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC_.*Parcellary.*.xlsx"))])
sc_struc1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC_.*Structure.*.xlsx"))])
# sc_isf1 = file.path(wd_rap, "SC_Structure_Relocation_compiled.xlsx")
sc_pier1 = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC.*Pier.*.xlsx"))])

sc_lot_rap = read.xlsx(sc_lot1)
sc_struc_rap = read.xlsx(sc_struc1)
sc_pier_rap = read.xlsx(sc_pier1)

### 3.2.2. SC1 (Contractors' Submission):----
sc1_lot = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC1_.*Parcellary.*.xlsx"))])
sc1_struc = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC1_.*Structure.*.xlsx"))])
sc1_barang = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC1_.*Brgy.*.xlsx"))])

sc1_lot_rap = read.xlsx(sc1_lot)
sc1_struc_rap = read.xlsx(sc1_struc)
sc1_barang_rap = read.xlsx(sc1_barang)

# HandOver = 1 to StatusLA
sc_lot_rap$HandOver = as.numeric(sc_lot_rap$HandOver)

id = which(sc_lot_rap$HandOver == 1)
if(length(id) == 0){
  print("")
} else {
  sc_lot_rap$StatusLA[id] = 0
}


#
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
unique(n2_lot_rap$LandUse)
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

## SC1: Contractor's Submission 
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
unique(n2_lot_rap$LotID)
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

## Check HandOverDate
### N2 Lot
head(n2_lot_rap)
unique(n2_lot_rap$HandOverDate)

### 4.2. Join SC Land to SC1 Land, SC1 Structure to SC structure in the RAP Teams+----
####### SC Lot
id = which(str_detect(colnames(sc1_lot_rap),"LotID|Subcon|Priority1|Reqs|ContSubm"))
y = sc1_lot_rap[,id]

xy = left_join(sc_lot_rap,y,by="LotID")
sc_lot_rap = xy

head(sc_lot_rap)
sc_lot_rap$Priority1.x = sc_lot_rap$Priority1.y
sc_lot_rap$Reqs.x = sc_lot_rap$Reqs.y
sc_lot_rap$Subcon.x = sc_lot_rap$Subcon.y

# Delete Priority.y and Reqs.y
ii = which(str_detect(colnames(sc_lot_rap),"^Priority1.*y$|^Reqs.*y$|^Subcon.*y"))
sc_lot_rap = sc_lot_rap[,-ii]

# Rename
ii = which(str_detect(colnames(sc_lot_rap),"^Priority1.*x$|^Reqs.*x$|^Subcon.*x"))
colnames(sc_lot_rap)[ii] = c("Subcon","Priority1","Reqs")

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

str(sc_struc_rap)

sc_struc_rap$BasicPlan.x = sc_struc_rap$BasicPlan.y
sc_struc_rap$Subcon.x = sc_struc_rap$Subcon.y

# Delete Priority.y and Subcon.y
ii = which(str_detect(colnames(sc_struc_rap),"^BasicPlan.*y$|^Subcon.*y$"))
sc_struc_rap = sc_struc_rap[,-ii]


# Rename
ii = which(str_detect(colnames(sc_struc_rap),"^BasicPlan.*x$|^Subcon.*x$"))
colnames(sc_struc_rap)[ii] = c("Subcon","BasicPlan")


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
  write.xlsx(n2_pier_gis, file.path(backup_dir_n2,paste(gsub("-","",previous_date),"_",basename(n2_pier),sep="")))

  # SC Land, SC Structure. SC Barangay
  write.xlsx(sc_lot_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_lot),sep="")))
  write.xlsx(sc_struc_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_struc),sep="")))
  write.xlsx(sc_isf_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_isf),sep="")))
  write.xlsx(sc_pier_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",basename(sc_pier),sep="")))
  
  # barangay
  write.xlsx(sc1_barang_gis, file.path(backup_dir_sc,paste(gsub("-","",previous_date),"_",SC1_Barangay_fileName,sep="")))
}

tryCatch(backupF(),
         error = function(e)
           print("You could not create backup files for one or more files. PLEASE CHECK"))

## 5.2. Add "SCale" from old master list to the new master list from the RAP Team
## N2 Lot
n2_lot_rap = n2_lot_rap[,-which(colnames(n2_lot_rap)=="Scale")]
y = n2_lot_gis[,c("LotID","Scale")]
n2_lot_rap = left_join(n2_lot_rap,y,by="LotID")

## SC Lot
sc_lot_rap = sc_lot_rap[,-which(colnames(sc_lot_rap)=="Scale")]
y = sc_lot_gis[,c("LotID","Scale")]
sc_lot_rap = left_join(sc_lot_rap,y,by="LotID")

## 5.3. Fix totalArea, AffectedArea and RemainingArea, Priority, and Status
## n2_lot_rap
## Remove empty space
id=which(str_detect("^TotalArea|^AffectedArea|^RemainingArea",colnames(n2_lot_rap)))
for(i in id) {
  n2_lot_rap[[i]] = gsub("-","",n2_lot_rap[[i]])
  n2_lot_rap[[i]] = gsub("[[:space:]]","",n2_lot_rap[[i]])
  n2_lot_rap[[i]] = as.numeric(n2_lot_rap[[i]])
}

## sc_lot_rap
id=which(str_detect("^TotalArea|^AffectedArea|^RemainingArea",colnames(sc_lot_rap)))
for(i in id) {
  sc_lot_rap[[i]] = gsub("-","",sc_lot_rap[[i]])
  sc_lot_rap[[i]] = gsub("[[:space:]]","",sc_lot_rap[[i]])
  sc_lot_rap[[i]] = as.numeric(sc_lot_rap[[i]])
}

## 5.4. Check and Change CP format
### N2
id = which(str_detect(n2_lot_rap$CP,"^N\\d+|^n\\d+"))
if (length(id)>0){
  n2_lot_rap$CP[id] = gsub("N|n","N-",n2_lot_rap$CP[id])
} else {
  pring("OK")
}
n2_lot_rap$CP = gsub(",.*","",n2_lot_rap$CP)

## SC
id = which(str_detect(sc_lot_rap$CP,"^S\\d+|^s\\d+"))
if (length(id)>0){
  sc_lot_rap$CP[id] = gsub("S|s","S-",sc_lot_rap$CP[id])
} else {
  print("OK")
}

#sc_lot_rap$CP = gsub(",.*","",sc_lot_rap$CP)

## 5.5. Fix HandOverArea and percentHandedOver:-----
## when affectedArea is missing, percentHandedOver = 0

### n2_lot_rap:-----
id=which(is.na(n2_lot_rap$HandOverArea))
n2_lot_rap$HandOverArea[id] = 0

# 1. Percentage handed over area
id = which(n2_lot_rap$HandOverArea>=0)
n2_lot_rap$percentHandedOver[id] = round(n2_lot_rap$HandOverArea[id]/n2_lot_rap$AffectedArea[id]*100,0)

# 2. When percentHandedOver = 100, HandOver = 1 and StatusLA = 0
id = which(n2_lot_rap$percentHandedOver == 100)
n2_lot_rap$HandOver[id] = 1
n2_lot_rap$StatusLA[id] = 0

n2_lot_rap[which(is.na(n2_lot_rap$StatusLA) & n2_lot_rap$HandOver == 1),]

## 3. When HandOverArea = 0, HandOver = 0 & percentHandedOver = 0
id = which(n2_lot_rap$HandOverArea == 0)
n2_lot_rap$HandOver[id] = 0
n2_lot_rap$percentHandedOver[id] = 0

## 4. when HandedOver = 1, percentHandedOver = 100
id = which(n2_lot_rap$HandOver == 1)
n2_lot_rap$percentHandedOver[id] = 100

## 5.
n2_lot_rap$HandOverDate = as.Date(n2_lot_rap$HandOverDate, origin = "1899-12-30")
n2_lot_rap$HandOverDate = as.Date(n2_lot_rap$HandOverDate, format="%m/%d/%y %H:%M:%S")

##id = which(n2_lot_rap$HandOverDate <= new_date)
##n2_lot_rap$HandOver[id] = 1
##n2_lot_rap$percentHandedOver[id] = 100
#n2_lot_rap$HandOverArea[id] = n2_lot_rap$AffectedArea
##n2_lot_rap$HandOverArea[id] = n2_lot_rap$AffectedArea[id]

### sc_lot_rap:----
id=which(is.na(sc_lot_rap$HandOverArea))
sc_lot_rap$HandOverArea[id] = 0

# 1. Percentage handed over area
id = which(sc_lot_rap$HandOverArea>=0)
sc_lot_rap$percentHandedOver[id] = round(sc_lot_rap$HandOverArea[id]/sc_lot_rap$AffectedArea[id]*100,0)

# 2. When percentHandedOver = 100, HandOver = 1
id = which(sc_lot_rap$percentHandedOver == 100)
sc_lot_rap$HandOver[id] = 1
sc_lot_rap$StatusLA[id] = 0

## 3. When HandOverArea = 0, HandOver = 0 & percentHandedOver = 0
id = which(sc_lot_rap$HandOverArea == 0)
sc_lot_rap$HandOver[id] = 0
sc_lot_rap$percentHandedOver[id] = 0

## 4. when HandedOver = 1, percentHandedOver = 100
id = which(sc_lot_rap$HandOver == 1)
sc_lot_rap$percentHandedOver[id] = 100

## 5.
sc_lot_rap$HandOverDate = as.Date(sc_lot_rap$HandOverDate, origin = "1899-12-30")
sc_lot_rap$HandOverDate = as.Date(sc_lot_rap$HandOverDate, format="%m/%d/%y %H:%M:%S")


##id = which(sc_lot_rap$HandOverDate <= new_date)
##sc_lot_rap$HandOver[id] = 1
##sc_lot_rap$percentHandedOver[id] = 100
##sc_lot_rap$HandOverArea[id] = sc_lot_rap$AffectedArea[id]


####################################################################
## 5.6. Convert dates used in the dropdown list in smart maps:----
### 5.6.1. N2 lot:----
unique(n2_lot_rap$HandOverDate)
n2_lot_rap$HandOverDate = as.Date(n2_lot_rap$HandOverDate, origin = "1899-12-30")
n2_lot_rap$HandOverDate = as.Date(n2_lot_rap$HandOverDate, format="%m/%d/%y %H:%M:%S")

# 5.6.1.1. We monitor monthly basis for visualization, so convert:----
years = unique(year(n2_lot_rap$HandOverDate)); years = years[!is.na(years)]
months = unique(month(n2_lot_rap$HandOverDate)); months = months[!is.na(months)]

# 5.6.1.2. Add temporary column names for year and month:----
n2_lot_rap$YEARS = year(n2_lot_rap$HandOverDate)
n2_lot_rap$MONTH = month(n2_lot_rap$HandOverDate)

# 5.6.1.3. Choose only filled rows:----
id = which(!is.na(n2_lot_rap$HandOverDate))

n2_lot_rap$HandOverDate1 = as.character(NA)

month_list = c("January","February","March","April","May","June","July","August","September","October","November","December")
for(i in 1:12){
  id = which(n2_lot_rap$MONTH==i)
  n2_lot_rap$HandOverDate1[id] = paste(month_list[i],n2_lot_rap$YEARS[id],sep=" ")
}

### 5.6.1.4. When 'HandedOver' = 1, null 'HandedOverDate1'
#### Handed-over dates should not be included in the hand-over dropdown list
id = which(n2_lot_rap$HandOver == 1)
n2_lot_rap$HandOverDate1[id] = NA

# 5.6.1.5. Delete temporary YEARS and MONTH:----
id = which(str_detect(colnames(n2_lot_rap),"YEARS|MONTH"))
n2_lot_rap = n2_lot_rap[,-id]


### 5.6.2. SC Lot:----
unique(sc_lot_rap$HandOverDate)
sc_lot_rap$HandOverDate = as.Date(sc_lot_rap$HandOverDate, origin = "1899-12-30")
sc_lot_rap$HandOverDate = as.Date(sc_lot_rap$HandOverDate, format="%m/%d/%y %H:%M:%S")

# 5.6.2.1. We monitor monthly basis for visualization, so convert:----
years = unique(year(sc_lot_rap$HandOverDate)); years = years[!is.na(years)]
months = unique(month(sc_lot_rap$HandOverDate)); months = months[!is.na(months)]

# 5.6.2.2. Add temporary column names for year and month:----
sc_lot_rap$YEARS = year(sc_lot_rap$HandOverDate)
sc_lot_rap$MONTH = month(sc_lot_rap$HandOverDate)

# 5.6.2.3. Choose only filled rows:----
id = which(!is.na(sc_lot_rap$HandOverDate))

sc_lot_rap$HandOverDate1 = as.character(NA)

month_list = c("January","February","March","April","May","June","July","August","September","October","November","December")
for(i in 1:12){
  id = which(sc_lot_rap$MONTH==i)
  sc_lot_rap$HandOverDate1[id] = paste(month_list[i],sc_lot_rap$YEARS[id],sep=" ")
}

### 5.6.2.4. When 'HandedOver' = 1, null 'HandedOverDate1'
#### Handed-over dates should not be included in the hand-over dropdown list
id = which(sc_lot_rap$HandOver == 1)
sc_lot_rap$HandOverDate1[id] = NA

# 5.6.2.5. Delete temporary YEARS and MONTH:----
id = which(str_detect(colnames(sc_lot_rap),"YEARS|MONTH"))
sc_lot_rap = sc_lot_rap[,-id]

#####################################################################:----
######### Perform QA/QC of master list to check errors ##############:----
#####################################################################:----
# 0.Add percent handed over
### if AffectedArea of PNR LANDS are not entered but HandedOverArea is,
### this will be filled with HandedOverArea ONLY IF HandOverArea>=0

## 0.1. N2 Lot
id = which(str_detect(n2_lot_rap$CN,"^PNR|RP") & is.na(n2_lot_rap$AffectedArea) & n2_lot_rap$HandOverArea>0)

if(length(id)==0){
  print("GOOD! No missing AffectedArea for PNR LANDS to calculate percent handedover")
} else {
  n2_lot_rap$AffectedArea[id] = n2_lot_rap$HandOverArea[id]
}


## 0.2. SC Lot
# Add percent handed over
### if AffectedArea of PNR LANDS are not entered but HandedOverArea is entered with greater than 0,
### this will be filled with HandedOverArea ONLY IF HandOverArea>=0

id = which(str_detect(sc_lot_rap$CN,"^PNR|RP") & is.na(sc_lot_rap$AffectedArea) & sc_lot_rap$HandOverArea>0)

if(length(id)==0){
  print("GOOD! No missing AffectedArea for PNR LANDS to calculate percent handedover")
} else {
  sc_lot_rap$AffectedArea[id] = sc_lot_rap$HandOverArea[id]
}

# check percentage with N-01 and calculate percentage
id = which(str_detect(sc_lot_rap$CP,"--"))
if (length(id) > 0){
  sc_lot_rap$CP[id] = gsub("--","",sc_lot_rap$CP)[id]
} else {
  print("")
}


# 1. If Affected area = 0 or empty. This is error:----
## 1.1. N2 Lot:----
id = which(n2_lot_rap$AffectedArea==0 | is.na(n2_lot_rap$AffectedArea))

if(length(id)>0){
  print("ERROR! There are ZERO or EMPTY affected area in one or more lots.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error1_n2 = data.frame(zero_affectedArea = n2_lot_rap$LotID[id])
} else {
  error1_n2=data.frame(zero_affectedArea=NA)
  print("GOOD!")
}

## 1.2. SC Lot:----
id = which(sc_lot_rap$AffectedArea==0 | is.na(sc_lot_rap$AffectedArea))

if(length(id)>0){
  print("ERROR! There are ZERO or EMPTY affected area in one or more lots.")
  print(paste(sc_lot_rap$LotID[id],sep=","))
  error1_sc = data.frame(zero_affectedArea = sc_lot_rap$LotID[id])
} else {
  error1_sc=data.frame(zero_affectedArea=NA)
  print("GOOD!")
}

# 2. If HandOverArea = 0 or empty:----
## 2.1. N2_lot:----
id = which(is.na(n2_lot_rap$HandOverArea))

if(length(id)>0){
  print("ERROR! There are EMPTY HandOverArea in one or more lots.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error2_n2 = data.frame(missing_handOverArea = n2_lot_rap$LotID[id])
} else {
  error2_n2=data.frame(missing_handOverArea=NA)
  print("GOOD!")
}

## 2.2. SC lot:----
id = which(is.na(sc_lot_rap$HandOverArea))

if(length(id)>0){
  print("ERROR! There are EMPTY HandOverArea in one or more lots.")
  print(paste(sc_lot_rap$LotID[id],sep=","))
  error2_sc = data.frame(missing_handOverArea = sc_lot_rap$LotID[id])
} else {
  error2_sc=data.frame(missing_handOverArea=NA)
  print("GOOD!")
}

# 3. HandOverArea > AffectedArea (THis is Error) Use percenHandedOver to detect this:----
## 3.1. N2 lot:----
id = which(n2_lot_rap$percentHandedOver > 100)

head(n2_lot_rap)

if(length(id)>0){
  print("ERROR! There are Lots whose handed-over area exceeds affected areas.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error3_n2 = data.frame(handOverArea_bigger_affectedArea = n2_lot_rap$LotID[id])
} else {
  error3_n2=data.frame(handOverArea_bigger_affectedArea=NA)
  print("GOOD!")
}


## 3.2. SC lot:----
id = which(sc_lot_rap$percentHandedOver > 100)

if(length(id)>0){
  print("ERROR! There are Lots whose handed-over area exceeds affected areas.")
  print(paste(sc_lot_rap$LotID[id],sep=","))
  error3_sc = data.frame(handOverArea_bigger_affectedArea = sc_lot_rap$LotID[id])
} else {
  error3_sc=data.frame(handOverArea_bigger_affectedArea=NA)
  print("GOOD!")
}


# 4. HandOver is 1 but with future HandOverDate:----
## 4.1. N2 lot:----
id = which(n2_lot_rap$HandOver==1 & n2_lot_rap$HandOverDate>new_date)
if(length(id)>0){
  print("ERROR! There are Lots which were already handed over but the handOverDate is future date.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error4_n2 = data.frame(handedOver_with_futureDate = n2_lot_rap$LotID[id])
} else {
  error4_n2 = data.frame(handedOver_with_futureDate=NA)
  print("GOOD!")
}

## 4.2. SC Lot:----
id = which(sc_lot_rap$HandOver==1 & sc_lot_rap$HandOverDate>new_date)
if(length(id)>0){
  print("ERROR! There are Lots which were already handed over but the handOverDate is future date.")
  print(paste(sc_lot_rap$LotID[id],sep=","))
  error4_sc = data.frame(handedOver_with_futureDate = sc_lot_rap$LotID[id])
} else {
  error4_sc = data.frame(handedOver_with_futureDate=NA)
  print("GOOD!")
}


# 5. When HandOver = 1, no affectedArea and HandOverArea should be zero nor empty.:----
## 5.1. N2 lot:----
id = which(n2_lot_rap$HandOver==1 & (is.na(n2_lot_rap$HandOverArea) | n2_lot_rap$HandOverArea==0))
id1 = which(n2_lot_rap$HandOver==1 & (is.na(n2_lot_rap$AffectedArea) | n2_lot_rap$AffectedArea==0))
ID = c(id, id1)

if(length(ID)>0){
  print("ERROR! There are Lots which were already handed over but either affected or handed over area is missing or zero.")
  print(paste(n2_lot_rap$LotID[ID],sep=","))
  error5_n2 = data.frame(handedOver_with_noArea = n2_lot_rap$LotID[ID])
} else {
  error5_n2 = data.frame(handedOver_with_noArea=NA)
  print("GOOD!")
}

## 5.2. SC Lot:----
id = which(sc_lot_rap$HandOver==1 & (is.na(sc_lot_rap$HandOverArea) | sc_lot_rap$HandOverArea==0))
id1 = which(sc_lot_rap$HandOver==1 & (is.na(sc_lot_rap$AffectedArea) | sc_lot_rap$AffectedArea==0))
ID = c(id, id1)

if(length(ID)>0){
  print("ERROR! There are Lots which were already handed over but either affected or handed over area is missing or zero.")
  print(paste(sc_lot_rap$LotID[ID],sep=","))
  error5_sc = data.frame(handedOver_with_noArea = sc_lot_rap$LotID[ID])
} else {
  error5_sc = data.frame(handedOver_with_noArea=NA)
  print("GOOD!")
}


# 6. HandOverDate is missing when HandOver = 0 (HandOverDate needs to be entered when lots are not handd over yet):----
## 6.1. N2 Lot:----
id = which(is.na(n2_lot_rap$HandOverDate) & n2_lot_rap$HandOver==0)
if(length(id)>0){
  print("ERROR! There are Lots which will be handed Over but missing expected hand-over date.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error6_n2 = data.frame(missing_handOverDate = n2_lot_rap$LotID[id])
} else {
  error6_n2 = data.frame(missing_handOverDate=NA)
  print("GOOD!")
}


## 6.2. SC Lot:----
id = which(is.na(sc_lot_rap$HandOverDate) & sc_lot_rap$HandOver==0)
if(length(id)>0){
  print("ERROR! There are Lots which will be handed Over but missing expected hand-over date.")
  print(paste(sc_lot_rap$LotID[id],sep=","))
  error6_sc = data.frame(missing_handOverDate = sc_lot_rap$LotID[id])
} else {
  error6_sc = data.frame(missing_handOverDate=NA)
  print("GOOD!")
}


# 7. Missing LotID
id = which(is.na(n2_lot_rap$LotID))
if(length(id)>0){
  print("ERROR: There is(are) missing LotID.")
  error7_n2 = data.frame(missing_LotID = n2_lot_rap$SurveyNo[id])
} else {
  print("GOOD")
  error7_n2 = data.frame(missing_LotID = NA)
}

id = which(is.na(sc_lot_rap$LotID))
if(length(id)>0){
  print("ERROR: There is(are) missing LotID.")
  error7_sc = data.frame(missing_LotID = sc_lot_rap$SurveyNo[id])
} else {
  print("GOOD")
  error7_sc = data.frame(missing_LotID = NA)
}

# 8. Missing Municipality
id = which(is.na(n2_lot_rap$Municipality))
if(length(id)>0){
  print("ERROR: There is(are) missing Municipality.")
  error8_n2 = data.frame(missing_Municipality = n2_lot_rap$LotID[id])
} else {
  print("GOOD")
  error8_n2 = data.frame(missing_Municipality = NA)
}

id = which(is.na(sc_lot_rap$Municipality))
if(length(id)>0){
  print("ERROR: There is(are) missing Municipality.")
  error8_sc = data.frame(missing_Municipality = sc_lot_rap$LotID[id])
} else {
  print("GOOD")
  error8_sc = data.frame(missing_Municipality = NA)
}


# 9. Missing Barangay
id = which(is.na(n2_lot_rap$Barangay))
if(length(id)>0){
  print("ERROR: There is(are) missing Barangay.")
  error9_n2 = data.frame(missing_Barangay = n2_lot_rap$LotID[id])
} else {
  print("GOOD")
  error9_n2 = data.frame(missing_Barangay = NA)
}

id = which(is.na(sc_lot_rap$Barangay))
if(length(id)>0){
  print("ERROR: There is(are) missing Barangay.")
  error9_sc = data.frame(missing_Barangay = sc_lot_rap$LotID[id])
} else {
  print("GOOD")
  error9_sc = data.frame(missing_Barangay = NA)
}



# 7. Compile all errors:----
library(qpcR)

## 7.1. N2 Lot:----
c_n2 = qpcR:::cbind.na(error1_n2,error2_n2,error3_n2,error4_n2,error5_n2,error6_n2,error7_n2,error8_n2,error9_n2)
write.xlsx(c_n2, file.path(wd_gis_n2,"Error_table_N2.xlsx"))

## 7.2. SC Lot:----
c_sc = qpcR:::cbind.na(error1_sc,error2_sc,error3_sc,error4_sc,error5_sc,error6_sc,error7_sc,error8_sc,error9_sc)
write.xlsx(c_sc, file.path(wd_gis_n2,"Error_table_SC.xlsx"))


################################################################################################
# 8. N2 and SC Pier master list:----
## 8.1. N2_PIer_masterlist (n2_pier_rap):----

## This code gives access date for each pier (i.e., pier-based access date)

## 8.1.1. Make sure that there are no redundant space
n2_pier_rap$Pier = gsub("[[:space:]]","",n2_pier_rap$Pier)

n2_pier_rap$CP = gsub("N","N-",n2_pier_rap$CP)
n2_pier_rap$CP = gsub(",.*","",n2_pier_rap$CP)

## 8.1.2. We need to delete this Pier numbers, as they do not often agree with ones in the GIS attribute tables
# If we use their format, the N2 Pier point feature may have wrong pier numbers.
id = which(colnames(n2_pier_rap)=="CP")
n2_pier_rap = n2_pier_rap[,-id]

#** Check pier No between GIS table and RAP Team's list
#aa = file.choose()
#n2_pier_pro = read.xlsx(aa)

#pier_pro = unique(n2_pier_pro$PIER)
#pier_rap = unique(n2_pier_rap$Pier)

#pier_pro[!pier_pro %in% pier_rap]
#pier_rap[!pier_rap %in% pier_pro]
#******

## 8.1.3. Convert some Pier No format to the GIS format
id=which(str_detect(n2_pier_rap$Pier,"^MT.*-\\d$"))
n2_pier_rap$Pier[id] = gsub("-1","-01",n2_pier_rap$Pier[id])
n2_pier_rap$Pier[id] = gsub("-2","-02",n2_pier_rap$Pier[id])
n2_pier_rap$Pier[id] = gsub("-3","-03",n2_pier_rap$Pier[id])
n2_pier_rap$Pier[id] = gsub("-4","-04",n2_pier_rap$Pier[id])

colNames = colnames(n2_pier_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(n2_pier_rap)[id] = "Municipality"

colNames = colnames(n2_pier_rap)
id = which(str_detect(colNames,"Pier|pier|PIER"))
colnames(n2_pier_rap)[id] = "PIER"

## 8.1.4. Convert Date format
n2_pier_rap$AccessDate = as.Date(n2_pier_rap$AccessDate, origin = "1899-12-30")
n2_pier_rap$AccessDate = as.Date(n2_pier_rap$AccessDate, format="%m/%d/%y %H:%M:%S")

## 8.2. SC_PIer_masterlist (sc_pier_rap):----

## This code gives access date for each pier (i.e., pier-based access date)

## 8.2.1. Make sure that there are no redundant space
sc_pier_rap$Pier = gsub("[[:space:]]","",sc_pier_rap$Pier)


id=which(str_detect(sc_pier_rap$CP,"^S\\d+|^s\\d+")) # e.g., S01, s01
if(length(id)>0){
  sc_pier_rap$CP[id] = gsub("S|s","S-",sc_pier_rap$CP[id])
} else {print("GOOD! This patten is not observed.")}

id=which(str_detect(sc_pier_rap$CP,"^s-")) # e.g., s-
if(length(id)>0){
  sc_pier_rap$CP[id] = gsub("s-","S-",sc_pier_rap$CP)
} else {print("GOOD")}


## 8.2.2. We need to delete this Pier numbers, as they do not often agree with ones in the GIS attribute tables
# If we use their format, the N2 Pier point feature may have wrong pier numbers.
id = which(colnames(sc_pier_rap)=="CP")
sc_pier_rap = sc_pier_rap[,-id]

#** Check pier No between GIS table and RAP Team's list
#aa = file.choose()
#c_pier_pro = read.xlsx(aa)

#pier_pro = unique(sc_pier_pro$PIER)
#pier_rap = unique(sc_pier_rap$Pier)


#pier_pro[!pier_pro %in% pier_rap]
#pier_rap[!pier_rap %in% pier_pro]

#******

## 8.2.3. Convert some Pier No format to the GIS format
### For SC, the following does not apply
#id=which(str_detect(sc_pier_rap$Pier,"^MT.*-\\d$"))

#sc_pier_rap$Pier[id] = gsub("-1","-01",sc_pier_rap$Pier[id])
#sc_pier_rap$Pier[id] = gsub("-2","-02",sc_pier_rap$Pier[id])
#sc_pier_rap$Pier[id] = gsub("-3","-03",sc_pier_rap$Pier[id])
#sc_pier_rap$Pier[id] = gsub("-4","-04",sc_pier_rap$Pier[id])

head(sc_pier_rap)

colNames = colnames(sc_pier_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(sc_pier_rap)[id] = "Municipality"

colNames = colnames(sc_pier_rap)
id = which(str_detect(colNames,"Pier|pier|PIER"))
colnames(sc_pier_rap)[id] = "PIER"



## 8.2.4. Convert Date format
str(sc_pier_rap)
sc_pier_rap$AccessDate = as.numeric(sc_pier_rap$AccessDate)
sc_pier_rap$AccessDate = as.Date(sc_pier_rap$AccessDate, origin = "1899-12-30")
sc_pier_rap$AccessDate = as.Date(sc_pier_rap$AccessDate, format="%m/%d/%y %H:%M:%S")

#######################################################################################################
## Final Export
## Basically, we will overwrite the RAP Team's excel master list tables that are edited in this code.
## and the GIS master list table are replaced with the edited tables (i.e., overwrite)

### N2
write.xlsx(n2_lot_rap,file.path(wd_gis_n2,basename(n2_lot)),overwrite=TRUE)
write.xlsx(n2_struc_rap,file.path(wd_gis_n2,basename(n2_struc)),overwrite=TRUE)
write.xlsx(n2_isf_rap,file.path(wd_gis_n2,basename(n2_isf)),overwrite=TRUE)
write.xlsx(n2_pier_rap,file.path(wd_gis_n2,basename(n2_pier)),overwrite=TRUE)


### SC

write.xlsx(sc_lot_rap,file.path(wd_gis_sc,basename(sc_lot)),overwrite=TRUE)
write.xlsx(sc_struc_rap,file.path(wd_gis_sc,basename(sc_struc)),overwrite=TRUE)
write.xlsx(sc_pier_rap,file.path(wd_gis_sc,basename(sc_pier)),overwrite=TRUE)
#write.xlsx(sc_isf_rap,file.path(wd_gis_sc,basename(sc_isf)))
write.xlsx(sc1_barang_rap,file.path(wd_gis_sc,SC1_Barangay_fileName),overwrite=TRUE)

# Output
#arc.write(result, sc1_barang_rap, overwrite = TRUE)
#return(out_params)


}

