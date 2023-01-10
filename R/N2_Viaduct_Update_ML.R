# This R code reads Google sheet from a table provided by N2 Civil Team for monitoring Viaduct construction
# The source of URL: "https://docs.google.com/spreadsheets/d/11NMBpr1nKXuOgooHDl-CARvrieVN7VjEpLM1XgNwR0c/edit#gid=499307998&fvid=1497289736"
# 
# I copied the Google Sheet using IMPORTRANGE and created a copied Google SHeet (i.e., replica of the source)
# but with only necessary information
# GIS URL: "https://docs.google.com/spreadsheets/d/11YqYaenIB0l3Bpiv398-0QO3mEIR_BjvnMIsIOF3ILI/edit#gid=0"
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


library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(fs)
library(lubridate)

####################################################################
### 0: PRELIMINARY WORK----
## Please run the following code when nPierNumber needs to be re-assigned

## Make sure that nPierNumber follows the format of each site planner from N-01 to N-04
aa = file.choose()
x = read.xlsx(aa)

x$pp2 = as.character(x$pp2)

id = which(x$pp<10)
x$pp2[id] = paste("0",x$pp[id],sep="")

## N-01 ##
# e.g., P24A, P24B,  (A and B is pile number)
id = which(x$CP=="N-01")
x$nPierNumber[id] = x$PierNumber[id]
x$nPierNumber[id] = gsub("-","",x$nPierNumber[id])


pierLetter = c("A","B","C","D","E","F","G","H","I","J","K","L")
upp = unique(x$pp[id])
upp = upp[!is.na(upp)]

head(x)
for(i in upp){
  id = which(x$CP=="N-01" & x$pp==i)
  x$nPierNumber[id] = paste(x$nPierNumber[id],pierLetter[i],sep="")
}

## N-02 ##
# e.g., P429-P01, P429-P02 (P01 and P02 are pile numbers)
id = which(x$CP=="N-02")
x$nPierNumber[id] = x$PierNumber[id]
x$nPierNumber[id] = gsub("-","",x$nPierNumber[id])

pile_id = which(x$CP=="N-02" & x$Type==1)
x$nPierNumber[pile_id] = paste(x$nPierNumber[pile_id],"-P",x$pp2[pile_id],sep="")

## N-03 #
# e.g., P826-1, P826-2 (1 and 2 are pile numbers)
id = which(x$CP=="N-03")
x$nPierNumber[id] = x$PierNumber[id]
x$nPierNumber[id] = gsub("-","",x$nPierNumber[id])

pile_id = which(x$CP=="N-03" & x$Type==1)
x$nPierNumber[pile_id] = paste(x$nPierNumber[pile_id],"-",x$pp[pile_id],sep="")

head(x[which(x$CP=="N-03"),],20)

## N-04 ##
# e.g., P1159-01, P1159-02 (01 is pile number)
id = which(x$CP=="N-04")
x$nPierNumber[id] = x$PierNumber[id]
x$nPierNumber[id] = gsub("-","",x$nPierNumber[id])

pile_id = which(x$CP=="N-04" & x$Type==1)
x$nPierNumber[pile_id] = paste(x$nPierNumber[pile_id],"-",x$pp2[pile_id],sep="")


## Reformat date
x$updated = "2022-02-07"
x$updated = as.Date(x$updated, origin = "1899-12-30")
x$updated = as.Date(x$updated, format="%m/%d/%y %H:%M:%S")

x$start_date = as.Date(x$start_date, origin = "1899-12-30")
x$start_date = as.Date(x$start_date, format="%m/%d/%y %H:%M:%S")

x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# Re-assign ID
## Bored Piles: Contract Package No. + Pier Number + Structure Type + Bored Pile No.
### e.g., N-04-PLK-1-Pile-L1

## Others: Contract Package No. + Pier Number + Structure Type
### e.g., N-04-PLK-1-PileCap

x$Status1 = as.numeric(x$Status1)

write.xlsx(x,MLTable)
##


############################################################################

#******************************************************************#
## Enter Date of Update ##
date_update = "2023-01-06"

#******************************************************************#

gs4_auth(email="matsuzaki-ei@ocglobal.jp") #matsuzakieiji0@gmail.com
path =  path_home()

## Define working directory
wd = file.path(path, "Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled")
setwd(wd)

# Read our master list table
## MasterList file name: "N2_Viaduct_MasterList.xlsx"
MLTable = file.choose()

# Read the masterlist:----
y = read.xlsx(MLTable)

############## BACKUP #################
## Skip if necessary
y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")
oldDate = gsub("-","",unique(y$updated))

fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(wd,"old")

write.xlsx(y,file.path(direct,fileName))
########## BACKUP END #################

##########************************************########
## The code below checks duplicated observations
## Run as necessary

#uType = unique(y$Type)
#uCP = unique(y$CP)

#temp = data.frame()
#for(i in uCP){
#  i="N-01"
#  for(j in uType){
#    j=2
#    yx = y[which(y$CP==i & y$Type==j),]
#    pierN = yx$nPierNumber
#    
#    dupPierN = pierN[duplicated(pierN)]
#
#    nrep = length(dupPierN)
#    t = data.frame(CP=rep(i,nrep),Type=rep(j,nrep),DupPierN=dupPierN)
#    temp = rbind(temp,t)
#  }
#}
#temp
#write.xlsx(temp,"N2_Duplicated_observations.xlsx")



###############################################################
####################### N-01 #################################:----
##############################################################

## Define URL where data is stored and updated
## I used "IMPORTRANGE" to copy information from the source URL to suit our needs.

url = "https://docs.google.com/spreadsheets/d/11NMBpr1nKXuOgooHDl-CARvrieVN7VjEpLM1XgNwR0c/edit?usp=sharing"
#################################
### N01: BORED PILES #############----
#################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 3)
v = data.frame(v)


# Extract only target field names
## CP, nPierNumber, end_date (K column), Remarks
#id = which(str_detect(colnames(v),"CP|nPierNumber|K|Remarks"))

#x = v[,id]
x = v[,c(3,12,22)]

colnames(x) = c("nPierNumber","end_date","Remarks")
x = x[-c(1,2),]

#id = which(str_detect(colnames(x),"K"))
#colnames(x)[3] = "end_date"

