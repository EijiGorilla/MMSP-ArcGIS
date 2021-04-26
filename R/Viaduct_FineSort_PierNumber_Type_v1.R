tool_exec=function(in_params,out_params){
# This R script sorts observations by PierNumber and Type

library(openxlsx)
library(dplyr)
library(stringr)
library(reshape2)

#################################################################################################
# #inFeature="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/002-ENV&S.gdb/Status20190913_1"
#
#
#################################################################################################
  
workSpace=in_params[[1]] # parameter: workspace
inTable=in_params[[2]] # parameter: table View (csv)

result=out_params[[1]] # parameter: Feature Layer

#inTable = file.choose()
x = read.csv(inTable, stringsAsFactors = FALSE)
x = x[, -1]

listPier = unique(x$PierNumber)
listType = unique(x$Type)

temp = data.frame()

for(p in listPier) {
  x1 = x[x$PierNumber == p,]
  x1$idd[x1$Type == 1] = 1
  x1$idd[x1$Type == 2] = 2
  x1$idd[x1$Type == 3] = 3
  x1$idd[x1$Type == 4] = 4
  x1$idd[x1$Type == 5] = 5
 
  x1 = x1[order(x1$idd),]
  
  temp = bind_rows(temp, x1)

}

# Add sequential number
temp$idd = 1:nrow(temp)


# Join temp to original feature layer
temp = temp[,c("idd", "tempid")]
finalT = left_join(x,temp,by="tempid")

# Sort

#finalT = temp1[order(temp1$idd),]

# Export result table:
arc.write(result,finalT,overwrite=TRUE)

# return result
return(out_params)
}
