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
date_update = "2022-04-08"

#******************************************************************#


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

wd = file.path(path, "Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled")

#a=choose.dir()
setwd(wd)

# Read our master list table
# C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\02-Civil\03-Viaduct\01-Masterlist\02-Compiled\N2_Viaduct_MasterList.xlsx"
MLTable = file.choose()
# Read the masterlist:----
y = read.xlsx(MLTable)

## Use the following code for concatenating pierNumber and pile numbers for site planner's format

##########************************************########
## The code below checks duplicated observations
## Run as necessary

uType = unique(y$Type)
uCP = unique(y$CP)

temp = data.frame()
for(i in uCP){
  i="N-01"
  for(j in uType){
    j=2
    yx = y[which(y$CP==i & y$Type==j),]
    pierN = yx$nPierNumber
    
    dupPierN = pierN[duplicated(pierN)]

    nrep = length(dupPierN)
    t = data.frame(CP=rep(i,nrep),Type=rep(j,nrep),DupPierN=dupPierN)
    temp = rbind(temp,t)
    
    
  }
}
temp
write.xlsx(temp,"N2_Duplicated_observations.xlsx")
##########************************************########
##########*
# Check duplicated observations if any
# Do NOT just Delete these observation. Multipatch layers may be duplicated in labels for two different piers



###############################################################
####################### N-01 #################################:----
##############################################################

## Define URL where data is stored and updated
## I used "IMPORTRANGE" to copy information from the source URL to suit our needs.
url = "https://docs.google.com/spreadsheets/d/11YqYaenIB0l3Bpiv398-0QO3mEIR_BjvnMIsIOF3ILI/edit#gid=0"

#################################
### N01: BORED PILES #############----
#################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

# Restruecture table
## I temporarliy used dummy field names to be discarded so need to remove it
#nChar = sapply(1:ncol(v), function(k) nchar(colnames(v)[k]))

# Extract only target field names
## CP, nPierNumber, end_date (K column), Remarks
id = which(str_detect(colnames(v),"CP|nPierNumber|K|Remarks"))
x = v[,id]

id = which(str_detect(colnames(x),"K"))
colnames(x)[3] = "end_date"

## Remove empty rows
rid = which(is.na(x$nPierNumber))
x = x[-rid,]

head(x)

# Remove bored piles for station structure
pile_id = which(str_detect(x$nPierNumber,"^P-|^P.*"))
x = x[pile_id,]

# some nPierNumber is not consistently labelled
## Correct notation is "P-61G", so correct piers with "P60"
##id = which(str_detect(x$nPierNumber,"^P\\d"))
##head(x)

## Add default status
x$Status1 = 0


# Remove hyphen from pierNumbe
x$nPierNumber = gsub("-","",x$nPierNumber)

uniqueRem = unique(x$Remarks)


x$Status1[str_detect(x$Remarks,pattern="Casted")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Remarks,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Remarks,pattern="Incomplete")] = 3 # Delayed

unique(x$Status1)

# Join new status to Viaduct masterlist
y = read.xlsx(MLTable)
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-01" & yx$Type==1)])

check = x_t %in% yx_t
if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)

# NA for status = 1 (To be Constructed)
gg = which(yx$CP.x=="N-01" & yx$Type==1)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")


yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]

#yx$Status1.y[is.na(yx$Status1.y)] = yx$Status1.x

