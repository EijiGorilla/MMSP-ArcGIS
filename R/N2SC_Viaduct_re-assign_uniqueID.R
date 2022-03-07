## This R code re-assigns uniqueID for Viaduct 
## after revising or adding revised viaduct 3d models to the source attribut table
## This code runs:
## 1. Extract dataset for each CP
## 2. Extract dataset for unique PierNumber
## 3. Sort the dataset by Type
## 4. Assign sequential numbers
## 5. Use the max number assigned in the step 4 and use the max as a starting number for the next

## BACKGROUND
### When new 3d models are added to the source attribute table, uniqueID is corrupted.
### Nonetheless, uniqueID must be re-assigned, as it is critical for re-structuring the table

# Keep the following variables when the source attributet able is copied from Pro
# PierNumber	Type	CP	nPierNumber	pp	pp2	temp


library(openxlsx)
library(dplyr)
library(fs)

path = path_home()
wd = file.path(path,"Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled")

setwd(wd)


a=file.choose()

x = read.xlsx(a)
head(x)
x$idd2 = 0

cp_id = unique(x$CP)
pier_id = unique(x$PierNumber)

temp = data.frame()
n = 0

for(i in c(cp_id)){
  xx = x[which(x$CP==i),]
  
  for(j in unique(xx$PierNumber)){
    n = n + 1
    xxx = xx[which(xx$PierNumber==j),]
    xxx = xxx[order(xxx$Type),]
    
      xxx$idd2 = 1:nrow(xxx)
      max_n = nrow(xxx)

    temp = rbind(temp,xxx)
    
  }
}
head(temp,20)

temp$pp2 = as.character(temp$pp2)
id = which(temp$pp < 10 & !is.na(temp$pp))

temp$pp2[id] = paste("0",temp$pp2[id],sep = "")

# 
temp$idd2 = 1:nrow(temp) 

write.xlsx(temp,"N2_Viaduct_uniqueID_reassigned.xlsx")

###
head(x)
x$pp2 = as.character(x$pp2)
id = which(x$pp < 10 & !is.na(x$pp))

x$pp2[id] = paste("0",x$pp2[id],sep = "")
write.xlsx(x,"temp_for_pp2.xlsx")
