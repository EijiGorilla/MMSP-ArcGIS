library(openxlsx)
library(dplyr)
library(stringr)


z=choose.dir()
setwd(z)
getwd()

# Excel master list
a=file.choose()
x=read.xlsx(a)

head(x)
tbm = unique(x$Line)

x = x[!is.na(x$status),]
x$seq = 0
temp = data.frame()
for(i in tbm){
  xx = x[x$Line==i,]
  xx$seq = 1:nrow(xx)
  temp = bind_rows(temp,xx)
  
}
write.xlsx(temp,"check.xlsx")

x$ID0[!x$ID0 %in% x$ID1]


id = which(is.na(x$COMPLETED))
xx = x[-id,]
write.xlsx(x,"kingpost_NAS_id.xlsx",row.names=FALSE,overwrite=TRUE)

# Attribute table in ArcGIS Pro
b=file.choose()
y=read.xlsx(b)

str(x)
str(y)
x[!x$ID %in% y$ID,]

xy = left_join(x,y,by="ID")
write.xlsx(xy,"merged.xlsx")

# Check data type of LotID and make sure that LotID data types are both "chr"
str(x)
str(y)

head(x)
length(unique(x$PIER))
x[duplicated(x$PIER),]

head(x)
unique(x$FamilyType)

# In case you need to keep excel Date format
colnames(y)[11] = "HandOverDate" 
y$HandOverDate = as.Date(y$HandOverDate, origin = "1899-12-30")
y$HandOverDate = as.Date(y$HandOverDate, format="%m/%d/%y %H:%M:%S")

y$start_date = as.Date(y$start_date,origin="1899-12-30")
y$start_date = as.Date(y$start_date,format="%m/%d/%y %H:%M:%S")
y$end_date = as.Date(y$end_date,origin="1899-12-30")
y$end_date = as.Date(y$end_date,format="%m/%d/%y %H:%M:%S")

# Join two tables
xy = left_join(x,y,by="LotID")
xy = left_join(x,y,by="uniqueID")
xy = left_join(x,y,by="PIER")

xy$start_date = as.Date(xy$start_date,origin="1899-12-30")
xy$start_date = as.Date(xy$start_date,format="%m/%d/%xy %H:%M:%S")
xy$end_date = as.Date(xy$end_date,origin="1899-12-30")
xy$end_date = as.Date(xy$end_date,format="%m/%d/%xy %H:%M:%S")

xy$updated = "2021-12-10"
xy$updated = as.Date(xy$updated,origin="1899-12-30")
xy$updated = as.Date(xy$updated,format="%m/%d/%xy %H:%M:%S")
head(xy)
# Export a joined table
write.xlsx(xy,"xy_merged_XXXX.xlsx",row.names=FALSE,overwrite = TRUE)
