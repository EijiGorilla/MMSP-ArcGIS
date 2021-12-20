# This R code reads Google sheet from a table provided by N2 Civil Team for monitoring Viaduct construction
# The source of URL: "https://docs.google.com/spreadsheets/d/11NMBpr1nKXuOgooHDl-CARvrieVN7VjEpLM1XgNwR0c/edit#gid=499307998&fvid=1497289736"
# 
# I copied the Google Sheet using IMPORTRANGE and created a copied Google SHeet (i.e., replica of the source)
# but with only necessary information
# Our URL: "https://docs.google.com/spreadsheets/d/11YqYaenIB0l3Bpiv398-0QO3mEIR_BjvnMIsIOF3ILI/edit#gid=0"
# 
# OPERATION STEPS:
# 1. Read the Google Sheet
# 2. Restructure the data set
# 3. Join the table to our master list table
# 4. Export

# MAKE SURE THAT Type of Viaduct in Domain of ArcGIS Pro follows this:
# Bored Pile = 1
# Pile Cap = 2
# Pier Column = 3
# Pier Head = 4
# Precast = 5

# MAKE SURE THAT Status1 of Viaduct in Domain of ArcGIS Pro follows this:
# To be Constructed = 1
# Under Construction = 2
# Delayed = 3
# Completed = 4




#******************************************************************#
## Enter Date of Update ##
date_update = "2021-12-17"

#******************************************************************#



library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)

google_app <- httr::oauth_app(
  "Desktop client 1",
  key = "603155182488-fqkuqgl6jgn3qp3lstdj6liqlvirhag4.apps.googleusercontent.com",
  secret = "bH1svdfg-ofOg3WR8S5WDzPu"
)
drive_auth_configure(app = google_app)
drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
#gs4_auth(email="matsuzakieiji0@gmail.com")
#gs4_auth(email="matsuzaki-ei@ocglobal.jp")


a = "C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled"
#a=choose.dir()
wd = setwd(a)

# Read our master list table
# C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\02-Civil\03-Viaduct\01-Masterlist\02-Compiled\N2_Viaduct_MasterList.xlsx"
MLTable = file.choose()
# Read the masterlist:----
y = read.xlsx(MLTable)

## Use the following code for concatenating pierNumber and pile numbers for site planner's format
#y$nPierNumber[y$CP=="N-04"] = y$PierNumber
#y$nPierNumber[y$CP=="N-04"] = gsub("-","",y$nPierNumber)
#y$nPierNumber[y$CP=="N-04"] = paste(y$nPierNumber,"-",y$pp2,sep="")
#y$nPierNumber[y$CP=="N-04"] = gsub("-NA","",y$nPierNumber)
#write.xlsx(y,"temp_test.xlsx")
##

###############################################################
####################### N-01 #################################:----
##############################################################

## Define URL where data is stored and updated
## I used "IMPORTRANGE" to copy information from the source URL to suit our needs.
url = "https://docs.google.com/spreadsheets/d/11YqYaenIB0l3Bpiv398-0QO3mEIR_BjvnMIsIOF3ILI/edit#gid=0"


### N01: BORED PILES #############----

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

# Restruecture table
## I temporarliy used dummy field names to be discarded so need to remove it
nChar = sapply(1:ncol(v), function(k) nchar(colnames(v)[k]))
id = which(nChar > 1)
x = v[,id]

## Remove empty rows
rid = which(is.na(x$nPierNumber))
x = x[-rid,]

# Remove bored piles for station structure
pile_st = min(which(str_detect(x$nPierNumber,"^APS")))
remove_rows = pile_st:nrow(x)
x = x[-remove_rows,] 


## Add default status
x$Status1 = 0


# Remove hyphen from pierNumbe
x$nPierNumber = gsub("-","",x$nPierNumber)

uniqueRem = unique(x$Remarks)


x$Status1[str_detect(x$Remarks,pattern="Casted")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Remarks,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Remarks,pattern="Incomplete")] = 3 # Delayed

head(x)
head(y)
# Join new status to Viaduct masterlist
yx = left_join(y,x,by="nPierNumber")

# NA for status = 1 (To be Constructed)
gg = which(yx$Status1.y>1)

yx$Status1.x[gg] = yx$Status1.y[gg]
#yx$Status1.y[is.na(yx$Status1.y)] = yx$Status1.x

