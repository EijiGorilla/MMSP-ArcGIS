library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)

# This R script compiles tables from Google spreadsheet available from DOTr.
# https://docs.google.com/spreadsheets/d/1zoQVPsWHfgZT1Q_Scz2lnkQKafeyI9c79yAbMEnBuno/edit#gid=743362036
# It adds four types of land acquisition processes to the table
# 1. Status3 (OtB for serving, Otb Accepted...) (I coded as below in the Domain of ArcGIS Pro)
#     1.OTB for Accepted
#     2.OTB for Serving
#     3.Pending Compilation of Documents
#     4.Pending Appraisal
#     5. Pending Documents from Other Agencies
#     6. Pending OTB Reply behond 30 Days (Cooperative)
#     7. Pending OTB Reply within 30 Days
#
# 2. StatusNVS (For submission to Legal Pass....)(I coded as below in the Domain of ArcGIS Pro)
#     1. For Submission to Legal Pass
#     2. Pending Legal Pass
#     3. Legal Pass Issued
#
# 3. StatusNVS2 (Payment Processing) (I coded as below in the Domain of ArcGIS Pro)
#     1. For Submission to Budget of MORS
#     2. With Budget for Oblication
#     3. With Acctg for CAF Issuance
#     4. For DOTr Signing
#     5. For Notarization
#     6. With GSD for CTC'ing
#     7. For Submission to CS of DV
#     8. DV with CS
#     9. Paid/Check Issued
#
# 4. StatusNVS3 (simplified version of the above three): (I coded as below in the Domain of ArcGIS Pro)
#    1.Paid,
#    2.Ongoing Payment Processing,
#    3.Ongoing Leagal Pass, 
#    4. Ongoing Appraisal/Offer to Buy, and
#    5. For Expro
# The script finally generates a compiled master list table used to join with GIS feature layers.



# STEP:1 Copy and Paste Google Sheets from DOTr's to My Google Sheets:----
#
# **READ first****READ first****READ first****READ first****READ first****READ first**
#
#WHen you copy and paste, make sure that column names are consistent.
# Make sure to check the Google Sheets to see if there are some anomalies or errors.
# For "NVS_TSS" Google Sheets of DOTr, there are forma links such that you will have errors when just copying and pasting.
# For "NVS_TSS", make sure to copy and paste to Excel Sheet (xlsx) first then copy and paste to my Google Sheet


# STEP 2: Authenticate Google Sheets:----

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


# STEP 3: Compile all Google Sheet Tables:----
## Parameter
a=choose.dir()

wd=setwd(a)


# Read an previous master list
c = file.choose()
x = read.xlsx(c) # master list 

## Collect all URLs
### NVS
NVS = c("NVS_Depot", "NVS_QH", "NVS_TSS")
EXPRO = c("Expro_Depot", "Expro_QH", "Expro_TSS") # Tandang Sora
url = "https://docs.google.com/spreadsheets/d/1KcbcdIp_3Tkq6y61CEeJSaVo9EKJ0VeDva2SBUZviZk"

## 2. Compile datasets
### 2.1. NVS
wd=setwd(a)
TEMP_NVS = data.frame()
n=0

for(i in NVS){
  #i=NVS[1]
  n=n+1
  
  # Read and write as CSV
  v = range_speedread(url, sheet = i)
  write.csv(v, "temp_NVS.csv", na="NA", row.names = FALSE)

  v1 = read.csv(file.path(wd,"temp_NVS.csv"), stringsAsFactors = FALSE)

  ## Add Station names
  if(n==1){
    v1$Station = "Depot"
  } else if(n==2){
    v1$Station = "Quirino Highway"
  } else {
    v1$Station = "Tandang Sora"
  }
  
  # Write and read back as xlsx
  ## Reorder: bring "Station" to the second name
  colnames(v1)
  v1 = v1[,c(1,ncol(v1),13:(ncol(v1)-1))]
  write.xlsx(v1, "temp_NVS1.xlsx", row.names = FALSE)

  temp = read.xlsx(file.path(wd, "temp_NVS1.xlsx"))

  # Convert to Date format (after compiling all)
  colNames = colnames(temp)[5:ncol(temp)]
  
  for(k in colNames){
    temp[[k]] = as.Date(temp[[k]], format = "%d %b %y")
    temp[[k]] = as.Date(temp[[k]], format = "1899-12-30")
    temp[[k]] = as.numeric(temp[[k]])
    temp[[k]] = gsub("N/A", "NA", temp[[k]]) # Some cells have "N/A" which must be converted to NA
  }
  
  # Convert "N/A" to "NA" in R format
  temp$Status = gsub("N/A", "NA", temp$Status)

  # Make sure that CN is text
  temp$CN = as.character(temp$CN)
  
  # Remove Structure
  t5 = str_detect(temp$CN, "S") # Structure's CN ends with "S"
  temp = temp[-which(t5==TRUE),]

  # Compile all NVS files for each station
  TEMP_NVS = bind_rows(TEMP_NVS, temp)
}

