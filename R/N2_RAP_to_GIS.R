### This R script imports compiled tables from the RAP Team
### to translate their tables into master list tables for GIS


# 0. read libraries
library(googlesheets4)
library(openxlsx)
library(dplyr)
library(stringr)
library(reshape2)
library(fs)
library(lubridate)
library(rrapply)
library(purrr)
library(qpcR)
library(tidyverse)

gs4_auth(email="matsuzaki-ei@ocglobal.jp") #matsuzakieiji0@gmail.com
path =  path_home()

################################################
new_date = "20230524"

## Set working directory
#z = choose.dir()
z = "C:\\Users\\eiji.LAPTOP-KSD9P6CP\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\02-Pre-Construction\\01-Environment\\01-LAR\\99-MasterList\\03-Compiled"
setwd(z)

# 1. Land:----
## 1.1. Land:----
## Main master list:----
# original source: https://docs.google.com/spreadsheets/d/1k3Q3-bEkAUed2NV_iVOnzsB6CC1dDkMbB5NrXjiTPaA/edit?usp=sharing
url = "https://docs.google.com/spreadsheets/d/1nQKLbkvr0zaH3KgqjZHyVV0iuMPO3g0jytuKr6Dsw7Q/edit?usp=sharing"

sheetNames <- url %>%
  sheet_names()

sheetLength = length(sheetNames) - 1
sheetNumbers = as.numeric(paste(1:sheetLength,sep=","))

landCompile = function(url, sheetNumbers) {
  temp = data.frame()
  for(i in sheetNumbers) {
    sheetname = sheetNames[i]
    
    v = range_read(url, sheet=sheetname)
    x = data.frame(v)
    
    ##. Check the presence of columns in the format of 'list'
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
    
    ## Get column numbers for the followings
    ### 1. LotID, 2.LandOwer, 3.CN, 4.StatusLA
    ### for StatusLA
    #### "Paid" - no info on the Google Sheet
    #### "For Payment Processing" - no info on the Google Sheet
    #### "For Legal Pass" - "Status" = ACCEPTED under "Offer to Buy" 
    #### "For Appraisal/Offer to Buy" - default so all the rows are filled with this first
    #### "For Expro" -  "Status" = REFUSED under "Offer to Buy" 

    ## Select certain columns
    coln = length(colnames(x))
    comp = data.frame()
    for(i in seq(coln)) {
      id = which(str_detect(x[[i]], "^Offer to Buy$"))
      if(length(id) > 0) {
        tt = data.frame(coln=i, rown=id)
        comp = rbind(comp, tt)
      }
    }
    
    if(nrow(comp) >= 2){
      print("Something is wrong. Fix your code")
    }
    
    # Keep columns
    columnKeep = comp[1,1]: (comp[1,1]+6)
    
    # Now select columns
    x = x[,c(5,7,8, columnKeep)]

    # Identify status column
    coln = length(colnames(x))
    comp = data.frame()
    for(i in seq(coln)) {
      id = which(str_detect(x[[i]], "^Status$"))
      if(length(id) > 0) {
        tt = data.frame(coln=i, rown=id)
        comp = rbind(comp, tt)
      }
    }
    
    if(nrow(comp) >= 2){
      print("Something is wrong. Fix your code")
    }
    
    # keep only status column
    x = x[,c(1,2,3,comp[1,1])]
    colnames(x) = c("LotID","CN","LandOwner","Status")

    ## identify first and end
    x$LotID = gsub("[[:space:]]","",x$LotID)
    id = which(str_detect(x$LotID,"^LOTID|^LotID|^lotID|^Lotid|^lotid"))
    x = x[-c(1:id),]

    ## Remove empy LotNo
    id = which(is.na(x$LotID))
    if (length(id) > 0) {
      x = x[-id,]
    } else {
      print("No empty LotID")
    }

    ## Remove punctuation
    x$LotID = gsub("[^[:alnum:][:space:]-]","",x$LotID)

    ## Remove all redundant space for each field name
    x$LotID = gsub("^\\s+|\\s+$","", x$LotID)
    x$CN = gsub("[[:space:]]","",x$CN)
    
    ## All capital letter
    x$CN = toupper(x$CN)
    x$Status = toupper(x$Status)
    
    ## Check duplicated
    id = anyDuplicated(x, incomparables=FALSE)

    if(id>0){
      x = x[-id,]
    } else {
      print("no duplicated observations")
    }

    ## Add Municipality and CP
    if(str_detect(sheetname,"Malolos|Apalit|Calumpit|Minalin")){
      x$CP = "N-01"
      
    } else if(str_detect(sheetname,"Sto.Tomas|SanFernando_N02")){
      x$CP = "N-02"
      
    } else if(str_detect(sheetname,"SanFernando_N03|Angeles")){
      x$CP = "N-03"
      
    }
    
    x$Municipality = sheetname

    # Status
    ## For Legal Pass: Status = ACCEPTED
    print(paste(sheetname, "; ", unique(x$Status)))
    id=which(str_detect(x$Status,"ACCEPTED|Accepted|accepted"))
    x$Status[id] = 3
  
    ## For Expro: Status = REFUSED
    id=which(str_detect(x$Status,"REFUSED|Refused|refused"))
    x$Status[id] = 5

    ## For Paid: define later
    
    ## For Payment Processing: define later
    
    ## Default = 4 (all the others = 4)
    id=which(is.na(x$Status))
    x$Status[id] = 4

    x$Status = as.numeric(x$Status)
    
    # anthygin does not belong = 4
    id=which(is.na(x$Status))
    x$Status[id] = 4

    # Compile 
    temp = rbind(temp,x)
  }
  return(temp)
}

