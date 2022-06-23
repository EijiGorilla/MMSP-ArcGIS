library(openxlsx)
library(dplyr)
library(stringr)

# A. Before you entering information in the GIS attribute table;----
wd = "C:\\Users\\eiji.LAPTOP-KSD9P6CP\\Dropbox\\01-Railway\\temp"
setwd(wd)

### THe code below:
### 1. Read station-structure attribute table copied from ArcGIS Pro
a = file.choose()
x = read.xlsx(a)

head(x)
### 2. Extract unique names for each level

blevel = unique(x$BldgLevel_Desc)
category = unique(x$Category)
family = unique(x$Family)
famType = unique(x$FamilyType)

temp = data.frame()

### 3. Check NA
for(i in blevel){
  print(i)
}
for(i in category){
  print(i)
}
for(i in family){
  print(i)
}
for(i in famType){
  print(i)
}


### 4. Create a cascading table sorted by: BldgLevel_Desc, Category, Family, and FamilyType

for(i in blevel){
  #i=blevel[2]
  if(is.na(i)){
    i="nna"
    x1 = x[which(is.na(x$BldgLevel_Desc)),]
  } else {
    x1 = x[which(x$BldgLevel_Desc==i),]
  }

  category1 = unique(x1$Category)
  
  for(j in category1){
    #j = category1[4]
    x2 = x1[which(x1$Category==j),]
    family1 = unique(x2$Family)
    
    for(k in family1){
     # k=family1[1]
      x3 = x2[which(x2$Family==k),]
      famType1 = unique(x3$FamilyType)
      
      for(l in famType1){
       # l = famType1[1]
        
        x4 = x3[which(x3$FamilyType==l),]
        x5 = distinct(x4)
        temp = rbind(temp,x5)
      }
    }
  }
}
xx = temp

### 5. We need to extract only distinct rows, as the above table has overlapping observations.


### 6. Sort by BldgLevel_Desc, Category, Family, FamilyType
xx = xx[order(xx$BldgLevel_Desc,xx$Category,xx$Family,xx$FamilyType),]
##write.xlsx(xx,"N2_station_structure_concatenated_table.xlsx")

xx
head(xx)
### 7. Reformat the table for using 'Selected By Attributes' in ArcGIS Pro
temp_n = data.frame()

blevel_n = unique(xx$BldgLevel_Desc)

for(i in blevel_n){
  #i = blevel_n[8]
  
  xx1 = xx[which(xx$BldgLevel_Desc==i),]
  category1_n = unique(xx1$Category)
  
  for(k in category1_n){
    #k = category1_n[1]
    xx2 = xx1[which(xx1$Category==k),]
    
    family_n = unique(xx2$Family)
    
    for(l in family_n){
      #l = family_n[1]
      xx3 = xx2[which(xx2$Family==l),]
      
      # unique FamilyType
      famType_n = unique(xx3$FamilyType)
      
      # Delete FamilyTYpe
      xx4 = xx3[,-which(colnames(xx3)=="FamilyType")]
      
      #
      xx4$FamilyType = paste0(famType_n,collapse="','")
      
      #
      xx4 = distinct(xx4)
      
      #
      temp_n = rbind(temp_n,xx4)

    }
  }

  
}

### 8. Extract only distinct rows
xxx = temp_n
colnames(xxx)


bldg_id = which(colnames(xxx)=="BldgLevel_Desc")
categ_id = which(colnames(xxx)=="Category")
fam_id = which(colnames(xxx)=="Family")
famType_id = which(colnames(xxx)=="FamilyType")

xxx = xxx[,c(bldg_id,categ_id,fam_id,famType_id)]

head(xxx)
### 9. Export the table

write.xlsx(xxx,"N2_DEP_CMV_conca_FamilyType.xlsx")



### 10. Sort by StructuralLevel
head(xxx)


#############################################################################
# B. Aftr you entered information in the GIS attribute table;----
## This command is used to get a table sorted by structureLevel, BldgeLevel_Desc, Category, Family, and Family Type
## This table may be used to document or record for the future.

a = file.choose()
x = read.xlsx(a)

head(x)
### 2. Extract unique names for each level

strucLevel = unique(x$StructureLevel)
blevel = unique(x$BldgLevel_Desc)
category = unique(x$Category)
family = unique(x$Family)
famType = unique(x$FamilyType)

temp = data.frame()
for(b in strucLevel){
  x0 = x[which(x$StructureLevel==b),]

for(i in blevel){
  #i=blevel[2]
  if(is.na(i)){
    i="nna"
    x1 = x0[which(is.na(x$BldgLevel_Desc)),]
  } else {
    x1 = x0[which(x$BldgLevel_Desc==i),]
  }
  
  category1 = unique(x1$Category)
  
  for(j in category1){
    #j = category1[4]
    x2 = x1[which(x1$Category==j),]
    family1 = unique(x2$Family)
    
    for(k in family1){
      # k=family1[1]
      x3 = x2[which(x2$Family==k),]
      famType1 = unique(x3$FamilyType)
      
      for(l in famType1){
        # l = famType1[1]
        
        x4 = x3[which(x3$FamilyType==l),]
        x5 = distinct(x4)
        temp = rbind(temp,x5)
      }
    }
  }
}
}
xx = temp

# Sort
xx = xx[order(xx$StructureLevel,xx$BldgLevel_Desc,xx$Category,xx$Family,xx$FamilyType),]

# Reformat the table
### 7. Reformat the table for using 'Selected By Attributes' in ArcGIS Pro
temp_n = data.frame()

strucLevel_n = unique(xx$StructureLevel)

for(b in strucLevel_n){
  xx1 = xx[which(xx$StructureLevel==b),]
  blevel_n = unique(xx$BldgLevel_Desc)

for(i in blevel_n){
  #i = blevel_n[8]
  
  xx1 = xx[which(xx$BldgLevel_Desc==i),]
  category1_n = unique(xx1$Category)
  
  for(k in category1_n){
    #k = category1_n[1]
    xx2 = xx1[which(xx1$Category==k),]
    
    family_n = unique(xx2$Family)
    
    for(l in family_n){
      #l = family_n[1]
      xx3 = xx2[which(xx2$Family==l),]
      
      # unique FamilyType
      famType_n = unique(xx3$FamilyType)
      
      # Delete FamilyTYpe
      xx4 = xx3[,-which(colnames(xx3)=="FamilyType")]
      
      #
      xx4$FamilyType = paste0(famType_n,collapse="','")
      
      #
      xx4 = distinct(xx4)
      
      #
      temp_n = rbind(temp_n,xx4)
      
    }
  }
  
  
}
}
### 8. Extract only distinct rows
xxx = temp_n
colnames(xxx)

strucLevel_id = which(colnames(xxx)=="StructureLevel")
bldg_id = which(colnames(xxx)=="BldgLevel_Desc")
categ_id = which(colnames(xxx)=="Category")
fam_id = which(colnames(xxx)=="Family")
famType_id = which(colnames(xxx)=="FamilyType")

xxx = xxx[,c(strucLevel_id,bldg_id,categ_id,fam_id,famType_id)]

head(xxx,10)
xxx
### 9. Export the table

write.xlsx(xxx,"N2_DEP_LRS_After_Enter.xlsx")


