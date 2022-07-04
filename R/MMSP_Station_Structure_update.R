# This R code reads Google sheet from a table provided by Civil Team for monitoring station structure construction
# The source of URL: "https://docs.google.com/spreadsheets/d/1wD-fgFafpUDNU270J9ggjtUSgZelfEqbkdRnfr7L2NU/edit#gid=516171899"
# 

# OPERATION STEPS:
# 1. Read the Google Sheet
# 2. Restructure the data set
# 3. Join the table to our master list table
# 4. Export

# MAKE SURE THAT Type of Viaduct in Domain of ArcGIS Pro follows this:
## D-Wall = 1
## Column = 2
## Slab = 3
## Kingpost = 4

# MAKE SURE THAT Status for Domain of ArcGIS Pro follows this:
## To be Constructed = 1
## Under Construction = 2
## Delayed = 3
## Completed = 4


# Station1 domain (text)
EVS = "ast Valenzuela"
DEP = "Depot"
QHS = "Quirino Highway"
TSS = "Tandang Sora"
NAS = "North Ave"
QAS = "Quezon Ave"
EAS = "East Ave"
ANS = "Anonas"
CAS = "Camp Aguinaldo"
ORS = "Ortigas"
SHS = "Shaw"
KAS = "Kalayaan Ave"
BGC = "Bonifacio Global City"
LAS = "Lawton"
SDS = "Senate-DepEd"
TE3 = "Terminal 3"
TE12 = "Terminal 1, Terminal 2"
FTI = "FTI"
BIC = "Bicutan"


# Setting

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

gs4_auth(email="matsuzaki-ei@ocglobal.jp")


# Define Working Directory
path = path_home()
wd = file.path(path,"Dropbox/01-Railway/01-MMSP/03-During-Construction/01-Station Structure/01-Masterlist/01-Compiled")

#a=choose.dir()
setwd(wd)
getwd()
## Enter Date of Update ##:----
date_update = "2022-07-04"

# Read our master list table
MLTable = file.path(wd,"MMSP_Station_Structure.xlsx")

# Read the masterlist:----
y = read.xlsx(MLTable)


#####################################
## Create backup files
y$updated = as.Date(y$updated, origin = "1899-12-30")
oldDate = gsub("-","",unique(y$updated))

fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(wd,"old")

write.xlsx(y,file.path(direct,fileName),row.names=FALSE)
#########################################

## Define Parameter:
# Define Type
type_dwall = 1
type_col = 2
type_slab = 3
type_kp = 4
type_secantP = 5

###############################################################
#######################:---- North Avenue Station ############:---- 
##############################################################

## Define URL where data is stored and updated
## I used "IMPORTRANGE" to copy information from the source URL to suit our needs.
url = "https://docs.google.com/spreadsheets/d/1wD-fgFafpUDNU270J9ggjtUSgZelfEqbkdRnfr7L2NU/edit?usp=sharing"

## Define Google Sheet number
nas_kp_sheet = 3
nas_secantPile_sheet = 2
nas_dwall_sheet = 1

### NAS: King post:----

# Read and write as CSV and xlsx
v = range_read(url, sheet = nas_kp_sheet)
v = data.frame(v)

# Find "KING POST ID" and "COMPLETED" column names
## #King POST ID" is at 5th columns and and 9th row
## COMPLETED is at at 22nd column and 9th row
head(v,20)
x = v[-c(1:10),c(5,11,22)]
colnames(x) = c("ID","end_date","Status")

#
x$ID = as.character(x$ID)
x$Status = as.character(x$Status)

# Retain only KP-
kp_id = which(str_detect(x$ID,"^KP|^kp|^Kp"))
x = x[kp_id,]

unique(x$Status)

status_rm_id = which(str_detect(x$Status,"NULL|null|Null|[[:space:]]"))

if(length(status_rm_id)>0){
  x = x[-status_rm_id,]
} else {
  print("No observations to be dropped")
}

# Make sure that ID is uppercase letter and no space
x$ID[] = gsub("[[:space:]]","",x$ID) # no space
x$ID[] = toupper(x$ID)

# Conver STatus to numeric
x$Status = as.numeric(x$Status)

# status = 1: Complted (4)
x$Status[x$Status==1] = 4

