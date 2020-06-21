tool_exec=function(in_params,out_params){
  library(rgdal)
  library(raster)
  
  source("https://raw.githubusercontent.com/EijiGorilla/R-Scripts-Collection/master/gsitiles.R-master/gsitiles.R")

  # set parameters
  dem=in_params[[1]]
  result=out_params[[1]]
  
  # Choose dem
  DEM=arc.raster(arc.open(dem))
  DEM=as.raster(DEM)
  
  # Make CS raster
  cs=makeCS(DEM,shaded=TRUE)
  cs1=brick(cs)
  
  # Export result
  arc.write(result,cs1,overwrite=TRUE)
  
  return(out_params)

}

