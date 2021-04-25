tool_exec=function(in_params,out_params){
library(openxlsx)
library(dplyr)
library(stringr)
library(reshape2)

  
workSpace=in_params[[1]] # parameter: workspace
tableL=in_params[[2]]
tableM=in_params[[3]] # parameter: Table View, multiple values (ensure that csf files have station names: new master list)
tableR=in_params[[4]] # Joine Field to be used between Old and New Master List tables
outFolder = in_params[[5]]

resultL=out_params[[1]] # parameter: Feature Layer
resultM=out_params[[2]] # parameter: Feature Layer
resultR=out_params[[3]] # parameter: Feature Layer


# Read tables as csv
tL = read.csv(tableL, stringsAsFactors = FALSE)
tM = read.csv(tableM, stringsAsFactors = FALSE)
tR = read.csv(tableR, stringsAsFactors = FALSE)

# Bind Rows of all tables
t = bind_rows(tL, tM)
x = bind_rows(t, tR)

x$id_temp = ""

# Delete the first column
x = x[, -1]

tempL = data.frame()
tempM = data.frame()
tempR = data.frame()

for(pno in unique(x$PileNo)){
  x1 = x[x$PileNo == pno,]

  for(k in unique(x1$PierNumber)){
    
    x2 = x1[x1$PierNumber==k,]
    x2$id_temp = 1:nrow(x2)

    if(pno == "L"){
      tempL = bind_rows(tempL, x2)
    } else {
    if(pno == "M"){
      tempM = bind_rows(tempM, x2)
    } else {
      tempR = bind_rows(tempR, x2)
    }
    }
  }
}

# Concatenate
tempL$ID = paste(tempL$CP, "-", tempL$PierNumber, "-", "PILE_", tempL$PileNo,tempL$id_temp, sep = "")
tempM$ID = paste(tempM$CP, "-", tempM$PierNumber, "-", "PILE_", tempM$PileNo, tempM$id_temp, sep = "")
tempR$ID = paste(tempR$CP, "-", tempR$PierNumber, "-", "PILE_", tempR$PileNo, tempR$id_temp, sep = "")

# Export
write.xlsx(tempL,file.path(outFolder, paste("Viaduct_Assign_ID_Piles_L_", unique(tempL$CP),"_",Sys.Date(),".xlsx",sep="")))
write.xlsx(tempM,file.path(outFolder, paste("Viaduct_Assign_ID_Piles_M_", unique(tempM$CP),"_",Sys.Date(),".xlsx",sep="")))
write.xlsx(tempR,file.path(outFolder, paste("Viaduct_Assign_ID_Piles_R_", unique(tempR$CP),"_",Sys.Date(),".xlsx",sep="")))

# Export result table:
arc.write(resultL,tempL,overwrite=TRUE)
arc.write(resultM,tempM,overwrite=TRUE)
arc.write(resultR,tempR,overwrite=TRUE)

# return result
return(out_params)


}