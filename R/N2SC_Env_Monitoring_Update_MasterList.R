#
# This R code updates our master list excel table for updating GIS attribute table
# 1. Read Google Sheet provided by Envi Team
# 2. Restructure data
# 3. Update masterlist

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(fs)
library(rrapply)

# This R script reads a Google Sheet and reshape the data table 
# to import into ArcGIS Pro

# Autheticate Google Sheets Access
## Step 1
# method 1: direct provision client ID and secret
#google_app <- httr::oauth_app(
#  "Desktop client 1",
#  key = "603155182488-fqkuqgl6jgn3qp3lstdj6liqlvirhag4.apps.googleusercontent.com",
#  secret = "bH1svdfg-ofOg3WR8S5WDzPu"
#)
#drive_auth_configure(app = google_app)
#drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
#drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")

## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
gs4_auth(email="matsuzaki-ei@ocglobal.jp")

########################################################################################
## Choose N2 or SC
cp = select.list(c("N2", "SC"), title="CHoose N2 or SC.")

path =  path_home()

## URL corresponding to CP chosen (this is Google Sheet)
if (cp == "N2") {
  url = "https://docs.google.com/spreadsheets/d/1rAWKvOMNrecKoLGnHaDz2UqcGszb4BnAhwVIkvXTtL4/edit#gid=1183706342"
  wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/01-Environment/01-EIA")
  setwd(wd)
  MLTable = file.path(wd,"N2_Envi_Monitoring_masterlist.xlsx")
  x = read.xlsx(MLTable)
  basename = basename(MLTable)
                      
} else {
  url = "https://docs.google.com/spreadsheets/d/1xkIIGOMFOEYKBmeXV2EVf8yl6Egan8V3H32o2L3odAA/edit#gid=762131956"
  wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/02-SC/03-During-Construction/01-Environment/01-EIA")
  setwd(wd)
  MLTable = file.path(wd,"SC_Envi_Monitoring_masterlist.xlsx")
  x = read.xlsx(MLTable)
  basename = basename(MLTable)
}

## Create backup Files
previous_date = "20220228"

backup = paste(previous_date,"_",basename,sep="")
write.xlsx(x,file.path(wd,"old",backup),row.names=FALSE)


# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

# Restructure table
v2 = v
newNames = c("StationNo","CP","Location","Latitude","Longitude","samplingDate","Status","sourceLink","parameter")
colnames(v2) = newNames

# Check the presence of columns in the format of 'list'
coln = colnames(v2)
for(i in seq(coln)) {
  type = class(v2[[i]])
  
  # if type is 'list', unlist
  if(type == "list") {
    ## Convert NULL to NA
    v2[[i]] = rrapply(v2[[i]], f = function(x) replace(x, is.null(x), NA))
    
    ## then unlist
    v2[[i]] = unlist(v2[[i]], use.names = FALSE)
  }
}

## Get indicator names
typeName = str_detect(v2$StationNo,"Air|air|water|Water|Vibration|vibration|Noise|noise")
typeName = v2$StationNo[typeName]

## Create a new column
v2$typeName = ""

## Get row numbers where type names appear
index = which(v2$StationNo %in% typeName)

v2$typeName[index[1]:index[2]-1] = typeName[1]
v2$typeName[index[2]:index[3]-1] = typeName[2]
v2$typeName[index[3]:index[4]-1] = typeName[3]
v2$typeName[index[4]:nrow(v2)] = typeName[4]

head(v2[1:20,c(1:5,ncol(v2))],20)

## Delete empty rows with empty cells
v2 = v2[-index,]

## Reformat latitude and longitude notation so that ArcGIS Pro can convert it to right coordinate notations
v2$Latitude = gsub("°|’|'"," ",v2$Latitude)
v2$Latitude = gsub('” |"',"",v2$Latitude)

v2$Longitude = gsub("°|’|'"," ",v2$Longitude)
v2$Longitude = gsub('” |"',"",v2$Longitude)

# some lat and long notations have redundant space before "N" or "E"
v2$Latitude[] = gsub("[[:space:]]N$","N", v2$Latitude)
v2$Longitude[] = gsub("[[:space:]]E$","E", v2$Longitude)

v2$Latitude = gsub("  ", " ", v2$Latitude)
v2$Longitude = gsub("  ", " ", v2$Longitude)

# Reformat
## Follow the Domain in ArcGIS Pro for Type
## 1: Noise, 2: Vibration, 3: Air Quality, 4:Soil Water, 5: Groundwater, 6: Surface WAter
noise = typeName[str_detect(typeName,"noise|Noise")]
v2$Type[v2$typeName==noise]=1

vibration = typeName[str_detect(typeName,"vibration|Vibration")]
v2$Type[v2$typeName==vibration]=2

air = typeName[str_detect(typeName,"air|Air")]
v2$Type[v2$typeName==air]=3

soilwater = typeName[str_detect(typeName,"Soil|SOil")]
v2$Type[v2$typeName==soilwater]=4

groundwater = typeName[str_detect(typeName,"ground|Ground")]
v2$Type[v2$typeName==groundwater]=5

surfacewater = typeName[str_detect(typeName,"Surface|Surface")]
v2$Type[v2$typeName==surfacewater]=6


# Add Remarks for comments
v2$Remarks = ""

# Convert data type to correnct one 
## 'samplingDate' is not consistent..
id_date = which(str_detect(v2$samplingDate, "^16"))
if (length(id_date) > 0) {
  dates = as.numeric(v2$samplingDate[id_date])
  dates = as.POSIXlt(dates, origin="1970-01-01",tZ="UTC")
  dates = as.Date(dates, origin="1899-12-30")
  dates = as.Date(dates, origin="%m/%d/%y %H:%M:%S")
  dates = as.character(dates)
  v2$samplingDate[id_date] = dates
} else {
  v2$samplingDate = as.character(v2$samplingDate)
}

v2$Status = as.numeric(v2$Status)
v2$sourceLink = as.character(v2$sourceLink)
v2$parameter = as.character(v2$parameter)

# Export
write.xlsx(v2,file.path(wd,basename))
