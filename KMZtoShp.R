# Convert KMZ file to shapfile in coordinate system for MMSP
library(sf)

file="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MainLines.kmz"

# Unzip and convert kmz to kml
unzip(file,junkpaths = TRUE) #creates "doc.kml"

# read and convert Projection:
data=st_read(file.path(getwd(),"doc.kml"))
data=readOGR(file.path(getwd(),"doc.kml"))
data_wgs84=spTransform(data,CRS=CRS("+init=epsg:32651"))

# Check the re-projected coordinate
proj4string(data_wgs84)

# Save it in shpefile
writeOGR(data,getwd(),"TESTT",driver="ESRI Shapefile")
