##
# This script joins GIS data to master list excel table based on LotID and
# returns observations that do not match.

library(rgdal)
library(sf)
library(dplyr)
library(openxlsx)

# 1. Read data
## 1.1. Master List Excel Table
a="C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi\\Land_Acquisition\\Master List\\PAB-MASTERLIST\\MasterList_Compiled.xlsx"
x=read.xlsx(a,sheet=1)

## 1.1.1 Remove all white space in the LotID
x$LotID=gsub(" ","",x$LotID)

## 1.2. GIS Data
library(arcgisbinding)
arc.check_product()

wd = setwd("C:\\Users\\oc3512\\OneDrive - Oriental Consultants Global JV\\Documents\\ArcGIS\\Projects\\NSCR-EX_envi")
b=file.path(wd,"NSCR-Backup.gdb")
y=grep("Parcellary_Merge",ogrListLayers(b),value=TRUE)
d=arc.open(file.path(b,y))
dd=arc.select(d,fields = "*")

g=data.frame(dd)

## 1.2.1. Remove all white space in the LotID
g$LotID=gsub(" ","",g$LotID)

# 2. Full Join (Note that no matching records of GIS data are left out at the bottom of the joined table)
joinT = full_join(x,g, by="LotID") # Join g (GIS data) to x (Master List Excel Table)

# 3. Identify observations that returned no matched records.
head(joinT,50)
unmatch = joinT[is.na(joinT$OBJECTID),]

# 4. Export
write.xlsx(joinT,file=file.path(wd,"Land_Acquisition","Master List","PAB-MASTERLIST","Joined_Table_GIS_MasterT.xlsx"),colNames = TRUE)
