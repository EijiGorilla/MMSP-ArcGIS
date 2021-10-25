# Read google sheet and generate output in xlsx format

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)

# This R script reads a Google Sheet and reshape the data table 
# to import into ArcGIS Pro

# Autheticate Google Sheets Access
## Step 1
# method 1: direct provision client ID and secret
google_app <- httr::oauth_app(
  "Desktop client 1",
  key = "603155182488-fqkuqgl6jgn3qp3lstdj6liqlvirhag4.apps.googleusercontent.com",
  secret = "bH1svdfg-ofOg3WR8S5WDzPu"
)
drive_auth_configure(app = google_app)
drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
gs4_auth(email="matsuzakieiji0@gmail.com")

a=choose.dir() #"C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\02-Pre-Construction\01-Environment\02-Tree Cutting"
wd = setwd(a)

## Define URL where data is stored and updated
url = "https://docs.google.com/spreadsheets/d/1IOQvv1sux2cgH185SZ7-zDQNUXCOv32m/edit#gid=1298799693"

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

####
d = "C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/01-N2/02-Pre-Construction/01-Environment/02-Tree Cutting/Trees_masterlist.xlsx"
v = read.xlsx(d,sheet=1)
colnames(v)=c("TreeNo","Province","CP","CommonName","ScientificName",
              "DBH","MH","TH","Volume","Latitude","Longitude",
              "PNR","Status","Compensation","Conservation")

write.xlsx(v,d,overwrite=TRUE)
