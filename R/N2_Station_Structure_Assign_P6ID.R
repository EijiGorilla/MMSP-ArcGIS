library(openxlsx)
library(dplyr)
library(googledrive)
library(stringr)
library(reshape2)

#
z = "C:\\Users\\oc3512\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\03-During-Construction\\02-Civil\\02-Station Structure\\01-Masterlist\\01-Compiled"
setwd(z)

a = file.choose()
x = read.xlsx(a)

head(x)
#x$GridX = as.character(x$GridX)
#x$GridY = as.character(x$GridY)



# P6 database:---- 
## Obtain keywords
b = "C:\\Users\\oc3512\\Dropbox\\01-Railway\\02-NSCR-Ex\\01-N2\\03-During-Construction\\02-Civil\\02-Station Structure\\00-Monitoring Doc\\CALUMPIT & APALIT STATION SCHEDULE DWP3_P6_database_sample.xlsx"
sheet = 2 # Apalit

y = read.xlsx(b,sheet=2)

## Re-structure P6 database
station = "Apalit"
y1 = y[,2:3]

colnames(y1) = c("Type","Desc")

# Parameter Setting:----

Station = 7
# Station
## 1.NCC
## 2.Depot
## 3.CIA
## 4.Clark
## 5.Angeles
## 6.San Fernando
## 7.Apalit
## 8.Calumpit
## 9.Malolos
## 10.Solis
## 11.Blumentritt
## 12.Espana
## 13.Santa Mesa
## 14.Paco
## 15.Buendia
## 16.EDSA
## 17.Nichols
## 18.FTI
## 19.Bicutan
## 20.Sucat
## 21.Alabang
## 22.Muntinlupa
## 23.San Pedro
## 24.Pacita
## 25.Binan
## 26.Santa Rosa
## 27.Cabuyao
## 28.Banlic Depot
## 29.Banlic
## 30.Calamba

# SubType
Pile_sub = 1
PileCap_sub = 2
Column_sub = 3
FG_sub = 4
Girder_sub = 5
RG_sub = 6
FB_sub = 7
Beam_sub = 8
Brace_sub = 9
FireE_sub = 10
SteelStair_sub = 11
Slab_sub = 12
RB_sub = 13

#substruc = which(str_detect(y1$Type,"Substructure"))
foundGird = which(str_detect(y1$Type, "Foundation Girder*"))
foundBeam = which(str_detect(y1$Type, "Foundation Beam"))

## Superstructure  & Structure Level & name
superstruc = which(str_detect(y1$Type, "Superstructure"))

### Concourse Level
concLevel = which(str_detect(y1$Type, "Councourse Level"))
concCol = which(str_detect(y1$Type, "Steel Column Erection"))
concFireE = which(str_detect(y1$Type, "Fire Exit"))
concSteelStair = which(str_detect(y1$Type, "Steel Staircase - Stair"))
concBeamSlab = which(str_detect(y1$Type, "(Beams & Slabs)"))

### Platform Level
PlatformLevel = which(str_detect(y1$Type, "Roof Level"))
platfBeam = which(str_detect(y1$Type, "Steel Framing & Decking"))
platfSlab = which(str_detect(y1$Desc, "concrete platform slab"))

### Roof Level
roofWorks = which(str_detect(y1$Type, "Roofing Works"))
roofGird = which(str_detect(y1$Desc, "Girder Installation"))
roofBeam_Brace = which(str_detect(y1$Desc, "Beam & Braces"))

### Grid X and Grid Y
grid_x = c("X01-X02","X02-X03","X03-X04","X04-X05","X05-X06",
           "X06-X07","X07-X08","X08-X09","X09-X10","X10-X11",
           "X11-X12","X12-X13","X13-X14","X14-X15","X15-X16",
           "X16-X17","X17-X18","X18-X19")

grid_x_s = c("X01","X02","X03","X04","X05",
             "X06","X07","X08","X09","X10",
             "X11","X12","X13","X14","X15",
             "X16","X17","X18","X19")

grid_x_d = c("X01-X02","X02-X03","X03-X04","X04-X05",
             "X05-X06","X06-X07","X07-X08","X08-X09",
             "X09-X10","X10-X11","X11-X12","X12-X13",
             "X13-X14","X14-X15","X15-X16","X16-X17","X17-X18","X18-X19")

grid_y = c("Y01","Y01-Y01","Y01-Y02","Y02","Y02-Y02")
grid_y_s = c("Y01","Y02")
grid_y_d = c("Y01-Y01","Y01-Y02","Y02-Y02")


## Substructure and Foundation:----

# Search for each category:----
head(y1)

## 1. Foundation Girder:----

##*******************************************************##
##*AS of December 31st, it is not possible to automate***##
##*It is probably better to manually enter for Foundation Girder**#
##* Enter "Cast Concrete" P6ID.
##********************************************************##


### between Foundation Girder and Foundation Beam
id = foundGird:(foundBeam-1)
y2 = y1[foundGird:(foundBeam-1),]

