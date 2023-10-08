# this code is to update construction progress for N1 in alignment maps of Site in Portal for ArcGIS

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(fs)
library(lubridate)
library(rrapply)
library(purrr)

############################################################################

## As of August 14, 2023
## the following piers are duplicated
## "PR-6"   "PR1-34" "PR1-35" "PR1-36" "PR1-37" "PR2-2" 

#******************************************************************#
## Enter Date of Update ##
old_date = "2023-07-31"
date_update = "2023-09-31"

#******************************************************************#

gs4_auth(email="matsuzaki-ei@ocglobal.jp") #matsuzakieiji0@gmail.com
path =  path_home()

## Define working directory
wd = file.path(path, "Dropbox/01-Railway/03-NSCR")
setwd(wd)

# Read our master list table
## MasterList file name: "NSCR_Constuction_Progress_by_pier.xlsx"
MLTable = file.choose()

# Read the masterlist:----
y = read.xlsx(MLTable)


############# BACKUP #################
## Skip if necessary
oldDate = gsub("-","",old_date)

fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(wd,"old")

write.xlsx(y,file.path(direct,fileName))
########## BACKUP END #################

# Main URL of Google Sheet
url = "https://docs.google.com/spreadsheets/d/1e9YmnTp99L6CcbbJokVLIxZX04NHl6YqFDU_dETPEZE/edit?usp=sharing"

## 1. Construction Progress by Pier:----
v = range_read(url, sheet = 1)
v = data.frame(v)

str(v)

# Extract only target field names
x = v[,1:4]
colnames(x) = c("PierNo","construcStat","uniqueID", "CP")

# make sure that construction status notation is correct
## To Be Constructed
id=which(str_detect(x$construcStat,"Constructed|constructed|^To Be.*"))
x$construcStat[id] = "To Be Constructed"

## On-going
id=which(str_detect(x$construcStat,"On-going|on-going|ongoing|Ongoing|going|going$|Going$"))
x$construcStat[id] = "On-going"

## Completed
id=which(str_detect(x$construcStat,"Completed|completed|^comp|^Comp"))
x$construcStat[id] = "Completed"

# Remove all space for PierNo
x$PierNo = gsub("[[:space:]]","",x$PierNo)

# In Google Sheet, the following pierNos need to add 'NS' to match with GIS attribute tables
id=which(str_detect(x$PierNo,"^PR-1$|^PR-2$|^PR-3$|^PR-4$|^PR-5$|^PR-6$"))
x$PierNo[id] = paste(x$PierNo[id],"NS",sep = "")

# Overwrite
write.xlsx(x, MLTable, overwrite = TRUE)

########################

# GIS table
b = file.choose()
gis = read.xlsx(b)

str(x)
str(gis)
x1 = x[,c(1,3)]
colnames(x1)[2] = "testID"
head(x1)
tail(x1)

xy = left_join(gis, x1, by="PierNo")
tail(xy)

# duplicated PierNo for attribute table
dup = gis$PierNo[duplicated(gis$PierNo)]
dup_gis = paste0(dup,collapse="|")
id=which(str_detect(gis$PierNo,dup_gis))
gis[id,]

# duplicated PierNo for google sheet
dup = x$PierNo[duplicated(x$PierNo)]
dup_x = paste0(dup,collapse="|")
id=which(str_detect(x$PierNo,dup_x))
write.xlsx(x[id,],"Duplicated_N1_pier_for_construction_monitoring.xlsx")

### Check for matching
gs_pier = x1$PierNo
gis_pier = gis$PierNo
#gis_pier = gsub("[[:space:]]","",gis_pier)

miss_in_gs = gis_pier[!gis_pier %in% gs_pier]
