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

#  table[,i]=as.Date(table[,i],format="%m/%d/%Y")
#  table[,i]=as.POSIXct(table[,i],format="%m/%d/%y %H:%M:%S")
# use the following date conversion if necessary
y$ActualDateofInitialSubmissionforLegalPass = as.Date(y$ActualDateofInitialSubmissionforLegalPass, origin = "1899-12-30")
y$ActualDateofInitialSubmissionforLegalPass = as.Date(y$ActualDateofInitialSubmissionforLegalPass, format="%m/%d/%y %H:%M:%S")

y$ActualDateofClearedLegalPass = as.Date(y$ActualDateofClearedLegalPass, origin = "1899-12-30")
y$ActualDateofClearedLegalPass = as.Date(y$ActualDateofClearedLegalPass, format="%m/%d/%y %H:%M:%S")




xy=left_join(x,y,by="CN")
xy=left_join(x,y,by=c("CN", "Station"))
 
str(xy)
       
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Time slice/v8/Joined.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Parcellary Map/20200706/merged_with_MasterList.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/temp.xlsx",row.names=FALSE)


##########
xy=left_join(x,y,by=c("Municipality", "LotID"))
?left_join

xy=full_join(x,y,by=c("Municipality", "LotID"))

write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Minalin_testJoin.xlsx",row.names=FALSE)
