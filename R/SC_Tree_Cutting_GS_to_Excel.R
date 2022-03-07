


# Tree Cutting Status
## 1. Cut
## 2. Earthballed
## 3. Permit Acquired
## 4. Submitted to DENR
## 5. Ongoing Acquisition of Application Documents

# Tree Conservation
## 1. Ex (Extinct)
## 2. EW (Extinct in the wild)
## 3. CR (Critically Endangered)
## 4. E (Endangered)
## 5. VU (Vulnerable)
## 6. NT (Near Threatened)
## 7. LC (Least Concerned)
## 8. DD (Data Deficient)
## 9. NE (Not Evaluated)
## 10. OTS (Other Threatened)


# Tree Compensation
## 1. Paid
## 2. For Payment Processing
## 3. For Legal Pass
## 4. For Appraisal/Offer to Compensate


# Read google sheet and generate output in xlsx format

library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(lubridate)

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
drive_auth_configure(api_key = "AIzaSyCqbwFnO6csUya-zKcXKXh_-unE_knZdd0")
#drive_auth(path = "G:/My Drive/01-Google Clould Platform/service-account-token.json")


## Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
gs4_auth(email="matsuzakieiji0@gmail.com")



######################### START
# New updated date
new_date = "2021-12-15"



# Choose working directory
path = path_home()

## "C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/02-SC/02-Pre-Construction/01-Environment/03-Tree/01-Masterlist"
wd = file.path(path, "Dropbox/01-Railway/02-NSCR-Ex/02-SC/02-Pre-Construction/01-Environment/03-Tree/01-Masterlist")
setwd(wd)

## Define URL where data is stored and updated
main_url = "https://docs.google.com/spreadsheets/d/1WzG0r_Fm5wfgrWhomACJyJ9dl1n4Sv6XXLDsKK1IZSU/edit?usp=sharing"
pnr_url = "https://docs.google.com/spreadsheets/d/1NaxfRVWRMHY4UtbS94XDbPl92maCFCj0RqFcEjAOgpI/edit?usp=sharing"


## Read original master list
MLTable = file.path(wd,"SC_Tree_merged.xlsx")
y = read.xlsx(MLTable)

colnamesY = colnames(y)



# Read tables from the above URL
x_main = range_read(main_url, sheet = 1)
x_main = data.frame(x_main)

x_pnr = range_read(pnr_url, sheet=1)
x_pnr = data.frame(x_pnr)

x = rbind(x_pnr,x_main)

col = colnames(x)

for(i in seq(col)){
  # delete stand-alone "-" hyphen
  x[[i]][] = gsub("^-","",x[[i]])
  
  # Remove any space before the 1st letter and after the last letter
  x[[i]][] = gsub("^\\s+|\\s+$", "",x[[i]])
}

# Update date
x$updated = new_date

x$updated = as.Date(x$updated, origin = "1899-12-30")
x$updated = as.Date(x$updated, format="%m/%d/%y %H:%M:%S")

# Use colnames from y
colnames(x) = colnamesY

# Convert Conservatino Status to numbers
## 1. Ex (Extinct)
## 2. EW (Extinct in the wild)
## 3. CR (Critically Endangered)
## 4. E (Endangered)
## 5. VU (Vulnerable)
## 6. NT (Near Threatened)
## 7. LC (Least Concerned)
## 8. DD (Data Deficient)
## 9. NE (Not Evaluated)
## 10. OTS (Other Threatened)
conserv = c("Ex","Ew","CR","E","VU",
            "NT","LC","DD","NE","OTS","NL","EN") # NL and EN are new ones?

for(i in 1:length(conserv)) x$Conservation[which(x$Conservation==conserv[i])] = i 


# Conver some variables to numeric
coln = c("DBH","MH","TH","StemQuality","Volume","Longitude","Latitude","Status","Conservation")
for(i in coln) x[[i]] = as.numeric(x[[i]])

x$LotNo = as.character(x$LotNo)

# Re-format CP
cp = unique(x$CP)

x$CP[] = gsub("CP|[[:space:]]","",x$CP)
x$CP[] = toupper(x$CP)




# Overwrite with updated table
write.xlsx(x,"SC_Tree_merged.xlsx")
str(x)



#######################################################################
#### INITIAL SETUP for MAKING MASTERLIST FROM THE RAP TEAM  ###:----
MLTable_pnr = file.path(a,"SC_PNR_Track_Relocation_Tree_Inventory.xlsx")
MLTable_main = file.path(a,"SC_Main_Alignment_Tree_Inventory.xlsx")

y_pnr = read.xlsx(MLTable_pnr)
y_main = read.xlsx(MLTable_main)

y = rbind(y_pnr,y_main)

# Delete redundant punctuation and space
col = colnames(y)

for(i in seq(col)){
  # delete stand-alone "-" hyphen
  y[[i]][] = gsub("^-","",y[[i]])
  
  # Remove any space before the 1st letter and after the last letter
  y[[i]][] = gsub("^\\s+|\\s+$", "",y[[i]])
}

# Update date
y$updated = new_date

y$updated = as.Date(y$updated, origin = "1899-12-30")
y$updated = as.Date(y$updated, format="%m/%d/%y %H:%M:%S")


write.xlsx(y,"SC_Tree_merged.xlsx")


#####################################################

# Read and write as CSV and xlsx
v = range_read(url, sheet = 1)
v = data.frame(v)
head(v)
# Create backup file of original masterlist
# "C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\02-Pre-Construction\01-Environment\02-Tree Cutting\old"
dir = choose.dir()
dates = gsub("-","",Sys.Date()) # today's date

backup = paste(dates,"_",basename,sep="") 

write.xlsx(x,file.path(dir,backup),row.names=FALSE)


## Rename variables
v2 = v
if(sum(str_detect(colnames(v2),"compensation|Compensation"))=1){
  colnames(v2)=c("TreeNo","Province","CP","CommonName","ScientificName",
                "DBH","MH","TH","Volume","Latitude","Longitude",
                "PNR","Status","Conservation","Compensation")
  write.xlsx(v2,file.path(wd,basename),overwrite=TRUE)
} else {
  colnames(v2)=c("TreeNo","Province","CP","CommonName","ScientificName",
                "DBH","MH","TH","Volume","Latitude","Longitude",
                "PNR","Status","Conservation")
  v2$Compensation = as.integer(NA)
  write.xlsx(v2,file.path(wd,basename),overwrite=TRUE)
}


