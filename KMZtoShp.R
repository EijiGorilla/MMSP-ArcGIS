# Convert KMZ file to shapfile in coordinate system for MMSP
library(sf)

# Choose kmz file
file=choose.files() # example: C:/....kmz

# Name the file:
fileName="mmsp"

# Unzip and convert kmz to kml
unzip(file,junkpaths = TRUE) #creates "doc.kml"

# read and convert Projection:
data=readOGR(file.path(getwd(),"doc.kml"))
data_wgs84=spTransform(data,CRS=CRS("+init=epsg:32651"))

# Check the re-projected coordinate
proj4string(data_wgs84)

# Save it in shpefile
writeOGR(data,getwd(),fileName,driver="ESRI Shapefile")

