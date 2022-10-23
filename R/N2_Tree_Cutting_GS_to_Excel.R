



#############################
new_date = "2022-08-01"




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

# Choose working directory
path = path_home()


wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/02-Tree Cutting")

setwd(wd)

## Define URL where data is stored and updated
url = "https://docs.google.com/spreadsheets/d/1LVcMTPahKD9-p_sTBL788qiUbFGTRc3jVgm_nlN-NQU/edit#gid=1298799693"

MLTable = file.path(wd,"Trees_masterlist.xlsx")

basename = basename(MLTable)

y = read.xlsx(MLTable)

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)


# Create backup file of original masterlist
# 

dir = file.path(wd,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/02-Tree Cutting/old")

y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")


old_date = gsub("-","",unique(y$updated))
backup = paste(old_date,"_",basename,sep="") 

write.xlsx(x,file.path(dir,backup),row.names=FALSE)

## Rename variables
v2 = v
v2$updated = new_date

v2$updated = as.Date(v2$updated, origin = "1899-12-30")
v2$updated = as.Date(v2$updated, format="%m/%d/%v2 %H:%M:%S")

head(v2)
str(v2)



# Rename colnames
colnames(v2)=c("TreeNo","Province","CP","CommonName","ScientificName",
               "DBH","MH","TH","Volume","Latitude","Longitude",
               "PNR","Status","Conservation","Compensation","updated")
for(i in 1:5) v2$CP = gsub(i,paste("N-0",i,sep=""),v2$CP)

write.xlsx(v2,file.path(wd,basename))



###############
head(v2)
x=v2
cut = length(which(x$Status==1))
total = nrow(x)
cut/total

head(x)
length(x$TreeNo)
