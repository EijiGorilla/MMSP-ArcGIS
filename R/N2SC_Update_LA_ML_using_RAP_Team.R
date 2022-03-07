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
previous_date = "2022-03-03"
new_date = "2022-03-07"


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

sc_lot = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Land.*xlsx$"))])
sc_struc = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Structure.*xlsx$"))])
sc_isf = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"ISF.*xlsx$"))])
sc1_barang = file.path(wd_gis_sc,gis_sc_files[which(str_detect(gis_sc_files,"Barangay.*xlsx$"))])


sc_lot_gis = read.xlsx(sc_lot)
sc_struc_gis = read.xlsx(sc_struc)
sc_isf_gis = read.xlsx(sc_isf)
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

sc_lot_rap = read.xlsx(sc_lot1)
sc_struc_rap = read.xlsx(sc_struc1)

### 3.2.2. SC1 (Contractors' Submission):----
sc1_lot = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC1_.*Parcellary.*.xlsx"))])
sc1_struc = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC1_.*Structure.*.xlsx"))])
sc1_barang = file.path(wd_rap,rap_files[which(str_detect(rap_files,"^SC1_.*Brgy.*.xlsx"))])

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


## Check HandOverDate
n2_lot_rap
head(n2_lot_rap)
unique(n2_lot_rap$HandOverDate)

### If handOverDate is entered in lots, these lots cannot have HandOver = 1
head(n2_lot_rap)
id = which(!is.na(n2_lot_rap$HandOverDate) & n2_lot_rap$StatusLA==0)

if(length(id)>0){
  print("There is error in data entry for 'HandOverDate' and/or 'StatusLA'. PLEASE CHECK")
} else {
  print("")
}


# if you found that lots are already handed over but with HandOverDate, I will delete HandOverDate for these lots.
n2_lot_rap$HandOverDate[id] = NA


### 4.2. Join SC Land to SC1 Land, SC1 Structure to SC structure in the RAP Teams+----
####### SC Lot
id = which(str_detect(colnames(sc1_lot_rap),"LotID|Subcon|Priority1|Reqs|ContSubm"))
y = sc1_lot_rap[,id]

xy = left_join(sc_lot_rap,y,by="LotID")
sc_lot_rap = xy

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

## 5.3. Fix totalArea, AffectedArea and RemainingArea, Priority, and Status
## n2_lot_rap
id=which(str_detect("^TotalArea|^AffectedArea|^RemainingArea",colnames(n2_lot_rap)))
for(i in id) n2_lot_rap[[i]] = as.numeric(n2_lot_rap[[i]])


id=which(str_detect("^TotalArea|^AffectedArea|^RemainingArea",colnames(sc_lot_rap)))
for(i in id) sc_lot_rap[[i]] = as.numeric(sc_lot_rap[[i]])

## 5.4. Change CP format from 'N01' to 'N-01'

n2_lot_rap$CP = gsub("N","N-",n2_lot_rap$CP)
n2_lot_rap$CP = gsub(",.*","",n2_lot_rap$CP)

sc_lot_rap$CP = gsub("S","S-",sc_lot_rap$CP)
sc_lot_rap$CP = gsub(",.*","",sc_lot_rap$CP)

## 5.5. Fill in zero for all empty cells in HandOverArea
id=which(is.na(n2_lot_rap$HandOverArea))
n2_lot_rap$HandOverArea[id] = 0


# Convert date
unique(n2_lot_rap$HandOverDate)
n2_lot_rap$HandOverDate = as.Date(n2_lot_rap$HandOverDate, origin = "1899-12-30")
n2_lot_rap$HandOverDate = as.Date(n2_lot_rap$HandOverDate, format="%m/%d/%y %H:%M:%S")

unique(n2_lot_rap$HandOverDate)