# Zone level
head(y2)
tail(y2)

zone1 = which(str_detect(y2$Type, "Zone 1"))
zone2 = which(str_detect(y2$Type, "Zone 2"))
zone3 = which(str_detect(y2$Type, "Zone 3"))
zone4 = which(str_detect(y2$Type, "Zone 4"))

Zones = c(zone1, zone2, zone3, zone4)

# For each zone, find P6ID


famType = c("FG1","FG2","FG3","FG4","FG5","FG11","FG12","FG21")

# Collapse
grid_x_c = paste0(grid_x,collapse = "|")
grid_x_sc = paste0(grid_x_s,collapse = "|")
grid_x_dc = paste0(grid_x_d,collapse="|")

grid_y_c = paste0(grid_y,collapse = "|")
grid_y_sc = paste0(grid_y_s,collapse = "|")
grid_y_dc = paste0(grid_y_d,collapse="|")


famType_c = paste0(famType,collapse="|")

temp = data.frame()
n=0

  gid_x = which(str_detect(y2$Type,grid_x_c))

  for(j in gid_x){ # For each Grid X
    n = n + 1

    if(length(gid_x) == n){
      jjd = j:nrow(y2)
    } else {
      jjd = j:(gid_x[n+1]-1)
    }
    print(paste(j," ,",n, ": ",min(jjd),"-",max(jjd),sep = ""))

    y3 = y2[jjd,]
    
    # Extract Grid x
    #gridx_sc = str_extract(y3$Desc,"X0\\d-X0\\d|X0\\d|X1\\d-X1\\d|X1\\d")
    gridx_sc = str_extract(y3$Desc,"X0\\d-X0\\d|X0\\d-X1\\d|X0\\d|X0\\d|X1\\d-X1\\d|X1\\d")
    y3$GridX = gridx_sc
    
    # Extract Grid y
    gridy_sc = str_extract(y3$Desc,"Y0\\d-Y0\\d|Y0\\d|Y1\\d-Y1\\d|Y1\\d")
    y3$GridY = gridy_sc
    
    # Create and extract FamilyType2
    y3$FamilyType2 = ""
    y3$FamilyType2[] = str_extract(y3$Desc,"FG\\d?\\d")
    
    # Bind row
    y4 = y3[-which(is.na(y3$GridX)),]
    y4 = y4[,-which(colnames(y4)=="Desc")]
    
    ## remove empty sapce in Type
    y4$Type[] = gsub("[[:space:]]","",y4$Type)
    
    temp = rbind(temp, y4)
    
    # note that the last row = "Cast Concrete"

  }

  temp$SubType = FG_sub
  temp$Station = Station
  colnames(temp)[which(colnames(temp)=="Type")]="P6ID"

  str(temp)
  
# Join this to the master list
### AS Gridx or GridY has missing cells, we need to add temporary values for join
na_x_gridx = which(is.na(x$GridX))
na_x_gridy = which(is.na(x$GridY))
na_x_Ftype2 = which(is.na(x$FamilyType2))

na_temp_gridx = which(is.na(temp$GridX))
na_temp_gridy = which(is.na(temp$GridY))
na_temp_Ftype2 = which(is.na(temp$FamilyType2))

# Fill in empty cells defined above with "M99"
x$GridX[na_x_gridx] = "M99"
x$GridY[na_x_gridy] = "M99"  
x$FamilyType2[na_x_Ftype2] = "M99"

temp$GridX[na_temp_gridx] = "M99"
temp$GridY[na_temp_gridy] = "M99"
temp$FamilyType2[na_temp_Ftype2] = "M99"


###
temp


yx = left_join(x,temp,by=c("Station","SubType","FamilyType2","GridX","GridY"))


  

## 2. Foundation Beam:----
### To identify number of rows for Foundation Beam, look for Zone 4

y2 = y1[foundBeam:nrow(y1),]
z4_row = which(str_detect(y2$Type,"Zone 4|Zone4|zone4|zone 4"))[1]

no_desc = which(is.na(y2$Desc))
# Basically, find the row number in "no_desc" next to z4_row
id = no_desc[no_desc > z4_row][1] - 1

y2 = y2[1:id,]

# Extract P6ID
y2$Type = gsub("[[:space:]]","",y2$Type)
gx = str_extract(y2$Type,"X0\\d-X0\\d|X0\\d-X1\\d|X0\\d|X0\\d|X1\\d-X1\\d|X1\\d")
gx = gx[complete.cases(gx)]

gx_id = which(str_detect(y2$Type,"X0\\d-X0\\d|X0\\d-X1\\d|X0\\d|X0\\d|X1\\d-X1\\d|X1\\d"))

