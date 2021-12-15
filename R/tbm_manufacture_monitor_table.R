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
gs4_auth()

# Choose "1!
1

# STEP 3: Compile all Google Sheet Tables:----
## Parameter
a=choose.dir()
wd = setwd(a)

## Define URL where data is stored and updated
url = "https://docs.google.com/spreadsheets/d/12mQTJH2SAwiQH2bUXLM2RkDA0kU4nzXmDb7Mi7rJm5E/edit#gid=762722994"

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)

#v = range_speedread(url, sheet = 1)

write.csv(v, "temp_NVS.csv", na="NA", row.names = FALSE)

v1 = read.csv(file.path(wd,"temp_NVS.csv"), stringsAsFactors = FALSE)
write.xlsx(v1, file.path(wd,"temp_NVS.xlsx"), row.names=FALSE)
head(v1)

v2 = read.xlsx(file.path(wd,"temp_NVS.xlsx"))

# Reshape the wide to long format
v3 = melt(v2, id.vars = c("TBM", "Parts"))
v3$variable = as.character(v3$variable)

# Rename variables

colnames(v3)[3:4] = c("Process", "Progress")

# Recode Parts: ArcGIS Pro uses domain for the Parts so use numeric values
## Parts:

v3$Parts[v3$Parts == "Cutter head"] = 1
v3$Parts[v3$Parts == "Driving unit"] = 2
v3$Parts[v3$Parts == "Erector"] = 3
v3$Parts[v3$Parts == "Shield Jack"] = 4
v3$Parts[v3$Parts == "Screw Conveyor"] = 5
v3$Parts[v3$Parts == "Front body (Hood)"] = 6
v3$Parts[v3$Parts == "Middle body"] = 7
v3$Parts[v3$Parts == "Tail body"] = 8
v3$Parts[v3$Parts == "Back up trolleys"] = 9
v3$Parts[v3$Parts == "M&E"] = 10

## Process:
unique(v3$Process)
v3$Process[v3$Process == "Design"] = 1
v3$Process[v3$Process == "Fabrication"] = 2
v3$Process[v3$Process == "Assembly"] = 3
v3$Process[v3$Process == "Inspection"] = 4 
v3$Process[v3$Process == "Transportation"] = 5

## Convert to numbers
v3$Parts = as.numeric(v3$Parts)
v3$Process = as.numeric(v3$Process)

# Expoert
write.xlsx(v3, file.path(wd,paste("TBM_manfaucturing_progress_",gsub("-","",Sys.Date()), ".xlsx", sep="")),row.names=FALSE)



