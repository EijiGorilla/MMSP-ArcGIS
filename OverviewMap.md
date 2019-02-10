Overview Map
================

GitHub Documents
----------------

This is an R Markdown format used for publishing markdown documents to GitHub. When you click the **Knit** button all R code chunks are run and a markdown file (.md) suitable for publishing to GitHub is generated.

Including Code
--------------

You can include R code in the document as follows:

    ## Warning: package 'sf' was built under R version 3.4.4

    ## Linking to GEOS 3.6.1, GDAL 2.2.3, PROJ 4.9.3

``` r
wd=getwd()

files1<-"C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP.gdb"
files2<-"C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP(20181005).gdb"

# Check layers in the gdb
layers1<-st_layers(files1)
layers2<-st_layers(files2)

# Read stations and main lines
stations<-st_read(files2,layers2$name[1])
```

    ## Reading layer `Points' from data source `C:\Users\oc3512\Documents\ArcGIS\Projects\MMSP\MMSP(20181005).gdb' using driver `OpenFileGDB'
    ## Simple feature collection with 16 features and 9 fields
    ## geometry type:  POINT
    ## dimension:      XYZ
    ## bbox:           xmin: 121.0156 ymin: 14.48836 xmax: 121.0695 ymax: 14.68945
    ## epsg (SRID):    4326
    ## proj4string:    +proj=longlat +datum=WGS84 +no_defs

``` r
ml<-st_read(files2,layers2$name[2])
```

    ## Reading layer `Polylines' from data source `C:\Users\oc3512\Documents\ArcGIS\Projects\MMSP\MMSP(20181005).gdb' using driver `OpenFileGDB'
    ## Simple feature collection with 8001 features and 10 fields
    ## geometry type:  MULTILINESTRING
    ## dimension:      XYZ
    ## bbox:           xmin: 121.0135 ymin: 14.47771 xmax: 121.0706 ymax: 14.70866
    ## epsg (SRID):    4326
    ## proj4string:    +proj=longlat +datum=WGS84 +no_defs

``` r
depot<-st_read(files2,layers2$name[4])
```

    ## Reading layer `Depot' from data source `C:\Users\oc3512\Documents\ArcGIS\Projects\MMSP\MMSP(20181005).gdb' using driver `OpenFileGDB'
    ## Simple feature collection with 1 feature and 10 fields
    ## geometry type:  MULTILINESTRING
    ## dimension:      XYZ
    ## bbox:           xmin: 121.0135 ymin: 14.69368 xmax: 121.0235 ymax: 14.70866
    ## epsg (SRID):    4326
    ## proj4string:    +proj=longlat +datum=WGS84 +no_defs

``` r
ml_noZ<-st_zm(ml,drop=TRUE,what="ZM")
ML<-as(ml_noZ,"Spatial")

esri <- grep("^Esri", providers, value = TRUE)
esri<-c(esri,"MtbMap","Stamen.TonerLines","Stamen.TonerLabels")

## Base codes
m <- leaflet() %>% 
  addAwesomeMarkers(data=stations,label=~as.character(stations$Name),group="Stations",
                    labelOptions=labelOptions(noHide=TRUE,textOnly=TRUE)) %>%
  addScaleBar(position="bottomleft") %>%
  addMiniMap(tiles=esri[[1]],zoomLevelOffset = -5,toggleDisplay = TRUE, position="bottomright") %>%
  addPolylines(data=ML,group="Main Line")
```
