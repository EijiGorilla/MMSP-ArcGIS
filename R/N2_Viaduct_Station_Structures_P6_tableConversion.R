
library(googlesheets4)
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)
library(fs)
library(lubridate)
library(rrapply)
library(purrr)


gs4_auth(email="matsuzaki-ei@ocglobal.jp") #matsuzakieiji0@gmail.com
path =  path_home()

## Define working directory
wd = file.path(path, "Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/02-Station Structure/00-Monitoring Doc")
setwd(wd)

# Read our master list table
## MasterList file name: "N2_Viaduct_MasterList.xlsx"
MLTable = file.choose()
y = read.xlsx(MLTable)

##########################################
# ********* Viaduct:---- ****************
##########################################

# N-01:----
piles_word = "Bored Piling.*"
pileCap_word = "Pile Cap"
pier_pierH_word = "WBS.*Pier & Pier Heads"
precast_word = "SPAN.*"

## NOTE: P0 only exists in P6 DB for precast

## 1. Bored Piles:----
## Filter 
y = read.xlsx(MLTable, sheet=1)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")
id=which(str_detect(y$PierNumber,piles_word))
y1 = y[id,]

## Keep only pier numbers
y1$PierNumber = gsub("Bored Piling -","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = toupper(y1$PierNumber)
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT01-","MT01-0",y1$PierNumber)
y1$PierNumber = gsub("ABUT","-ABUT",y1$PierNumber)
y1$PierNumber = gsub("^P","P-",y1$PierNumber)

# P-158, P-169. Add manually P-158, P-158NB, P-158SB
id=which(str_detect(y1$PierNumber,"P-158|P-169"))

temp = data.frame()
for(i in seq(id)){
  d = y1[id,]
  center = d$PierNumber[i]
  nb = paste(center,"NB",sep = "")
  sb = paste(center,"SB",sep = "")
  d2 = data.frame(ID=d$ID[i],PierNumber=c(center,nb,sb),duration="",start="",finish=d$finish[i])
  temp = rbind(temp, d2)
}

y1 = rbind(y1,temp)
y1 = y1[-id,]

## Add CP and Type
y1$CP = "N-01"
y1$Type = 1
n01_piles = y1

## 2. Pile Cap:----
## Filter 
pileCap_word = "^\\Pile Cap\\b"

y = read.xlsx(MLTable, sheet=1)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")
id=grep(pileCap_word,y$PierNumber) ## Exact match
y1 = y[id,]

## Clean 
y1$PierNumber = str_trim(y1$PierNumber, side="both") ## Remove any space before and after
y1$PierNumber = toupper(y1$PierNumber)
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

y1$PierNumber = gsub("PILECAP-","",y1$PierNumber) # Remove notation

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT01-","MT01-0",y1$PierNumber)
y1$PierNumber = gsub("ABUT","-ABUT",y1$PierNumber)
y1$PierNumber = gsub("^P","P-",y1$PierNumber)

# P-158, P-169. Add manually P-158, P-158NB, P-158SB
id=which(str_detect(y1$PierNumber,"P-158|P-169"))

temp = data.frame()
for(i in seq(id)){
  d = y1[id,]
  center = d$PierNumber[i]
  nb = paste(center,"NB",sep = "")
  sb = paste(center,"SB",sep = "")
  d2 = data.frame(ID=d$ID[i],PierNumber=c(center,nb,sb),duration="",start="",finish=d$finish[i])
  temp = rbind(temp, d2)
}

y1 = rbind(y1,temp)
y1 = y1[-id,]

## Add CP and Type
y1$CP = "N-01"
y1$Type = 2
n01_pileCap = y1


## 2. Pier & Pier Head:----
## Filter 
y = read.xlsx(MLTable, sheet=1)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

# Convert to uppercase to avoid missing misspelled ones
y1 = y
y1$PierNumber = toupper(y1$PierNumber)
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
pierPierHead_word = "^\\PIER&PIERHEAD\\b"

id=grep(pierPierHead_word,y1$PierNumber) ## Exact match
y1 = y1[id,]

## Clean 
y1$PierNumber = str_trim(y1$PierNumber, side="both") ## Remove any space before and after
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

y1$PierNumber = gsub(paste(pierPierHead_word,"-",sep = ""),"",y1$PierNumber) # Remove notation

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT01-","MT01-0",y1$PierNumber)
y1$PierNumber = gsub("ABUT","-ABUT",y1$PierNumber)
y1$PierNumber = gsub("^P","P-",y1$PierNumber)

# P-158, P-169. Add manually P-158, P-158NB, P-158SB
id=which(str_detect(y1$PierNumber,"P-158|P-169"))

temp = data.frame()
for(i in seq(id)){
  d = y1[id,]
  center = d$PierNumber[i]
  nb = paste(center,"NB",sep = "")
  sb = paste(center,"SB",sep = "")
  d2 = data.frame(ID=d$ID[i],PierNumber=c(center,nb,sb),duration="",start="",finish=d$finish[i])
  temp = rbind(temp, d2)
}

y1 = rbind(y1,temp)
y1 = y1[-id,]

## Add CP and Type
y1$CP = "N-01"
y1$Type = 3
n01_pier = y1

# Duplicate for Pier Head
y1$Type = 4
n01_pierHead = y1


## 3. Precast:----
## Filter 
y = read.xlsx(MLTable, sheet=1)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

# Convert to uppercase to avoid missing misspelled ones
## For precast other than MT01
y1 = y
y1$PierNumber = toupper(y1$PierNumber)
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
id=grep(precast_word,y1$PierNumber) ## Exact match

## one span to multipel joint spans, multiple joint spans to one span
y1$ID = toupper(y1$ID)
y1$ID = gsub("[[:space:]]","",y1$ID)
precast_wbs = "WBS:SPAN"
id1=grep(precast_wbs,y1$ID) ## Exact match
y1$PierNumber[id1] = y1$ID[id1]

## Join
y2 = y1[c(id,id1),]

## Clean 
y2$PierNumber = str_trim(y2$PierNumber, side="both") ## Remove any space before and after
y2$PierNumber = gsub("-CENTER|CENTER","",y2$PierNumber)
y2$PierNumber = gsub("[(]CENTER[)]","",y2$PierNumber)
y2$PierNumber = gsub("[(]NORTHBOUND[)]","NB",y2$PierNumber)
y2$PierNumber = gsub("[(]SOUTHBOUND[)]","SB",y2$PierNumber)
y2$PierNumber = gsub("-NORTH","NB",y2$PierNumber)
y2$PierNumber = gsub("-SOUTH","SB",y2$PierNumber)

id=which(str_detect(y2$PierNumber, "[()]"))
y2$PierNumber[id] = gsub("\\([^)]*\\)","",y2$PierNumber[id])

y2$PierNumber = gsub("WBS:SPAN|SPAN","",y2$PierNumber) # Remove notation

id = which(str_detect(y2$PierNumber, "^P|^MT|^DEP"))
y2 = y2[id,]
y2$PierNumber = gsub("MT01-","MT01-0",y2$PierNumber)
y2$PierNumber = gsub("0ABUT","ABUT",y2$PierNumber)
y2$PierNumber = gsub("-NB","NB",y2$PierNumber)
y2$PierNumber = gsub("-SB","SB",y2$PierNumber)

## There are three cases
y2$temp = str_extract_all(y2$PierNumber,"P",simplify=TRUE)
id=which(str_detect(y2$PierNumber,"^MT01.*"))
y2$temp[id] = ""

### 1. P10-P11SB -> P10SB
## easy way is to extract 'P' and count
tempD = data.frame()
for(j in 1:nrow(y2)){
  temp=vector()
  for(i in 1:4){
    temp = c(temp,y2$temp[j,i])
    temp1 = paste0(temp,collapse="")
  }
  d = data.frame(temp=temp1)
  tempD = rbind(tempD, temp1)
}

y2$temp = tempD[[1]]
id=which(str_detect(y2$PierNumber,"SB$|NB$") & y2$temp=="PP")

## Directly edit 
nbsb = str_extract(y2$PierNumber[id],"NB$|SB$")
y2$PierNumber[id] = str_extract(y2$PierNumber[id],"^P\\d+|^P\\d+")
y2$PierNumber[id] = paste(y2$PierNumber[id],nbsb,sep="")

## delete 'P' from temp field
y2$temp[id] = ""

### 2. P158-P159-P160-P161SB -> P158SB, P159SB, P160SB, P161SB
id=which(str_detect(y2$PierNumber,"SB$|NB$") & y2$temp=="PPPP")

temp = data.frame()
for(i in seq(y2$PierNumber[id])){
  testP = y2$PierNumber[id][i]
  pos = str_extract(testP,"NB|SB")
  finish = y2$finish[id][i]
  piers = unlist(str_extract_all(testP,"P\\d+"))
  piers = piers[-length(piers)] # Remove the last pier number, as this is already included
  piers = paste(piers,pos,sep="")
  dataF = data.frame(ID="", PierNumber=piers, duration="", start="", finish=finish, temp="")
  temp = rbind(temp, dataF)
}
y2 = rbind(y2,temp)

## Delete originla rows
y2 = y2[-id,]

## 3. P158-P159-P160-P161 -> P158, P159, P160, P161
id=which(!str_detect(y2$PierNumber,"SB$|NB$") & y2$temp=="PPPP")
y2$PierNumber[id]

temp = data.frame()
for(i in seq(y2$PierNumber[id])){
  testP = y2$PierNumber[id][i]
  finish = y2$finish[id][i]
  piers = unlist(str_extract_all(testP,"P\\d+"))
  piers = piers[-length(piers)] # Remove the last pier number, as this is already included
  dataF = data.frame(ID="", PierNumber=piers, duration="", start="", finish=finish, temp="")
  temp = rbind(temp, dataF)
}
y2 = rbind(y2,temp)

## Delete originla rows
y2 = y2[-id,]

# 4. Fix MT01 precast
id=which(str_detect(y2$PierNumber,"^MT01.*"))
y2$PierNumber[id] = str_extract(y2$PierNumber[id],"^MT\\d+-\\w+|^MT\\d+-\\d+")

## Re-format PierNumber for the ramaining
id=which(str_detect(y2$temp,"P|PP|PPP|PPPP"))
y2$PierNumber[id] = str_extract(y2$PierNumber[id],"P\\d+|P\\d+")

## Delete rows in missing PierNumber
id=which(is.na(y2$PierNumber))
if(length(id)>0){
  y2 = y2[-id,]
}

## 
y2$PierNumber = gsub("^P","P-",y2$PierNumber)

# P-10NB is wrong => P-10
id=which(str_detect(y2$PierNumber,"P-10SB|P-10NB"))
y2$PierNumber[id] = "P-10"

## Add CP and Type
y2$CP = "N-01"
y2$Type = 5
y2$duration = as.numeric(y2$duration)
y2=y2[,-which(colnames(y2)=="temp")]
n01_precast = y2

## 4. Compile All Components:----
cp01_VIA = rbind(n01_piles, n01_pileCap, n01_pier, n01_pierHead, n01_precast)

## Fix finish 
### Row for '27-Sep-22' format
id=which(str_detect(cp01_VIA$finish,"^\\d+-\\w+-\\d+"))
dates = str_extract(cp01_VIA$finish[id],"^\\d+-\\w+-\\d+")
dates = as.Date(cp01_VIA$finish[id], format= "%d-%b-%y" )

### Row for number date
cp01_VIA$finish = as.numeric(cp01_VIA$finish)
cp01_VIA$finish = as.Date(cp01_VIA$finish, origin = "1899-12-30")
cp01_VIA$finish = as.Date(cp01_VIA$finish, format="%m/%d/%y %H:%M:%S")

## Add back dates
cp01_VIA$finish[id] = dates

## Remove space for ID
cp01_VIA$ID = gsub("[[:space:]]","",cp01_VIA$ID)
id = which(!str_detect(cp01_VIA$ID,"^N01"))
cp01_VIA$ID[id] = ""

## PR7-120(ST). P6 uses P0, but civil uses PR7-120(ST). P0 => PR7-120
id = which(str_detect(cp01_VIA$PierNumber,"P-0NB"))
cp01_VIA$PierNumber[id] = "PR7-120"

id = which(str_detect(cp01_VIA$PierNumber,"P-0SB"))
cp01_VIA$PierNumber[id] = "PR7-120ST"

## Remove redundant fields
id = which(str_detect(colnames(cp01_VIA),"duration|start"))
cp01_VIA = cp01_VIA[,-id]



##########################################################################
# N-02:----
piles_word = ".*EXECUTION PILES PIER.*"
pileCap_word = ".*EXECUTION PILE CAP.*"
pier_word = ".*EXECUTION PIER COLUMN.*"
pierHead_word = ".*EXECUTION PIER HEAD*"
precast_word = ".*PC SEGMENT ERECTION*"

## 1. Bored Piles:----
## Filter 
y = read.xlsx(MLTable, sheet=2)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,piles_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PILES PIER","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT02-","MT02-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## Add CP and Type
y1$CP = "N-02"
y1$Type = 1
n02_piles = y1
head(n02_piles)

## 2. Pile Cap:----
## Filter 
y = read.xlsx(MLTable, sheet=2)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pileCap_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PILE CAP","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber,".*]$"))
if (length(id) > 0) {
  y1 = y1[-id,]
}

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT02-","MT02-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## Add CP and Type
y1$CP = "N-02"
y1$Type = 2
n02_pileCap = y1


