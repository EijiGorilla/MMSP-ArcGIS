tool_exec=function(in_params,out_params){
  library(openxlsx)
  library(dplyr)
  # This R code assigns pierID to each Viaduct component
  # The result table is exported to workspace as file geodatabase table
  # for joining to the multipatch layer
  
  workSpace=in_params[[1]] # parameter: workspace
  table=in_params[[2]]
  
  #table = file.choose()
  
  result=out_params[[1]] # parameter: Feature Layer
  
  x = read.csv(table, stringsAsFactors = FALSE)
  x = x[,-1]

x$pierHead = as.numeric(NA)

j = 0
for(i in 1:nrow(x)) {
  #print(i)
  
  if(x[i, 4] == 2){
    j = j +1
    x$pierHead[i] = j
  } else {
    x$pierHead[i] = j
  }
}

print("Success")
# Replace empty cell with some other values for simplicity
x$PierNumber[x$PierNumber == "" | is.na(x$PierNumber)] = "xxxx"

n = unique(x$pierHead)
temp = data.frame()
for(i in n){
  x1 = x[x$pierHead == i,]
  id = unique(x1$PierNumber)

  if(sum("xxxx" %in% id) >= 1 & length(id) == 2 ){
    id = id[-which("xxxx" %in% id)]
    x1$PierNumber[x1$pierHead == i] = id
  } else if (sum("xxxx" %in% id) == 0){
    x1$PierNumber[x1$pierHead == i] = id
  } else if ("xxxx" %in% id){ # just NA
    x1$PierNumber[x1$pierHead == i] = NA
  } else {
    x1$PierNumber[x1$pierHead == i] = id
  }
  
  temp = bind_rows(temp, x1)
}

print("Success")

temp$ID = as.character(temp$ID)
temp$PileNo = as.character(temp$PileNo)

write.xlsx(temp, "Assigned_pierIDs.xlsx",overwrite=TRUE)

print("Success")

arc.write(result, temp, overwrite = TRUE)


print("Success")
# return result
return(out_params)

}