# We monitor monthly basis for visualization, so convert
n2_lot_rap$HandOverDate1[n2_lot_rap$HandOverDate<=as.Date("2021-05-31") & n2_lot_rap$HandOverDate>=as.Date("2021-05-01")] = "May 2021"
n2_lot_rap$HandOverDate1[n2_lot_rap$HandOverDate<=as.Date("2022-06-30") & n2_lot_rap$HandOverDate>=as.Date("2022-06-01")] = "June 2022"
n2_lot_rap$HandOverDate1[n2_lot_rap$HandOverDate<=as.Date("2022-07-31") & n2_lot_rap$HandOverDate>=as.Date("2022-07-01")] = "Julay 2022"

n2_lot_rap$HandOverDate1[n2_lot_rap$HandOverDate<=as.Date("2022-08-31") & n2_lot_rap$HandOverDate>=as.Date("2022-08-01")] = "August 2022"
n2_lot_rap$HandOverDate1[n2_lot_rap$HandOverDate<=as.Date("2022-09-30") & n2_lot_rap$HandOverDate>=as.Date("2022-09-01")] = "September 2022"
n2_lot_rap$HandOverDate1[n2_lot_rap$HandOverDate<=as.Date("2022-12-31") & n2_lot_rap$HandOverDate>=as.Date("2022-12-01")] = "December 2022"


# Add percent handed over
### if AffectedArea of PNR LANDS are missing, this has be filled using HandedOverARea
id = which(n2_lot_rap$CN=="PNR LANDS" & is.na(n2_lot_rap$AffectedArea) & n2_lot_rap$HandOverArea>=0)
if(length(id)==0){
  print("GOOD! No missing AffectedArea for PNR LANDS to calculate percent handedover")
} else {
  n2_lot_rap$AffectedArea[id] = n2_lot_rap$HandOverArea[id]
}

# check percentage with N-01 and calculate percentage
tt = n2_lot_rap[n2_lot_rap$CP=="N-02",]
sum(tt$HandOverArea,na.rm=TRUE)/sum(tt$AffectedArea,na.rm=TRUE)

id = which(n2_lot_rap$HandOverArea>=0)
n2_lot_rap$percentHandedOver[id] = round(n2_lot_rap$HandOverArea[id]/n2_lot_rap$AffectedArea[id]*100,0)

#####################################################################:----
######### Perform QA/QC of master list to check errors ##############:----
#####################################################################:----
# 1. If Affected area = 0. This is error:----
id = which(n2_lot_rap$AffectedArea==0 | is.na(n2_lot_rap$AffectedArea))