# Priorit3
dd = str_detect(colnames(TEMP_NVS), "Priority")
colnames(TEMP_NVS)[which(dd==TRUE)] = "Priority3"
#which(dd==TRUE)

### 2.2. Expro
TEMP_EXPRO = data.frame()
n=0

for(i in EXPRO){
 # i=EXPRO[2]
  n=n+1
  v = range_speedread(url, sheet = i)
  write.csv(v, "temp_EXPRO.csv", na="NA", row.names = FALSE)
  
  v1 = read.csv(file.path(wd,"temp_EXPRO.csv"), stringsAsFactors = FALSE)
  
  ## Add Station names
  if(n==1){
    v1$Station = "Depot"
  } else if(n==2){
    v1$Station = "Quirino Highway"
  } else {
    v1$Station = "Tandang Sora"
  }
  
  # Write and read back as xlsx
  ## Reorder: bring "Station" to the second name
  v1 = v1[,c(1,ncol(v1),3:(ncol(v1)-1))]
  write.xlsx(v1, "temp_EXPRO1.xlsx", row.names = FALSE)
  
  temp = read.xlsx(file.path(wd, "temp_EXPRO1.xlsx"))
  
  ## Get "Priority" location
  rr=str_detect(colnames(temp), "Priority")
  temp = temp[,c(1,2,which(rr==TRUE))]
  colnames(temp)[3] = "Priority3_expro" # Rename priority
  
  # Add a field name to indicate the lots in this table is subject to Expropriation
  temp$ForExpro = 1
  
  # Make sure that CN is text
  temp$CN = as.character(temp$CN)

  # Compile all NVS files for each station
  TEMP_EXPRO = bind_rows(TEMP_EXPRO, temp)
  
}


# STEP 4: Add LAR Processes for Osec Maps:----
# 1. Read Tables
nvs = TEMP_NVS
expro = TEMP_EXPRO


# Define names of Status 3
Status3Names = c("OTB Accepted",
                 "OTB for Serving",
                 "Pending Compilation of Documents",
                 "Pending Appraisal",
                 "Pending Documents from Other Agencies",
                 "Pending OTB Reply beyond 30 days (Cooperative)",
                 "Pending OTB Reply within 30 days",
                 "For Expropriation")

# 2. Add Field Names
### 2.1 NVS Table
# Change field names of Dates that are used to add processes (names are too long)
colnames(nvs)
dateNames = c("P", "Q", "R", "S", "TT", "U", "V", "W", "X", "Y", "Z",
              "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK")
# P: "Date of Initial Submission for Legal Pass", AK: "Actual Date of Check Issuance"
colnames(nvs)[c(5:ncol(nvs))]=dateNames

# Add processes:
## StatusNVS
nvs$StatusNVS = 0
nvs$StatusNVS[nvs$Status==Status3Names[1] & nvs$P>1 & is.na(nvs$Q)]=1
nvs$StatusNVS[nvs$Q>1 & nvs$R>1 & is.na(nvs$S)]=2
nvs$StatusNVS[nvs$S>1]=3

## Status3
nvs$Status3 = 0
nvs$Status3[nvs$Status==Status3Names[1]]=1
nvs$Status3[nvs$Status==Status3Names[2]]=2
nvs$Status3[nvs$Status==Status3Names[3]]=3
nvs$Status3[nvs$Status==Status3Names[4]]=4
nvs$Status3[nvs$Status==Status3Names[5]]=5
nvs$Status3[nvs$Status==Status3Names[6]]=6
nvs$Status3[nvs$Status==Status3Names[7]]=7
nvs$Status3[nvs$Status==Status3Names[8]]=8

## StatusNVS2
nvs$StatusNVS2 = 0
nvs$StatusNVS2[nvs$TT>1 & is.na(nvs$U)]=1
nvs$StatusNVS2[nvs$U>1 & nvs$V>1 & is.na(nvs$W)]=2
nvs$StatusNVS2[nvs$W>1 & is.na(nvs$AA)]=3
nvs$StatusNVS2[nvs$AC>1 & is.na(nvs$AD) & is.na(nvs$AE)]=4
nvs$StatusNVS2[nvs$AE>1 & is.na(nvs$AG)]=5
nvs$StatusNVS2[nvs$AG>1 & nvs$AH>1 & is.na(nvs$AI)]=7
nvs$StatusNVS2[nvs$AI>1 & is.na(nvs$AK)]=8
nvs$StatusNVS2[nvs$AK>1]=9


