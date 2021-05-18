library(openxlsx)
library(dplyr)

#####################################
# This R script compiles tables from Google spreadsheet available from DOTr.
# https://docs.google.com/spreadsheets/d/1zoQVPsWHfgZT1Q_Scz2lnkQKafeyI9c79yAbMEnBuno/edit#gid=743362036
# It adds four types of land acquisition processes to the table
# 1. Status3 (OtB for serving, Otb Accepted...) (I coded as below in the Domain of ArcGIS Pro)
#     1.OTB for Accepted
#     2.OTB for Serving
#     3.Pending Compilation of Documents
#     4.Pending Appraisal
#     5. Pending Documents from Other Agencies
#     6. Pending OTB Reply behond 30 Days (Cooperative)
#     7. Pending OTB Reply within 30 Days
#
# 2. StatusNVS (For submission to Legal Pass....)(I coded as below in the Domain of ArcGIS Pro)
#     1. For Submission to Legal Pass
#     2. Pending Legal Pass
#     3. Legal Pass Issued
#
# 3. StatusNVS2 (Payment Processing) (I coded as below in the Domain of ArcGIS Pro)
#     1. For Submission to Budget of MORS
#     2. With Budget for Oblication
#     3. With Acctg for CAF Issuance
#     4. For DOTr Signing
#     5. For Notarization
#     6. With GSD for CTC'ing
#     7. For Submission to CS of DV
#     8. DV with CS
#     9. Paid/Check Issued
#
# 4. StatusNVS3 (simplified version of the above three): (I coded as below in the Domain of ArcGIS Pro)
#    1.Paid,
#    2.Ongoing Payment Processing,
#    3.Ongoing Leagal Pass, 
#    4. Ongoing Appraisal/Offer to Buy, and
#    5. For Expro
# The script finally generates a compiled master list table used to join with GIS feature layers.

# 0. Choose working directory
z = choose.dir()
wd = setwd(z)

# 1. Read Tables
## nvs table is a xlsx table copied from Google sheet provided by DOTr
a = file.choose()
nvs = read.xlsx(a)

## expro table is a xlsx table copied from Google sheet provided by DOTr
b = file.choose()
expro =read.xlsx(b)

c = file.choose()
x = read.xlsx(c) # master list 

Status3Names = c("OTB Accepted",
                 "OTB for Serving",
                 "Pending Compilation of Documents",
                 "Pending Appraisal",
                 "Pending Documents from Other Agencies",
                 "Pending OTB Reply beyond 30 days (Cooperative)",
                 "Pending OTB Reply within 30 days",
                 "For Expropriation")

# 2. Add Field Names
### 2.1 NVS Table
# Change field names of Dates that are used to add processes (names are too long)
colnames(nvs)
dateNames = c("P", "Q", "R", "S", "TT", "U", "V", "W", "X", "Y", "Z",
              "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK")
# P: "Date of Initial Submission for Legal Pass", AK: "Actual Date of Check Issuance"
colnames(nvs)[c(16:37)]=dateNames

# Add processes:
## StatusNVS
nvs$StatusNVS = 0
nvs$StatusNVS[nvs$Status==Status3Names[1] & nvs$P>1 & is.na(nvs$Q)]=1
nvs$StatusNVS[nvs$Q>1 & nvs$R>1 & is.na(nvs$S)]=2
nvs$StatusNVS[nvs$S>1]=3

## Status3
nvs$Status3 = 0

nvs$Status3[nvs$Status==Status3Names[1]]=1
nvs$Status3[nvs$Status==Status3Names[2]]=2
nvs$Status3[nvs$Status==Status3Names[3]]=3
nvs$Status3[nvs$Status==Status3Names[4]]=4
nvs$Status3[nvs$Status==Status3Names[5]]=5
nvs$Status3[nvs$Status==Status3Names[6]]=6
nvs$Status3[nvs$Status==Status3Names[7]]=7
nvs$Status3[nvs$Status==Status3Names[8]]=8

## StatusNVS2
nvs$StatusNVS2 = 0
nvs$StatusNVS2[nvs$TT>1 & is.na(nvs$U)]=1
nvs$StatusNVS2[nvs$U>1 & nvs$V>1 & is.na(nvs$W)]=2
nvs$StatusNVS2[nvs$W>1 & is.na(nvs$AA)]=3
nvs$StatusNVS2[nvs$AC>1 & is.na(nvs$AD) & is.na(nvs$AE)]=4
nvs$StatusNVS2[nvs$AE>1 & is.na(nvs$AG)]=5
nvs$StatusNVS2[nvs$AG>1 & nvs$AH>1 & is.na(nvs$AI)]=7
nvs$StatusNVS2[nvs$AI>1 & is.na(nvs$AK)]=8
nvs$StatusNVS2[nvs$AK>1]=9


