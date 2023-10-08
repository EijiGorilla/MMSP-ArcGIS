


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
date_update = "2023-09-27"


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
library(lubridate)

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

MLTable = file.path(wd,"N2_station_structure_P6ID.xlsx")
  
#MLTable = file.choose(a_ML)
# Read the masterlist:----
y = read.xlsx(MLTable)

################# BACKUP IF necessary
## Backup old ones in case
head(y)
y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")
y$end_date = as.Date(y$end_date, origin = "1899-12-30")
y$end_date = as.Date(y$end_date, format="%m/%d/%y %H:%M:%S")
y$target_date = as.Date(y$target_date, origin = "1899-12-30")
y$target_date = as.Date(y$target_date, format="%m/%d/%y %H:%M:%S")
oldDate = gsub("-","",unique(y$updated))

fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(wd,"old")

write.xlsx(y,file.path(direct,fileName),row.names=FALSE)

################# BACKUP IF necessary using above

###############################################################
#######################:---- N-01 #################################:----
##############################################################

## Google Sheet for monitoring sheet for station structure

############################################
### N01: BORED PILES #############----
#####################################
url = "https://docs.google.com/spreadsheets/d/11NMBpr1nKXuOgooHDl-CARvrieVN7VjEpLM1XgNwR0c/edit?usp=sharing"

pile_sheet = 2


# Read and write as CSV and xlsx
v = range_read(url, sheet = pile_sheet)
v = data.frame(v)

#x = v[,id]
x = v[,c(3,12,22)]

colnames(x) = c("nPierNumber","end_date","Remarks")
x = x[-c(1,2),]

#id = which(str_detect(colnames(x),"K"))
#colnames(x)[3] = "end_date"

## Remove empty rows
rid = which(is.na(x$nPierNumber))
x = x[-rid,]

## I temporarliy used dummy field names to be discarded so need to remove it
#nChar = sapply(1:ncol(v), function(k) nchar(colnames(v)[k]))
#id = which(nChar > 1)
#x = v[,id]

# Keep bored piles of station structure
x$nPierNumber
pile_st = min(which(str_detect(x$nPierNumber,"^APS|^CPS")))
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

x$Status[str_detect(x$Remarks,pattern="Casted|casted|CASTED")] = 4 # Bored Pile completed
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

# unlist for end_date and Remarks
# Unlist end_date
id = which(x$end_date == "NULL")
x$end_date[id] = NA

end_date_ = unlist(x$end_date, use.names = FALSE)
x$end_date = end_date_

# No need to keep Remarks
x = x[,-which(str_detect(colnames(x),"Remarks"))]

# Check spelling error (correct format = "APS-xxx" and "CPS-xxx")
id = which(str_detect(x$ID, "^APS-|^CPS-"))
## then find IDs not conforming to this format
x$ID[-id] = gsub("APS", "APS-", x$ID[-id])
x$ID[-id] = gsub("CPS", "CPS-", x$ID[-id])

# Join new status to Viaduct masterlist
## Read master list table
y = read.xlsx(MLTable)

y$Status = as.numeric(y$Status)
yx = left_join(y,x,by="ID")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$CP == "N-01" & yx$SubType==1)])

check = x_t %in% yx_t
check_function = function(){
  if(length(which(check=="FALSE"))>0){
    print("Number of Status1 is DIFFERENT. PLEASE CHECK")
  } else (
    print("GOOD! The number of Status1 is same between Civil and joined excel ML.")
  )
}

x_pile = x$ID
yx_pile = yx$ID[which(yx$Status.y==4 & yx$CP=="N-01" & yx$SubType==1)]
x_pile[!x_pile %in% yx_pile]

check_function()

# Update Status
gg = which(yx$Status.y>1)
yx$Status.x[gg] = yx$Status.y[gg]

delField = which(str_detect(colnames(yx),"Status.y|Remarks|CP.y|end_date.y"))
yx = yx[,-delField]

# Rename Status.x to Status
colnames(yx)[which(str_detect(colnames(yx),"CP"))] = "CP"
colnames(yx)[which(str_detect(colnames(yx),"Status.x$"))] = "Status"
colnames(yx)[which(str_detect(colnames(yx),"end_date"))] = "end_date"

# Date
library(lubridate)


## Overwrite master list with new date
yx$updated = ymd(date_update)
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")
yx$target_date = as.Date(yx$target_date, origin = "1899-12-30")
yx$target_date = as.Date(yx$target_date, format="%m/%d/%y %H:%M:%S")

# 
write.xlsx(yx, MLTable)

