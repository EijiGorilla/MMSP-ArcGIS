# This R code populates chainage distance in the following format: 56+100, 56+200,... from the format of
# 56K, 1, 2, 3, 4, 5, 6, 7, 8, 9, 57K, 1, 2, 3....


library(tidyr)
library(openxlsx)
library(dplyr)

z = choose.dir()
wd = setwd(z)
a=file.choose()
x = read.xlsx(a)

# If a value has "K", return 1 else 0
test = x$Name
test1 = grepl("K",test)
test1 = ifelse(test1=="TRUE",1,0)

# Bind the above to the original table
x$n = test1

# Create a new column.
## If the returned value is 1 above, return  
x$n1 = NA
x$n1 = as.character(x$n1)
x$n1 = ifelse(x$n==1,x$Name,NA)
x$n1 = gsub("K","",x$n1)

# Re-order
x1 = x
xx = x1[order(-x1$Id),]

# use 'fill' of tidyr
xx1 = xx %>% fill(n1)
head(xx1,n=20)

xx1$n2 = ifelse(xx1$n==1,"000",paste(xx1$Name,"00",sep = ""))
head(xx1)

head(xx1,n=50)
xx1$n3 = paste(xx1$n1,"+",xx1$n2,sep = "")

# Sort back to the original
xx1 = xx1[order(xx1$Id),]

# 
xx2 = xx1[,c(1,4,8)]

write.xlsx(xx2,"SC_Chainage_converted.xlsx",row.names=FALSE)
