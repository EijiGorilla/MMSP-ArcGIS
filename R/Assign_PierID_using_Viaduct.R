library(openxlsx)
library(dplyr)
library(stringr)

wd = choose.dir()
setwd(wd)

# Choose SC viaduct Excel masterlist exported from GIS attribute table
a = file.choose()
x = read.xlsx(a)

# Get unique pier No
piers = unique(x$PierNumber)

x$pier_id = NA

for(i in piers) {
  # Subset for each pier no
  id = which(x$PierNumber == i)
  x1 = x[id,]
  
  # count the number pier
  n_pier = length(which(x1$Type == 3))
  
  # If the number of piers = 1, return 1, 
  # else if the number piers = 2, return 2, 
  # else if the number piers = 3, return 3
  if(n_pier == 1) {
    x$pier_id[id] = 1 
  } else if (n_pier == 2) {
    x$pier_id[id] = 2
  } else if (n_pier == 3) {
    x$pier_id[id] = 3
  }
  
}
write.xlsx(x, "temp_SC_Viaduct_for_pierNoPoint.xlsx")


