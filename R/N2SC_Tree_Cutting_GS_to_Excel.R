



#############################
old_date = "2022-03-13"
new_date = "2022-04-12"
###############################


# Read google sheet and generate output in xlsx format

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(lubridate)
library(fs)

# This R script reads a Google Sheet and reshape the data table 
# to import into ArcGIS Pro

# Autheticate Google Sheets Access
## Step 1
# method 1: direct provision client ID and secret
#google_app <- httr::oauth_app(
 # "Desktop client 1",
#  key = "603155182488-fqkuqgl6jgn3qp3lstdj6liqlvirhag4.apps.googleusercontent.com",
#  secret = "bH1svdfg-ofOg3WR8S5WDzPu"
#)
#drive_auth_configure(app = google_app)
#drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
#drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
gs4_auth(email="matsuzaki-ei@ocglobal.jp")

### N2:----
# Choose working directory
path = path_home()
wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/02-Tree Cutting")

setwd(wd)

## Define URL where data is stored and updated
url = "https://docs.google.com/spreadsheets/d/1LVcMTPahKD9-p_sTBL788qiUbFGTRc3jVgm_nlN-NQU/edit#gid=1298799693"
MLTable = file.path(wd,"Trees_masterlist.xlsx")
basename = basename(MLTable)

y = read.xlsx(MLTable)

# Create backup file of original masterlist
# 
dir = file.path(wd,"old")

y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")
old_date = gsub("-","",unique(y$updated))
backup = paste(old_date,"_",basename,sep="") 

write.xlsx(x,file.path(dir,backup),row.names=FALSE)

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

## Rename variables
x = v
x$updated = new_date
x$updated = as.Date(x$updated, origin = "1899-12-30")
x$updated = as.Date(x$updated, format="%m/%d/%x %H:%M:%S")

# Rename colnames
colnames(x)=c("TreeNo","Province","CP","CommonName","ScientificName",
               "DBH","MH","TH","Volume","Latitude","Longitude",
               "PNR","Status","Conservation","Compensation","updated")
for(i in 1:5) x$CP = gsub(i,paste("N-0",i,sep=""),x$CP)

write.xlsx(x,file.path(wd,basename))



#########################################
### SC:----
#a = choose.dir()
path = path_home()
a = file.path(path, "Dropbox\\01-Railway\\02-NSCR-Ex\\02-SC\\02-Pre-Construction\\01-Environment\\03-Tree\\01-Masterlist")

fileNames = list.files(a)
names = fileNames[str_detect(fileNames, "^SC_Main.*.xlsx$|^SC_PNR.*xlsx$")]
x = read.xlsx(file.path(a,names[1]))
x1 = read.xlsx(file.path(a,names[2]))

colnames(x)=c("CP","Barangay","District","Municipality","TreeNo",
               "LocalName","FamilyName","ScientificName",
               "DBH","MH","TH","Volume","Longitude","Latitude",
               "Conservation","StemQuality","Planted","LotNo","PNR_ROW","Status")

colnames(x1)=c("CP","Barangay","District","Municipality","TreeNo",
              "LocalName","FamilyName","ScientificName",
              "DBH","MH","TH","Volume","Longitude","Latitude",
              "Conservation","StemQuality","Planted","LotNo","PNR_ROW","Status")

xx = rbind(x,x1)

write.xlsx(xx, "SC_Tree_merged.xlsx")