delField = which(str_detect(colnames(yx),"Status1.y|Remarks|CP.y|end_date.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"

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

#yx$Updated = as.Date(yx$Updated, origin = "1899-12-30")
#yx$Updated = as.Date(yx$Updated, format="%m/%d/%y %H:%M:%S")

## Backup old ones in case

y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")
oldDate = gsub("-","",unique(y$updated))

fileName = paste(oldDate,"_",basename(MLTable),sep="")
direct = file.path(wd,"old")

write.xlsx(y,file.path(direct,fileName))


# Recover data in excel format
#yx$end_date = as.Date(yx$end_date, origin ="1899-12-30")

yx$start_date = as.Date(yx$start_date, origin = "1899-12-30")
yx$start_date = as.Date(yx$start_date, format="%m/%d/%y %H:%M:%S")

yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

yx[is.na(yx$Status1),]

str(yx)

# 
write.xlsx(yx, MLTable)

###################################################
# N-01: PILE CAP, PIER COLUN, and PIER HEAD:----
###################################################

v = range_read(url, sheet = 2)
v = data.frame(v)

# Remove redundant columns and observations
colnames(v)
col = colnames(v)[str_detect(colnames(v),"CP|PILE|PIER|Pier|Pile|end_date")]
id = which(colnames(v) %in% col)

v2 = v[-c(1:5),id]

id = which(str_detect(colnames(v2),"PIER.COLUMN.end_date2"))
v2 = v2[,-id]

# for now delete PIER.COLUMN.end_date2 (2nd lift). I cannot convert this to date format because of "n/a" character

# Delete observations with PierNo is null
id = which(is.na(v2$PierNo))
v2=v2[-id,]

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

id = which(str_detect(colnames(v2),"end_date|CP|PierNo"))
v3 = v2[,id]
xx1 = melt(v3,id=c("CP","PierNo"))
xx1$variable = as.character(xx1$variable)

### Need to add Type to each row
head(xx1)
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

### Re-format nPierNumber

id = which(str_detect(xx1$nPierNumber,"Center$|center$|Right$|right$|Left$|left$"))
id_extract = str_extract(xx1[id,"nPierNumber"],"Center$|center$|Right$|right$|Left$|left$")
del_w = unique(id_extract)
del_w = paste(del_w,collapse="|",sep="")

## Delete these words from nPierNumber
xx1$nPierNumber[id] = gsub(del_w,"",xx1$nPierNumber[id])

## Check pier Number
unique(xx1$nPierNumber)
### make sure that nPierNumber is all uppercase letter
xx1$nPierNumber = toupper(xx1$nPierNumber)

### Remove all spaces
xx1$nPierNumber = gsub("[[:space:]]","",xx1$nPierNumber)

### Remove bracket if present
xx1$nPierNumber = gsub("[()]","",xx1$nPierNumber)

## Delete empty observation of end_date
id = which(is.na(xx1$end_date))

xx1 = xx1[-id,]

####################################
## 1.2. Only fields with numbers*----
id = which(str_detect(colnames(v2),"end_date"))
v4 = v2[,-id]
xx = melt(v4, id=c("CP","PierNo"))

# Delete empty observations
iddd = which(xx$value==0 | is.na(xx$value))
xx = xx[-iddd,]
xx[xx$PierNo==""]

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
xx$Status1[which(xx$Type=="PILE.CAP.done" & xx$Status1==1)]=4
xx$Status1[which(xx$Type=="PIER.COLUMN.done" & xx$Status1==1)]=4
xx$Status1[which(xx$Type=="PIER.HEAD.done" & xx$Status1==1)]=4

## Ongoing
xx$Status1[which(xx$Type=="PILE.CAP.done" & xx$Status1 < 1)]=2 # if less than 1, ongoing
xx$Status1[which(xx$Type=="PILE.CAP.ongoing" & xx$Status1==1)]=2

xx$Status1[which(xx$Type=="PIER.COLUMN.ongoing" & xx$Status1==1)]=2
xx$Status1[which(xx$Type=="PIER.COLUMN.done" & xx$Status1 < 1)]=2

xx$Status1[which(xx$Type=="PIER.HEAD.ongoing" & xx$Status1==1)]=2
xx$Status1[which(xx$Type=="PIER.HEAD.done" & xx$Status1 < 1)]=2

unique(xx$Status1)

# Re-code Type

xx$Type[xx$Type=="PILE.CAP.done" | xx$Type=="PILE.CAP.ongoing"]=2
xx$Type[xx$Type=="PIER.COLUMN.done" | xx$Type=="PIER.COLUMN.ongoing"]=3
xx$Type[xx$Type=="PIER.HEAD.done" | xx$Type=="PIER.HEAD.ongoing"]=4
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


## 1.3. Finaly, join with end_date:---- 
xx1$end_date = as.Date(xx1$end_date, origin = "1899-12-30")
xx1$end_date = as.Date(xx1$end_date, format="%m/%d/%y %H:%M:%S")

xxx = left_join(xx,xx1,by=c("nPierNumber","Type"))


# Unlike bored piles, we need to use nPierNumber AND Type to join Status1 to our master list
# This is because bored piles have unique nPierNumber, while other components do not.
# This means that we cannot bind tables generated here between bored piles and others.
# As such, we will join this updated table of other components to our original master list directly.

# remove CP for join

#
y = read.xlsx(MLTable)

yxx = left_join(y,xxx,by=c("Type","nPierNumber"))

# Delete andRe-name variables again
## Extract row numbers to be replaced with new status
# Because we only want to update status with pier numbers that need to be updated in xx,
# we replace Status1.x with only these pier numbers.

## Check if the number of Status1 for each Type is same between x and yx.

xx_t = table(xx$Type,xx$Status1)
id=which(yxx$CP=="N-01" & (yxx$Type>=2 & yxx$Type<5)) # pile cap, pier, pier head

yxx_t = table(yxx$Type[id],yxx$Status1.y[id])

check = xx_t %in% yxx_t

if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)

### use the following when you need to check
xx_pier = xx$nPierNumber[which(xx$Type>=2 & xx$Status1<5)]
yxx_pier = yxx$nPierNumber[which(yxx$Type>=2 & yxx$Status1.y<5 & yxx$CP=="N-01")]

xx_pier[!xx_pier %in% yxx_pier]
yxx_pier[!yxx_pier %in% xx_pier]

# Be careful, we need to replace all observations with new ones, not just updated ones
gg = which(yxx$CP=="N-01" & yxx$Type>1 & yxx$Type<5)

library(lubridate)
yxx$end_date.x = as.Date(yxx$end_date.x, origin = "1899-12-30")
yxx$end_date.x = as.Date(yxx$end_date.x, format="%m/%d/%y %H:%M:%S")

#gg = which(yxx$Status1.y>0)
yxx$Status1.x[gg] = yxx$Status1.y[gg]
yxx$end_date.x[gg] = yxx$end_date.y[gg]

## Rename and delete Status1.y
delField = which(str_detect(colnames(yxx),"Status1.y|end_date.y"))
yxx = yxx[,-delField]

# Change Status name
colnames(yxx)[str_detect(colnames(yxx),pattern="Status1")] = "Status1"
colnames(yxx)[str_detect(colnames(yxx),pattern="end_date")] = "end_date"

# Convert nA to 1 (to be Constructed)
id = which(is.na(yxx$Status1))
yxx$Status1[id] = 1


## Re-format Date for excel
yxx$updated = as.Date(yxx$updated, origin = "1899-12-30")
yxx$updated = as.Date(yxx$updated, format="%m/%d/%y %H:%M:%S")

yxx$start_date = as.Date(yxx$start_date, origin = "1899-12-30")
yxx$start_date = as.Date(yxx$start_date, format="%m/%d/%y %H:%M:%S")

yxx$end_date = as.Date(yxx$end_date, origin = "1899-12-30")
yxx$end_date = as.Date(yxx$end_date, format="%m/%d/%y %H:%M:%S")

unique(yxx$end_date)

# Check if Status1 has any empty observations. iF present, something is wrong with the code above

yxx[is.na(yxx$Status1),]

# overwrite masterlist
write.xlsx(yxx, MLTable)


###################################################
# N-01: Pre-CAST                        :----
###################################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 3)
v = data.frame(v)


# Re structure
x = v[,c(1,18,ncol(v)-1,ncol(v))]

# 
id = which(str_detect(x$nPierNumber,"^P\\d+|^Concrete|^concrete"))
id1 = which(!is.na(x$TotalQ))
idd = sort(c(id,id1))
x = x[idd,]

colnames(x)[2] = "end_date"

# remove unnecessary rows from each field
pier = x$nPierNumber[which(str_detect(x$nPierNumber,"^P\\d+"))]
total = x$TotalQ[!is.na(x$TotalQ)]
cast = x$Casted[!is.na(x$Casted)]

x$end_date[which(x$end_date=="NULL")]=NA
endDate = unlist(x$end_date[x$nPierNumber=="Concrete Casting"])
endDate=endDate[-1] # first one is not needed

endDate = as.POSIXlt(endDate, origin="1970-01-01", tz="UTC")
endDate = as.Date(endDate, origin = "1899-12-30")


xx = data.frame(nPierNumber=pier,TotalQ=total,Casted=cast,end_date=endDate)

# Delete all the spaces
xx$nPierNumber = gsub("[[:space:]]","",xx$nPierNumber)

## Add field
xx$Status1 = 1
xx$temp = xx$Casted/xx$TotalQ

# fill in status
xx$Status1[which(xx$temp==1)] = 4
xx$Status1[which(xx$temp<1)] = 2

xx$Type = 5

## extract only first pier numbers to join with GIS ML
xx$temp1 = str_extract(xx$nPierNumber,"^P\\d+|^DEP\\d+-ABUT")
xx$nPierNumber = xx$temp1

head(xx)
id=which(str_detect(colnames(xx),"nPierNumber|Status|Type|end_date"))
xx = xx[,id]

# Join new status to Viaduct masterlist
y = read.xlsx(MLTable)

yx = left_join(y,xx,by=c("nPierNumber","Type"))

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(xx$Status)
yx_t = table(yx$Status1.y[which(yx$CP=="N-01" & yx$Type==5)])

check = x_t %in% yx_t
if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)

