# Convert KMZ file to shapfile in coordinate system for MMSP
library(sf)
library(rgdal)

# Choose kmz file
file=choose.files() # example: C:/....kmz


# Name the file:
fileName="mmsp"

# Unzip and convert kmz to kml
unzip(file,junkpaths = TRUE) #creates "doc.kml"

##
data=st_read(file.path(getwd(),"MMSP.kml"))
data_utm=st_transform(data,crs=32651)
data_prs=st_transform(data_utm,crs=3123)

data=st_zm(st_cast(data,"LINESTRING"),drop=TRUE,what="ZM")
plot(st_geometry(data_prs))

st_cast(ln_pts, "POINT")
class(data_prs)
st_write(data_prs,"MMSP.shp",delete_layer=TRUE)

library(mapview)
ln_pts = st_line_sample(st_cast(trails, "LINESTRING"), 1)

## does not work
st_zm(ln_pts)

## works
st_zm(st_cast(ln_pts, "POINT"))

## seems to only fail for single MULTIPOINT features
pts = matrix(1:10, , 2)
mp1 = st_multipoint(pts)

st_zm(mp1)
# read and convert Projection:
data=readOGR(file.path(getwd(),"MMSP.kml"))
data_utm=spTransform(data,CRS=CRS("+init=epsg:32651"))
data_prs=spTransform(data_utm,CRS=CRS("+init=epsg:3123"))

# Check the re-projected coordinate
proj4string(data_prs)

plot(data_prs,axes=TRUE)
# Save it in shpefile
writeOGR(data_prs,getwd(),fileName,driver="ESRI Shapefile")