## StatusNVS3
nvs$StatusNVS3 = 0
nvs$StatusNVS3[nvs$Status==Status3Names[1] & nvs$S>1 & is.na(nvs$AK)]=2
nvs$StatusNVS3[nvs$Status==Status3Names[1] & is.na(nvs$S)]=3
nvs$StatusNVS3[nvs$Status==Status3Names[2] | nvs$Status==Status3Names[3] |
                 nvs$Status==Status3Names[4] | nvs$Status==Status3Names[5] |
                 nvs$Status==Status3Names[6] | nvs$Status==Status3Names[7] |
                 nvs$Status==Status3Names[8]]=4
nvs$StatusNVS3[nvs$AK>1]=1 # Make sure that Paid (1) must come at last

write.xlsx(nvs, "Table_toBeChecked.xlsx",row.names = FALSE)

## Keep only necessary fields
nvs = nvs[,c("CN", "Station","Priority3", "StatusNVS", "Status3", "StatusNVS2", "StatusNVS3")]

## FOr counting the total number of target lots for NVS
nvs$count_nvs = 1

### 2.2. Expro Table
expro$count_nvs = 1
expro$ForExpro = 1

# 3. Join NVS table with a Master List table
## 3.1. Delete NVS Status fields from a master list table
x = x[,-c(which(colnames(x)=="Priority3"):ncol(x))] # Delete from "StatusNVS" to the end of fields

## 3.2 Join
x_nvs = left_join(x, nvs, by=c("CN", "Station"))

# 4. Join expro table to x_nvs table
xy_nvs_expro = left_join(x_nvs, expro, by=c("CN", "Station"))


# 5. Update tables
## 5.1. Convert N/A to 0
xy_nvs_expro$StatusNVS[is.na(xy_nvs_expro$StatusNVS)]=0
xy_nvs_expro$Status3[is.na(xy_nvs_expro$Status3)]=0
xy_nvs_expro$StatusNVS2[is.na(xy_nvs_expro$StatusNVS2)]=0
xy_nvs_expro$StatusNVS3[is.na(xy_nvs_expro$StatusNVS3)]=0
xy_nvs_expro$ForExpro[is.na(xy_nvs_expro$ForExpro)]=0

## Priority for NVS
colnames(xy_nvs_expro)
xy_nvs_expro$Priority3[is.na(xy_nvs_expro$Priority3)]=0
xy_nvs_expro$Priority3_expro[is.na(xy_nvs_expro$Priority3_expro)]=0

## Count NVS
xy_nvs_expro$count_nvs.x[is.na(xy_nvs_expro$count_nvs.x)]=0
xy_nvs_expro$count_nvs.y[is.na(xy_nvs_expro$count_nvs.y)]=0

## 5.2. Merge Priority and Count NVS with Expro 
xy_nvs_expro$Priority3 = xy_nvs_expro$Priority3 + xy_nvs_expro$Priority3_expro
xy_nvs_expro$count_nvs = xy_nvs_expro$count_nvs.x + xy_nvs_expro$count_nvs.y
colnames(xy_nvs_expro)

## 5.3 Add StatusNVS3 for For Expro
xy_nvs_expro$StatusNVS3[xy_nvs_expro$ForExpro==1]=5 # Add For Expro process to statusNVS3

# Delete supplementary count and priority fields
xy_nvs_expro = xy_nvs_expro[,-c(which(colnames(xy_nvs_expro)=="count_nvs.x"):which(colnames(xy_nvs_expro)=="count_nvs.y"))]


# STEP 5: Save an output table:----
# 6. Write a new master list
#dropboxFolder = "C:/Users/oc3512/Dropbox/???01-Railway/01-MMSP/02-Pre-Construction/01-Environment/01-LAR/99-MasterList"
#write.xlsx(xy_nvs_expro,file.path(dropboxFolder,paste("MasterList_",gsub("-","",Sys.Date()), ".xlsx", sep="")),row.names=FALSE)
write.xlsx(xy_nvs_expro,file.path(wd,paste("MasterList_",gsub("-","",Sys.Date()), ".xlsx", sep="")),row.names=FALSE)


# Check
print(table(xy_nvs_expro$StatusNVS, dnn="StatusNVS"))
print(table(xy_nvs_expro$Status3, dnn="Status3"))
print(table(xy_nvs_expro$StatusNVS2, dnn="StatusNVS2"))
print(table(xy_nvs_expro$StatusNVS3, dnn="StatusNVS3"))

# Make a summary table
summaryT = data.frame(xy_nvs_expro %>% group_by(StatusNVS3, Station) %>% summarise(n = n()))

# Recoode StatusNVS3 for easier interpretation
summaryT$StatusNVS3 = recode(summaryT$StatusNVS3, '1'="Paid", '2'="Ongoing Payment Processing",
       '3'="Ongoing Legal Pass", '4'="Ongoing Appraisal/OtB", '5'="For Expro")
summaryT

# Total Number of observations for subject Lots (i.e., only StatusNVS3)
sum(summaryT$n[which(!is.na(summaryT$StatusNVS3))])