## Remove empty rows
rid = which(is.na(x$nPierNumber))
x = x[-rid,]

# Remove bored piles for station structure
pile_id = which(str_detect(x$nPierNumber,"^P-|^P.*"))
x = x[pile_id,]

## Add default status
x$Status1 = 0


# Remove hyphen from npierNumber
x$nPierNumber = gsub("-","",x$nPierNumber)

uniqueRem = unique(x$Remarks)

# Assign status numbers
x$Status1[str_detect(x$Remarks,pattern="Casted|casted")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Remarks,pattern="Inprogress|inprogress|In-Progress|in-progress")] = 2 # Under Construction
x$Status1[str_detect(x$Remarks,pattern="Incomplete|incomplete")] = 3 # Delayed

unique(x$Status1)

# Detect duplicated nPierNumbers and if present delete
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Join new status to Viaduct masterlist
y = read.xlsx(MLTable)
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
x.pile = x$nPierNumber[x$Status1==4]
yx.pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==1 & yx$CP=="N-01")]

missing_in_yx = x.pile[!x.pile %in% yx.pile] # not exist in yx table
missing_in_x = yx.pile[!yx.pile %in% x.pile] # not exist in x table

check_Completed = function(){
  if(length(missing_in_yx)>0){
    print("You have missing nPierNumber in yx table compared with x table")
  } else {
  if(length(missing_in_x)>0){
    print("YOu have missing nPierNumber in x table compared with yx table")
  }
  }
}
check_Completed()


# Check for all statuses
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP=="N-01" & yx$Type==1)])

check = x_t %in% yx_t

check_function = function(){
  if(length(which(check=="FALSE"))>0){
    print("Number of Status1 is DIFFERENT. PLEASE CHECK")
  } else (
    print("GOOD! The number of Status1 is same between Civil and joined excel ML.")
  )
}

check_function()

# NA for status = 1 (To be Constructed)
gg = which(yx$CP.x=="N-01" & yx$Type==1)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]

## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

#yx$Status1.y[is.na(yx$Status1.y)] = yx$Status1.x

