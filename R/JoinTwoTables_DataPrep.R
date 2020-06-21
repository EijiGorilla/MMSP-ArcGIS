library(openxlsx)
library(dplyr)

# matser list (sde)
a=file.choose()
x=read.xlsx(a)

# new list (local)
b=file.choose()
y=read.xlsx(b)


# Join 
head(x)
head(y)

xy=left_join(x,y,by=c("Station", "CN"))

xy=left_join(x,y,by="Id")
        
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Time slice/v6/delete.xlsx",row.names=FALSE)


##########
xy=left_join(x,y,by=c("Municipality", "LotID"))
?left_join

xy=full_join(x,y,by=c("Municipality", "LotID"))

write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Minalin_testJoin.xlsx",row.names=FALSE)
