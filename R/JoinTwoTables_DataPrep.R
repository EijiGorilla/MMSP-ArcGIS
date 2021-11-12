library(openxlsx)
library(dplyr)
library(stringr)


z=choose.dir()
setwd(z)
getwd()

# Excel master list
a=file.choose()
x=read.xlsx(a)

# Attribute table in ArcGIS Pro
b=file.choose()
y=read.xlsx(b)

# Check data type of LotID and make sure that LotID data types are both "chr"
str(x)
str(y)

head(x)
length(unique(x$PIER))
x[duplicated(x$PIER),]


# In case you need to keep excel Date format
colnames(y)[11] = "HandOverDate" 
y$HandOverDate = as.Date(y$HandOverDate, origin = "1899-12-30")
y$HandOverDate = as.Date(y$HandOverDate, format="%m/%d/%y %H:%M:%S")


# Join two tables
xy = left_join(x,y,by="LotID")
xy = left_join(x,y,by="uniqueID")
xy = left_join(x,y,by="PIER")


# Export a joined table
write.xlsx(xy,"xy_merged_XXXX.xlsx",row.names=FALSE,overwrite = TRUE)
