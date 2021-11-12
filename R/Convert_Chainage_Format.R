# This R code populates chainage distance in the following format: 56+100, 56+200,... from the format of
# 56K, 1, 2, 3, 4, 5, 6, 7, 8, 9, 57K, 1, 2, 3....

library(tidyr)
library(openxlsx)
library(dplyr)

z = file.choose()
setwd(z)
a=file.choose()
x = read.xlsx(a)

# If a value has "K", return 1 else 0
## Make sure 
  test = x$Name

test1 = grepl("K",test)
test1 = ifelse(test1=="TRUE",1,0)

# Bind the above to the original table
x$n = test1

head(x)

# Create a new column.
## If the returned value is 1 above, return  
x$n1 = NA
x$n1 = as.character(x$n1)
x$n1 = ifelse(x$n==1,x$Name,NA)
x$n1 = gsub("Km","",x$n1)

# Re-order
x1 = x
xx = x1 %>% fill(n1)
head(xx,50)
tail(xx,50)
#xx = x1[order(-x1$iid),]


xx$n2 = ifelse(xx$n==1,"000",paste(xx$Name,"00",sep = ""))
xx$n3 = paste(xx$n1,"+",xx$n2,sep = "")
head(xx,50)

# Sort back to the original
#xx1 = xx1[order(xx1$iid),]


# 
#xx2 = xx1[,c(1,4,8)]

write.xlsx(xx,"Chainage_converted.xlsx",row.names=FALSE)