# NA for status = 1 (To be Constructed)
gg = which(yx$CP=="N-01" & yx$Type==5)

# end_date
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

#gg = which(yx$Status1.y>1)
yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]

#yx$Status1.y[is.na(yx$Status1.y)] = yx$Status1.x
head(yx)
delField = which(str_detect(colnames(yx),"Status1.y|end_date.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"

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

# 
write.xlsx(yx, MLTable)


## note that GIS pre-cast is numbered using only one pier No. where the beginning pier no is used
## in the direction of chainage
## This means that we can only extract the first pier No. from the google sheet to align the GIS monitoring sheet


###############################################################
####################### N-02 #################################:----
##############################################################

#url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?userstoinvite=junsanjose@gmail.com&actionButton=1#gid=0"
url = "https://docs.google.com/spreadsheets/d/1du9qnThdve1yXBv-W_lLzSa3RMd6wX6_NlNCz8PqFdg/edit?usp=sharing"

###########################
### N-02: BORED PILES #:----
################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

id = which(str_detect(v[[2]], "^P-"))
x = v[id,]


# Restruecture table
## Remove empty rows and unneeded rows
x = x[,c(2,9,ncol(x))]
colnames(x) = c("nPierNumber", "end_date","Status1")
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


id = which(x$end_date=="NULL")
x$end_date[id] = NA

da=unlist(x$end_date, use.names = FALSE)

x$end_date = da
x$end_date = as.POSIXlt(x$end_date, origin="1970-01-01", tz="UTC")
x$end_date = as.Date(x$end_date, origin = "1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

unique(x$end_date)


# Join 
y = read.xlsx(MLTable)

yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-02" & yx$Type==1)])

check = x_t %in% yx_t
if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)


# NA for status = 1 (To be Constructed)
#gg = which(yx$Status1.y>0)

gg = which(yx$CP.x=="N-02" & yx$Type==1)

library(lubridate)
yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]

delField = which(str_detect(colnames(yx),"Status1.y|Remarks|CP.y|end_date.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"

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


# 
write.xlsx(yx, MLTable)

###################################################
# N-02: PILE CAP, PIER COLUN, and PIER HEAD:----
###################################################




###############################################################
####################### N-03 #################################:----
##############################################################
url = "https://docs.google.com/spreadsheets/d/19TBfdEpRuW7edwhiP7YdVSJQgrkot9wN7tDwzSTF76E/edit#gid=0"

n03_pile = 1
CP = "N-03"

############################################
###### N-03: Bored Piles #######:----
###########################################

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

head(x)

## Convert date format
# Convert date format
x$end_date[which(is.null(x$end_date))] = NA
endDate = unlist(x$end_date)

endDate = as.POSIXlt(endDate, origin="1970-01-01", tz="UTC")
endDate = as.Date(endDate, origin = "1899-12-30")
endDate= as.Date(endDate, format="%m/%d/%y %H:%M:%S")

x$end_date = endDate

# Read master list and join
y = read.xlsx(MLTable)

## Join 
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-03" & yx$Type==1)])

check = x_t %in% yx_t
if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)


# NA for status = 1 (To be Constructed)
gg = which(yx$CP.x=="N-03" & yx$Type==1)

yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")


yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]

delField = which(str_detect(colnames(yx), "Status1.y|CP.y|end_date.y"))
yx = yx[,-delField]

# Change Status name
head(yx)
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"

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
url = "https://docs.google.com/spreadsheets/d/1OWdmM36PWL5MgH0lK9HpigaoVq4L7Q6hm7DSN2FxiAA/edit#gid=0"

### N-04: BORED PILES #:----


# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

# Restruecture table
## I temporarliy used dummy field names to be discarded so need to remove it
head(v)

id =which(str_detect(colnames(v),"Status1|CP|nPierNumber|end_date"))
x = v[,id]

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

uniqueRem = unique(x$Remarks)
head(x)
unique(x$Status1)

x$Status1[str_detect(x$Status1,pattern="Casted|casted")] = 4 # Bored Pile completed
x$Status1[str_detect(x$Status1,pattern="Inprogress")] = 2 # Under Construction
x$Status1[str_detect(x$Status1,pattern="Incomplete")] = 3 # Delayed

# Delete na status
del_id = which(is.na(x$Status1))
x = x[-del_id,]

x$Status1 = as.numeric(x$Status1)

## Fix some wrong notation of nPierNumber
id_LS = which(str_detect(x$nPierNumber,'LS$'))
id_RS = which(str_detect(x$nPierNumber,'RS$'))

x$nPierNumber[id_LS] = gsub("01LS","1LS",x$nPierNumber[id_LS])
x$nPierNumber[id_LS] = gsub("02LS","2LS",x$nPierNumber[id_LS])
x$nPierNumber[id_RS] = gsub("01RS","1RS",x$nPierNumber[id_RS])
x$nPierNumber[id_RS] = gsub("02RS","2RS",x$nPierNumber[id_RS])

# Convert date format
x$end_date = as.Date(x$end_date, origin="1899-12-30")
x$end_date = as.Date(x$end_date, format="%m/%d/%y %H:%M:%S")

#id = which(str_detect(x$nPierNumber,'^DEP'))
# Join new status to Viaduct masterlist

y = read.xlsx(MLTable)
yx = left_join(y,x,by="nPierNumber")

## Check if the number of Status1 for each Type is same between x and yx.
x_t = table(x$Status1)
yx_t = table(yx$Status1.y[which(yx$CP.x=="N-04" & yx$Type==1)])

check = x_t %in% yx_t
if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)