## StatusNVS3
nvs$StatusNVS3 = 0
nvs$StatusNVS3[nvs$Status==Status3Names[1] & nvs$S>1 & is.na(nvs$AK)]=2
nvs$StatusNVS3[nvs$Status==Status3Names[1] & is.na(nvs$S)]=3
nvs$StatusNVS3[nvs$Status==Status3Names[2] | nvs$Status==Status3Names[3] |
                 nvs$Status==Status3Names[4] | nvs$Status==Status3Names[5] |
                 nvs$Status==Status3Names[6] | nvs$Status==Status3Names[7] |
                 nvs$Status==Status3Names[8]]=4
nvs$StatusNVS3[nvs$AK>1]=1 # Make sure that Paid (1) must come at last

## Keep only necessary fields
nvs = nvs[,c("CN", "Station","Priority3", "StatusNVS", "Status3", "StatusNVS2", "StatusNVS3")]
colnames(nvs)
## FOr counting the total number of target lots for NVS
nvs$count_nvs = 1

### 2.2. Expro Table
expro$count_nvs = 1
expro$ForExpro = 1

# 3. Join NVS table with a Master List table
## 3.1. Delete NVS Status fields from a master list table
x = x[,-c(which(colnames(x)=="Priority3"):ncol(x))] # Delete from "StatusNVS" to the end of fields

## 3.2 Join
x_nvs = left_join(x, nvs, by=c("CN", "Station"))

# 4. Join expro table to x_nvs table
xy_nvs_expro = left_join(x_nvs, expro, by=c("CN", "Station"))


# 5. Update tables
## 5.1. Convert N/A to 0
xy_nvs_expro$StatusNVS[is.na(xy_nvs_expro$StatusNVS)]=0
xy_nvs_expro$Status3[is.na(xy_nvs_expro$Status3)]=0
xy_nvs_expro$StatusNVS2[is.na(xy_nvs_expro$StatusNVS2)]=0
xy_nvs_expro$StatusNVS3[is.na(xy_nvs_expro$StatusNVS3)]=0
xy_nvs_expro$ForExpro[is.na(xy_nvs_expro$ForExpro)]=0

## Priority for NVS
colnames(xy_nvs_expro)
xy_nvs_expro$Priority3[is.na(xy_nvs_expro$Priority3)]=0
xy_nvs_expro$Priority3_expro[is.na(xy_nvs_expro$Priority3_expro)]=0

## Count NVS
xy_nvs_expro$count_nvs.x[is.na(xy_nvs_expro$count_nvs.x)]=0
xy_nvs_expro$count_nvs.y[is.na(xy_nvs_expro$count_nvs.y)]=0

## 5.2. Merge Priority and Count NVS with Expro 
xy_nvs_expro$Priority3 = xy_nvs_expro$Priority3 + xy_nvs_expro$Priority3_expro
xy_nvs_expro$count_nvs = xy_nvs_expro$count_nvs.x + xy_nvs_expro$count_nvs.y
colnames(xy_nvs_expro)

## 5.3 Add StatusNVS3 for For Expro
xy_nvs_expro$StatusNVS3[xy_nvs_expro$ForExpro==1]=5 # Add For Expro process to statusNVS3

# Delete supplementary count and priority fields
xy_nvs_expro = xy_nvs_expro[,-c(which(colnames(xy_nvs_expro)=="count_nvs.x"):which(colnames(xy_nvs_expro)=="count_nvs.y"))]

# 6. Write a new master list
write.xlsx(xy_nvs_expro,file.path(wd,paste("test_",Sys.Date(), ".xlsx", sep="")),row.names=FALSE)

table(xy_nvs_expro$StatusNVS)
table(xy_nvs_expro$Status3)
table(xy_nvs_expro$StatusNVS2)
table(xy_nvs_expro$StatusNVS3)




######################################################################
## Practice script where you may need for temporary operation
# matser list (sde)


z=choose.dir()
wd=setwd(z)

# Excel master list
a=file.choose()
x=read.xlsx(a)

# Attribute table in ArcGIS Pro
b=file.choose()

y=read.xlsx(b)
head(y)

y$id = 1:nrow(y)
head(y)
y$HandOverDate = as.Date(y$HandOverDate, origin = "1899-12-30")
y$HandOverDate = as.Date(y$HandOverDate, format="%m/%d/%y %H:%M:%S")


head(x)
xy = left_join(x,y,by="LotID")

id = unique(y$StrucID)
test = data.frame(StrucID = id, n=1:length(id))

xy = full_join(x,y,by="StrucID")
write.xlsx(xy,"xy_merged_XXXX.xlsx",row.names=FALSE)





y$nidy = 1:nrow(y)
x$nidx = 1:nrow(x)

# Find observations that are present in x (excel master list) and missing in y (ArcGIS Pro)
# !! Look for missing 'nidy'
xy=full_join(x,y,by=("LotID"))
xy=full_join(x,y,by=("StrucID"))