temp = landCompile(url=url, sheetNumbers = sheetNumbers)

# Export output
write.xlsx(test, paste("N2_Land_",new_date,".xlsx",sep=""))


## Other master list:----
### We need these master list
a = "C:/Users/eiji.LAPTOP-KSD9P6CP/Dropbox/01-Railway/02-NSCR-Ex/99-MasterList_RAP_Team/N2/Land"

## Make sure to close all the excel files in the folder
list_files = list.files(a)

temp2 = data.frame()
for(i in list_files){
  #i=list_files[6]
  municipal = str_extract(i, "Angeles|Apalit|Calumpit|Minalin|San Fernando|SF")

  print(municipal)
  x = read.xlsx(file.path(a,i))

  # identify beginning
  id=which(str_detect(x[[1]],"^LOT"))
  if(id<=1){
    print("no need to identify the beginning")
  } else {
    x = x[-(id-1),]
  }
 
  # Columun names
  colnames = as.character(x[1,])

  # Remove the first row
  x = x[-1,]
  colnames(x) = colnames

  ## Change column names
  colnames(x)[which(str_detect(colnames(x),"^LOT.*ID$"))] = "LotID"
  colnames(x)[which(str_detect(colnames(x),"^START|^Start"))] = "Start"
  colnames(x)[which(str_detect(colnames(x),"^END|$END"))] = "End"
  colnames(x)[which(str_detect(colnames(x),"^BARANGAY|^Barangay"))] = "Barangay"
  colnames(x)[which(str_detect(colnames(x),"^TITLE NUMBER$|^Title Number$"))] = "TitleNo"
  colnames(x)[which(str_detect(colnames(x),"^LOT NUMBER$|^Lot Number$"))] = "LotNo"
  colnames(x)[which(str_detect(colnames(x),"^SURVEY.*NUMBER$"))] = "SurveyNo"
  colnames(x)[which(str_detect(colnames(x),"^REGISTERED.*OWNER"))] = "LandOwner"
  colnames(x)[which(str_detect(colnames(x),"^TOTAL.*AREA"))] = "TotalArea"
  colnames(x)[which(str_detect(colnames(x),"^AFFECTED.*AREA"))] = "AffectedArea"
  colnames(x)[which(str_detect(colnames(x),"^REMAINING.*AREA"))] = "RemainingArea"

  # Remove other columns 
  id=which(colnames(x)=="RemainingArea")
  x = x[,-c(id+1:ncol(x))]
  
  # Convert total area and affected area to numeric
  x$TotalArea = as.numeric(x$TotalArea)
  x$AffectedArea = as.numeric(x$AffectedArea)

  ## Remove all spaces in LotID
  x$LotID = gsub("[[:space:]]","",x$LotID)
  x$LotID
  
  ## remove ".0"
  #x$LotID = gsub(".0$","",x$LotID)

  ## Remove punctuation
  #x$LotID = gsub("[^[:alnum:][:space:]-]","",x$LotID)
  
  ## Remove all redundant space for each field name
  x$LotID = gsub("^\\s+|\\s+$","", x$LotID)
  
  ## All uppercase
  x$LotID = toupper(x$LotID)
  
  # Add municipality
  x$Municipality = unique(municipal)
  
  #
  temp2 = rbind(temp2,x)
}

