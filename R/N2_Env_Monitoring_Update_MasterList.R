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
gs4_auth(email="matsuzakieiji0@gmail.com")

# URL of Google Sheet provided by Envi. Team
url = "https://docs.google.com/spreadsheets/d/1rAWKvOMNrecKoLGnHaDz2UqcGszb4BnAhwVIkvXTtL4/edit#gid=1183706342"


# Choose working directory
# C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\01-Environment\01-EIA
path =  path_home()
wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/01-Environment/01-EIA")
setwd(wd)

# Read two tables: our GIs masterlist and master list from Envi Team
# C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\01-Environment\01-EIA\N2_Envi_Monitoring_masterlist.xlsx
MLTable = "C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/01-Environment/01-EIA/N2_Envi_Monitoring_masterlist.xlsx"
x = read.xlsx(MLTable)
basename = basename(MLTable)

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

# Restructure table
v2 = v
newNames = c("StationNo","CP","Location","Latitude","Longitude","samplingDate","Status","sourceLink","parameter")
colnames(v2) = newNames

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
v2$Latitude[] = gsub("[[:space:]]N$","N",x$Latitude)
v2$Longitude[] = gsub("[[:space:]]E$","E",x$Longitude)

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


# Create back up first
# C:\\Users\\oc3512\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\03-During-Construction\\01-Environment\\01-EIA\\old
dates = gsub("-","",Sys.Date()) # today's date

backup = paste(dates,"_",basename,sep="") 
write.xlsx(x,file.path(wd,"old",backup),row.names=FALSE)

# Add Remarks for comments
v2$Remarks = ""
  
# Export
write.xlsx(v2,file.path(wd,basename))