## 3. Pier:----
## Filter 
y = read.xlsx(MLTable, sheet=2)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pier_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PIER COLUMN","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber,".*]$"))
if (length(id) > 0) {
  y1 = y1[-id,]
}


id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT02-","MT02-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## Add CP and Type
y1$CP = "N-02"
y1$Type = 3
n02_pier = y1

## 4. Pier Head:----
## Filter 
y = read.xlsx(MLTable, sheet=2)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pierHead_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PIER HEAD","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber,".*]$"))
if (length(id) > 0) {
  y1 = y1[-id,]
}


id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("MT02-","MT02-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## Add CP and Type
y1$CP = "N-02"
y1$Type = 4
n02_pierHead = y1

## 5. Precast:----
## Filter 
y = read.xlsx(MLTable, sheet=2)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,precast_word))
y1 = y1[id,]


## Keep only pier numbers
y1$PierNumber = gsub(".*PC SEGMENT ERECTION LG\\d+:","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]

y1$PierNumber = gsub("LEARNINGCURVE","",y1$PierNumber)


## pattern: 'P-529 - P-528' => 'P-528'
##          'P-771 - P-772' => 'P-771'
y1$temp1 = str_extract(y1$PierNumber,"^P-\\d+") # frist pier number
y1$temp1 = gsub("P-","",y1$temp1)
y1$temp1 = as.numeric(y1$temp1)

y1$temp2 = str_extract(y1$PierNumber,"P-\\d+$|P-\\d+?SB$|P-\\d+?NB$") # last pier 
y1$temp2 = gsub("SB|NB","",y1$temp2)
y1$temp2 = gsub("P-","",y1$temp2)
y1$temp2 = as.numeric(y1$temp2)

y1$temp3 = str_extract(y1$PierNumber,"SB$|NB$")

y1$temp4 = ""
for(i in 1:nrow(y1)){
  if(y1$temp1[i] > y1$temp2[i]){
    y1$temp4[i] = y1$temp2[i]
    
  } else if(y1$temp1[i] < y1$temp2[i]) {
    y1$temp4[i] = y1$temp1[i]
  }
}

## P-661N, P-661S, P-662N, P-662S (Cantilever): Ignore these
## the following pierNumbers will be missed so manually create 
## Use 'temp2'
# 457, 458, 459 => 456 (temp2)
# 467, 468, 469 => 466 (temp2)
# 595, 596 => 594 (temp2)
# 609, 610 => 608 (temp2)
# 631, 632, 633 => 630 (temp2)
# 660, 661, 662 => 659 (temp2)
# 695, 696, 697 => 694 (temp2)

mPiers = c(456,466,594,608,630,659,694,695)

temp = data.frame()
for(i in mPiers){
  if(i == 456){
    d = y1[which(y1$temp2==i),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=457:459)
    temp = rbind(temp, d1)
    
  } else if(i == 466){
    d = y1[which(y1$temp2==i),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=467:469)
    temp = rbind(temp, d1)
  
  } else if(i == 594){
    d = y1[which(y1$temp2==i),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=595:596)
    temp = rbind(temp, d1)
  
  } else if(i == 608){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=609:610)
    temp = rbind(temp, d1)
  
  } else if(i == 630){
    d = y1[which(y1$temp2==i),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=631:633)
    temp = rbind(temp, d1)
    
  } else if(i == 659){
    d = y1[which(y1$temp2==i),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=660:662)
    temp = rbind(temp, d1)
    
  } else if(i == 694){
    d = y1[which(y1$temp2==i),]
    d1 = data.frame(ID=d$ID,PierNumber="",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="",temp4=695:697)
    temp = rbind(temp, d1)
  
  } else if(i == 695){ # use temp1 and temp3
    d = y1[which(y1$temp1==i),]
    d1 = data.frame(ID=d$ID,PierNumber="P-695A",duration="",start="",finish=d$finish,temp1="",temp2="",temp3="A",temp4=695)
    temp = rbind(temp, d1)
}
}

