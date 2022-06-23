


#########################
# DOMAIN in ArcGIS PRo

# Station
## 1.NCC
## 2.Depot
## 3.CIA
## 4.Clark
## 5.Angeles
## 6.San Fernando
## 7.Apalit
## 8.Calumpit
## 9.Malolos
## 10.Solis
## 11.Blumentritt
## 12.Espana
## 13.Santa Mesa
## 14.Paco
## 15.Buendia
## 16.EDSA
## 17.Nichols
## 18.FTI
## 19.Bicutan
## 20.Sucat
## 21.Alabang
## 22.Muntinlupa
## 23.San Pedro
## 24.Pacita
## 25.Binan
## 26.Santa Rosa
## 27.Cabuyao
## 28.Banlic Depot
## 29.Banlic
## 30.Calamba


# StructureType
## 1. Substructure
## 3. Superstructure

# StructureLevel
## 1. Foundation
## 2. Ground Level
## 3. Concourse Level
## 4. Platform Level
## 5. Roof Level

# Type
## 1. Foundations
## 2. Columns
## 3. Framing
## 4. Roofs
## 5. Floor

# SubType
## 1. Pile
## 2. Pile Cap
## 3. Column
## 4. Foundation Girder
## 5. Girder
## 6. Roof Girder
## 7. Foundation Beam
## 8. Beam
## 9. Brace
## 10. Fire Exit Stair
## 11. Steel Staircase
## 12. Slab
## 13. Roof Beam

# DEFINE PARAMETERS
#******************************************************************#
## Enter Date of Update ##
date_update = "2022-06-17"


strucType = c("Substructure", "Superstructure")
strucLevel = c("Foundation", "Ground Level", "Concourse Level", "Platform Level", "Roof Level")
Type = c("Foundations", "Columns", "Framing", "Roofs", "Floor")

subType = c("Pile", "Pile Cap","Column","Foundation Girder","Girder",
            "Roof Girder","Foundation Beam","Beam","Brace","Fire Exit Stair",
            "Steel Staircase","Slab","Roof Beam")

N2_station = c("NCC","Depot","CIA","Clark","Angeles",
               "San Fernando","Apalit","Calumpit","Malolos","Solis",
               "Blumentritt","Espana","Santa Mesa","Paco","Buendia",
               "EDSA","Nichols","FTI","Bicutan","Sucat",
               "Alabang","Muntinlupa","San Pedro","Pacita","Binan",
               "Santa Rosa","Cabuyao","Banlic Depot","Banlic","Calamba")

stn_URL = "https://docs.google.com/spreadsheets/d/1U7NKHyRleRGQYXj382bRVFbvM5ZUlqfMHMGScd6gxO8/edit#gid=0"

### VERY IMPORTANT: READ ! ###
# The Source Google Sheet is different between bored piles and other structural components

# BORED PILES:
## 1. Read Google Sheet Owned by Civil Team
## 2. Restructure
## 3. Update GIS mater list

# OTHERS:
## 1. Read Google Sheet owned by GIS Team
## 2. Restructure
## 3. Update GIS master list


#******************************************************************#

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(fs)

#google_app <- httr::oauth_app(
#  "Desktop client 1",
#  key = "603155182488-fqkuqgl6jgn3qp3lstdj6liqlvirhag4.apps.googleusercontent.com",
#  secret = "bH1svdfg-ofOg3WR8S5WDzPu"
#)
#drive_auth_configure(app = google_app)
#drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
#drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
#gs4_auth(email="matsuzakieiji0@gmail.com")
gs4_auth(email="matsuzaki-ei@ocglobal.jp")


path =  path_home()
wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/02-Station Structure/01-Masterlist/01-Compiled")
#a=choose.dir()
setwd(wd)

# Read our master list table
# C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\02-Civil\03-Viaduct\01-Masterlist\02-Compiled\N2_Viaduct_MasterList.xlsx"

MLTable = file.path(wd,"N2_station_structure.xlsx")
  
#MLTable = file.choose(a_ML)
# Read the masterlist:----
y = read.xlsx(MLTable)

###############################################################
#######################:---- N-01 #################################:----
##############################################################

## Google Sheet for monitoring sheet for station structure

############################################
### N01: BORED PILES #############----
#####################################
url = "https://docs.google.com/spreadsheets/d/11YqYaenIB0l3Bpiv398-0QO3mEIR_BjvnMIsIOF3ILI/edit#gid=0"

pile_sheet = 1


# Read and write as CSV and xlsx
v = range_read(url, sheet = pile_sheet)
v = data.frame(v)

## I temporarliy used dummy field names to be discarded so need to remove it
nChar = sapply(1:ncol(v), function(k) nchar(colnames(v)[k]))
id = which(nChar > 1)
x = v[,id]