if(length(id)>0){
  print("ERROR! There are ZERO or EMPTY affected area in one or more lots.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error1 = data.frame(zero_affectedArea = n2_lot_rap$LotID[id])
} else {
  error1=data.frame(zero_affectedArea=NA)
  print("GOOD!")
}

# 2. If HandOverArea = 0 or empty
id = which(is.na(n2_lot_rap$HandOverArea))

if(length(id)>0){
  print("ERROR! There are EMPTY HandOverArea in one or more lots.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error2 = data.frame(missing_handOverArea = n2_lot_rap$LotID[id])
} else {
  error2=data.frame(missing_handOverArea=NA)
  print("GOOD!")
}

# 3. HandOverArea > AffectedArea (THis is Error) Use percenHandedOver to detect this
id = which(n2_lot_rap$percentHandedOver > 100)

head(n2_lot_rap)

if(length(id)>0){
  print("ERROR! There are Lots whose handed-over area exceeds affected areas.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error3 = data.frame(handOverArea_bigger_affectedArea = n2_lot_rap$LotID[id])
} else {
  error3=data.frame(handOverArea_bigger_affectedArea=NA)
  print("GOOD!")
}

# 4. HandOver is 1 but with future HandOverDate
id = which(n2_lot_rap$HandOver==1 & n2_lot_rap$HandOverDate>new_date)
if(length(id)>0){
  print("ERROR! There are Lots which were already handed over but the handOverDate is future date.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error4 = data.frame(handedOver_with_futureDate = n2_lot_rap$LotID[id])
} else {
  error4=data.frame(handedOver_with_futureDate=NA)
  print("GOOD!")
}

# 5. When HandOver = 1, not affectedArea and HandOverArea should be zero nor empty.
id = which(n2_lot_rap$HandOver==1 & (is.na(n2_lot_rap$HandOverArea) | n2_lot_rap$HandOverArea==0))
id1 = which(n2_lot_rap$HandOver==1 & (is.na(n2_lot_rap$AffectedArea) | n2_lot_rap$AffectedArea==0))
ID = c(id, id1)

if(length(ID)>0){
  print("ERROR! There are Lots which were already handed over but either affected or handed over area is missing or zero.")
  print(paste(n2_lot_rap$LotID[ID],sep=","))
  error5 = data.frame(handedOver_with_noArea = n2_lot_rap$LotID[ID])
} else {
  error5=data.frame(handedOver_with_noArea=NA)
  print("GOOD!")
}

# 6. HandOverDate = missing but HandOver = 0 (supposed to be handed over but missing to be handedOverDate)
id = which(is.na(n2_lot_rap$HandOverDate) & n2_lot_rap$HandOver==0)
if(length(id)>0){
  print("ERROR! There are Lots which will be handed Over but missing expected hand-over date.")
  print(paste(n2_lot_rap$LotID[id],sep=","))
  error6 = data.frame(missing_handOverDate = n2_lot_rap$LotID[id])
} else {
  error6=data.frame(missing_handOverDate=NA)
  print("GOOD!")
}


# Column bind all errors
library(qpcR)
c1 = qpcR:::cbind.na(error1,error2,error3,error4,error5,error6)
write.xlsx(c1, file.path(wd_gis_n2,"Error_table.xlsx"))


#### N2_PIer_masterlist (n2_pier_rap):----
## This code gives access date for each pier (i.e., pier-based access date)
head(n2_pier_rap)
## 1. Make sure that there are no redundant space
n2_pier_rap$Pier = gsub("[[:space:]]","",n2_pier_rap$Pier)

n2_pier_rap$CP = gsub("N","N-",n2_pier_rap$CP)
n2_pier_rap$CP = gsub(",.*","",n2_pier_rap$CP)

# We need to delete this Pier numbers, as they do not often agree with ones in the GIS attribute tables
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

## 2. Convert some Pier No format to the GIS format
id=which(str_detect(n2_pier_rap$Pier,"^MT.*-\\d$"))
n2_pier_rap$Pier[id] = gsub("-1","-01",n2_pier_rap$Pier[id])
n2_pier_rap$Pier[id] = gsub("-2","-02",n2_pier_rap$Pier[id])
n2_pier_rap$Pier[id] = gsub("-3","-03",n2_pier_rap$Pier[id])
n2_pier_rap$Pier[id] = gsub("-4","-04",n2_pier_rap$Pier[id])

head(n2_pier_rap)

colNames = colnames(n2_pier_rap)
id = which(str_detect(colNames,"^City|^city|Municipality$"))
colnames(n2_pier_rap)[id] = "Municipality"

colNames = colnames(n2_pier_rap)
id = which(str_detect(colNames,"Pier|pier|PIER"))
colnames(n2_pier_rap)[id] = "PIER"


## 3. Conver Date format
n2_pier_rap$AccessDate = as.Date(n2_pier_rap$AccessDate, origin = "1899-12-30")
n2_pier_rap$AccessDate = as.Date(n2_pier_rap$AccessDate, format="%m/%d/%y %H:%M:%S")


## 
head(n2_lot_rap)
n2_lot_rap[which(n2_lot_rap$HandOverDate>=new_date & n2_lot_rap$HandOver==1),]


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
#write.xlsx(sc_isf_rap,file.path(wd_gis_sc,basename(sc_isf)))
write.xlsx(sc1_barang_rap,file.path(wd_gis_sc,SC1_Barangay_fileName),overwrite=TRUE)

# Output
#arc.write(result, sc1_barang_rap, overwrite = TRUE)
#return(out_params)


}
