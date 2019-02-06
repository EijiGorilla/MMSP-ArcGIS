Overview Map
================

GitHub Documents
----------------

This is an R Markdown format used for publishing markdown documents to GitHub. When you click the **Knit** button all R code chunks are run and a markdown file (.md) suitable for publishing to GitHub is generated.

Including Code
--------------

You can include R code in the document as follows:

    ## Warning: package 'leaflet' was built under R version 3.4.4

    ## Warning: package 'mapview' was built under R version 3.4.4

    ## Warning: replacing previous import 'gdalUtils::gdal_rasterize' by
    ## 'sf::gdal_rasterize' when loading 'mapview'

    ## 
    ## Attaching package: 'mapview'

    ## The following object is masked from 'package:leaflet':
    ## 
    ##     addMapPane

    ## Warning: package 'sf' was built under R version 3.4.4

    ## Linking to GEOS 3.6.1, GDAL 2.2.3, PROJ 4.9.3

    ## Warning: package 'dplyr' was built under R version 3.4.4

    ## 
    ## Attaching package: 'dplyr'

    ## The following objects are masked from 'package:stats':
    ## 
    ##     filter, lag

    ## The following objects are masked from 'package:base':
    ## 
    ##     intersect, setdiff, setequal, union

    ## Warning: package 'htmlwidgets' was built under R version 3.4.4

    ## Warning: package 'bindrcpp' was built under R version 3.4.4

    ## Reading layer `Points' from data source `C:\Users\oc3512\Documents\ArcGIS\Projects\MMSP\MMSP(20181005).gdb' using driver `OpenFileGDB'
    ## Simple feature collection with 16 features and 9 fields
    ## geometry type:  POINT
    ## dimension:      XYZ
    ## bbox:           xmin: 121.0156 ymin: 14.48836 xmax: 121.0695 ymax: 14.68945
    ## epsg (SRID):    4326
    ## proj4string:    +proj=longlat +datum=WGS84 +no_defs

    ## Reading layer `Polylines' from data source `C:\Users\oc3512\Documents\ArcGIS\Projects\MMSP\MMSP(20181005).gdb' using driver `OpenFileGDB'
    ## Simple feature collection with 8001 features and 10 fields
    ## geometry type:  MULTILINESTRING
    ## dimension:      XYZ
    ## bbox:           xmin: 121.0135 ymin: 14.47771 xmax: 121.0706 ymax: 14.70866
    ## epsg (SRID):    4326
    ## proj4string:    +proj=longlat +datum=WGS84 +no_defs

    ## Reading layer `Depot' from data source `C:\Users\oc3512\Documents\ArcGIS\Projects\MMSP\MMSP(20181005).gdb' using driver `OpenFileGDB'
    ## Simple feature collection with 1 feature and 10 fields
    ## geometry type:  MULTILINESTRING
    ## dimension:      XYZ
    ## bbox:           xmin: 121.0135 ymin: 14.69368 xmax: 121.0235 ymax: 14.70866
    ## epsg (SRID):    4326
    ## proj4string:    +proj=longlat +datum=WGS84 +no_defs

Including Plots
---------------

You can also embed plots, for example:

Note that the `echo = FALSE` parameter was added to the code chunk to prevent printing of the R code that generated the plot.
