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


# Station domain
## East Valenzuela = 1
## Quirino Highway = 2
## Tandang Sora = 3
## North Avenue = 4
## Quezon Avenue = 5
## East Avenue = 6
## Anonas = 7
## Camp Aguinaldo = 8
## Ortigas = 9
## Shaw = 10
## Kalayaan = 11
## BGC = 12
## Lawton = 13
## Senate = 14

# Setting

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)

#google_app <- httr::oauth_app(
#  "Desktop client 1",
#  key = "603155182488-fqkuqgl6jgn3qp3lstdj6liqlvirhag4.apps.googleusercontent.com",
#  secret = "bH1svdfg-ofOg3WR8S5WDzPu"
#)
#drive_auth_configure(app = google_app)
#drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")



# Define Working Directory
a = "C:/Users/oc3512/Dropbox/01-Railway/01-MMSP/03-During-Construction/01-Station Structure/01-Masterlist/01-Compiled"
#a=choose.dir()
wd = setwd(a)

## Enter Date of Update ##:----
date_update = "2021-01-16"

# Read our master list table
MLTable = "C:/Users/oc3512/Dropbox/01-Railway/01-MMSP/03-During-Construction/01-Station Structure/01-Masterlist/01-Compiled/MMSP_Station_Structure.xlsx"

# Read the masterlist:----
y = read.xlsx(MLTable)

head(y)
## Define Parameter:
# Define Type
type_dwall = 1
type_col = 2
type_slab = 3
type_kp = 4

# Define Station
st_EV = 1
st_QH = 2 # Quirino Highway 
st_TS = 3 # Tandang Sora
st_NA = 4 # North Avenue
st_QA = 5 # Quezon Avenue
st_EA = 6 # East Avenue
st_AN = 7 # Anonas stat
st_CA = 8 # Camp Aguinaldo
st_OR = 9 # Ortigas
st_SH = 10 # Ortigas
st_KL = 11 #  Kalayaan
st_BGC = 12 # BGC
st_LAW = 13 #  Lawton
st_SN = 14 #  Senate

###############################################################
#######################:---- North Avenue Station ############:---- 
##############################################################

## Define URL where data is stored and updated
## I used "IMPORTRANGE" to copy information from the source URL to suit our needs.
url = "https://docs.google.com/spreadsheets/d/1wD-fgFafpUDNU270J9ggjtUSgZelfEqbkdRnfr7L2NU/edit?usp=sharing"

## Define Google Sheet number
nas_kp_sheet = 1
nas_dwall_sheet = 2

### NAS: King post:----

# Read and write as CSV and xlsx
v = range_read(url, sheet = nas_kp_sheet)
1
v = data.frame(v)

# Find "KING POST ID" and "COMPLETED" column names
## #King POST ID" is at 5th columns and and 9th row
## COMPLETED is at at 22nd column and 9th row
head(v)
x = v[-c(1:9),c(5,22)]
colnames(x) = c("ID","Status")

head(x)

#
x$ID = as.character(x$ID)
x$Status = as.character(x$Status)

# Retain only KP-
kp_id = which(str_detect(x$ID,"^KP|^kp|^Kp"))
x = x[kp_id,]

status_rm_id = which(str_detect(x$Status,"NULL|null|Null|[[:space:]]"))
x = x[-status_rm_id,]

# Make sure that ID is uppercase letter and no space
x$ID[] = gsub("[[:space:]]","",x$ID) # no space
x$ID[] = toupper(x$ID)

# Conver STatus to numeric
x$Status = as.numeric(x$Status)

# status = 1: Complted (4)
x$Status[x$Status==1] = 4

# Add type
x$Type = type_kp
x$Station = st_NA

head(x)

# Merge this to masterlist
y = read.xlsx(MLTable)

head(y)
yx = left_join(y,x,by=c("Station","Type","ID"))

## Replace Status.x rows with only updated status from Status.y
gg = which(yx$Status.y>0)
yx$Status.x[gg] = yx$Status.y[gg]

# Delete Status.y and rename Status.x to Status
rm_status = which(colnames(yx)=="Status.y")
yx = yx[, -rm_status]

status_name = which(str_detect(colnames(yx),"Status"))
colnames(yx)[status_name] = "Status"

## Create backup files
y$updated = as.Date(y$updated, origin = "1899-12-30")
oldDate = gsub("-","",unique(y$updated))

fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(a,"old")

write.xlsx(y,file.path(direct,fileName),row.names=FALSE)

# Add the latest date
yx$updated = date_update

# Convert date to Excel date format
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

yx$EndDate = as.Date(yx$EndDate, origin = "1899-12-30")
yx$EndDate = as.Date(yx$EndDate, format="%m/%d/%y %H:%M:%S")

write.xlsx(yx,MLTable)


### NAS: D-Wall:----
# Read and write as CSV and xlsx
v = range_read(url, sheet = nas_dwall_sheet)
v = data.frame(v)

# Find "Dwall ID" and "COMPLETED" column names
## #King POST ID" is at 4th columns and and 6th row
## COMPLETED is at at 18th column and 6th row
x = v[-c(1:6),c(4,18)]

colnames(x) = c("ID","Status")


#
x$ID = as.character(x$ID)
x$Status = as.character(x$Status)

head(x)
# Retain only KP-
dwall_id = which(str_detect(x$ID,"^P|^p|^p"))
x = x[dwall_id,]

status_rm_id = which(str_detect(x$Status,"NULL|null|Null|[[:space:]]"))
x = x[-status_rm_id,]

# Make sure that ID is uppercase letter and no space
x$ID[] = gsub("[[:space:]]","",x$ID) # no space
x$ID[] = toupper(x$ID)


# Conver STatus to numeric
x$Status = as.numeric(x$Status)

# status = 1: Complted (4)
x$Status[x$Status==1] = 4

# Add type
x$Type = type_dwall
x$Station = st_NA

# Merge this to masterlist
y = read.xlsx(MLTable)

yx = left_join(y,x,by=c("Station","Type","ID"))

## Replace Status.x rows with only updated status from Status.y
gg = which(yx$Status.y>0)
yx$Status.x[gg] = yx$Status.y[gg]

# Delete Status.y and rename Status.x to Status
rm_status = which(colnames(yx)=="Status.y")
yx = yx[, -rm_status]

status_name = which(str_detect(colnames(yx),"Status"))
colnames(yx)[status_name] = "Status"

# Add the latest date
yx$updated = date_update

# Convert date to Excel date format
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

yx$EndDate = as.Date(yx$EndDate, origin = "1899-12-30")
yx$EndDate = as.Date(yx$EndDate, format="%m/%d/%y %H:%M:%S")

write.xlsx(yx,MLTable)



######################## Quirino Highway Station #########################:------





######################## Tandang Sora Station #########################:------