delField = which(colnames(yx)=="Status1.y" | colnames(yx)=="Remarks" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
library(lubridate)


yx$updated = ymd(date_update)


#yx$Updated = as.Date(yx$Updated, origin = "1899-12-30")
#yx$Updated = as.Date(yx$Updated, format="%m/%d/%y %H:%M:%S")

## Backup old ones in case
y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")
oldDate = gsub("-","",unique(y$updated))



fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = "C:\\Users\\oc3512\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\03-During-Construction\\02-Civil\\03-Viaduct\\01-Masterlist\\02-Compiled\\old"

write.xlsx(y,file.path(direct,fileName),row.names=FALSE)


# Recover data in excel format
yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


# 
write.xlsx(yx, MLTable, row.names=FALSE,overwrite = TRUE)

# N-01: PILE CAP, PIER COLUN, and PIER HEAD:----

v = range_read(url, sheet = 2)
v = data.frame(v)

# Remove redundant columns and observations
colnames(v)
col = colnames(v)[str_detect(colnames(v),"CP|PILE|PIER|Pier|Pile")]
id = which(colnames(v) %in% col)

v2 = v[-c(1:5),id]


# Re-format column
idd = which(colnames(v2) %in% colnames(v2)[str_detect(colnames(v2),"PILE|PIER")])

head(v2)
for(i in 1:length(idd)){
  v2[[idd[i]]][v2[[idd[i]]]=="NULL"] = 0
  v2[[idd[i]]] = as.numeric(v2[[idd[i]]])
}
str(v2)

# Convert wide to long format
xx <- melt(v2, id=c("CP","PierNo"))

head(xx,20)


# Delete empty observations
iddd = which(xx$value==0 | is.na(xx$value))
xx = xx[-iddd,]

xx
# Update column names
# Bored Pile = 1
# Pile Cap = 2
# Pier Column = 3
# Pier Head = 4
# Precast = 5

colnames(xx) = c("CP","nPierNumber","Type","Status1")
xx$Type = as.character(xx$Type)


xx$Type[xx$Type=="PILE.CAP.done" | xx$Type=="PILE.CAP.ongoing"]=2
xx$Type[xx$Type=="PIER.COLUMN.done" | xx$Type=="PIER.COLUMN.ongoing"]=3
xx$Type[xx$Type=="PIER.HEAD.done" | xx$Type=="PIER.HEAD.ongoing"]=4
xx$Type = as.numeric(xx$Type)

# Status1 = 1: Ongoing (2)
# Status1 > 1: Completed (4)
xx$Status1[xx$Status1==1]=2
xx$Status1[xx$Status1>3]=4

# Delete CP
xx = xx[,-1]

# Unlike bored piles, we need to use nPierNumber AND Type to join Status1 to our master list
# This is because bored piles have unique nPierNumber, while other components do not.
# This means that we cannot bind tables generated here between bored piles and others.
# As such, we will join this updated table of other components to our original master list directly.

# remove CP for join

#
y = read.xlsx(MLTable)

str(y)
str(xx)

yxx = left_join(y,xx,by=c("Type","nPierNumber"))

# OK here


# Delete andRe-name variables again
## Extract row numbers to be replaced with new status
# Because we only want to update status with pier numbers that need to be updated in xx,
# we replace Status1.x with only these pier numbers.


gg = which(yxx$Status1.y>0)
yxx$Status1.x[gg]=yxx$Status1.y[gg]


## Rename and delete Status1.y
id.status1.y = which(colnames(yxx)=="Status1.y")
yxx = yxx[,-id.status1.y]

id.status1.x = which(colnames(yxx)=="Status1.x")
colnames(yxx)[id.status1.x] = "Status1"

## Re-format Date for excel
str(yxx)
yxx$updated = as.Date(yxx$updated, origin = "1899-12-30")
yxx$updated = as.Date(yxx$updated, format="%m/%d/%y %H:%M:%S")

yxx$start_date = as.Date(yxx$start_date, origin = "1899-12-30")
yxx$start_date = as.Date(yxx$start_date, format="%m/%d/%y %H:%M:%S")

yxx$end_date = as.Date(yxx$end_date, origin = "1899-12-30")
yxx$end_date = as.Date(yxx$end_date, format="%m/%d/%y %H:%M:%S")

# Check if Status1 has any empty observations. iF present, something is wrong with the code above

yxx[is.na(yxx$Status1),]


# overwrite masterlist
write.xlsx(yxx, MLTable, row.names=FALSE,overwrite = TRUE)



###############################################################
####################### N-02 #################################:----
##############################################################

url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?userstoinvite=junsanjose@gmail.com&actionButton=1#gid=0"

### N-02: BORED PILES #:----


# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)


id = which(str_detect(v[[2]], "Viaduct"))
del_row = 1:id
x = v[-del_row,]

# Restruecture table
## Remove empty rows and unneeded rows
x = x[,c(2,ncol(x))]
colnames(x)[1:2] = c("nPierNumber", "Status1")
x$Status1 = as.character(x$Status1)

## Find pier numbers starting with only "P" and "MT"
keep_row = which(str_detect(x$nPierNumber, "^P-|^MT"))
x = x[keep_row,]

# Recode Status1
st = unique(x$Status1)

completed_row = which(str_detect(x$Status1,"Completed|completed|Complete|complete"))
inprogress_row = which(str_detect(x$Status1,"In-progress|in-progress|In-Progress|Inprogress"))

x$Status1[completed_row] = 4
x$Status1[inprogress_row] = 2

x$Status1 = as.numeric(x$Status1)
x$CP = "N-02"

# For N-02, I want the first "P-" to be "P"
x$nPierNumber[] = gsub("^P-|^p-|^P|^p", "P",x$nPierNumber)

# Join 
y = read.xlsx(MLTable)

yx = left_join(y,x,by="nPierNumber")


# NA for status = 1 (To be Constructed)
gg = which(yx$Status1.y>0)

yx$Status1.x[gg] = yx$Status1.y[gg]
delField = which(colnames(yx)=="Status1.y" | colnames(yx)=="Remarks" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
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
yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

head(yx)

# 
write.xlsx(yx, MLTable, row.names=FALSE,overwrite = TRUE)



###############################################################
####################### N-03 #################################:----
##############################################################
url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit#gid=0"

n03_pile = 1
CP = "N-03"
  
# read and write as CSV and xlsx
v = range_read(url, sheet = n03_pile)
v = data.frame(v)

# filter out
x = v[,c(2,14)]

colnames(x)[c(1,2)] = c("nPierNumber", "Status1")

# Convert to string
x$nPierNumber = as.character(x$nPierNumber)
x$Status1 = as.character(x$Status1)
x$CP = CP

# Delete empty cells
rem_id = which(is.na(x$nPierNumber))
x = x[-rem_id,]

# Extract only piles
pile_id = which(str_detect(x$nPierNumber,"^P-"))
x = x[pile_id,]

x$nPierNumber = gsub("^P-","P",x$nPierNumber)

# convert stats
x$Status1[str_detect(x$Status1,pattern="Completed|completed")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Status1,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Status1,pattern="Incomplete")] = 3 # Delayed

x$Status1 = as.numeric(x$Status1)


# Read master list and join
y = read.xlsx(MLTable)

## Join 
yx = left_join(y,x,by="nPierNumber")

# NA for status = 1 (To be Constructed)
gg = which(yx$Status1.y>0)

yx$Status1.x[gg] = yx$Status1.y[gg]
delField = which(colnames(yx)=="Status1.y" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Change Status name
head(yx)
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
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

yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

head(yx)

# 
write.xlsx(yx, MLTable, row.names=FALSE,overwrite = TRUE)


###############################################################
####################### N-04 #################################:----
##############################################################
url = "https://docs.google.com/spreadsheets/d/1OWdmM36PWL5MgH0lK9HpigaoVq4L7Q6hm7DSN2FxiAA/edit#gid=0"

### N-04: BORED PILES #:----


# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

# Restruecture table
## I temporarliy used dummy field names to be discarded so need to remove it
nChar = sapply(1:ncol(v), function(k) nchar(colnames(v)[k]))
id = which(nChar > 1)
x = v[,id]

## Remove empty rows
head(x)
rid = which(is.na(x$nPierNumber))

if(length(rid)==0){
  print("no nrows being removed")
} else {
  x = x[-rid,]
}

x$nPierNumber = as.character(x$nPierNumber)

## Add default status
x$Status1 = 0
head(x)

# Remove hyphen from pierNumber
## correct with "P-"
x$nPierNumber = gsub("[[:space:]]","",x$nPierNumber)
#x$nPierNumber = gsub("^[P]","P-",x$nPierNumber)
#x$nPierNumber = gsub("^PLK ","PLK-",x$nPierNumber)
x$nPierNumber = gsub("DEPO","DEP0",x$nPierNumber)

# Remove rows that do not contain the following texts "P", "PLK", "DEP0"
x = x[str_detect(x$nPierNumber,"^P|^PLK|^DEP0"),]

unique(x$nPierNumber)

uniqueRem = unique(x$Remarks)


x$Status1[str_detect(x$Remarks,pattern="Casted|casted")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Remarks,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Remarks,pattern="Incomplete")] = 3 # Delayed

del_id = which(x$Status1 == 0)
x = x[-del_id,]

# Join new status to Viaduct masterlist
y = read.xlsx(MLTable)

yx = left_join(y,x,by="nPierNumber")

# NA for status = 1 (To be Constructed)
gg = which(yx$Status1.y>0)

yx$Status1.x[gg] = yx$Status1.y[gg]
delField = which(colnames(yx)=="Status1.y" | colnames(yx)=="Remarks" | colnames(yx)=="CP.y")
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
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
yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

head(yx)

# 
write.xlsx(yx, MLTable, row.names=FALSE,overwrite = TRUE)

###################
### N-04: Pilec Caps #;----
#####################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 2)
v = data.frame(v)


# Remove redundant columns and observations
colnames(v)
col = colnames(v)[str_detect(colnames(v),"CP|PILE|PIER|Pier|Pile|Remarks")]
id = which(colnames(v) %in% col)

v2 = v[,id]

#
head(v2)
v2$nPierNumber[] = gsub("^P ","P",v2$nPierNumber)
v2$nPierNumber[] = gsub("P-","P",v2$nPierNumber)

# Delete empty observations
unique(v2$nPierNumber)
iddd = which(is.na(v2$Remarks))
xx = v2[-iddd,]

# Update column names
# Bored Pile = 1
# Pile Cap = 2
# Pier Column = 3
# Pier Head = 4
# Precast = 5

xx$Type = 2
xx$Status1 = 0

# if Casted, status1 = 1
casted_id = which(str_detect(xx$Remarks, "Casted|casted"))

xx$Status1[casted_id] = 4


# Delete CP and Remarks
del_id = which(str_detect(colnames(xx),"CP|Remarks"))
xx = xx[,-del_id]
# Unlike bored piles, we need to use nPierNumber AND Type to join Status1 to our master list
# This is because bored piles have unique nPierNumber, while other components do not.
# This means that we cannot bind tables generated here between bored piles and others.
# As such, we will join this updated table of other components to our original master list directly.

# remove CP for join

#
y = read.xlsx(MLTable)

yxx = left_join(y,xx,by=c("Type","nPierNumber"))

head(yxx)
# Delete andRe-name variables again
## Extract row numbers to be replaced with new status
# Because we only want to update status with pier numbers that need to be updated in xx,
# we replace Status1.x with only these pier numbers.
gg = which(yxx$Status1.y>0)
yxx$Status1.x[gg]=yxx$Status1.y[gg]

## Rename and delete Status1.y
id.status1.y = which(colnames(yxx)=="Status1.y")
yxx = yxx[,-id.status1.y]

id.status1.x = which(colnames(yxx)=="Status1.x")
colnames(yxx)[id.status1.x] = "Status1"

## Re-format Date for excel
str(yxx)
yxx$updated = as.Date(yxx$updated, origin = "1899-12-30")
yxx$updated = as.Date(yxx$updated, format="%m/%d/%y %H:%M:%S")

yxx$start_date = as.Date(yxx$start_date, origin = "1899-12-30")
yxx$start_date = as.Date(yxx$start_date, format="%m/%d/%y %H:%M:%S")

yxx$end_date = as.Date(yxx$end_date, origin = "1899-12-30")
yxx$end_date = as.Date(yxx$end_date, format="%m/%d/%y %H:%M:%S")

# Check if Status1 has any empty observations. iF present, something is wrong with the code above

yxx[is.na(yxx$Status1),]


# overwrite masterlist
write.xlsx(yxx, MLTable, row.names=FALSE,overwrite = TRUE)