delField = which(str_detect(colnames(yx),"Status1.y|Remarks|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
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


# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(str_detect(colnames(yx),"updated|Updated|UPDATED"))
yx = yx[,-iid]

## Add new dates
library(lubridate)

yx$updated = ymd(date_update)

# Recover data in excel format
#yx$end_date = as.Date(yx$end_date, origin ="1899-12-30")
head(yx)
yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

yx[is.na(yx$Status1),]

# Overwrite MasterList
write.xlsx(yx, MLTable, overwrite = TRUE)

###################################################
# N-01: PILE CAP, PIER COLUN, and PIER HEAD:----
###################################################
url = "https://docs.google.com/spreadsheets/d/1Cl_tn3dTPdt8hrqzZtl_WjCxy9L-ltn7GrOmQpHdBw4/edit#gid=0"
v = range_read(url, sheet = 1)
v = data.frame(v)

# Remove redundant columns and observations
colnames(v)
col = colnames(v)[str_detect(colnames(v),"PILE|PIER|Pier|Pile|end_date")]
id = which(colnames(v) %in% col)

v2 = v[,id]

# for now delete PIER.COLUMN.end_date2 (2nd lift). I cannot convert this to date format because of "n/a" character
# Delete observations with PierNo is null
id = which(is.na(v2$nPierNumber))
if(length(id)==0){
  print("no need to delete any rows")
} else {
  v2=v2[-id,]
}

# Re-format column
colnames(v2)
idd = which(colnames(v2) %in% colnames(v2)[str_detect(colnames(v2),"PILE|PIER")])

for(i in idd){
  if(str_detect(colnames(v2[i]),"end_date|end_date1$|end_date2$")){
    print("no need to change data type")
  } else {
    v2[[i]][v2[[i]]=="NULL"] = 0
    v2[[i]] = as.numeric(v2[[i]])
  }
}

# Convert wide to long format
v2$CP = "N-01"

## 1.1. Only fields with dates*----
id = which(str_detect(colnames(v2),"end_date|CP|nPierNumber"))
v3 = v2[,id]

library("tidyr")
xx1 = gather(v3, variable, value, -CP, -nPierNumber)
#xx1 = melt(v3,id=c("CP","nPierNumber"))
xx1$variable = as.character(xx1$variable)

### Need to add Type to each row
xx1$Type = 0

xx1$Type[which(str_detect(xx1$variable,"^PILE.CAP"))] = 2
xx1$Type[which(str_detect(xx1$variable,"^PIER.COLUMN"))] = 3
xx1$Type[which(str_detect(xx1$variable,"^PIER.HEAD"))] = 4

# check if there is any 0
unique(xx1$Type)

### Delete and rename
head(xx1)
id = which(str_detect(colnames(xx1),"CP|variable"))
xx1 = xx1[,-id]

colnames(xx1) = c("nPierNumber","end_date","Type")

xx1[xx1$Type==2,]

#########################################
### Re-format nPierNumber ###
id = which(str_detect(xx1$nPierNumber,"Center$|center$|Right$|right$|Left$|left$"))
id_extract = str_extract(xx1[id,"nPierNumber"],"Center$|center$|Right$|right$|Left$|left$")
del_w = unique(id_extract)
del_w = paste(del_w,collapse="|",sep="")

#### Delete these words from nPierNumber
xx1$nPierNumber[id] = gsub(del_w,"",xx1$nPierNumber[id])
unique(xx1$nPierNumber)

#### make sure that nPierNumber is all uppercase letter
xx1$nPierNumber = toupper(xx1$nPierNumber)

#### Remove all spaces
xx1$nPierNumber = gsub("[[:space:]]","",xx1$nPierNumber)

#### Remove bracket if present
xx1$nPierNumber = gsub("[()]","",xx1$nPierNumber)

#### Delete empty observation of end_date
####
id = which(xx1$end_date=="NULL")
xx1$end_date[id] = NA

#x$end_date = unlist(x$end_date, use.names=FALSE)
da = unlist(xx1$end_date, use.names=FALSE)
xx1$end_date = as.POSIXlt(da, origin="1970-01-01", tz="UTC")
xx1$end_date = as.Date(xx1$end_date, origin = "1899-12-30")
xx1$end_date = as.Date(xx1$end_date, format="%m/%d/%y %H:%M:%S")

### Re-format nPierNumber END ###
#########################################

## 1.2. Only fields with numbers*----
id = which(str_detect(colnames(v2),"end_date"))
v4 = v2[,-id]
xx = melt(v4, id=c("CP","nPierNumber"))

# Delete empty observations
iddd = which(xx$value==0 | is.na(xx$value))
xx = xx[-iddd,]
xx[xx$nPierNumber == ""]

# Update column names
# Bored Pile = 1
# Pile Cap = 2
# Pier Column = 3
# Pier Head = 4
# Precast = 5

colnames(xx) = c("CP","nPierNumber","Type","Status1")
xx$Type = as.character(xx$Type)

# Status1 = 1: Ongoing (2)
# Status1 > 1: Completed (4)

## Completed
xx$Status1[which(xx$Type=="PILE.CAP.Status" & xx$Status1==1)]=4
xx$Status1[which(xx$Type=="PIER.COLUMN.Status" & xx$Status1==1)]=4
xx$Status1[which(xx$Type=="PIER.HEAD.Status" & xx$Status1==1)]=4

## Ongoing
xx$Status1[which(xx$Type=="PILE.CAP.Status" & xx$Status1 < 1)]=2
xx$Status1[which(xx$Type=="PIER.COLUMN.Status" & xx$Status1 < 1)]=2
xx$Status1[which(xx$Type=="PIER.HEAD.Status" & xx$Status1 < 1)]=2

# Re-code Type
xx$Type[xx$Type=="PILE.CAP.Status"]=2
xx$Type[xx$Type=="PIER.COLUMN.Status"]=3
xx$Type[xx$Type=="PIER.HEAD.Status"]=4
xx$Type = as.numeric(xx$Type)

# Delete CP
xx = xx[,-1]

xx[which(xx$Type==3 & xx$Status1==4),]

# Edit nPierNumber
id = which(str_detect(xx$nPierNumber,"Center$|center$|Right$|right$|Left$|left$"))
id_extract = str_extract(xx[id,"nPierNumber"],"Center$|center$|Right$|right$|Left$|left$")
del_w = unique(id_extract)
del_w = paste(del_w,collapse="|",sep="")

## Delete these words from nPierNumber
xx$nPierNumber[id] = gsub(del_w,"",xx$nPierNumber[id])

## Check pier Number
unique(xx$nPierNumber)
### make sure that nPierNumber is all uppercase letter
xx$nPierNumber = toupper(xx$nPierNumber)

### Remove all spaces
xx$nPierNumber = gsub("[[:space:]]","",xx$nPierNumber)

### Remove bracket if present
xx$nPierNumber = gsub("[()]","",xx$nPierNumber)

unique(xx$nPierNumber)

## we need to check duplicated observations for each type
type=unique(xx$Type)

for(i in type){
  id = which(duplicated(xx$nPierNumber[xx$Type==i]))
  if(length(id)>0){
    xx = xx[-id,]
  } else {
    print("no duplicated observations")
  }
  
}

## 1.3. Finaly, join with end_date:---- 
xxx = left_join(xx,xx1,by=c("nPierNumber","Type"))

# Unlike bored piles, we need to use nPierNumber AND Type to join Status1 to our master list
# This is because bored piles have unique nPierNumber, while other components do not.
# This means that we cannot bind tables generated here between bored piles and others.
# As such, we will join this updated table of other components to our original master list directly.

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
xxx$Year = as.numeric(format(xxx$end_date, format="%Y"))
xxx$Month = as.numeric(format(xxx$end_date,format="%m"))

id = which(xxx$Status1 > 4)
if(length(id) > 0){
  xxx = xxx[-id,]
} else {
  print("")
}

# remove CP for join
y = read.xlsx(MLTable)
yxx = left_join(y,xxx,by=c("Type","nPierNumber"))

# Delete andRe-name variables again
## Extract row numbers to be replaced with new status
# Because we only want to update status with pier numbers that need to be updated in xx,
# we replace Status1.x with only these pier numbers.

## Check if the number of Status1 for each Type is same between x and yx.
xx_t = table(xxx$Type,xxx$Status1)
id=which(yxx$CP=="N-01" & (yxx$Type>=2 & yxx$Type<5)) # pile cap, pier, pier head

yxx_t = table(yxx$Type[id],yxx$Status1.y[id])

check = xx_t %in% yxx_t
check_function()

## N-01 Pier Head for P169 is causing this difference, but make it 'Completed' and ignore this warning.

### use the following when you need to check
xx_pier = xx$nPierNumber[which(xx$Type>=2 & xx$Status1<5)]
yxx_pier = yxx$nPierNumber[which(yxx$Type>=2 & yxx$Status1.y<5 & yxx$CP=="N-01")]

xx_pier[!xx_pier %in% yxx_pier]
yxx_pier[!yxx_pier %in% xx_pier]

id = which(yxx$nPierNumber == 'P169' & yxx$Type == 4)
yxx$Status1.y[id] = 4

# Be careful, we need to replace all observations with new ones, not just updated ones
gg = which(yxx$CP=="N-01" & yxx$Type>1 & yxx$Type<5)

library(lubridate)
yxx$end_date.x = as.Date(yxx$end_date.x, origin = "1899-12-30")
yxx$end_date.x = as.Date(yxx$end_date.x, format="%m/%d/%y %H:%M:%S")

#gg = which(yxx$Status1.y>0)

yxx$Status1.x[gg] = yxx$Status1.y[gg]
yxx$end_date.x[gg] = yxx$end_date.y[gg]

## Year and Date
gg2 = which(yxx$Year.y>0)
yxx$Year.x[gg2] = yxx$Year.y[gg2]
yxx$Month.x[gg2] = yxx$Month.y[gg2]

## Rename and delete Status1.y
delField = which(str_detect(colnames(yxx),"Status1.y|end_date.y|Year.y|Month.y"))
yxx = yxx[,-delField]

# Change Status name
colnames(yxx)[str_detect(colnames(yxx),pattern="Status1")] = "Status1"
colnames(yxx)[str_detect(colnames(yxx),pattern="end_date")] = "end_date"
colnames(yxx)[which(str_detect(colnames(yxx),"Year"))] = "Year"
colnames(yxx)[which(str_detect(colnames(yxx),"Month"))] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yxx$Status1))
yxx$Status1[id] = 1


