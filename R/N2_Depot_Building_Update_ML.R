#******************************************************************#
## Enter Date of Update ##
date_update = "2022-01-21"
# This R code reads Google sheet monitoring sheets owned by N2 Civil Team and
# updates GIS master list.

### COnstruction Status
# 1. To be Constructed
# 2. Under Contruction
# 3. Delayed
# 4. COmpleted

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
drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
#gs4_auth(email="matsuzakieiji0@gmail.com")
gs4_auth(email="matsuzaki-ei@ocglobal.jp")


path = path_home()

a = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/04-Building_Depot/01-MasterList/01-Compiled")

#a=choose.dir()
wd = setwd(a)

# Read our master list table
# C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\02-Civil\03-Viaduct\01-Masterlist\02-Compiled\N2_Viaduct_MasterList.xlsx"
MLTable = file.path(a,"N2_Depot_Building_ML.xlsx")
# Read the masterlist:----
y = read.xlsx(MLTable)

###################################################################################################
# Read Googel Sheet from the CIvil Team and Update GIS Mater List;------------

## VERY IMPORTANT ###
## Source link of Google SHeet provided by Civil Team for monioring N2 depot buildings is saved in 
## .XLSX format. THe problem is that I cannot read the Google SHeet saved in XLSX format.
## The only work-around is visit the source link and "save as Google Sheet".
## However, if you do this, the URL link changes every time, as copied Google Sheet is not linked to the
## source link. As such, at present, I have to update the URL every time the master list is updated

#***************************************************************************************
## FOllow this step before running the code
### 1. Open the source url (Civil Team)
source_url = "https://docs.google.com/spreadsheets/d/1uo67rFwdQc4bi1y4TRugGJjT5hndnofN/edit#gid=2110596593"

### 2. Go to File and Save as Google Sheet
### 3. Open the saved link from below
https://docs.google.com/spreadsheets/u/0/?tgif=d

### 4. Click and Open the copied Google Sheet
### 5. Copy new link and paste in the following "working_url"
working_url = "https://docs.google.com/spreadsheets/d/1cnGA4c9nBMO5UI7qTd-A9jVrwCDnkyHYY90wx7P_L-k/edit?usp=sharing"

#*****************************************************************************************************

######################################################################################
# 1. BORED PILES:----
######################################################################################
temp = data.frame()

## Sheet Number
WS = 4
LRS = 5
OCC = 7
TRC = 8
CER = 9
URS = 10
UCS = 11
WRS = 12
DB1 = 13
DB2 = 14

# 1. WS (Workshop):-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = WS)
v = data.frame(v)

head(v[,c(3,4)],20)
# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "WS"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

# Compile
temp = rbind(temp,x)

unique(temp$Status)
# 2. LRS :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = LRS)
v = data.frame(v)

head(v[,c(3,4)],20)
# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "LRS"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

# Compile
temp = rbind(temp,x)


# 3. OCC :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = OCC)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "OCC"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

# Compile
temp = rbind(temp,x)


# 4. TRC :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = TRC)
v = data.frame(v)

# Extract fields only needed
## TRC has unknown bored pile Nos. some are duplicated so I filtered only needed piles. Is this right?
x = v[1:50,c(3,4)]


## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]


# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "TRC"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

# Compile
temp = rbind(temp,x)


# 5. CER :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = CER)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "CER"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

head(x)
# Compile
temp = rbind(temp,x)


# 6. URS :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = URS)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "URS"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

head(x)
# Compile
temp = rbind(temp,x)


# 7. UCS :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = UCS)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "UCS"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

head(x)
# Compile
temp = rbind(temp,x)


# 8. WRS :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = WRS)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "WRS"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

head(x)
# Compile
temp = rbind(temp,x)


# 9. DB1 :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = DB1)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "DB1"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

head(x)
# Compile
temp = rbind(temp,x)


# 10. DB2 :-----

# Read and write as CSV and xlsx
v = range_read(working_url, sheet = DB2)
v = data.frame(v)

# Extract fields only needed
x = v[,c(3,4)]

## add Column names
colnames(x) = c("PileNo", "Status")
id = which(str_detect(x$PileNo,"^Bored|^bored"))

x = x[(id+1):nrow(x),]

# Delete null values
id = which(is.na(x$PileNo))
x = x[-id,]

# Add column name
x$Name = "DB2"
x$ID = paste(x$Name,"-",x$PileNo,sep="")

# Compile
temp = rbind(temp,x)



# Fix 
xx = temp
id_comp = which(str_detect(xx$Status,"^Compl|^compl")) # Comopleted
id_under = which(str_detect(xx$Status,"remedial")) # under construction
id_tobe = which(is.na(xx$Status))

xx$Status[id_tobe] = "1"
xx$Status[id_comp] = "4"
xx$Status[id_under] = "2"

xx$Status = as.numeric(xx$Status)