# Keep bored piles of station structure
pile_st = min(which(str_detect(x$nPierNumber,"^APS")))
rows = pile_st:nrow(x)
x = x[rows,] 

# Keep only "APS" (Apalit statin) and "CPS" (Calumpit station)
pile_id = which(str_detect(x$nPierNumber,"^APS|^Aps|^APs|^CPS|^Cps|^CPs"))
x = x[pile_id,]

# Make sure that nPierNumber has no space and all letters are uppercase
x$nPierNumber[] = gsub("[[:space:]]","",x$nPierNumber)
x$nPierNumber[] = toupper(x$nPierNumber)

# Status
## Add default status
x$Status = 0

x$Status[str_detect(x$Remarks,pattern="Casted")] = 4 # Bored Pile completed
x$Status[str_detect(x$Remarks,pattern="Inprogress")] = 2 # Under Construction
x$Status[str_detect(x$Remarks,pattern="Incomplete")] = 3 # Delayed

# Bored Piles use "ID"
colnames(x)[which(colnames(x)=="nPierNumber")] = "ID"

# Check duplicated pier numbers
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}


# Join new status to Viaduct masterlist
## Read master list table
y = read.xlsx(MLTable)

y$Status = as.numeric(y$Status)

yx = left_join(y,x,by="ID")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$CP.x=="N-01" & yx$SubType==1)])

check = x_t %in% yx_t
check_function = function(){
  if(length(which(check=="FALSE"))>0){
    print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
  } else (
    print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
  )
}

check_function()

gg = which(yx$Status.y>1)
yx$Status.x[gg] = yx$Status.y[gg]

delField = which(colnames(yx)=="Status.y" | colnames(yx)=="Remarks" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Rename Status.x to Status
colnames(yx)[which(str_detect(colnames(yx),"CP"))] = "CP"
colnames(yx)[which(str_detect(colnames(yx),"Status"))] = "Status"


# Date
library(lubridate)

################# BACKUP IF necessary
## Backup old ones in case
head(y)
y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")
oldDate = gsub("-","",unique(y$updated))


fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(wd,"old")

write.xlsx(y,file.path(direct,fileName),row.names=FALSE)

################# BACKUP IF necessary using above

## Overwrite master list with new date
yx$updated = ymd(date_update)
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

# Recover data in excel format
yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

yx$TargetDate = as.Date(yx$TargetDate, origin = "1899-12-30")
yx$TargetDate = as.Date(yx$TargetDate, format="%m/%d/%y %H:%M:%S")

head(yx)

# 
write.xlsx(yx, MLTable)


### N01: OTHERS #############----

## When you need to convert string to numeric for the following field names

# We need to convert string to numbers for smart maps.
## These strings must be used for site palnners who will update the master list

for(i in 1:length(strucType)) {
  yx$StructureType[which(yx$StructureType==strucType[i])] = i
}

for(i in 1:length(strucLevel)) {
  yx$StructureLevel[which(yx$StructureLevel==strucLevel[i])] = i
}

for(i in 1:length(Type)) {
  yx$Type[which(yx$Type==Type[i])] = i
}

for(i in 1:length(subType)) {
  yx$SubType[which(yx$SubType==subType[i])] = i
}

for(i in 1:length(N2_station)) {
  yx$Station[which(yx$Station==N2_station[i])] = i
}


# check
unique(yx$StructureType)
unique(yx$StructureLevel)
unique(yx$Type)
unique(yx$SubType)
unique(yx$Station)

# Convert string to numeric
yx$StructureType = as.numeric(yx$StructureType)
yx$StructureLevel = as.numeric(yx$StructureLevel)
yx$Type = as.numeric(yx$Type)
yx$SubType = as.numeric(yx$SubType)
yx$Station = as.numeric(yx$Station)




###############################################################
#######################:---- N-02 #################################:----
##############################################################

### N-02: BORED PILES #:----
#url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?userstoinvite=junsanjose@gmail.com&actionButton=1#gid=0"
url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?usp=sharing"

n02_pile = 1
CP = "N-02"

# Read and write as CSV and xlsx
v = range_read(url, sheet = n02_pile)
v = data.frame(v)


# Restruecture table
## Remove empty rows and unneeded rows
x = v[,c(2,ncol(v))]
colnames(x)[1:2] = c("ID", "Status")
x$Status = as.character(x$Status)

## Find pier numbers starting with only "P" and "MT"
keep_row = which(str_detect(x$ID, "^SF-|^SFP-"))
str(keep_row)
x = x[keep_row,]

# Recode Status1
st = unique(x$Status1)

completed_row = which(str_detect(x$Status,"Completed|completed|Complete|complete"))
inprogress_row = which(str_detect(x$Status,"In-progress|in-progress|In-Progress|Inprogress"))

x$Status[completed_row] = 4
x$Status[inprogress_row] = 2

x$Status = as.numeric(x$Status)
x$CP = CP

x$ID = as.character(x$ID)

# Check duplicated pier numbers
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}