## Re-format Date for excel
str(yxx)
yxx$updated = as.Date(yxx$updated, origin = "1899-12-30")
yxx$updated = as.Date(yxx$updated, format="%m/%d/%y %H:%M:%S")

yxx$start_date = as.Date(yxx$start_date, origin = "1899-12-30")
yxx$start_date = as.Date(yxx$start_date, format="%m/%d/%y %H:%M:%S")

#yxx$end_date = as.Date(yxx$end_date, origin = "1899-12-30")
#yxx$end_date = as.Date(yxx$end_date, format="%m/%d/%y %H:%M:%S")

unique(yxx$end_date)

# Check if Status1 has any empty observations. iF present, something is wrong with the code above

yxx[is.na(yxx$Status1),]

# overwrite masterlist
write.xlsx(yxx, MLTable)


###################################################
# N-01: Pre-CAST                        :----
###################################################
url = "https://docs.google.com/spreadsheets/d/1Cl_tn3dTPdt8hrqzZtl_WjCxy9L-ltn7GrOmQpHdBw4/edit#gid=0"
# Read and write as CSV and xlsx
v = range_read(url, sheet = 2)
v = data.frame(v)

# Keep only fields needed
id=which(str_detect(colnames(v),"nPierNumber|start_date|end_date|Status1"))
x = v[,id]

## Identify a row number where nPierNumber is cut-off.  
#idr=min(which(is.na(v$nPierNumber)))
#x=v[1:idr-1,id]

x = x[-c(1:2),]

# Delete empty Status
id = which(is.na(x$Status1))
x = x[-id,]

# Re-format fields
x$nPierNumber = as.character(x$nPierNumber)

## start-date
da = unlist(x$start_date, use.names=FALSE)
x$start_date = as.POSIXlt(da, origin="1970-01-01", tz="UTC")
x$start_date = as.Date(x$start_date, origin = "1899-12-30")
x$start_date = as.Date(x$start_date, format="%m/%d/%y %H:%M:%S")

# end-date
end_date_ = x$end_date
uu = unique(end_date_)

if(is.na(uu)){
  print("SKIP the this, as all observations are NA = no end_date")
  x$end_date = "NA"

} else {
  id = which(x$end_date=="NULL")
  x$end_date[id] = NA
  #x$end_date = unlist(x$end_date, use.names=FALSE)
  da = unlist(x$end_date, use.names=FALSE)
  x$end_date = as.POSIXlt(da, origin="1970-01-01", tz="UTC")
  x$end_date = as.Date(x$end_date, origin = "1899-12-30")
  x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")
}

# Edit nPierNumber
## There are some pier number with curly brackest. Remove this
rem = unique(str_extract(x$nPierNumber,"\\([^()]+\\)"))

## remove NA
rem = rem[!is.na(rem)]
rem = paste0(rem,collapse = "|")

## remove from nPierNumber
id = which(str_detect(x$nPierNumber,rem))
x$nPierNumber[id] = gsub(rem,"",x$nPierNumber[id])

## Remove curly bracket
id=which(str_detect(x$nPierNumber,"[()]"))
x$nPierNumber[id] = gsub("[()]","",x$nPierNumber[id])

## Remove all spaces
x$nPierNumber = gsub("[[:space:]]","",x$nPierNumber)

## All Uppercase letter for nPierNumber
x$nPierNumber = toupper(x$nPierNumber)

### Re-format nPierNumber so that it aligns with the GIS attribute table
id_NB = which(str_detect(x$nPierNumber,"NB"))
id_SB = which(str_detect(x$nPierNumber,"SB"))

x$nPierNumber = str_extract(x$nPierNumber,"^P\\d+|MT.*")
x$nPierNumber[id_NB] = paste(x$nPierNumber[id_NB],"NB",sep = "")
x$nPierNumber[id_SB] = paste(x$nPierNumber[id_SB],"SB",sep = "")

x$nPierNumber = gsub("-","",x$nPierNumber)

## Status1: if Status is NOT 1 (completed), convert them to NA
id=which(x$Status1 != 1)
x$Status1[id] = 2

id=which(x$Status1==1)
x$Status1[id] = 4

id=which(is.na(x$Status1))
x$Status1[id]=1

## Enter precast 
x$Type = 5

# Check Duplicated observation
id = which(duplicated(x$nPierNumber))

## note that duplicated observations could simply be derived from wron
if(length(id)>0){
  ##xx = xx[-id,]
  print("There are duplicated nPierNumbers PLEASE CHCECK!!!")
} else {
  print("no duplicated observations")
}

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Join new status to Viaduct masterlist
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP=="N-01" & yx$Type==5)])

check = x_t %in% yx_t
check_function()

x.precast = x$nPierNumber[x$Status1>=1]
yx.precast = yx$nPierNumber[which(yx$Type==5 & yx$CP=="N-01")]

missing_in_yx = x.precast[!x.precast %in% yx.precast] # not exist in yx table
##missing_in_x = yx.precast[!yx.precast %in% x.precast] # not exist in x table

# NA for status = 1 (To be Constructed)
gg = which(yx$CP=="N-01" & yx$Type==5)

# start_date and end_date
yx$start_date.x = as.Date(yx$start_date.x, origin = "1899-12-30")
yx$start_date.x = as.Date(yx$start_date.x, format="%m/%d/%y %H:%M:%S")
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

# when end_date.y is all NA or empty
yx$end_date.y = as.Date(yx$end_date.y, format="%m/%d/%y %H:%M:%S")
#gg = which(yx$Status1.y>1
yx$Status1.x[gg] = yx$Status1.y[gg]
yx$start_date.x[gg] = yx$start_date.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