# NA for status = 1 (To be Constructed)
gg = which(yx$CP.x=="N-04" & yx$Type==1)

yx$end_date.x = as.Date(yx$end_date.x, origin = "1899-12-30")
yx$end_date.x = as.Date(yx$end_date.x, format="%m/%d/%y %H:%M:%S")

yx$Status1.x[gg] = yx$Status1.y[gg]
yx$end_date.x[gg] = yx$end_date.y[gg]

delField = which(str_detect(colnames(yx), "Status1.y|Remarks|CP.y|end_date.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status1")] = "Status1"
colnames(yx)[str_detect(colnames(yx),pattern="CP")] = "CP"
colnames(yx)[str_detect(colnames(yx),pattern="end_date")] = "end_date"

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

yx$StartDate = as.Date(yx$StartDate, origin = "1899-12-30")
yx$StartDate = as.Date(yx$StartDate, format="%m/%d/%y %H:%M:%S")

yx$TargetDate = as.Date(yx$TargetDate, origin = "1899-12-30")
yx$TargetDate = as.Date(yx$TargetDate, format="%m/%d/%y %H:%M:%S")

yx[is.na(yx$Status1),]

# 
write.xlsx(yx, MLTable)

###################################################
### N-04: Pilec Caps, Pier, and Pier Head #;----
###################################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 2)
v = data.frame(v)

