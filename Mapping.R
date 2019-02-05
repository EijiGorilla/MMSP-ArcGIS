library(leaflet)
library(sf)


wd=getwd()

files1="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP.gdb"
files2="C:/Users/oc3512/Documents/ArcGIS/Projects/MMSP/MMSP(20181005).gdb"

# Check layers in the gdb
layers1=st_layers(files1)
layers2=st_layers(files2)

stations=st_read(files2,layers2$name[1])
ml=st_read(files2,layers2$name[2])
depot=st_read(files2,layers2$name[4])
ml_noZ=st_zm(ml,drop=TRUE,what="ZM")
ML=as(ml_noZ,"Spatial")

### use "leaflet"
## Basemap
## Collect providers
esri <- grep("^Esri", providers, value = TRUE)
esri=c(esri,"MtbMap","Stamen.TonerLines","Stamen.TonerLabels")

TEST=leaflet() %>% 
  addAwesomeMarkers(data=stations,label=~as.character(stations$Name),group="Stations",
                    labelOptions=labelOptions(noHide=TRUE,textOnly=TRUE)) %>%
  addScaleBar(position="bottomleft") %>%
  addMiniMap(tiles=esri[[1]],zoomLevelOffset = -5,toggleDisplay = TRUE, position="bottomright") %>%
  addPolylines(data=ML,group="Main Line")

## Add each provider map to TEST
for (provider in esri) {
  if(provider=="Stamen.TonerLines"){
    TEST <- TEST %>% addProviderTiles(provider,group=provider,options=providerTileOptions(opacity=0.25))
  } else {
    TEST <- TEST %>% addProviderTiles(provider, group = provider)  
  }
}

## 
TEST %>%
  setView(121.07,14.61,zoom=12) %>%
  addLayersControl(baseGroups = names(esri),options = layersControlOptions(collapsed = TRUE),
                   overlayGroups = c("Stations", "Main Line"))
  htmlwidgets::onRender("
    function(el, x) {
      var myMap = this;
      myMap.on('baselayerchange',
        function (e) {
          myMap.minimap.changeLayer(L.tileLayer.provider(e.name));
        })
    }")

  
  
### Use "mapview"
  library(dplyr)
  library(mapview)
  stNames=unique(stations$Name)
depot$Contract="CP101"

MMSP=stations %>% mutate(Contract=factor(ifelse(stNames %in% stNames[1:3],"CP101",
                                           ifelse(stNames %in% stNames[4:8],"CP102",
                                                  ifelse(stNames %in% stNames[9:16],"CP103","CP109"))))) %>%
  mapview(zcol="Contract",burst=TRUE,layer.name="Stations") + 
  mapview(depot,zcol="Contract",burst=TRUE,layer.name="Depot (CP101)") +
  mapview(ml,color="red",lwd=0.5,layer.name="Main Line")

mapshot(MMSP, url = paste0(getwd(), "/map.html"))
        
addLogo(MMSP, "C:/Users/oc3512/Desktop/Logo (OCGlobal-JV).png",
        position = "topright",
        offset.x = 5,
        offset.y = 40,
        width = 200,
        height = 200)