#yx$Status1.y[is.na(yx$Status1.y)] = yx$Status1.x
delField = which(str_detect(colnames(yx),"Status1.y|start_date.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="start_date")] = "start_date"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
library(lubridate)

yx$updated = ymd(date_update)

# Recover data in excel format
y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")

yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

yx[is.na(yx$Status1),]

# Output 
write.xlsx(yx, MLTable)


###############################################################
####################### N-02 #################################:----
##############################################################

#url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?userstoinvite=junsanjose@gmail.com&actionButton=1#gid=0"
url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?usp=sharing"

# sheet no
boredPile = 2
pileCap = 4
PierCol = 5
PierHead = 6

## TEMP
a = file.choose()
x = read.xlsx(a,sheet = 1)
head(x)

###########################
### N-02: BORED PILES #:----
################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = boredPile)
v = data.frame(v)

id = which(str_detect(v[[2]], "^P-"))
x = v[id,]

# Restruecture table
## Remove empty rows and unneeded rows
x = x[,c(2,9,ncol(x))]
colnames(x) = c("nPierNumber", "end_date","Status1")
x$Status1 = as.character(x$Status1)

## No. 999
## Find pier numbers starting with only "P" and "MT"
keep_row = which(str_detect(x$nPierNumber, "^P-|^MT"))
x = x[keep_row,]

# Recode Status1
st = unique(x$Status1)

completed_row = which(str_detect(x$Status1,"Completed|completed|Complete|complete"))
inprogress_row = which(str_detect(x$Status1,"In-progress|in-progress|In-Progress|Inprogress"))

x$Status1[completed_row] = 4
x$Status1[inprogress_row] = 2

unique(x$Status1)

x$Status1 = as.numeric(x$Status1)
x$CP = "N-02"

# For N-02, I want the first "P-" to be "P"
x$nPierNumber[] = gsub("^P-|^p-|^P|^p", "P",x$nPierNumber)

id = which(x$end_date=="NULL")
x$end_date[id] = NA

da=unlist(x$end_date, use.names = FALSE)


x$end_date = da
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01", tz="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")


## There are some duplicated observations
#id = x$nPierNumber[duplicated(x$nPierNumber)]
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
x_pile = x$nPierNumber[which(x$Status1==4)]
yx_pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==1 & yx$CP.x=="N-02")]

yx_pile[duplicated(yx_pile)]

str(x_pile)
str(yx_pile)

nn_x = str_extract(x_pile,"^P\\d+")
nn_x = gsub("P","",nn_x)
nn_x = unique(nn_x)

nn_y = str_extract(yx_pile,"^P\\d+")
nn_y = gsub("P","",nn_y)
nn_y = unique(nn_y)


missing_in_yx = x_pile[!x_pile %in% yx_pile] # not exist in yx table
missing_in_x = yx_pile[!yx_pile %in% x_pile] # not exist in x table

check_Completed()

# check all statuses
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-02" & yx$Type==1)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP.x=="N-02" & yx$Type==1)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

# Rename column
delField = which(str_detect(colnames(yx),"Status1.y|Remarks|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")
yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


yx[is.na(yx$Status1),]

#t=yx$nPierNumber[which(yx$CP=="N-02" & yx$Type==1 & yx$Status1==4)]

# 
write.xlsx(yx, MLTable)

###################################################
# N-02: PILE CAP, PIER COLUN, and PIER HEAD:----
###################################################
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 6)
x = x[-c(1:3),c(2,8,9)]
x[[2]] = as.numeric(x[[2]])
##

## N-02 PILE CAP:-----
v = range_read(url, sheet = pileCap)
v = data.frame(v)

x=v[,c(2,29,ncol(v))]
x=x[6:nrow(x),]

colnames(x) = c("nPierNumber","end_date","Status1")

id=which(is.na(x$nPierNumber))
x=x[-id,]

##
x$Status1 = gsub("[[:space:]]","",x$Status1)

# keep only completed
completed_row = which(x$Status1 == 1)
x$Status1[completed_row] = 4

# remove na
id = which(is.na(x$Status1))
if(length(id)){
  x = x[-id,]
} else {
  print("")
}


x$Status1 = as.numeric(x$Status1)
x$CP = "N-02"

# date
for(i in seq(length(x$end_date))){
  if(is.null(x$end_date[[i]])){
    x$end_date[[i]]=NA
  }
}
x$end_date = unlist(x$end_date)

x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01",tZ="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# type
x$Type = 2

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))


# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
head(yx)
x_pile = x$nPierNumber[which(x$Status1==4)]
yx_pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==2 & yx$CP.x=="N-02")]

str(x_pile)
str(yx_pile)

missing_in_yx = x_pile[!x_pile %in% yx_pile] # not exist in yx table
missing_in_x = yx_pile[!yx_pile %in% x_pile] # not exist in x table

check_Completed()

# check all statuses
head(yx)
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-02" & yx$Type==2)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP.x=="N-02" & yx$Type==2)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

str(yx)
delField = which(str_detect(colnames(yx),"Status1.y|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


yx[is.na(yx$Status1),]

#t=yx$nPierNumber[which(yx$CP=="N-02" & yx$Type==2 & yx$Status1==4)]

# 
write.xlsx(yx, MLTable)


######################
# N-02: PIER COLUMN:----
######################
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 6)
x = x[-c(1:3),c(2,14,15)]
x[[2]] = as.numeric(x[[2]])
##

v = range_read(url, sheet = PierCol)
v = data.frame(v)

head(v)
x=v[,c(2,17,ncol(v))]
x=x[6:nrow(x),]

colnames(x) = c("nPierNumber","end_date","Status1")

id=which(is.na(x$nPierNumber))
x=x[-id,]

##
x$Status1 = gsub("[[:space:]]","",x$Status1)

# keep only completed
completed_row = which(x$Status1 == 1)
x$Status1[completed_row] = 4

# remove na
id = which(is.na(x$Status1))
if(length(id)){
  x = x[-id,]
} else {
  print("")
}

x$Status1 = as.numeric(x$Status1)
x$CP = "N-02"

# date
for(i in seq(length(x$end_date))){
  if(is.null(x$end_date[[i]])){
    x$end_date[[i]]=NA
  }
}
x$end_date = unlist(x$end_date)

x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01",tZ="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# type
x$Type = 3

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
x_pc = x$nPierNumber[which(x$Status1==4)]
yx_pc = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==3 & yx$CP.x=="N-02")]