head(v)
# Remove redundant columns and observations
# Column 'M' for pile caps
colnames(v)
id = which(str_detect(colnames(v),"CP|nPierNumber|PILE|PIER"))

v2 = v[,id]

#
unique(v2$nPierNumber)
v2$nPierNumber = gsub("[[:space:]]","",v2$nPierNumber)

v2$nPierNumber[] = gsub("^P ","P",v2$nPierNumber)
v2$nPierNumber[] = gsub("P-","P",v2$nPierNumber)

v2$nPierNumber = gsub("LS","-LS",v2$nPierNumber)
v2$nPierNumber = gsub("RS","-RS",v2$nPierNumber)

# Delete empty observations
unique(v2$nPierNumber)


#######################
xx = v2
# For Status1 = 4 (completed)
## Note that for N-04, we do not have information to know the status "Under Construction"
## As such, we will just collect "Completed" status.
## Pile Cap
xx.pc = xx[,c("nPierNumber","PILE.CAP.end_date")]
xx.pc$Type = 2
id=which(str_detect(colnames(xx.pc),"PILE.CAP"))
colnames(xx.pc)[id] = "end_date"

id=which(is.na(xx.pc$end_date))
xx.pc = xx.pc[-id,]

## Pier
head(xx)
id = which(str_detect(colnames(xx),"nPierNumber|PIER.done|PIER.end_date"))
xx.pi = xx[,id]