# rbind
y1 = rbind(y1, temp)

# Now fix PierNumber based on this
y1$PierNumber = paste("P-",y1$temp4,sep="")
id=which(!is.na(y1$temp3))
y1$PierNumber[id] = paste("P-",y1$temp4[id],y1$temp3[id],sep="")

# Delete temp fields
id=which(str_detect(colnames(y1),"^temp"))
y1 = y1[,-id]

# for MT02-01, Mt02-ABUT
y$ID = gsub("[[:space:]]","",y$ID)
id=which(str_detect(y$ID, "MT02-01toMT02-ABUT"))
y2 = y[id,]
y2$ID = gsub(".*[(]","",y2$ID)
y2$ID = gsub("[)]$","",y2$ID)

piers = c("MT02-01","MT02-ABUT")
temp = data.frame()
for(i in seq(piers)){
  d = data.frame(ID="",PierNumber=piers[i],duration="",start="",finish=y2$finish[1])
  temp = rbind(temp, d)
}

y1 = rbind(y1, temp)

## Add CP and Type
y1$CP = "N-02"
y1$Type = 5
n02_precast = y1

## 6. Compile All Components:----
cp02_VIA = rbind(n02_piles, n02_pileCap, n02_pier, n02_pierHead, n02_precast)

## Fix finish 
### Row for '27-Sep-22' format
id=which(str_detect(cp02_VIA$finish,"^\\d+-\\w+-\\d+"))
dates = str_extract(cp02_VIA$finish[id],"^\\d+-\\w+-\\d+")
dates = as.Date(cp02_VIA$finish[id], format= "%d-%b-%y" )