missing_in_yx = x_pc[!x_pc %in% yx_pc] # not exist in yx table
missing_in_x = yx_pc[!yx_pc %in% x_pc] # not exist in x table

check_Completed()

# check all statuses
head(yx)
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-02" & yx$Type==3)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP.x=="N-02" & yx$Type==3)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

delField = which(str_detect(colnames(yx),"Status1.y|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


yx[is.na(yx$Status1),]

t=yx$nPierNumber[which(yx$CP=="N-02" & yx$Type==3 & yx$Status1==4)]

# 
write.xlsx(yx, MLTable)


######################
# N-02: PIER Head:----
######################
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 6)
x = x[-c(1:3),c(2,20,21)]
x[[2]] = as.numeric(x[[2]])
##

v = range_read(url, sheet = PierHead)
v = data.frame(v)

head(v)
x=v[,c(2,17,ncol(v))]
x=x[6:nrow(x),]

colnames(x) = c("nPierNumber","end_date","Status1")

id=which(is.na(x$nPierNumber))
x=x[-id,]

##
x$Status1 = gsub("[[:space:]]","",x$Status1)

# keep only completed
completed_row = which(x$Status1 == 1)
x$Status1[completed_row] = 4

# remove na
id = which(is.na(x$Status1))
if(length(id)){
  x = x[-id,]
} else {
  print("")
}

x$Status1 = as.numeric(x$Status1)
x$CP = "N-02"

# date
for(i in seq(length(x$end_date))){
  if(is.null(x$end_date[[i]])){
    x$end_date[[i]]=NA
  }
}
x$end_date = unlist(x$end_date)

x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01",tZ="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

#

# type
x$Type = 4

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
x_pc = x$nPierNumber[which(x$Status1==4)]
yx_pc = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==4 & yx$CP.x=="N-02")]

missing_in_yx = x_pc[!x_pc %in% yx_pc] # not exist in yx table
missing_in_x = yx_pc[!yx_pc %in% x_pc] # not exist in x table

check_Completed()

# check all statuses
head(yx)
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-02" & yx$Type==4)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP.x=="N-02" & yx$Type==4)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

delField = which(str_detect(colnames(yx),"Status1.y|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


yx[is.na(yx$Status1),]

# 
write.xlsx(yx, MLTable)



###############################################################
####################### N-03 #################################:----
##############################################################
# original
#url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit#gid=0"

url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit?usp=sharing"
n03_pile = 1
CP = "N-03"

############################################
###### N-03: Bored Piles #######:----
###########################################
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 1)
x = x[,c(2,15,24)]
id = which(x[[2]] == "Date")
x = x[-c(1:12),]
x[[2]] = as.numeric(x[[2]])
##

# read and write as CSV and xlsx
v = range_read(url, sheet = n03_pile)
v = data.frame(v)

# filter out
x = v[,c(2,8,14)]
colnames(x) = c("nPierNumber", "end_date","Status1")

# Convert to string
x$nPierNumber = as.character(x$nPierNumber)
x$Status1 = as.character(x$Status1)
x$CP = CP

# Delete empty cells
rem_id = which(is.na(x$nPierNumber))
if(length(rem_id)) {
  x = x[-rem_id,]
} else {
  print("No empty cells")
}


# Extract only piles
pile_id = which(str_detect(x$nPierNumber,"^P-"))
x = x[pile_id,]

x$nPierNumber = gsub("^P-","P",x$nPierNumber)

# Note if pier number has these notations, we need to fix this. "P976R-4" = "P976-R4"
id = which(str_detect(x$nPierNumber, ".*L-"))
x$nPierNumber[id] = gsub("L-", "-L",x$nPierNumber[id])

id = which(str_detect(x$nPierNumber, ".*R-"))
x$nPierNumber[id] = gsub("R-", "-R",x$nPierNumber[id])

# convert stats
x$Status1[str_detect(x$Status1,pattern="Completed|completed")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Status1,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Status1,pattern="Incomplete")] = 3 # Delayed

x$Status1 = as.numeric(x$Status1)

head(x)

## Convert date format
# Convert date format
for(i in seq(length(x$end_date))){
  if(is.null(x$end_date[[i]])){
    x$end_date[[i]]=NA
  }
}
x$end_date = unlist(x$end_date)

x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01",tZ="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# Remove duplicated observations if any
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))


# Read master list and join
y = read.xlsx(MLTable)

## Join 
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
x.pile = x$nPierNumber[x$Status1==4]
yx.pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==1 & yx$CP.x=="N-03")]

missing_in_yx = x.pile[!x.pile %in% yx.pile] # not exist in yx table
missing_in_x = yx.pile[!yx.pile %in% x.pile] # not exist in x table

check_Completed()


# check all statuses
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-03" & yx$Type==1)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
gg = which(yx$CP.x=="N-03" & yx$Type==1)

yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")


yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

delField = which(str_detect(colnames(yx), "Status1.y|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
head(yx)
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1


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
yx[is.na(yx$Status1),]

# 
write.xlsx(yx, MLTable)



###################################################
# N-03: PILE CAP, PIER COLUN, and PIER HEAD:----
###################################################




###############################################################
####################### N-04 #################################:----
##############################################################

#url = "https://docs.google.com/spreadsheets/d/1OWdmM36PWL5MgH0lK9HpigaoVq4L7Q6hm7DSN2FxiAA/edit#gid=0"
url = "https://docs.google.com/spreadsheets/d/1YEm8iXc8D9Rn3Gdma-PcXyFW_rk6f5clC7hhnsb2biE/edit?usp=sharing"

### N-04: BORED PILES #:----
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 2)
head(x,20)
x = x[,c(6,19,30)]

id = which(x[[3]] == "Status")
x = x[-c(1:id),]
x[[2]] = as.numeric(x[[2]])

##

# Read and write as CSV and xlsx
v = range_read(url, sheet = 3)
v = data.frame(v)

# Restruecture table
## I temporarliy used dummy field names to be discarded so need to remove it
x = v[,c(6,19,30)]
colnames(x) = c("nPierNumber","end_date","Status1")

## Remove empty rows
rid = which(is.na(x$nPierNumber))

if(length(rid)==0){
  print("no nrows being removed")
} else {
  x = x[-rid,]
}

x$nPierNumber = as.character(x$nPierNumber)

# Remove hyphen from pierNumber
## correct with "P-"
x$nPierNumber = gsub("[[:space:]]","",x$nPierNumber)
#x$nPierNumber = gsub("^[P]","P-",x$nPierNumber)
#x$nPierNumber = gsub("^PLK ","PLK-",x$nPierNumber)
x$nPierNumber = gsub("DEPO","DEP0",x$nPierNumber)

# Remove rows that do not contain the following texts "P", "PLK", "DEP0"
x = x[str_detect(x$nPierNumber,"^P|^PLK|^DEP0"),]

# Unlist Status1
id = which(x$Status1=="NULL")
x$Status1[id] = NA

Status1_ = unlist(x$Status1, use.names = FALSE)
x$Status1 = Status1_

x$Status1[str_detect(x$Status1,pattern="Casted|casted")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Status1,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Status1,pattern="Incomplete")] = 3 # Delayed

