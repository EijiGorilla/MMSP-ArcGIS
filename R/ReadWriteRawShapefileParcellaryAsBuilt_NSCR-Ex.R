##########################################################################################
# This R script read raw shape files of Parcellary and Structure from NSCR-Ex Envi Team
# and only extract LotID or Strucure_ID and add their respective Municipality names.
# It also exports each file to file geodatabase
########################################################################################


library(sf)

a = choose.dir() # where you store raw shapefiles
wd=setwd(a)
listFiles = list.files(wd, pattern=".shp")


names = c("Banlic", "Banlic", "Binan", "Binan", "Cabuyao", "Cabuyao", "Calamba", "Calamba",
          "ManilaPhase1", "ManilaPhase1", "San Pedro", "San Pedro", "Santa Rosa", "Santa Rosa")
names[1]


# Read and collect feature layers in a temporary list
temp = list()
n = 1
for (shp in listFiles){
  if(length(grep(".xml",basename(shp)))==1){
    print("not shapefile")
  } else {
    temp[[n]] = assign(gsub(".shp","",shp), st_read(shp))# use gsub to remove ".shp" character to assign shapefile names
    
    if(n == 2){
      temp[[n]] = temp[[n]][,grep(c("Text"), colnames(temp[[n]]))]
      temp[[n]]$Municipality = names[n]
    } else {
      temp[[n]] = temp[[n]][,grep(c("STRUC_ID|STRUCT_ID|Struct_ID|LOT_ID|LOTID|LotID"), colnames(temp[[n]]))]
      temp[[n]]$Municipality = names[n]
    }
    temp[[n]] = st_zm(temp[[n]],drop=TRUE, what='ZM')
  }
  n = n + 1
}

# For only Banic Depot Parcellary
colnames(temp[[2]])[1] = "LotID"

# Check colnames
for(i in temp){
  print(colnames(i))
}

for(i in seq(temp)){
  fileNames = "C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi"
  st_write(temp[[i]], paste0(fileNames, "/", listFiles[i]))
}
sf::st_write(temp[[1]],"C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/testDDDD.shp")
warnings()









# Export to fiel geodatabase
library(arcgisbinding)
arc.check_product()

for(i in seq(temp)){
  FileGDB_Dir = "NSCR-Ex_envi.gdb"
  fileNames = paste0(file.path("C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi", FileGDB_Dir),
                     "/", gsub(".shp","",listFiles[i]))
  arc.write(fileNames,data=temp[[i]],overwrite=TRUE)
}

arc.write("C:/Users/oc3512/OneDrive - Oriental Consultants Global JV/Documents/ArcGIS/Projects/NSCR-EX_envi/NSCR-EX_envi.gdb/testDDD",
          data=temp[[1]],overwrite=TRUE)

