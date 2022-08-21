# This R script converts excel master list: N2_workable_areas_xxx to
# GIS format. 
# Data Provider: Tina (RAP Team Leader)
# Data type: Excel
# Note: this table is original source of "N2_Pier masterlist" from Wesley (RAP Team)
# Wesley converts this table to his own excel sheet for the GIS Team.

library(openxlsx)
library(dplyr)
library(stringr)
library(fs)
library(lubridate)
library(tidyr)


z = choose.dir()
setwd(z)

a = file.choose()
x = read.xlsx(a)

x1 = x[, c(2,9:11,13:15)]
colnames(x1) = c("Pier","Available", "December2022", "December2022_1", "February2023", "March2023", "April2023")
x1 = x1[-c(1,nrow(x1),nrow(x1)-1),]

# check unique values for each column
colName = colnames(x1)
for(i in colName){
  t = unique(x1[,i])
  print(t)
}

# convert character to numeric
for(i in 2:ncol(x1)){
  x1[[i]] = as.numeric(x1[[i]])

}

# Add "P-" except with "MT"
id = which(str_detect(x1$Pier,"^MT"))
idd = 1:nrow(x1)
id = idd[-id]

x1$Pier[id] = paste("P-",x1$Pier[id],sep = "")

#
x2 = x1

# if Pier is AVAILABLE, simply add old date "2022-01-01"
x2$AccessDate = as.Date("2022-01-01")

# Empty rows with not "AVAILABLE"
id = which(is.na(x2$Available))
x2$AccessDate[id] = NA

dateCol = c("2022-12-31",
             "2022-12-10",
             "2023-02-28",
             "2023-03-31",
             "2023-04-30")

# fill in AccessDate based on colnames
for(i in seq(colName)) {
  if(i == 3){ # "2022-12-31"
    id = which(x2[[i]] == 1)
    x2$AccessDate[id] = dateCol[1]

  } else if(i == 4) { # "2022-12-10???
    id = which(x2[[i]] == 1)
    x2$AccessDate[id] = dateCol[2]
    
  } else if(i == 5) { # 2023-02-28
    id = which(x2[[i]] == 1)
    x2$AccessDate[id] = dateCol[3]
    
  } else if(i == 6) {# 2023-03-31
    id = which(x2[[i]] == 1)
    x2$AccessDate[id] = dateCol[4]
    
  } else if(i == 7) {
    id = which(x2[[i]] == 1)
    x2$AccessDate[id] = dateCol[5]
  }
  
}

id = which(is.na(x2$AccessDate))

# Delete all space in Pier
x2$Pier = gsub("[[:space:]]","",x2$Pier)

# all capital letter
x2$Pier = toupper(x2$Pier)

# MT01-2 (X) -> MT01-02
head(x2)
id = which(str_detect(x2$Pier,"^MT"))

# first, extract the last digit
for(i in 1:length(id)){
  j = id[i]
  lastd = str_extract(x2$Pier[j],"-[0-9]$") # e.g., "-2" of "MT02-2"
  main = gsub(lastd,"",x2$Pier[j]) # e.g., MT02
  num = gsub("-","",lastd) #e.g., "2"
  x2$Pier[j] = paste(main,"-0",num,sep = "") # e.g., "MT02-02"
}

# finally only keep Pier and AccessDate
x2 = x2[,c(1,ncol(x2))]


### Join this with N2_pier masterlist from GIS
b = file.choose()
y = read.xlsx(b)