### Row for number date
cp02_VIA$finish = as.numeric(cp02_VIA$finish)
cp02_VIA$finish = as.Date(cp02_VIA$finish, origin = "1899-12-30")
cp02_VIA$finish = as.Date(cp02_VIA$finish, format="%m/%d/%y %H:%M:%S")

## Add back dates
cp02_VIA$finish[id] = dates

## Remove space for ID
cp02_VIA$ID = gsub("[[:space:]]","",cp02_VIA$ID)

## Remove redundant fields
id = which(str_detect(colnames(cp02_VIA),"duration|start"))
cp02_VIA = cp02_VIA[,-id]




##########################################################################
# N-03:----
piles_word = ".*BORED PILING.*"
pileCap_word = ".*CONSTRUCT FOOTINGS.*"
pier_word = ".*CONSTRUCT LOWER COLUMN.*"
pierHead_word = ".*CONSTRUCT UPPER COLUMN*"
precast_word = ".*PRE-CASTING OF SPAN*"

## 1. Bored Piles:----
## Filter 
y = read.xlsx(MLTable, sheet=3)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,piles_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub("BORED PILING.*","",y1$PierNumber)
y1$PierNumber = str_extract(y1$PierNumber,"P-\\d+\\w|P-MT03.*")


### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("P-MT03","MT03",y1$PierNumber)
y1$PierNumber = gsub("MT03-","MT03-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## S = SB, N = NB, M = delete
y1$PierNumber = gsub("S$", "SB", y1$PierNumber)
y1$PierNumber = gsub("N$", "NB", y1$PierNumber)
y1$PierNumber = gsub("M$", "NB", y1$PierNumber)

## Add CP and Type
y1$CP = "N-03"
y1$Type = 1
n03_piles = y1

## 2. Pile Cap:----
## Filter 
y = read.xlsx(MLTable, sheet=3)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pileCap_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub("CONSTRUCT FOOTINGS.*","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)
y1$PierNumber = str_extract(y1$PierNumber,"P-.*")
y1$PierNumber = gsub("BALANCED.*","",y1$PierNumber)

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("P-MT03","MT03",y1$PierNumber)
y1$PierNumber = gsub("MT03-","MT03-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## S = SB, N = NB, M = delete
y1$PierNumber = gsub("S$", "SB", y1$PierNumber)
y1$PierNumber = gsub("N$", "NB", y1$PierNumber)
y1$PierNumber = gsub("M$", "NB", y1$PierNumber)

## Add CP and Type
y1$CP = "N-03"
y1$Type = 2
n03_pileCap = y1

## 3. Pier:----
## Filter 
y = read.xlsx(MLTable, sheet=3)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pier_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub("CONSTRUCT LOWER COLUMN.*","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)
y1$PierNumber = str_extract(y1$PierNumber,"P-.*")
y1$PierNumber = gsub("BALANCED.*","",y1$PierNumber)

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("P-MT03","MT03",y1$PierNumber)
y1$PierNumber = gsub("MT03-","MT03-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## S = SB, N = NB, M = delete
y1$PierNumber = gsub("S$", "SB", y1$PierNumber)
y1$PierNumber = gsub("N$", "NB", y1$PierNumber)
y1$PierNumber = gsub("M$", "NB", y1$PierNumber)

## Add CP and Type
y1$CP = "N-03"
y1$Type = 3
n03_pier = y1


## 4. PierHead:----
## Filter 
y = read.xlsx(MLTable, sheet=3)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pierHead_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub("CONSTRUCT UPPER COLUMN.*","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)
y1$PierNumber = str_extract(y1$PierNumber,"P-.*")
y1$PierNumber = gsub("BALANCED.*","",y1$PierNumber)

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("P-MT03","MT03",y1$PierNumber)
y1$PierNumber = gsub("MT03-","MT03-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## S = SB, N = NB, M = delete
y1$PierNumber = gsub("S$", "SB", y1$PierNumber)
y1$PierNumber = gsub("N$", "NB", y1$PierNumber)
y1$PierNumber = gsub("M$", "NB", y1$PierNumber)

## Add CP and Type
y1$CP = "N-03"
y1$Type = 4
n03_pierHead = y1


## 5. Precast:----

#***********
# MT03-01, MT03-02, MT03-ABUT do not exist in P6
#***********

## Filter 
y = read.xlsx(MLTable, sheet=3)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,precast_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*PRE-CASTING OF SPAN","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)
y1$PierNumber = gsub("PRE-CASTINGOFSPAN","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

y1 = y1[id,]
y1$PierNumber = gsub("P-MT03","MT03",y1$PierNumber)
y1$PierNumber = gsub("MT03-","MT03-0",y1$PierNumber)
y1$PierNumber = gsub("0ABUT","ABUT",y1$PierNumber)

## S = SB, N = NB, M = delete
y1$PierNumber = gsub("S$", "SB", y1$PierNumber)
y1$PierNumber = gsub("N$", "NB", y1$PierNumber)
y1$PierNumber = gsub("M$", "", y1$PierNumber)
y1$PierNumber = gsub("TO", "-", y1$PierNumber)

## Separate numbers
y1$temp1 = str_extract(y1$PierNumber,"^\\d+\\w+") # start: precast
y1$temp2 = str_extract(y1$PierNumber,"\\d+\\w+$") # end of: precast
y1$PierNumber = paste("P-",y1$temp1,sep = "")

y1$temp3 = str_extract(y1$PierNumber,"NB$|SB$")

## Case 2: 877 - 878 (User the first number as PierNumber)
y1$temp1 = as.numeric(y1$temp1) # IGnore warning
y1$temp2 = as.numeric(y1$temp2) # Ignore warning
y1$temp5 = y1$temp1 - y1$temp2

id=which(y1$temp5 <= -2)

temp = data.frame()
for(i in seq(nrow(y1[id,]))){
  d = y1[id,][i,]
  d1 = data.frame(ID=d$ID,PierNumber=d$PierNumber,duration=d$duration,start=d$start,finish=d$finish,
                  temp1=0,temp2=0,temp3=d$temp3,temp5=as.numeric(d$temp1:(d$temp2-1)))
  d1$PierNumber=paste("P-",d1$temp5,sep = "")
  temp=rbind(temp,d1)
}
str(temp)

## Delete the processed rows before rbinding the 'temp', compiled dataframe
y1 = y1[-id,] # delete temp1 and temp2 for binding with temp

# Rbind temp to original
y1 = rbind(y1,temp)


##################
## P-661N, P-661S, P-662N, P-662S (Cantilever): Ignore these
## the following pierNumbers will be missed so manually create 
## Use 'temp2'
# 1021 => 1021 (temp2)
# 1048, 1049 => 1048 (temp2)
# 1050 => 1052 (temp2)
# 1091, 1092, 1093 => 1091 (temp2)
# 1106, 1107 => 1106 (temp2)
# 1120, 1121 => 1120 (temp2)
# 1130 => 1130 (temp2)
# 1142 => 1142 (temp2)
# 888, 889, 890 => 888 (temp2)
# 968 => 966 (temp2)
# 974, 975, 976 => 974 (temp2)
# 989, 990, 992 => 989 (temp2)


mPiers = c(1021,1048,1052,1091,1106,1120,1130,1142,888,966,974,989)

temp = data.frame()
for(i in mPiers){
  if(i == 1021){
    d = y1[which(y1$temp2==i),]
    addPier = 1021
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 1048){
    d = y1[which(y1$temp2==i),]
    addPier = 1048:1049
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 1052){
    d = y1[which(y1$temp2==i),]
    addPier = 1050
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 1091){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 1091:1093
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 1106){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 1106:1107
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    
  } else if(i == 1120){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 1120
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 1130){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 1130
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 1142){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 1142
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 888){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 888:890
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 966){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 968
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 974){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = 974:976
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
    
  } else if(i == 989){
    d = y1[which(y1$temp2==i & is.na(y1$temp3)),]
    addPier = c(989,990,992)
    d1 = data.frame(ID=d$ID,PierNumber=paste("P-",addPier,sep=""),duration=0,start="",finish=d$finish)
    temp = rbind(temp, d1)
}
}
y1=y1[,-which(str_detect(colnames(y1),"^temp"))]
y1 = rbind(y1, temp)

## Add CP and Type
y1$CP = "N-03"
y1$Type = 5
n03_precast = y1

## 6. Compile All Components:----
cp03_VIA = rbind(n03_piles, n03_pileCap, n03_pier, n03_pierHead, n03_precast)

## Fix finish 
### Row for '27-Sep-22' format
id=which(str_detect(cp03_VIA$finish,"^\\d+-\\w+-\\d+"))
dates = str_extract(cp03_VIA$finish[id],"^\\d+-\\w+-\\d+")
dates = as.Date(cp03_VIA$finish[id], format= "%d-%b-%y" )

### Row for number date
cp03_VIA$finish = as.numeric(cp03_VIA$finish)
cp03_VIA$finish = as.Date(cp03_VIA$finish, origin = "1899-12-30")
cp03_VIA$finish = as.Date(cp03_VIA$finish, format="%m/%d/%y %H:%M:%S")

## Add back dates
cp03_VIA$finish[id] = dates

## Remove space for ID
cp03_VIA$ID = gsub("[[:space:]]","",cp03_VIA$ID)

## Remove redundant fields
id = which(str_detect(colnames(cp03_VIA),"duration|start"))
cp03_VIA = cp03_VIA[,-id]



############################################################################
# N-04:----
b = "C:/Users/eiji.LAPTOP-KSD9P6CP/Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled"
gis = read.xlsx(file.path(b,"Viaduct_MasterList.xlsx"))

piles_word = ".*EXECUTION PILES PIER.*"
pileCap_word = ".*EXECUTION PILE CAP.*"
pier_word = ".*EXECUTION PIER COLUMN.*"
pierHead_word = ".*EXECUTION PAD AND BEARING*"
precast_word = "CASTING DIAPHRAGM AND SLAB*"

## 1. Bored Piles:----
## Filter 
y = read.xlsx(MLTable, sheet=4)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,piles_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PILES PIER","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("@.*","",y1$PierNumber)
y1$PierNumber = gsub("N$","NB",y1$PierNumber)
y1$PierNumber = gsub("S$","SB",y1$PierNumber)

## Add CP and Type
y1$CP = "N-04"
y1$Type = 1
n04_piles = y1

## 2. Pile Cap:----
## Filter 
y = read.xlsx(MLTable, sheet=4)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pileCap_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PILE CAP","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber,".*]$"))
if (length(id) > 0) {
  y1 = y1[-id,]
}

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("@.*","",y1$PierNumber)
y1$PierNumber = gsub("N$","NB",y1$PierNumber)
y1$PierNumber = gsub("S$","SB",y1$PierNumber)

## Add CP and Type
y1$CP = "N-04"
y1$Type = 2
n04_pileCap = y1


## 3. Pier:----
## Filter 
y = read.xlsx(MLTable, sheet=4)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pier_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub(".*EXECUTION PIER COLUMN","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber,".*]$"))
if (length(id) > 0) {
  y1 = y1[-id,]
}


id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]
y1$PierNumber = gsub("@.*","",y1$PierNumber)
y1$PierNumber = gsub("N$","NB",y1$PierNumber)
y1$PierNumber = gsub("S$","SB",y1$PierNumber)

## Add CP and Type
y1$CP = "N-04"
y1$Type = 3
n04_pier = y1

## 4. Pier Head:----
## Filter 
y = read.xlsx(MLTable, sheet=4)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,pierHead_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub("EXECUTION PAD AND BEARING","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber,".*]$"))
if (length(id) > 0) {
  y1 = y1[-id,]
}

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

id = which(str_detect(y1$PierNumber, "^P|^MT|^DEP"))
y1 = y1[id,]

y1$PierNumber = gsub("@.*","",y1$PierNumber)
y1$PierNumber = gsub("N$","NB",y1$PierNumber)
y1$PierNumber = gsub("S$","SB",y1$PierNumber)

## Add CP and Type
y1$CP = "N-04"
y1$Type = 4
n04_pierHead = y1

## 5. Precast:----
## Filter 
y = read.xlsx(MLTable, sheet=4)
colnames(y) = c("ID", "PierNumber", "duration", "start", "finish")

y1 = y
y1$PierNumber = toupper(y1$PierNumber)
id=which(str_detect(y1$PierNumber,precast_word))
y1 = y1[id,]

## Keep only pier numbers
y1$PierNumber = gsub("CASTING DIAPHRAGM AND SLAB","",y1$PierNumber)

### make sure that first letter starts with 'P' or 'MT'
y1$PierNumber = str_trim(y1$PierNumber, side="both")
y1$PierNumber = gsub("[[:space:]]","",y1$PierNumber)
y1$PierNumber = gsub("CENTER","",y1$PierNumber)

id=which(str_detect(y1$PierNumber, "[()]"))
y1$PierNumber[id] = gsub("\\([^)]*\\)","",y1$PierNumber[id])

y1$PierNumber = gsub("^-","",y1$PierNumber)
y1$PierNumber = gsub("@.*","",y1$PierNumber)
y1$PierNumber = gsub("N$","-NB",y1$PierNumber)
y1$PierNumber = gsub("S$","-SB",y1$PierNumber)
y1$ID = gsub("[[:space:]]","",y1$ID)

###### Re-format precast PierNumber to our format
x = gis[which(gis$CP=="N-04" & gis$Type==5),]
x$finish = as.numeric(NA)

# P-1192NB - DEP01-ABUT => P-1192NB - P-1205NB for GIS
PierNumber = paste("P-",1192:1205,"NB",sep="")

## Find ID
id = which(str_detect(y1$PierNumber,"ABUT-NB$"))
ID = y1$ID[id]
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish


# P-1192SB - DEP01-ABUT => P-1192SB - P-1205SB for GIS
PierNumber = paste("P-",1192:1205,"SB",sep="")

## Find ID
id = which(str_detect(y1$PierNumber,"ABUT-SB$"))
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish

# P-1192 - P-1206 => P-1192 - P-1205 for GIS
PierNumber = paste("^","P-",1192:1205,"$",sep="") # get exact word without NB/SB

## Find ID
id = which(str_detect(y1$PierNumber,".*-P1206$"))
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish


# P1192A - PLK25 => P-1182 - P2206 for GIS
## We need to split the pier numbers
### P-1181 - P-1191
PierNumber = paste("^","P-",1181:1191,"$",sep="")

## P-1191A
PierNumber = c(PierNumber, "^P-1191A$")

## P-2192 - P-2206
PierNumber = c(PierNumber, paste("^","P-",2192:2206,"$",sep="")) # get exact word without NB/SB

## Find ID
id = which(str_detect(y1$PierNumber,".*PLK25$"))
ID = y1$ID[id]
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish


# P1182-P1172 => P-1170 P-1181 for GIS
PierNumber = paste("^","P-",1170:1181,"$",sep="") # get exact word without NB/SB

## Find ID
id = which(str_detect(y1$PierNumber,".*-P1172$"))
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish


# P-1169 - P-1143 => P-1143 - P-1169 for GIS
PierNumber = paste("^","P-",1143:1169,"$",sep="") # get exact word without NB/SB

## Find ID
id = which(str_detect(y1$PierNumber,".*-P1143$"))
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish


# PLK01-PLK24 (old) => P2143 - P2154
PierNumber = paste("^","P-",2143:2154,"$",sep="") # get exact word without NB/SB

## Find ID
id = which(str_detect(y1$PierNumber,".*-PLK24$"))
finish = y1$finish[id]

## Join ID to corresponding PierNumber in x
id = which(str_detect(x$PierNumber,paste0(PierNumber,collapse="|")))
x$ID[id] = ID
x$finish[id] = finish


# For compilation purpose with other CPs, re-create data.frame
d = x[which((!is.na(x$ID))),]
y1 = data.frame(ID=d$ID,PierNumber=d$PierNumber,duration="",start=as.numeric(NA),finish=d$finish)

## Add CP and Type
y1$CP = "N-04"
y1$Type = 5
n04_precast = y1

## 6. Compile All Components:----
cp04_VIA = rbind(n04_piles, n04_pileCap, n04_pier, n04_pierHead, n04_precast)

## Fix finish 
### Row for '27-Sep-22' format
id=which(str_detect(cp04_VIA$finish,"^\\d+-\\w+-\\d+"))
dates = str_extract(cp04_VIA$finish[id],"^\\d+-\\w+-\\d+")
dates = as.Date(cp04_VIA$finish[id], format= "%d-%b-%y" )

### Row for number date
cp04_VIA$finish = as.numeric(cp04_VIA$finish)
cp04_VIA$finish = as.Date(cp04_VIA$finish, origin = "1899-12-30")
cp04_VIA$finish = as.Date(cp04_VIA$finish, format="%m/%d/%y %H:%M:%S")

## Add back dates
cp04_VIA$finish[id] = dates

## Remove space for ID
cp04_VIA$ID = gsub("[[:space:]]","",cp04_VIA$ID)

## Remove redundant fields
id = which(str_detect(colnames(cp04_VIA),"duration|start"))
cp04_VIA = cp04_VIA[,-id]





########################################################
#### COMPILE ALL CPs #########
########################################################
x = rbind(cp01_VIA,cp02_VIA,cp03_VIA,cp04_VIA)

## Final correction, 'P211' => 'P-211'
id = which(str_detect(x$PierNumber,"^P\\d+"))
x$PierNumber[id] = gsub("P","P-",x$PierNumber[id])

write.xlsx(x,file.path(b,"N2_Viaduct_P6DB.xlsx"))

# Add to viaduct masterlist
ml = read.xlsx(file.path(b, "Viaduct_MasterList.xlsx"))
head(x)
head(ml)

xx = left_join(ml,x,by=c("CP","Type","PierNumber"))

## Identify mismatched pierNumber (i.e., not exist in x)
id=which(is.na(xx$finish))
xx1 = xx[id,]

checkPier = "P-992";xx[which(xx$PierNumber==checkPier),]

xx1[which(xx1$CP=="N-03"),]
unique(xx1$PierNumber)

## 
x[which(x$PierNumber=="MT01-04"),]
ml[which(ml$PierNumber=="MT01-04"),]