# Unlist end_date
id = which(x$end_date == "NULL")
x$end_date[id] = NA

end_date_ = unlist(x$end_date, use.names = FALSE)
x$end_date = end_date_

# Delete na status
del_id = which(is.na(x$Status1))
if(length(del_id)){
  x = x[-del_id,]
} else {
  print("")
}


x$Status1 = as.numeric(x$Status1)

## Fix some wrong notation of nPierNumber
id_LS = which(str_detect(x$nPierNumber,'LS$'))
id_RS = which(str_detect(x$nPierNumber,'RS$'))

x$nPierNumber[id_LS] = gsub("01LS","1LS",x$nPierNumber[id_LS])
x$nPierNumber[id_LS] = gsub("02LS","2LS",x$nPierNumber[id_LS])
x$nPierNumber[id_RS] = gsub("01RS","1RS",x$nPierNumber[id_RS])
x$nPierNumber[id_RS] = gsub("02RS","2RS",x$nPierNumber[id_RS])

# Convert date format
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01",tZ="UTC")
x$end_date = as.Date(x$end_date, origin="1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# Remove duplicated observations if any
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

#id = which(str_detect(x$nPierNumber,'^DEP'))
# Join new status to Viaduct masterlist

y = read.xlsx(MLTable)
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
x.pile = x$nPierNumber[x$Status1==4]
yx.pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==1 & yx$CP=="N-04")]

missing_in_yx = x.pile[!x.pile %in% yx.pile] # not exist in yx table
missing_in_x = yx.pile[!yx.pile %in% x.pile] # not exist in x table

check_Completed()

# check all statuses
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP=="N-04" & yx$Type==1)])

check = x_t %in% yx_t
check_function() 
# if the number discrepancey originates from P1159 and P1160, you can skip. Civil Team's
# master list duplicates these observations.

# NA for status = 1 (To be Constructed)
gg = which(yx$CP.x=="N-04" & yx$Type==1)

yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

delField = which(str_detect(colnames(yx), "Status1.y|Remarks|CP.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"


# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

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

yx[is.na(yx$Status1),]

# 
write.xlsx(yx, MLTable)

###################################################
### N-04: Pilec Caps, Pier, and Pier Head #;----
###################################################
url = "https://docs.google.com/spreadsheets/d/1Cl_tn3dTPdt8hrqzZtl_WjCxy9L-ltn7GrOmQpHdBw4/edit?usp=sharing"

## N-04 Pile Cap:-----------
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 1)
head(x,30)
x = x[,c(2,15)]

id = which(x[[2]] == "Date Completed")
x = x[-c(1:id),]
x[[2]] = as.numeric(x[[2]])
colnames(x) = c("nPierNumber", "end_date")
##


v = range_read(url, sheet = 3)
v = data.frame(v)

id = which(str_detect(colnames(v),"nPierNumber|end_date"))
x = v[,id]

# Add Type
x$Type = 2

# Keep only finished
id = which(!is.na(x$end_date))
x = x[id,]

# Add Status1
x$Status1 = 4

# Extract only piles
pile_id = which(str_detect(x$nPierNumber,"^P-"))
x = x[pile_id,]

x$nPierNumber = gsub("^P-","P",x$nPierNumber)

## Fix some wrong notation of nPierNumber
id_LS = which(str_detect(x$nPierNumber,'LS$'))
id_RS = which(str_detect(x$nPierNumber,'RS$'))

x$nPierNumber[id_LS] = gsub("[[:space:]]","",x$nPierNumber[id_LS])
x$nPierNumber[id_RS] = gsub("[[:space:]]","",x$nPierNumber[id_RS])

x$nPierNumber[id_LS] = gsub("LS","-LS",x$nPierNumber[id_LS])
x$nPierNumber[id_RS] = gsub("RS","-RS",x$nPierNumber[id_RS])

## find duplicated if any
# Detect duplicated nPierNumbers and if present delete
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

## reformat date
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))


# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
head(yx)
x_pile = x$nPierNumber[which(x$Status1==4)]
yx_pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==2 & yx$CP=="N-04")]

missing_in_yx = x_pile[!x_pile %in% yx_pile] # not exist in yx table
missing_in_x = yx_pile[!yx_pile %in% x_pile] # not exist in x table

check_Completed()

# check all statuses
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP=="N-04" & yx$Type==2)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP=="N-04" & yx$Type==2)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