# Find observations that are present in y(arcgis pro) and missing in x (excel masterlist)
# !! Look for missing 'nidx'
yx=full_join(y,x,by=("LotID"))
yx=full_join(y,x,by=("StrucID"))

# Extract observations that exist in x but missing in y
xy = xy[is.na(xy$nid),]
write.xlsx(xy,"xy_merged_demolitionM.xlsx",row.names = FALSE)


write.xlsx(yx,"yx_merged_missing_in_x.xlsx",row.names = FALSE)

write.xlsx(xy, "00-xy_merged_StrucID_missing_in_y.xlsx", row.names=FALSE)
#########################################s
write.xlsx(xy,"delete.xlsx",row.names = FALSE)
str(y)

y$LotID = as.character(y$LotID)
# Join 
head(x)
head(y)

str(x);str(y)

x=filter(x,Municipality=="Malolos"|Municipality=="San Fernando")
y=filter(y,Municipality=="Malolos"|Municipality=="San Fernando")
?filter
head(x)

#  table[,i]=as.Date(table[,i],format="%m/%d/%Y")
#  table[,i]=as.POSIXct(table[,i],format="%m/%d/%y %H:%M:%S")
# use the following date conversion if necessary


y$ActualDateofInitialSubmissionforLegalPass = as.Date(y$ActualDateofInitialSubmissionforLegalPass, origin = "1899-12-30")
y$ActualDateofInitialSubmissionforLegalPass = as.Date(y$ActualDateofInitialSubmissionforLegalPass, format="%m/%d/%y %H:%M:%S")

y$ActualDateofClearedLegalPass = as.Date(y$ActualDateofClearedLegalPass, origin = "1899-12-30")
y$ActualDateofClearedLegalPass = as.Date(y$ActualDateofClearedLegalPass, format="%m/%d/%y %H:%M:%S")

?left_join


xy=left_join(x,y,by="Id")
xy=left_join(x,y,by=c("CN", "Station"))

head(xy)
str(xy)
# Convert NA to 0 for the following status
xy$StatusNVS.y[is.na(xy$StatusNVS.y)]=0
xy$Status3.y[is.na(xy$Status3.y)]=0
xy$StatusNVS2.y[is.na(xy$StatusNVS2.y)]=0
xy$StatusNVS3.y[is.na(xy$StatusNVS3.y)]=0
xy$ForExpro[is.na(xy$ForExpro)]=0
xy$count_NVS.y[is.na(xy$count_NVS.y)]=0 # count total target lots numbers

xy$count_NVS.y[xy$ForExpro==1]=1 # count total target lots numbers
xy$StatusNVS3.y[xy$ForExpro==1]=5 # Add For Expro process to statusNVS3


xy$Priority3.y[is.na(xy$Priority3.y)]=0
xy$Priority3_expro[is.na(xy$Priority3_expro)]=0
unique(xy$Priority3.y)
unique(xy$Priority3)

xy$Priority3 = xy$Priority3.y + xy$Priority3_expro
unique(xy$Priority3)
       
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Time slice/v8/Joined.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/Envi/Parcellary Map/20200706/merged_with_MasterList_v2.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/temp.xlsx",row.names=FALSE)
write.xlsx(xy, "xy_merged_corrected_comparison.xlsx",row.names = FALSE)
write.xlsx(xy, "temp.xlsx",row.names = FALSE)

##########
xy=left_join(x,y,by=("Id"))

?left_join

?full_join
xy=full_join(x,y,by=c("Municipality", "LotID"))
xy=left_join(x,y,by="LotID")
xy=full_join(x,y,by="LotID")

head(x)

#xy=filter(xy,Municipality.x==c("Malolos","San Fernando"))
unique(xy$Municipality.x)

write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/02-xy_merged.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/03-xy_merged_with_Expro.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Desktop/04-xy_merged_with_MasterList.xlsx",row.names=FALSE)
write.xlsx(xy,"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/01-Environment/N2/Land_Acquisition/Master List/PAB-MASTERLIST/Calumpit/New_to_Old_20200716.xlsx",row.names=FALSE)
write.xlsx(xy,"xy_merged.xlsx",row.names = FALSE)
write.xlsx(xy,"new_xy_handover.xlsx",row.names = FALSE)

####
colnames(xy)
xy1 = filter(xy, count_NAS==1)


t=table(xy1$StatusNVS3.y)
sum(t)

a=file.choose()
x=read.xlsx(a)

colnames(x)
head(x)

cp = unique(x$CP)

temp = data.frame()
for (i in cp){
  #i=cp[1]
  x1 = x[x$CP == i,]
  nn = 1:nrow(x1)
  x1$Id1 = paste(i,nn,sep = "")
  x1$Id1 = gsub("-","",x1$Id1)
  
  temp = bind_rows(temp,x1)
  
}

str(temp)
head(temp)
write.xlsx(temp,"tree_compiled_20201202.xlsx",row.names = FALSE)


head(xy)
xy$comCN = cbind(xy$CN.x, xy$CN.y)
head(xy)