# Remove ".0" from LotID
temp2$LotID = gsub("[.][0-9]","",temp2$LotID)

# Remove non-LotIDs
id=which(str_detect(temp2$LotID,"LOT$|LOTS$"))
temp2 = temp2[-id,]


##########################
# Compile 'temp' and 'temp2'
comp = full_join(temp,temp2,by="LotID")

# 1.Land Owner:----
# check missing landowner from both tables
miss_LO_x = which(is.na(comp$LandOwner.x) & !is.na(comp$LandOwner.y))
if(length(miss_LO_x)>0){
  comp$LandOwner.x[miss_LO_x] = comp$LandOwner.y[miss_LO_x]
}

miss_LO_y = which(is.na(comp$LandOwner.y) & !is.na(comp$LandOwner.x))
if(length(miss_LO_y)>0){
  comp$LandOwner.y[miss_LO_y] = comp$LandOwner.x[miss_LO_y]
}

# check
miss_LO_x = which(is.na(comp$LandOwner.x) & !is.na(comp$LandOwner.y))
miss_LO_y = which(is.na(comp$LandOwner.y) & !is.na(comp$LandOwner.x))
length(miss_LO_x)
length(miss_LO_y)

# Delete LandOwner.y
id=which(str_detect(colnames(comp),"^Land.*.y$"))
comp = comp[,-id]

# Rename
id=which(str_detect(colnames(comp),"^Land.*.x$"))
colnames(comp)[id] = "LandOwner"

# 2.Municipality:----
# check missing municipality from both tables
miss_MP_x = which(is.na(comp$Municipality.x) & !is.na(comp$Municipality.y))
if(length(miss_MP_x)>0){
  comp$Municipality.x[miss_MP_x] = comp$Municipality.y[miss_MP_x]
}

miss_MP_y = which(is.na(comp$Municipality.y) & !is.na(comp$Municipality.x))
if(length(miss_MP_y)>0){
  comp$Municipality.y[miss_MP_y] = comp$Municipality.x[miss_MP_y]
}

# check
miss_MP_x = which(is.na(comp$Municipality.x) & !is.na(comp$Municipality.y))
miss_MP_y = which(is.na(comp$Municipality.y) & !is.na(comp$Municipality.x))
length(miss_MP_x)
length(miss_MP_y)

# Delete Municipality.y
id=which(str_detect(colnames(comp),"^Municipality.*.y$"))
comp = comp[,-id]

# Rename
id=which(str_detect(colnames(comp),"^Municipality.*.x$"))
colnames(comp)[id] = "Municipality"

# Fix Municipality name
id=which(str_detect(comp$Municipality,"^SanFernando|^SF"))
comp$Municipality[id] = "San Fernando"

# Add missing CP
## Add Municipality and CP
id=which(str_detect(comp$Municipality,"Minalin|Malolos|Apalit|Calumpit|Minalin"))
comp$CP[id] = "N-01"

id=which(str_detect(comp$Municipality,"Sto.Tomas|San Fernando"))
comp$CP[id] = "N-02"

id=which(str_detect(comp$Municipality,"Angeles"))
comp$CP[id] = "N-03"


# Remove Orientation
id=which(str_detect(colnames(comp),"^ORIEN|^Orien|^orien"))
comp = comp[,-id]

# Remove when affected area = 0
id=which(comp$AffectedArea == 0)
comp = comp[-id,]

# 3. Export final output:----
write.xlsx(comp,paste("N2_land_compiled_RAP_",new_date,".xlsx",sep=""))


# compare this compiled with gis data
a = file.choose()
gis = read.xlsx(a)

comp_lotid = comp$LotID
gis_lotid = gis$LotID

missing_in_gis = comp_lotid[!comp_lotid %in% gis_lotid]
missing_in_comp = gis_lotid[!gis_lotid %in% comp_lotid]

# Check compiled table when lotids are missing in gis attribute table.
# see if there are important lotIDs which has status information
comp[id,]