# Add type
x$Type = type_kp
x$Station1 = NAS

x$end_date = unlist(x$end_date)
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01", tz="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Merge this to masterlist
y = read.xlsx(MLTable)

y$end_date = as.Date(y$end_date, origin = "1899-12-30")

yx = left_join(y,x,by=c("Station1","Type","ID"))

## Check if the number of Status1 for each Type is same between x and yx.
head(x)
head(yx)
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$Station1==NAS & yx$Type==4 & yx$Status.y==4)])


check = x_t %in% yx_t
check_function = function(){
  if(length(which(check=="FALSE"))>0){
    print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
  } else (
    print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
  )
}

check_function()


x_kp = x$ID
yx_kp = yx$ID[which(yx$Station1==NAS & yx$Type==4 & yx$Status.y==4)]

str(x_kp)
str(yx_kp)

x_kp[!x_kp %in% yx_kp]
yx_kp[!yx_kp %in% x_kp]

head(x_kp)
head(yx)

unique(yx$ID)

## Replace Status.x rows with only updated status from Status.y

gg = which(yx$Status.y>0)
yx$Status.x[gg] = yx$Status.y[gg]

gg1 = which(yx$end_date.y>0)
yx$end_date.x[gg1] = yx$end_date.y[gg1]

## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

# Delete Status.y and rename Status.x to Status
rm_status = which(str_detect(colnames(yx),"Status.y|end_date.y|Year.y|Month.y"))
yx = yx[, -rm_status]

colnames(yx)[str_detect(colnames(yx),pattern="Status")] = "Status"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Add the latest date
yx$updated = date_update

# Convert date to Excel date format
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

# count for checking
id = which(str_detect(yx$ID,"^KP-") & yx$Status==4)
str(id)

write.xlsx(yx,MLTable)

###

kingpost_yx = unique(yx$ID[id])
kingpost_sour = unique(x$ID)

test = paste(kingpost_sour,collapse="','",sep="")
length(kingpost_sour)

str(kingpost_yx)
str(kingpost_sour)

kingpost_yx[!kingpost_yx %in% kingpost_sour]
kingpost_sour[!kingpost_sour %in% kingpost_yx]



### NAS: Secant Piles:----
# Read and write as CSV and xlsx
v = range_read(url, sheet = nas_secantPile_sheet)
v = data.frame(v)

# Find "KING POST ID" and "COMPLETED" column names
## #King POST ID" is at 5th columns and and 9th row
## COMPLETED is at at 22nd column and 9th row

x = v[-c(1:7),c(3,ncol(v)-1,ncol(v))]
colnames(x) = c("ID","end_date","Status")

#
x$ID = as.character(x$ID)
x$Status = as.character(x$Status)

# Retain only KP-
kp_id = which(str_detect(x$ID,"^S|^s"))
x = x[kp_id,]

unique(x$Status)

status_rm_id = which(str_detect(x$Status,"NULL|null|Null|[[:space:]]"))

if(length(status_rm_id)>0){
  x = x[-status_rm_id,]
} else {
  print("No observations to be dropped")
}

# Make sure that ID is uppercase letter and no space
x$ID[] = gsub("[[:space:]]","",x$ID) # no space
x$ID[] = toupper(x$ID)

# Conver STatus to numeric
x$Status = as.numeric(x$Status)

# status = 1: Complted (4)
x$Status[x$Status==1] = 4

# Add type
x$Type = type_secantP
x$Station1 = NAS

x$end_date = unlist(x$end_date)
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01", tz="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))


# Align Secant Piles IDs based on the GIS table
x$ID = paste("NA-SP-",x$ID,sep="")

# Merge this to masterlist
y = read.xlsx(MLTable)

y$end_date = as.Date(y$end_date, origin = "1899-12-30")

str(x)

yx = left_join(y,x,by=c("Station1","Type","ID"))

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$Station1==NAS & yx$Type==5 & yx$Status.y==4)])

check = x_t %in% yx_t
check_function = function(){
  if(length(which(check=="FALSE"))>0){
    print("Number of Status1 for Secant pile is DIFFERENT. PLEASE CHECK")
  } else (
    print("GOOD! The number of Secant pile is same between Civil and joined excel ML.")
  )
}

