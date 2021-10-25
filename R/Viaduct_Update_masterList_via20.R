tool_exec=function(in_params,out_params){

#
# This R script is used to update a masterlist for monitoring construction status of viaduct in N2
# Specifically, it imports a table provided by Civil Team and is re-structured for joining to 3d model in ArcGIS Pro
#

library(openxlsx)
library(dplyr)

wd = in_params[[1]] # working directory
inTable=in_params[[2]] # Progress table derived from Civil Team
MLTable = in_params[[2]] # masterlist table to be joined to viaduct multipatch layer
  
result=out_params[[1]] # parameter: Feature Layer

#wd = setwd("C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled")

# Choose source excel file provided by Civil Team
#C:\Users\oc3512\Dropbox\01-Railway\02-NSCR-Ex\01-N2\03-During-Construction\02-Civil\03-Viaduct\01-Masterlist\01-fromCivil
#a = file.choose()

# Get sheet name
sheetN = getSheetNames(inTable)


boredPile = grep("Bored Pile|bored pile|Bored pile|bored Pile", sheetN)

x = read.xlsx(inTable, sheet=boredPile, startRow = 10)

# Select only Activity (pierNumber), Remarks
ids = which(colnames(x)=="Activity" | colnames(x)=="Remarks")
x1 = x[!is.na(x$Activity),ids]

x1$Status1 = 1 # default is "To be Constructed"
colnames(x1)[1] = "nPierNumber"

# Remove hyphen from pierNumbe
x1$nPierNumber = gsub("-","",x1$nPierNumber)

uniqueRem = unique(x1$Remarks)

x1$Status1[x1$Remarks=="Casted"] = 4 # Bored Pile completed
x1$Status1[x1$Remarks=="Inprogress"] = 2 # Uncer Construction
x1$Status1[x1$Remarks==grep("Incomplete Casting*",uniqueRem,value = TRUE)] = 3 # Delayed

# Merge to Viaduct Masterlist:----
#MLdir = "C:/Users/oc3512/Dropbox/01-Railway/02-NSCR-Ex/01-N2/03-During-Construction/02-Civil/03-Viaduct/01-Masterlist/02-Compiled"
#MLfile = "N2_Viaduct_MasterList.xlsx"

# Read the masterlist:----
y = read.xlsx(MLTable)


# Join new status to Viaduct masterlist
yx = left_join(y,x1,by="nPierNumber")

# NA for status = 1 (To be COnstructed)
yx$Status1.y[is.na(yx$Status1.y)] = 1
delField = which(colnames(yx)=="Status1.x" | colnames(yx)=="Remarks")
yx = yx[,-delField]

# Change Status name
statusField = which(colnames(yx)=="Status1.y")
colnames(yx)[statusField] = "Status1"

#
yx$Updated = as.Date(yx$Updated, origin = "1899-12-30")
yx$Updated = as.Date(yx$Updated, format="%m/%d/%y %H:%M:%S")

# overwrite masterlist
write.xlsx(yx, MLTable, row.names=FALSE,overwrite = TRUE)


# Output
arc.write(result, yx, overwrite = TRUE)
return(out_params)



# PENDING
# Pile cap:----
pileCap = grep("PileCap|pile cap|Pilecap|pileCap", sheetN)

}
