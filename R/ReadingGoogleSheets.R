library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)


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


## Step 2: Authorize (Choose 'matsuzakieiji0@gmail.com'. OCG gmail may not work)
gs4_auth()

## Paramter
a=choose.dir()
wd=setwd(a)

## Collect all URLs
### NVS
NVS = c("NVS_Depot", "NVS_QH", "NVS_TSS")
EXPRO = c("Expro_Depot", "Expro_QH", "Expro_TSS") # Tandang Sora
url = "https://docs.google.com/spreadsheets/d/1KcbcdIp_3Tkq6y61CEeJSaVo9EKJ0VeDva2SBUZviZk"

## 2. Compile datasets
### 2.1. NVS
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
  v1 = v1[,c(1,ncol(v1),2:(ncol(v1)-1))]
  write.xlsx(v1, "temp_NVS1.xlsx", row.names = FALSE)

  temp = read.xlsx(file.path(wd, "temp_NVS1.xlsx"))
  head(temp)
  colnames(temp)

  # Convert to Date format (after compiling all)
  colNames = colnames(temp)[16:ncol(temp)]
  
  for(k in colNames){
    temp[[k]] = as.Date(temp[[k]], format = "%d %b %y")
    temp[[k]] = as.Date(temp[[k]], format = "1899-12-30")
    temp[[k]] = as.numeric(temp[[k]])
  }

  # Make sure that CN is text
  temp$CN = as.character(temp$CN)
  
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

nvs = TEMP_NVS
expro = TEMP_EXPRO
write.xlsx(TEMP_NVS,"TEMP_NVS.xlsx", row.names = FALSE)
write.xlsx(TEMP_EXPRO,"TEMP_EXPRO.xlsx", row.names = FALSE)