###############################################################
#######################:---- N-02 #################################:----
##############################################################

### N-02: BORED PILES #:----
#url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?userstoinvite=junsanjose@gmail.com&actionButton=1#gid=0"
url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?usp=sharing"

n02_pile = 3
CP = "N-02"

# Read and write as CSV and xlsx
v = range_read(url, sheet = n02_pile)
v = data.frame(v)

# Restruecture table
## Remove empty rows and unneeded rows
id=which(str_detect(colnames(v),"^Date.*Casted$"))

x = v[,c(2,id)]

coln = colnames(x)
for(i in seq(coln)) {
  type = class(x[[i]])
  
  # if type is 'list', unlist
  if(type == "list") {
    ## Convert NULL to NA
    x[[i]] = rrapply(x[[i]], f = function(x) replace(x, is.null(x), NA))
    
    ## then unlist
    x[[i]] = unlist(x[[i]], use.names = FALSE)
  }
}

colnames(x)[1:2] = c("ID", "end_date")

## Find pier numbers starting with only "P" and "MT"
keep_row = which(str_detect(x$ID, "^SF|^SFP"))
x = x[keep_row,]

# TargetDate = end_date (casted date)
x$end_date = as.numeric(x$end_date)
id=which(!is.na(x$end_date))
if(length(id)>0){
  x = x[id,]
}

#Status
x$Status = 4

# ID
x$ID = toupper(x$ID)
x$ID = gsub("P-","P",x$ID)
x$ID = gsub("SF","SF-",x$ID)
x$ID = gsub("[[:space:]]","",x$ID)

## note that if 'SFP-' is found, this is error. We need to convert 'SFP-' to 'SF-Pxx'
id = which(str_detect(x$ID,"^SFP-"))
if(length(id)>0){
  x$ID[id] = gsub("SFP-","SF-P",x$ID[id])
}

# Check duplicated pier numbers
id = which(duplicated(x$ID))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

x$CP = "N-01"


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

yx$Status.x[gg] = yx$Status.y[gg]

delField = which(str_detect(colnames(yx),"Status.y|Remarks|CP.y|end_date.y"))
yx = yx[,-delField]

# Rename Status.x to Status
colnames(yx)[which(str_detect(colnames(yx),"CP"))] = "CP"
colnames(yx)[which(str_detect(colnames(yx),"Status.x$"))] = "Status"
colnames(yx)[which(str_detect(colnames(yx),"end_date"))] = "end_date"

# Date
library(lubridate)


## Overwrite master list with new date
yx$updated = ymd(date_update)
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")
yx$target_date = as.Date(yx$target_date, origin = "1899-12-30")
yx$target_date = as.Date(yx$target_date, format="%m/%d/%y %H:%M:%S")

# Make sure to have no empty Status
yx[is.na(yx$Status),]

# 
write.xlsx(yx, MLTable)

###############################################################
#######################:---- N-03 #################################:----
##############################################################
### N-03: BORED PILES #:----
#url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit#gid=0"

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

id=which(str_detect(x$ID,"^AC"))
unique(x$ID)

# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by="ID")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$CP.x=="N-03" & yx$SubType==1)])

check = x_t %in% yx_t
check_function()


x.pile = x$ID
yx.pile = yx$ID[which(yx$CP.x=="N-03" & yx$SubType==1)]

x.pile[!x.pile %in% yx.pile]


# NA for status = 1 (To be Constructed)
gg = which(yx$Status.y>0)

yx$Status.x[gg] = yx$Status.y[gg]
delField = which(str_detect(colnames(yx),"Status.y|Remarks|CP.y|end_date.y"))
yx = yx[,-delField]

# Rename Status.x to Status
colnames(yx)[which(str_detect(colnames(yx),"CP"))] = "CP"
colnames(yx)[which(str_detect(colnames(yx),"Status.x$"))] = "Status"
colnames(yx)[which(str_detect(colnames(yx),"end_date"))] = "end_date"

# Date
library(lubridate)


## Overwrite master list with new date
yx$updated = ymd(date_update)
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")
yx$target_date = as.Date(yx$target_date, origin = "1899-12-30")
yx$target_date = as.Date(yx$target_date, format="%m/%d/%y %H:%M:%S")

# 
write.xlsx(yx, MLTable)

########################################
##### Update Status for Delay ###:------
########################################
# If planned_date < current date & Status is NOT complete, Status1 = 3 (delayed)
today = Sys.Date()
id = which(y$target_date < today & y$Status != 4)

y$Status[id] = 3 # delayed status
write.xlsx(y, MLTable)