str(yx)
delField = which(str_detect(colnames(yx),"Status1.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


yx[is.na(yx$Status1),]

#t=yx$nPierNumber[which(yx$CP=="N-02" & yx$Type==2 & yx$Status1==4)]

# 
write.xlsx(yx, MLTable)

#-------------------------------------------------------#
## Pier:----
## Currently No Pier
## TEMP run
### When google sheet is not available but excel version is availablef from N2 civil
a = file.choose()
x = read.xlsx(a, sheet = 1)
x = x[,c(2,26,29)]
head(x,50)
id = which(x[[2]] == "Date Completed")
x = x[-c(1:id),]
x[[2]] = as.numeric(x[[2]])
colnames(x) = c("nPierNumber", "end_date", "Status1")
##


v = range_read(url, sheet = 3)
v = data.frame(v)

id = which(str_detect(colnames(v),"nPierNumber|end_date"))
x = v[,id]

# Add Type
x$Type = 3

# Keep only finished
id = which(!is.na(x$end_date))
x = x[id,]

# Add Status1
x$Status1 = 4

# Extract only piles
pile_id = which(str_detect(x$nPierNumber,"^P-"))
x = x[pile_id,]

x$nPierNumber = gsub("^P-","P",x$nPierNumber)

## Fix some wrong notation of nPierNumber
id_LS = which(str_detect(x$nPierNumber,'LS$'))
id_RS = which(str_detect(x$nPierNumber,'RS$'))

x$nPierNumber[id_LS] = gsub("[[:space:]]","",x$nPierNumber[id_LS])
x$nPierNumber[id_RS] = gsub("[[:space:]]","",x$nPierNumber[id_RS])

x$nPierNumber[id_LS] = gsub("LS","-LS",x$nPierNumber[id_LS])
x$nPierNumber[id_RS] = gsub("RS","-RS",x$nPierNumber[id_RS])

## find duplicated if any
# Detect duplicated nPierNumbers and if present delete
id = which(duplicated(x$nPierNumber))

if(length(id)>0){
  x = x[-id,]
} else {
  print("no duplicated observations")
}

## reformat date
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))


# Join 
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
## Check for piles with completed status
head(yx)
x_pile = x$nPierNumber[which(x$Status1==4)]
yx_pile = yx$nPierNumber[which(yx$Status1.y==4 & yx$Type==3 & yx$CP=="N-04")]

missing_in_yx = x_pile[!x_pile %in% yx_pile] # not exist in yx table
missing_in_x = yx_pile[!yx_pile %in% x_pile] # not exist in x table

check_Completed()

# check all statuses
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP=="N-04" & yx$Type==3)])

check = x_t %in% yx_t
check_function()

# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP=="N-04" & yx$Type==3)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

str(yx)
delField = which(str_detect(colnames(yx),"Status1.y|end_date.y|Year.y|Month.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"
colnames(yx)[str_detect(colnames(yx),pattern="Year")] = "Year"
colnames(yx)[str_detect(colnames(yx),pattern="Month")] = "Month"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yx$Status1))
yx$Status1[id] = 1

# Add date of updating table
## Delete old ones
iid = which(colnames(yx) %in% colnames(yx)[str_detect(colnames(yx),"updated|Updated|UPDATED")])
yx = yx[,-iid]

## Add new dates
yx$updated = ymd(date_update)

yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")


yx[is.na(yx$Status1),]

#t=yx$nPierNumber[which(yx$CP=="N-02" & yx$Type==2 & yx$Status1==4)]

# 
write.xlsx(yx, MLTable)

## Pier head:----
## Currently No Pier


## Precast:----
## Currently no Precast


## Compile all the master list into a single data frame




# Re-format nPierNumber
unique(x$nPierNumber)
x$nPierNumber = gsub("[[:space:]]","",x$nPierNumber)

x$nPierNumber[] = gsub("^P ","P",x$nPierNumber)
x$nPierNumber[] = gsub("P-","P",x$nPierNumber)

x$nPierNumber = gsub("LS","-LS",x$nPierNumber)
x$nPierNumber = gsub("RS","-RS",x$nPierNumber)

# Delete empty observations
unique(x$nPierNumber)


## Re-format end_date
str(x)
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01", tz="UTC")
x$end_date = as.Date(x$end_date,origin = "1899-12-30")
x$end_date = as.Date(x$end_date,format="%m/%d/%y %H:%M:%S")

# Add Year and Month to generate stacked bar chart for monitoring monthly progress
x$Year = as.numeric(format(x$end_date, format="%Y"))
x$Month = as.numeric(format(x$end_date,format="%m"))

# join this table to original master list
y = read.xlsx(MLTable)
yx = left_join(y,x,by=c("Type","nPierNumber"))

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Type,x$Status1)
id=which(yx$CP=="N-04" & (yx$Type==2 & yx$Type<5)) # pile cap, pier, pier head

yx_t = table(yx$Type[id],yx$Status1.y[id])

x_pileC = x$nPierNumber[x$Type == 2 & x$Status1 == 4]
yx_pileC = yx$nPierNumber[yx$Type == 2 & yx$Status1.y == 4]

x_pileC[!x_pileC %in% yx_pileC]


check = x_t %in% yx_t
check_function()

# Delete andRe-name variables again
## Extract row numbers to be replaced with new status
# Because we only want to update status with pier numbers that need to be updated in xx,
# we replace Status1.x with only these pier numbers.
gg = which(yx$CP=="N-04" & yx$Type>1 & yx$Type<5)

yx$end_date.x = as.Date(yx$end_date.x,origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x,format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg]=yx$Status1.y[gg]
yx$end_date.x[gg]=yx$end_date.y[gg]
## Year and Date
gg2 = which(yx$Year.y>0)
yx$Year.x[gg2] = yx$Year.y[gg2]
yx$Month.x[gg2] = yx$Month.y[gg2]

## Rename and delete Status1.y
id = which(str_detect(colnames(yx),"Status1.y|end_date.y|Year.y|Month.y"))
yx = yx[,-id]

colnames(yx)[which(str_detect(colnames(yx),"Status1"))] = "Status1"
colnames(yx)[which(str_detect(colnames(yx),"end_date"))] = "end_date"
colnames(yx)[which(str_detect(colnames(yx),"Year"))] = "Year"
colnames(yx)[which(str_detect(colnames(yx),"Month"))] = "Month"

# Convert nA to 1 (to be Constructed)

id = which(is.na(yx$Status1))
yx$Status1[id] = 1

## Re-format Date for excel
str(yx)
yx$updated = as.Date(yx$updated, origin = "1899-12-30")
yx$updated = as.Date(yx$updated, format="%m/%d/%y %H:%M:%S")

yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

# Check if Status1 has any empty observations. iF present, something is wrong with the code above

yx[is.na(yx$Status1),]

## Convert status to numeric format
yx$Status1 = as.numeric(yx$Status1)

# overwrite masterlist
write.xlsx(yx, MLTable)


###
# summary table to check
y = read.xlsx(MLTable)
y1 = y[which(y$Status1 == 4),]
agg_df <- aggregate(y1$Status1, by=list(y1$CP, y1$Type, y1$Status1), FUN=length)