id.done3 = which(!is.na(xx.pi$PIER.done3))
id.done2 = which(!is.na(xx.pi$PIER.done2))
id.done1 = which(!is.na(xx.pi$PIER.done1))

#ids = c(id.done3,id.done2,id.done1)

#id.none = xx.pi$nPierNumber[-ids]

# collect pier numbers and end date for each lift
pn3="0"
pn2="0"
pn1="0"

eDate1="0"
eDate2="0"
eDate3="0"

# Collect pier number and end_date by screening from 3rd lift, 2nd lift, and 1st lift.
if(length(id.done3)>0){
  pn3 = xx.pi$nPierNumber[id.done3]
  eDate3 = xx.pi$PIER.end_date3[id.done3]
} else if(length(id.done2)>0){
  pn2 = xx.pi$nPierNumber[id.done2]
  eDate2 = xx.pi$PIER.end_date2[id.done2] 
} else if(length(id.done1)>0){
  pn1 = xx.pi$nPierNumber[id.done1]
  eDate1 = xx.pi$PIER.end_date1[id.done1] 
}

pns = c(pn3,pn2,pn1)
eDates = c(eDate3,eDate2,eDate1)
#######################################
## For now use only 3rd lift concrete as completed or not

xx.pier = data.frame(nPierNumber=pn3,end_date=eDate3)
id = which(xx.pier$nPierNumber==0)
xx.pier = xx.pier[-id,]