check_function()


x_kp = x$ID
yx_kp = yx$ID[which(yx$Station1==NAS & yx$Type==5 & yx$Status.y==4)]

str(x_kp)
str(yx_kp)

x_kp[!x_kp %in% yx_kp]
yx_kp[!yx_kp %in% x_kp]

head(x_kp)
head(yx)

unique(yx$ID)

## Replace Status.x rows with only updated status from Status.y
gg = which(yx$Status.y>0)
yx$Status.x[gg] = yx$Status.y[gg]

gg1 = which(yx$end_date.y>0)
yx$end_date.x[gg1] = yx$end_date.y[gg1]

## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

# Delete Status.y and rename Status.x to Status
rm_status = which(str_detect(colnames(yx),"Status.y|end_date.y|Year.y|Month.y"))
yx = yx[, -rm_status]

colnames(yx)[str_detect(colnames(yx),pattern="Status")] = "Status"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Add the latest date
yx$updated = date_update

# Convert date to Excel date format
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

write.xlsx(yx,MLTable)


### NAS: D-Wall:----
# Read and write as CSV and xlsx
v = range_read(url, sheet = nas_dwall_sheet)
v = data.frame(v)


# Find "Dwall ID" and "COMPLETED" column names
## #King POST ID" is at 4th columns and and 6th row
## COMPLETED is at at 18th column and 6th row
x = v[-c(1:6),c(4,17,18)]
colnames(x) = c("ID","end_date","Status")

#
x$ID = as.character(x$ID)
x$Status = as.character(x$Status)

head(x)
# Retain only KP-
dwall_id = which(str_detect(x$ID,"^P|^p|^p"))
x = x[dwall_id,]

status_rm_id = which(str_detect(x$Status,"NULL|null|Null|[[:space:]]"))
if (length(status_rm_id) > 0){
  x = x[-status_rm_id,]
} else {
  print("no need to remove")
}


# Make sure that ID is uppercase letter and no space
x$ID[] = gsub("[[:space:]]","",x$ID) # no space
x$ID[] = toupper(x$ID)


# Conver STatus to numeric
x$Status = as.numeric(x$Status)

# status = 1: Complted (4)
x$Status[x$Status==1] = 4

# Add type

x$Type = type_dwall
x$Station1 = NAS

# re-format date
id = which(x$end_date=="NULL")
x$end_date[id] = NA

x$end_date=unlist(x$end_date, use.names = FALSE)
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01", tz="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Merge this to masterlist
y = read.xlsx(MLTable)

y$end_date = as.Date(y$end_date, origin = "1899-12-30")

yx = left_join(y,x,by=c("Station1","Type","ID"))

##

## Check if the number of Status1 for each Type is same between x and yx.
head(x)
head(yx)
x_t = table(x$Status)
yx_t = table(yx$Status.y[which(yx$Station1==NAS & yx$Type==1 & yx$Status.y==4)])


check = x_t %in% yx_t
check_function()


## Replace Status.x rows with only updated status from Status.y
gg = which(yx$Status.y>0)
yx$Status.x[gg] = yx$Status.y[gg]

gg1 = which(yx$end_date.y>0)
yx$end_date.x[gg1] = yx$end_date.y[gg1]

gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

# Delete Status.y and rename Status.x to Status
rem_id = which(str_detect(colnames(yx),"Status.y|end_date.y|Year.y|Month.y"))
yx = yx[,-rem_id]

# Rename columns
colnames(yx)[which(str_detect(colnames(yx),"Status"))] = "Status"
colnames(yx)[which(str_detect(colnames(yx),"end_date"))] = "end_date"
colnames(yx)[which(str_detect(colnames(yx),"Year"))] = "Year"
colnames(yx)[which(str_detect(colnames(yx),"Month"))] = "Month"


## Delete when Year and Month = 0
id = which(yx$Year == 0)
if(length(id) > 0){
  yx$Year[id] = NA
  yx$Month[id] = NA
} else {
  print("")
}


# Add the latest date
yx$updated = date_update

# Convert date to Excel date format
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

write.xlsx(yx,MLTable)



######################## Quirino Highway Station #########################:------



######################## Tandang Sora Station #########################:------
