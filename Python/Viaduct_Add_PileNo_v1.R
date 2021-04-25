tool_exec=function(in_params,out_params){
library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)

  
workSpace=in_params[[1]] # parameter: workspace
tableL=in_params[[2]]
tableM=in_params[[3]] # parameter: Table View, multiple values (ensure that csf files have station names: new master list)
tableR=in_params[[4]] # Joine Field to be used between Old and New Master List tables
result=out_params[[1]] # parameter: Feature Layer
  
t = bind_rows(tableL, tableM)
x = bind_rows(x, tableR)



a = choose.dir()
wd = setwd(a)

b = file.choose()
x = read.xlsx(b) # master list 

x$ID = ""

temp = data.frame()

for(pno in unique(x$PileNo)){
  x1 = x[x$PileNo == pno,]
  for(k in unique(x1$PierNumber)){
    x1 = x[x$PierNumber==k,]
    x1$ID = 1:nrow(x1)
    temp = bind_rows(temp, x1)
  }
}

# Concatenate
temp$ID1 = paste(temp$CP, temp$PierNumber, "-", temp$PileNo, temp$ID, sep = "")

# Export
write.xlsx(temp,file.path(dir,paste("Viaduct_Assign_ID_", unique(temp$CP),"_",Sys.Date(),".xlsx",sep="")))

# Export result table:
arc.write(result,temp,overwrite=TRUE)

# return result
return(out_params)


}