n=0
temp = data.frame()
for(i in gx){
  # only each zone
  #i=gx[1]
  n = n +1
  
  if(length(gx) == n){ # last set
    nn = seq(gx_id[n],nrow(y2))
  } else {
    nn = seq(gx_id[n]+1,gx_id[n+1]-1)
  }
  
  y3 = y2[nn,]
  
  # Find "Cast Concrete"
  p6_row = which(str_detect(y3$Desc,"cast Concrete|Cast Concrete|cast concrete|castConcrete|CastConcrete"))
  
  zz = data.frame(GridX=i, P6ID=y3$Type[p6_row], SubType=7)
  
  # Rbind
  temp = rbind(temp,zz)
}

temp$GridY = ""
temp$Station = Station

# Join to the master list table
y = temp

y = y[,-which(colnames(y)=="GridY")]

xy = left_join(x,y,by=c("Station","SubType","GridX"))

head(xy)

# Update GridX with new ones
id_p6 = which(!is.na(xy$P6ID.y))
xy$P6ID.x[id_p6] = xy$P6ID.y[id_p6]

# Delete P6ID.y and rename P6ID
xy = xy[,-which(colnames(xy)=="P6ID.y")]
colnames(xy)[which(str_detect(colnames(xy),"P6ID"))] = "P6ID"


#
library(lubridate)

xy$updated = as.Date(xy$updated, origin = "1899-12-30")
xy$updated = as.Date(xy$updated, format="%m/%d/%y %H:%M:%S")

# Recover data in excel format
xy$StartDate = as.Date(xy$StartDate, origin = "1899-12-30")
xy$StartDate = as.Date(xy$StartDate, format="%m/%d/%y %H:%M:%S")

xy$TargetDate = as.Date(xy$TargetDate, origin = "1899-12-30")
xy$TargetDate = as.Date(xy$TargetDate, format="%m/%d/%y %H:%M:%S")

head(xy)

# Export
write.xlsx(xy,basename(a))


# 3. Beams
## Beams at Concourse Level (B)
## Beams at Platform Level (SB)

x = read.xlsx(a)
beam_id = which(str_detect(y1$Type, "Beams & Slabs")) # Concreting Works (Beams & Slabs)




y2 = y1[seq(beam_id+1,nrow(y1)),]
z4_row = which(str_detect(y2$Type,"Zone 4|Zone4|zone4|zone 4"))[1]
y2
no_desc = which(is.na(y2$Desc))

# Basically, find the row number in "no_desc" next to z4_row
id = no_desc[no_desc > z4_row][1] - 1

id
y2

y2 = y2[1:id,]

# Extract P6ID


######## Tempoerary code for joining Pro tables to excel master list
x = read.xlsx(a)

bb = file.choose()
y = read.xlsx(bb)

xy = left_join(x,y,by="ObjectId1")

#Update GridX
head(xy)
gridx_id = which(!is.na(xy$GridX.y))
xy$GridX.x[gridx_id] = xy$GridX.y[gridx_id]

# Update P6ID
P6ID_id = which(!is.na(xy$P6ID.y))
xy$P6ID.x[P6ID_id] = xy$P6ID.y[P6ID_id]

# Update StructuralLevel

st_id = which(!is.na(xy$StructureLevel.y))
xy$StructureLevel.x[st_id] = xy$StructureLevel.y[st_id]

head(xy)
drop_id = which(colnames(xy)=="SubType.y" | colnames(xy)=="StructureLevel.y" | colnames(xy)=="P6ID.y" | colnames(xy)=="GridX.y")
xy = xy[,-drop_id]

col_id = which(colnames(xy)=="GridX.x" | colnames(xy)=="StructureLevel.x" | colnames(xy)=="P6ID.x")
colnames(xy)[col_id] = c("StructureLevel","GridX","P6ID")

g = unique(xy$StructureLevel)
xy$StructureLevel[which(xy$StructureLevel=="Foundation")] = 1
xy$StructureLevel[which(xy$StructureLevel=="Concourse Level")] = 3
xy$StructureLevel[which(xy$StructureLevel=="Platform Level")] = 4
xy$StructureLevel[which(xy$StructureLevel=="Roof Level")] = 5

xy$StructureLevel = as.numeric(xy$StructureLevel)
head(xy)

iiid = which(!is.na(xy$P6ID) & xy$Station == 7)
xy$P6ID[iiid] = paste("N01-STN-YN-",xy$P6ID[iiid],sep = "")
head(xy)

library(lubridate)

xy$updated = as.Date(xy$updated, origin = "1899-12-30")
xy$updated = as.Date(xy$updated, format="%m/%d/%y %H:%M:%S")

# Recover data in excel format
xy$StartDate = as.Date(xy$StartDate, origin = "1899-12-30")
xy$StartDate = as.Date(xy$StartDate, format="%m/%d/%y %H:%M:%S")

xy$TargetDate = as.Date(xy$TargetDate, origin = "1899-12-30")
xy$TargetDate = as.Date(xy$TargetDate, format="%m/%d/%y %H:%M:%S")

head(xy)

getwd()
write.xlsx(xy,basename(a))