# Join 
# Read Google Sheet 
y = read.xlsx(MLTable)
yx = left_join(y,x,by="ID")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$CP.x=="N-02" & yx$SubType==1)])

check = x_t %in% yx_t
check_function()

x.pile = x$ID
yx.pile = yx$ID[which(yx$CP.x=="N-02" & yx$SubType==1)]

x.pile[!x.pile %in% yx.pile]


# NA for status = 1 (To be Constructed)
gg = which(yx$Status.y>0)
yx[gg,]

yx$Status.x[gg] = yx$Status.y[gg]
delField = which(colnames(yx)=="Status.y" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status")] = "Status"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"


# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
library(lubridate)

yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

yx$TargetDate = as.Date(yx$TargetDate, origin = "1899-12-30")
yx$TargetDate = as.Date(yx$TargetDate, format="%m/%d/%y %H:%M:%S")

head(yx)

# 
write.xlsx(yx, MLTable)

###############################################################
#######################:---- N-03 #################################:----
##############################################################

### N-03: BORED PILES #:----
#url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit#gid=0"

# Temporary
url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit?usp=sharing"

n03_pile = 1
CP = "N-03"

# Read and write as CSV and xlsx
v = range_read(url, sheet = n03_pile)
v = data.frame(v)

# filter out 
x = v[,c(2,14)]
colnames(x)[c(1,2)] = c("ID", "Status")
x$Status = as.character(x$Status)

# Extract only statin structure piles
id = which(str_detect(x$ID, "^AS|^CK|^CS"))
x = x[id,]

# Restruecture table

# Recode Status1
st = unique(x$Status)

completed_row = which(str_detect(x$Status,"Completed|completed|Complete|complete"))
inprogress_row = which(str_detect(x$Status,"In-progress|in-progress|In-Progress|Inprogress"))

x$Status[completed_row] = 4
x$Status[inprogress_row] = 2

x$Status = as.numeric(x$Status)
x$CP = CP

x$ID = as.character(x$ID)

### Some IDS have redundant "0" so need to remove
id = which(str_detect(x$ID,"-0\\d{2}|-00\\d{1}"))
x$ID[id] = gsub("-0","-",x$ID[id])

# Check duplicated pier numbers
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}


# Join 
y = read.xlsx(MLTable)

yx = left_join(y,x,by="ID")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$CP.x=="N-03" & yx$SubType==1)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
gg = which(yx$Status.y>0)

yx$Status.x[gg] = yx$Status.y[gg]
delField = which(colnames(yx)=="Status.y" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status")] = "Status"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"


# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
library(lubridate)

yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

yx$TargetDate = as.Date(yx$TargetDate, origin = "1899-12-30")
yx$TargetDate = as.Date(yx$TargetDate, format="%m/%d/%y %H:%M:%S")

head(yx)

# 
write.xlsx(yx, MLTable)

###############################

#############################
z = choose.dir()
setwd(z)


aa = file.choose()
y = read.xlsx(aa)


bb = file.choose()
x = read.xlsx(bb)

head(x)
head(y)

head(y)
id = which(colnames(y)=="ID" | colnames(y)=="Status")

y1 = y[,id]
na_id = which(is.na(y1$ID))
y1 = y1[-na_id,]

xy1 = left_join(x,y1,by="ID")

gg = which(!is.na(xy1$ID))

xy1$Status.x[gg] = xy1$Status.y[gg]

xy1 = xy1[,-ncol(xy1)]
head(xy1)
colnames(xy1)[which(colnames(xy1)=="Status.x")] = "Status"

xy1$updated = "2022-01-07"


xy1$updated = as.Date(xy1$updated, origin = "1899-12-30")
xy1$updated = as.Date(xy1$updated, format="%m/%d/%y %H:%M:%S")

# Recover data in excel format
xy1$StartDate = as.Date(xy1$StartDate, origin = "1899-12-30")
xy1$StartDate = as.Date(xy1$StartDate, format="%m/%d/%y %H:%M:%S")

xy1$TargetDate = as.Date(xy1$TargetDate, origin = "1899-12-30")
xy1$TargetDate = as.Date(xy1$TargetDate, format="%m/%d/%y %H:%M:%S")


write.xlsx(xy1,"N2_Station_Structure_masterList_new.xlsx")
