#******************************************************************#
## Enter Date of Update ##
date_update = "2022-06-24"
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
#drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


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
### 3. Copy the link and paste it to the working_url below

### 4. Copy new link and paste in the following "working_url"
working_url = "https://docs.google.com/spreadsheets/d/1TdUTIpp7pyjkPNpZDvNa6l8BDvYBu5agO6jOEfPbvhg/edit?usp=sharing"

#*****************************************************************************************************

######################################################################################
# 1. BORED PILES:----
######################################################################################


## Sheet Number
WS = "WS ABR" # Workshop
LRS = "LRS ABR"
OCC = "OCC ABR"
TRC = "TRC ABR" # TRCE is also included
CER = "CER ABR"
URS = "URS ABR"
UCS = "UCS ABR"
WRS = "WRS ABR"
DB1 = "DB1 ABR"
DB2 = "DB2 ABR"

sheetID = c(WS,LRS,OCC,TRC,CER,URS,UCS,WRS,DB1,DB2)

# Read and write as CSV and xlsx

DEP_UPDATE_PILE = function()
{
  temp = data.frame()
  for(i in sheetID){
    #i=TRC
    v = range_read(working_url, sheet = i)
    v = data.frame(v)
    
    # Extract fields only needed
    x = v[,c(3,4)]
    
    ## add Column names
    colnames(x) = c("PileNo", "Status")
    id = which(str_detect(x$PileNo,"[0-9]+"))
    x = x[id,]
  
    # Check if data has any status or not. If not, skip this depot building
    count = length(unique(x$Status[!is.na(x$Status)]))
    if(count>0){
      
      # Delete null values in Status
      id = which(is.na(x$Status))
    
      if(length(id)==0){
        print("")
      } else {
        x = x[-id,]
      }

      # Add column name
      x$Name = gsub(" ABR","",i) 
      x$ID = paste(x$Name,"-P",x$PileNo,sep="")
      
      # If TRC, some observations need to be converted from TRC to TRCE
    if(i=="TRC ABR"){
      id=which(x$PileNo=="001")
      ids = id[2]:nrow(x)
      x$Name[ids] = "TRCE"
      x$ID[ids] = gsub("TRC","TRCE",x$ID[ids])
    } else {
      print("")
    }
      # Compile
      temp = rbind(temp,x)
    
      ## Update Status
      completed_case = "^completed|^Completed|^complete|^Complete"
      id=which(str_detect(temp$Status,completed_case))
    
      temp$Status[id] = 4

      rem.id = which(temp$Status!="4")
        if(length(rem.id)==0){
          print("No rows to be removed")
        } else {
          temp = temp[-rem.id,]
        }
      
    } else {
      depName = gsub(" ABR","",i)
      print(paste(depName," has NO Status.",sep = ""))
    }
  }
  temp$Status = as.numeric(temp$Status)
  save(temp,file="temp_compiled.rda")
}

DEP_UPDATE_PILE()
load(file="temp_compiled.rda")

## Join updated tables to ML
y = read.xlsx(MLTable)

### Check ID between x and y
id=which(str_detect(colnames(temp),"Status|ID"))
x = temp[,id]

## Always check duplicated observations

id.rem = x$ID[duplicated(x$ID)]
if(length(id.rem)==0){
  print("NO Duplicated Observations")
} else {
  print("Check and remove any duplicated observations")
}

x.ID = unique(x$ID)
y.ID = unique(y$ID)

x.ID[!x.ID %in% y.ID] # not present in y
y.ID[!y.ID %in% x.ID]


# join
yx = left_join(y,x,by="ID")

## 
gg = which(!is.na(yx$Status.y))
yx$Status.x[gg] = yx$Status.y[gg]

str(yx)

library(lubridate)
yx$end_date = as.Date(yx$end_date, origin = "1899-12-30")
yx$end_date = as.Date(yx$end_date, format="%m/%d/%y %H:%M:%S")

#yx$Status1.y[is.na(yx$Status1.y)] = yx$Status1.x

delField = which(str_detect(colnames(yx),"Status.y"))
yx = yx[,-delField]

# Change Status name
colnames(yx)[str_detect(colnames(yx),pattern="Status")] = "Status"
unique(yx$end_date)
head(yx)
## Output
write.xlsx(yx,MLTable)