if(nrow(xx.pier)==0){
  print("Proceed without PIER")
} else {
  xx.pier$Type = 3
  xx.pier$end_date = as.numeric(xx.pier$end_date)
  xx.pier$end_date = as.POSIXlt(xx.pier$end_date, origin="1970-01-01", tz="UTC")
}


### Pier Head
head(xx)
xx.ph = xx[,c("nPierNumber","PIERHEAD.end_date")]
xx.ph$Type = 4

id=which(str_detect(colnames(xx.ph),"PIERHEAD"))
colnames(xx.ph)[id] = "end_date"

xx.ph$end_date = as.numeric(xx.ph$end_date)
xx.ph$end_date = as.POSIXlt(xx.ph$end_date, origin="1970-01-01", tz="UTC")

id = which(is.na(xx.ph$end_date))
xx.ph = xx.ph[-id,]

## Compile
xx1 = rbind(xx.pc,xx.pier,xx.ph)

xx1$end_date = as.Date(xx1$end_date,origin = "1899-12-30")
xx1$end_date = as.Date(xx1$end_date,format="%m/%d/%y %H:%M:%S")

#####################
# Update column names
# Bored Pile = 1
# Pile Cap = 2
# Pier Column = 3
# Pier Head = 4
# Precast = 5

xx1$Status1 = 4

# Unlike bored piles, we need to use nPierNumber AND Type to join Status1 to our master list
# This is because bored piles have unique nPierNumber, while other components do not.
# This means that we cannot bind tables generated here between bored piles and others.
# As such, we will join this updated table of other components to our original master list directly.

str(xx1)

#
y = read.xlsx(MLTable)

yxx = left_join(y,xx1,by=c("Type","nPierNumber"))

## Check if the number of Status1 for each Type is same between x and yx.

xx_t = table(xx1$Type,xx1$Status1)
id=which(yxx$CP=="N-04" & (yxx$Type==2 & yxx$Type<5)) # pile cap, pier, pier head

yxx_t = table(yxx$Type[id],yxx$Status1.y[id])

check = xx_t %in% yxx_t

if(str_detect(unique(check),"TRUE")){
  print("GOOD! The number of Status1 for N-01 Bored piles is same between Civil and joined excel ML.")
} else (
  print("Number of Status1 for N-01 Bored piles is DIFFERENT. PLEASE CHECK")
)


# Delete andRe-name variables again
## Extract row numbers to be replaced with new status
# Because we only want to update status with pier numbers that need to be updated in xx,
# we replace Status1.x with only these pier numbers.
gg = which(yxx$CP=="N-04" & yxx$Type>1 & yxx$Type<5)

yxx$end_date.x = as.Date(yxx$end_date.x,origin = "1899-12-30")
yxx$end_date.x = as.Date(yxx$end_date.x,format="%m/%d/%y %H:%M:%S")

yxx$Status1.x[gg]=yxx$Status1.y[gg]
yxx$end_date.x[gg]=yxx$end_date.y[gg]

## Rename and delete Status1.y
id = which(str_detect(colnames(yxx),"Status1.y|end_date.y"))
yxx = yxx[,-id]

colnames(yxx)[which(str_detect(colnames(yxx),"Status1"))] = "Status1"
colnames(yxx)[which(str_detect(colnames(yxx),"end_date"))] = "end_date"

# Convert nA to 1 (to be Constructed)

id = which(is.na(yxx$Status1))
yxx$Status1[id] = 1

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

## Convert status to numeric format
yxx$Status1 = as.numeric(yxx$Status1)

# overwrite masterlist
write.xlsx(yxx, MLTable)
