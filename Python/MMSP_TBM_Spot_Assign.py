<html>
  <head>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="initial-scale=1,maximum-scale=1,user-scalable=no"
    />
    <!--
  ArcGIS API for JavaScript, https://js.arcgis.com
  For more information about the views-switch-2d-3d sample, read the original sample description at developers.arcgis.com.
  https://developers.arcgis.com/javascript/latest/sample-code/views-switch-2d-3d/index.html
  -->
<title>MMSP Tunnel</title>

    <style>
    html,
    body,
    #viewDiv {
      padding: 0;
      margin: 0;
      height: 100%;
      width: 100%;
    }

    #headerTitleDiv {
        font-size: 3vw;
        vertical-align: middle;
        padding-top: 3px;
        z-index: 99;
        position: absolute;
        left: 17;
        top: 18;
        color: white;
      }

      .dateDiv {
        color: rgb(0, 197, 255);
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        text-align: left;
        font-weight: normal;
        font-size: 1.1vw;
        padding-top: 2%;
        margin: 0;
        z-index:99;
        top: 55;
        left: 30;
        position: absolute;
      }

      .responsive {
        float: left;
        z-index: 99;
        position: absolute;
        right: 10%;
        bottom: 20%;
        width: 100%;
        max-width: 50px;
        height: auto;
      }

.img {
  float: left;
  padding-left: 20;
}

img {
  width: 40;
  height: 40;
  /*- center images-*/
  display: block;
  margin-left: auto;
  margin-right: auto;
}



#labelTbm,
#labelNatm,
#labelSurvey,
#labelTotalDiv {
  color: white;
  font-weight: bold;
  font-size: 1.5vw;
  text-align: center;
  width: 14vw;
  height: 4vh;
  padding-top: 3;
}

.lowerPanelBox {
  display: flex;
  height: 70%;
}

#logoDiv {
  width: 35%;
  height: 100%;
  /*-Vertically align in the middle-*/
  display: flex;
  align-items: center;
}

#chartPanel {
    display: inline-block;
    width: 100%;
    height: 100%;
    /*-Vertically align in the middle-*/
}


#boxTBM {
  position: absolute;
  z-index: 99;
  background-image: linear-gradient(rgb(0,0,0,0), rgb(0,185,242,0.4));
  border-color: white;
  box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19);
  background-color: rgb(0,0,0,0.5);
  bottom: 20;
  left: 0.5%;
  color: white;
  font-size: 2vw;
  text-align: center;
  aspect-ratio: auto 4 / 2;
}

#boxNATM {
  position: absolute;
  z-index: 99;
  background-image: linear-gradient(rgb(0,0,0,0), rgb(0,185,242,0.4));
  border-color: white;
  box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19);
  background-color: rgb(0,0,0,0.5);
  bottom: 20;
  left: 15%;
  color: white;
  font-size: 2vw;
  text-align: center;
  aspect-ratio: auto 4 / 2;
}

#boxTotal {
  position: absolute;
  z-index: 99;
  background-image: linear-gradient(rgb(0,0,0,0), rgb(0,185,242,0.4));
  border-color: white;
   box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19);
  background-color: rgb(0,0,0,0.5);
  bottom: 20;
  left: 29.5%;
  color: white;
  font-size: 2vw;
  text-align: center;
  width: 14vw;
  aspect-ratio: auto 4 / 2;
}

#boxSurvey {
    position: absolute;
    z-index: 99;
    background-image: linear-gradient(rgb(0,0,0,0), rgb(0,185,242,0.4));
    border-color: white;
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2), 0 6px 20px 0 rgba(0,0,0,0.19);
    background-color: rgb(0,0,0,0.5);
    bottom: 20;
    left: 44%;
    color: white;
    font-size: 2vw;
    text-align: center;
    aspect-ratio: auto 4 / 2;
}

#chartTbmDiv,
#chartNatmDiv,
#chartSurveyDiv {
  position: absolute;
  padding-top: 5%;
  margin-top: 0;
  z-index: 99;
  background-color: rgb(0,0,0,0);
  aspect-ratio: auto 4 / 2;
}

      #dropdownDiv {
        background-color: rgb(0, 0, 0 ,0);
        font-size: 1.1vw;
        opacity: 1;
        color: white;
        font-weight: bold;
        padding-right: 5;
        padding-top: 6;
        right: 100;
        top: 19;
        z-index: 99;
        position: absolute;
      }

#totalProgressDiv {
  position: absolute;
  color: rgb(0, 197, 255);
  font-size: 3vw;
  text-align: center;
  width: 14vw;
  padding-top: 4%;
}
      
      p {
        color: rgb(0, 197, 255);
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        width: auto;
        vertical-align: text-bottom;
        padding: 3px;
        margin-top: 10px;
      }

      h2 {
        font-weight: 400;
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        font-style: normal;
        font-size: 1.8vw;
        color: white;
        padding:3px;
        margin: 0px;
        vertical-align: text-top;
      }


      h4 {
        color: rgb(0, 197, 255);
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        text-align: left;
        font-weight: normal;
        font-size: 1.2vw;
        padding-top: 10%;
        margin: 0;
        width: 10vw;
        vertical-align: text-bottom;
      }

      h5 {
        color: gray;
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        padding: 3;
        margin: 10;
      }

      h6 {
        color: rgb(0, 197, 255);
        font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
        text-align: center;
        font-weight: normal;
        font-size: 3rem;
        margin-top: 30px;
        padding: 0px 0px 5px 0px;
        }

      #menu {
        background-color: rgb(0, 0, 0 ,0);
        width: 11vw;
        z-index: 99;
        bottom: 0;
        right: 5;
        position: absolute;
      }

      br{content:' ';}
      br:after{content:' ';}

      .esri-layer-list__item-toggle-icon,
     .esri-layer-list__item-title {
      color: white;
     }

      .sassy-theme .esri-menu,
      .sassy-theme .esri-popup__main-container,
      .sassy-theme .esri-popup .esri-popup__pointer-direction,
      .sassy-theme .esri-popup .esri-popup__button,
      .sassy-theme .esri-button,
      .sassy-theme .esri-input,
      .sassy-theme .esri-legend,
      .sassy-theme .esri-layer-list,
      .sassy-theme .esri-widget a {
        background-color: rgb(0, 0, 0, 0.5);
        color: #fff;
      }

      .sassy-theme .esri-legend__layer-caption {
    display: none;
  }

      /* Browser Setting */
      ::-webkit-scrollbar {
        display: none;
      }


      
    </style>

    <link
      rel="stylesheet"
      href="https://js.arcgis.com/4.24/esri/themes/dark/main.css"
    />
        <!-- Resources -->
    <script src="https://cdn.amcharts.com/lib/4/core.js"></script>
    <script src="https://cdn.amcharts.com/lib/4/charts.js"></script>
    <script src="https://www.amcharts.com/lib/4/themes/dark.js"></script>
    <script src="https://cdn.amcharts.com/lib/4/themes/animated.js"></script>
    <script src="https://js.arcgis.com/4.24/"></script>

    <script>
      require([
        "esri/Basemap",
        "esri/Map",
        "esri/views/MapView",
        "esri/views/SceneView",
        "esri/layers/FeatureLayer",
        "esri/views/layers/support/FeatureFilter",
        "esri/layers/SceneLayer",
        "esri/layers/Layer",
        "esri/layers/TileLayer",
        "esri/layers/VectorTileLayer",
        "esri/layers/support/LabelClass",
        "esri/symbols/LabelSymbol3D",
        "esri/WebMap",
        "esri/WebScene",
        "esri/portal/PortalItem",
        "esri/portal/Portal",
        "esri/widgets/TimeSlider",
        "esri/widgets/Legend",
        "esri/widgets/LayerList",
        "esri/widgets/Fullscreen",
        "esri/rest/geometryService",
        "esri/rest/support/Query",
        "esri/rest/support/StatisticDefinition",
        "esri/symbols/WebStyleSymbol",
        "esri/TimeExtent",
        "esri/widgets/Expand",
        "esri/widgets/Editor",
        "esri/renderers/UniqueValueRenderer",
        "esri/widgets/support/DatePicker",
        "esri/widgets/FeatureTable",
        "esri/widgets/Compass",
        "esri/TimeExtent",
        "esri/layers/ElevationLayer",
        "esri/Ground",
        "esri/widgets/Search",
        "esri/widgets/BasemapToggle",
        "esri/geometry/geometryEngine",
        "esri/geometry/Polygon",
        "esri/geometry/support/webMercatorUtils",
        "esri/layers/GraphicsLayer",
        "esri/geometry/SpatialReference"
      ], function(Basemap, Map, MapView, SceneView, 
                  FeatureLayer, FeatureFilter,
                  SceneLayer, Layer, TileLayer, VectorTileLayer,
                  LabelClass, LabelSymbol3D, WebMap,
                  WebScene, PortalItem, Portal,
                  TimeSlider, Legend, LayerList, Fullscreen,
                  geometryService, Query,
                  StatisticDefinition, WebStyleSymbol,
                  TimeExtent, Expand, Editor, UniqueValueRenderer, DatePicker,
                  FeatureTable, Compass, TimeExtent, ElevationLayer, Ground, Search,
                  BasemapToggle, geometryEngine, Polygon,
                  webMercatorUtils, GraphicsLayer, SpatialReference) {

let chartLayerView;
//const features = [];
const spatialReference = SpatialReference.WebMercator;

        var basemap = new Basemap({
        baseLayers: [
          new VectorTileLayer({
            portalItem: {
              id: "3a62040541b84f528da3ac7b80cf4a63" 
            }
          })
        ]
      });
      
      // Add custom DEM to the default elevation layer of esri
      const worldElevation = new ElevationLayer({
        url: "//elevation3d.arcgis.com/arcgis/rest/services/WorldElevation3D/Terrain3D/ImageServer"
        });
        
      const dem = new ElevationLayer({
        portalItem: {
          id: "dd2e85411a504182adb99215aa98ab68",
          portal: {
              url: "https://gis.railway-sector.com/portal"
          },
        }
        });

        var map = new Map({
              basemap: basemap, // "streets-night-vector", basemap, topo-vector
              ground: new Ground({
                layers: [worldElevation, dem]
              })
        });
        //map.ground.surfaceColor = "#FFFF";
        //map.ground.opacity = 0.1;
         
        var view = new SceneView ({
            map: map,
            container: "viewDiv",
            viewingMode: "local",
            camera: {
                position: {
                    x: 121.0322874,
                    y: 14.6750462,
                    z: 1000
                    },
                    tilt: 65
                    },
            environment: {
                background: {
                    type: "color", // autocasts as new ColorBackground()
                    color: [0, 0, 0, 1]
                    },
                    // disable stars
                    starsEnabled: false,
                    //disable atmosphere
                    atmosphereEnabled: false
                    }
        });

        const toggle = new BasemapToggle({
          view: view,
          nextBaseMap: "hybrid"
        });

        view.ui.add(toggle, "top-right");

// OpenStreetMap 3D Buildings
let osmSymbol = {
  type: "mesh-3d",
  symbolLayers: [
    {
      type: "fill",
      material: {
        color: [74, 80, 87, 0.5],
        colorMixMode: "replace"
      },
      edges: {
        type: "solid", // autocasts as new SolidEdges3D()
        color: [225, 225, 225, 0.3]
      }
  }
]
};


var osm3D = new SceneLayer({
  portalItem: {
    id: "ca0470dbbddb4db28bad74ed39949e25"
  },
  title: "OpenStreetMap 3D Buildings"
});
map.add(osm3D);
osm3D.renderer = {
  type: "simple",
  symbol: osmSymbol
}

        //
        function shiftCamera(deg) {
          var camera = view.camera.clone();
          camera.position.longitude += deg;
          return camera;
        }

        function catchAbortError(error) {
          if (error.name != "AbortError") {
            console.error(error);
          }
        }

        // Setup UI
        var headerTitleDiv = document.getElementById("headerTitleDiv");
        const chartTbmDiv = document.getElementById("chartTbmDiv");




//*******************************//
// Label Class Property Settings //
//*******************************//

 //********* Define LabelingInfo *************//
// Station labels
var stationLabelClass = new LabelClass({
          symbol: {
            type: "label-3d",// autocasts as new LabelSymbol3D()
            symbolLayers: [
              {
                type: "text", // autocasts as new TextSymbol3DLayer()
                material: {
                  color: "white"
                },
                size: 10,
                color: "black",
                haloColor: "black",
                haloSize: 1,
                font: {
                  family: "Ubuntu Mono",
                  //weight: "bold"
                },
              }
            ],
            verticalOffset: {
              screenLength: 40,
              maxWorldLength: 100,
              minWorldLength: 20
            },

          },
          labelPlacement: "above-center",
          labelExpressionInfo: {
            expression: 'DefaultValue($feature.Station, "no data")'
          }
        });

// TBM spot label class using transit layer

var tbmSpotLabel2 = new LabelClass({
  symbol: {
    type: "label-3d", // autocast as new LabelSymbol3D()
    symbolLayers: [
      {
        type: "text",
        material: {
          color: "#E83618"
        },
        size: 15,
        haloColor: "black",
        haloSize: 1,
        font: {
          family: "Ubuntu Mono",
          weight: "bold"
        },
      }
    ],
    verticalOffset: {
      screenLength: 100,
      maxWorldLength: 500,
      minWorldLength: 10
    },
    callout: {
      type: "line",
      size: 3,
      color: "#E83618",
      border: {
        color: "#E83618"
      }
    }
  },
  labelPlacement: "above-center",
  labelExpressionInfo: {
    expression: "IIF($feature.tbmSpot == 1, $feature.line, '')"
    //'DefaultValue($feature.GeoTechName, "no data")'
    //"IIF($feature.Score >= 13, '', '')"
    //value: "{Type}"
  },
  maxScale: 200,
  minScale: 1000,
});



// monitor buildings Label
        var monitorBuillabelClass = new LabelClass({
          symbol: {
            type: "label-3d", // autocast as new LabelSymbol3D()
            symbolLayers: [
              {
                type: "text",
                material: {
                  color: [137, 205, 102]
                },
                size: 9,
                color: "black",
                haloColor: "black",
                haloSize: 1,
                font: {
                  family: "Ubuntu Mono",
                  weight: "regular"
                },
              }
            ],
            verticalOffset: {
              screenLength: 80,
              maxWorldLength: 500,
              minWorldLength: 30
            },
            callout: {
              type: "line",
              size: 0.5,
              color: [0, 0, 0],
              border: {
                color: [255, 255, 255, 0.7]
              }
            }
          },
          labelPlacement: "above-center",
          labelExpressionInfo: {
            expression: "IIF($feature.Type == 'Hospital' || $feature.Type == 'School' || $feature.Type == 'Government', $feature.Type, '')"
            //'DefaultValue($feature.GeoTechName, "no data")'
            //"IIF($feature.Score >= 13, '', '')"
            //value: "{Type}"
          }
        });


//*****************************//
//      Renderer Settings      //
//*****************************//        
        // convenience function to retrieve the WebStyleSymbols based on their name
        function stationsSymbol(name) {
          return {
            type: "web-style", // autocasts as new WebStyleSymbol()
            name: name,
            styleName: "EsriIconsStyle"//EsriRealisticTransportationStyle, EsriIconsStyle
          };
        }

        function tbmspotSymbol(name) { // TBM Spot 
          return {
            type: "web-style",
            name: name,
            styleName: "EsriRealisticTransportationStyle"
          };
        }

// Statin Renderer
        var stationsRenderer = {
          type: "unique-value", // autocasts as new UniqueValueRenderer()
          field: "Name",
          defaultSymbol: stationsSymbol("Train"),//Backhoe, Train
        };
       
// Geotechnical information Renderer:-------------------
        ///-- Profile Options for rendering geotechnical informatino (polyline Z)
        const options_g = {
          profile: "circle",
          cap: "none",
          join: "miter",
          width: 6,
          height: 6,
          color: [200, 200, 200],
          profileRotation: "all"
        };

        ///-- Color
        const colors_g = {
          'Sandy Sand': [0, 112, 255, 1],
          'Silty Sand': [230, 230, 0, 1],
          'Rock Type': [197, 0, 255, 1]
        };

// TBM Alignment:-------------------
const options = {
          profile: "circle",
          cap: "butt", // butt
          join: "miter",
          width: 5,
          height: 5,
          color: [200, 200, 200, 0.3],
          profileRotation: "all"
        };

        /* The colors used for the each transit line */
        const colors = {
          1: [225, 225, 225, 0.1], // To be Constructed (white)
          2: [130, 130, 130, 0.5], // Under Construction
          3: [255, 0, 0, 0.8], // Delayed
          4: [0, 112, 255, 0.8], // Completed
        };

// Bridge: -----------
const colorsBridge = {
          'Minor': [112, 168, 0, 0.4], // To be Constructed (white)
          'Moderate': [230, 230, 0, 0.4], // Excavation (Dark brown)
          'Severe': [230, 0, 0, 0.7], // Rebar (Yellow)
        };

// Monitored Buildings:-----
    /*****************************************************************
         * Define symbols for each unique type of building. One each for
         * Government, Septic Tank, Ordinary House, Gas Station, Hospital, School, Pedestrian.
         * Good, Fair, and Dilapidated
         *****************************************************************/

         var goodSym = {
          type: "polygon-3d", // autocasts as new PolygonSymbol3D()
          symbolLayers: [
            {
              type: "extrude", // autocasts as new ExtrudeSymbol3DLayer()
              material: {
                color: [112, 168, 0, 0.4]
              },
              edges: {
                type: "solid",
                color: "#4E4E4E",
                size: 1.0
              }
            }
          ]
        };

        var fairSym = {
          type: "polygon-3d", // autocasts as new PolygonSymbol3D()
          symbolLayers: [
            {
              type: "extrude", // autocasts as new ExtrudeSymbol3DLayer()
              material: {
                color: [230, 230, 0, 0.4]
              },
              edges: {
                type: "solid",
                color: "#4E4E4E",
                size: 1.0
              }
            }
          ]
        };

        var dilapSym = {
          type: "polygon-3d", // autocasts as new PolygonSymbol3D()
          symbolLayers: [
            {
              type: "extrude", // autocasts as new ExtrudeSymbol3DLayer()
              material: {
                color: [230, 0, 0, 0.7]
              },
              edges: {
                type: "solid",
                color: "#4E4E4E",
                size: 1.0
              }
            }
          ]
        };


var obstructionRenderer = {
          type: "unique-value", // autocasts as new UniqueValueRenderer()
          defaultSymbol: {
            type: "polygon-3d", // autocasts as new PolygonSymbol3D()
            symbolLayers: [
              {
                type: "extrude", // autocasts as new ExtrudeSymbol3DLayer()
                material: {
                  color: "#E1E1E1"
                },
                edges: {
                  type: "solid",
                  color: "#4E4E4E",
                  size: 1.0
                }
              }
            ]
          },
          defaultLabel: "Other",
          field: "Rating",
          legendOptions: {
            title: "Rating for Defects"
            },
          uniqueValueInfos: [
            {
              value: "Good",
              symbol: goodSym,
              label: "Good"
            },
            {
              value: "Fair",
              symbol: fairSym,
              label: "Fair"
            },
            {
              value: "Dilapidated",
              symbol: dilapSym,
              label: "Dilapidated"
            }          
          ],
          visualVariables: [
            {
              type: "size",
              field: "Height",
              valueUnit: "meter" // Converts and extrudes all data values in feet
            }
          ]
        };


//*******************************//
// Import Layers                 //
//*******************************//       
// Construction boundary
// Construction boundary
let ConstructionBoundaryFill = {
                type: "unique-value",
                valueExpression: "When($feature.MappingBoundary == 1, 'Boundary',$feature.MappingBoundary)",
                uniqueValueInfos: [
                    {
                        value: "Boundary",
                        symbol: {
                            type: "simple-fill",
                            color: [0, 0, 0,0],
                            outline: {
                                width: 2.5,
                                color: [220,220,220],
                                style: "short-dash"
                            }
                        }
                    }

                ]
};


// Construction Boundary
var constBoundary = new FeatureLayer({
  portalItem: {
    id: "b0cf28b499a54de7b085725bca08deee",
    portal: {
      url: "https://gis.railway-sector.com/portal"
    }
  },
  layerId: 4,
  outFields: ["*"],
  renderer: ConstructionBoundaryFill,
  definitionExpression: "MappingBoundary = 1",
  title: "Construction Boundary",
  elevationInfo: {
     mode: "on-the-ground",
  },
  popupEnabled: false
});
constBoundary.listMode = "hide";
map.add(constBoundary);

// Station Layer:-------------------
var stationLayer = new SceneLayer({
          portalItem: {
            id: "6d8d606fee5841ea80fa133adbb028fc",
            portal: {
              url: "https://gis.railway-sector.com/portal"
            },
          },
             labelingInfo: [stationLabelClass],
             renderer: stationsRenderer,
             definitionExpression: "sector = 'MMSP'",
             popupEnabled: false,
             elevationInfo: {
                 // this elevation mode will place points on top of
                 // buildings or other SceneLayer 3D objects
                 mode: "relative-to-ground"
                 },
              //screenSizePerspectiveEnabled: false, // gives constant size regardless of zoom
        });
        stationLayer.listMode = "hide";
        map.add(stationLayer);

// Geotechnical information:-------------------
var geotech = new FeatureLayer({
        portalItem: {
            id: "30cdb9f9775146308a05dd17cfbfa87a",
            portal: {
              url: "https://gis.railway-sector.com/portal"
            }
          },
          layerId: 3,
          elevationInfo: {
          mode: "absolute-height", //absolute-height
          offset: 0,
        },
        hasZ: true,
         //renderer: roundTubeSymbol,
         title: "Soil Profile",
         //definitionExpression: "sens='Aller'",
         outFields: ["*"]
        });
        map.add(geotech);

        function renderGeotechLayer() {
          const renderer = new UniqueValueRenderer({
            field: "Class"
          });

          for (let property in colors_g) {
            if (colors_g.hasOwnProperty(property)) {
              renderer.addUniqueValueInfo({
                value: property,
                symbol: {
                  type: "line-3d",
                  symbolLayers: [
                    {
                      type: "path",
                      profile: options_g.profile,
                      material: {
                        color: colors_g[property]
                      },
                      width: options_g.width,
                      height: options_g.height,
                      join: options_g.join,
                      cap: options_g.cap,
                      anchor: "bottom",
                      profileRotation: options_g.profileRotation
                    }
                  ]
                }
              });
            }
          }

          geotech.renderer = renderer;
        }
        renderGeotechLayer();

// NATM

const colors_NATM = {
          1: [225, 225, 225, 0.1], // To be Constructed (white)
          2: [130, 130, 130, 0.5], // Under Construction
          3: [255, 0, 0, 0.8], // Delayed
          4: [0, 112, 255, 0.8], // Completed
        };

var natmLayer = new SceneLayer({
        portalItem: {
          id: "d8a87f380b69495a9906fb7035ca84a9",
          portal: {
        url: "https://gis.railway-sector.com/portal"
    }
        },
        elevationInfo: {
          mode: "absolute-height",//"on-the-ground", relative-to-ground, absolute-height
          offset: 0
        },

         //renderer: roundTubeSymbol,
         title: "NATM",
         //definitionExpression: "sens='Aller'",
         outFields: ["*"]
        });
        map.add(natmLayer);

// Symbology for natmLayer
function renderNATMLayer() {
  // Obtain unique values from Status1
  const renderer = new UniqueValueRenderer({
    field: "status"
  });
  
  for (let property in colors_NATM) {
    if (colors_NATM.hasOwnProperty(property)) {
      renderer.addUniqueValueInfo({
        value: property,
        symbol: {
          type: "mesh-3d",
          symbolLayers: [
            {
              type: "fill",
              material: {
                color: colors_NATM[property],
                colorMixMode: "replace"
              },
              edges: {
                type: "solid", // autocasts as new SolidEdges3D()
                color: [225, 225, 225, 0.3]
              }
            }
          ]
        }
      });
    }
  }
  natmLayer.renderer = renderer;
}
renderNATMLayer();


// TBM segmented line:-------------------
      var tbmTunnelLayer = new FeatureLayer({
        portalItem: {
          id: "af9539f5e41e4bd8b694973972e3faf4",
          portal: {
        url: "https://gis.railway-sector.com/portal"
    }
        },
        elevationInfo: {
          mode: "absolute-height",//"on-the-ground", relative-to-ground, absolute-height
          offset: -2
        },
        layerId: 2,
        labelingInfo: [tbmSpotLabel2],
         title: "TBM Segment",
         //definitionExpression: "sens='Aller'",
         outFields: ["*"]
        });
        map.add(tbmTunnelLayer);

        function renderTransitLayer() {
          const renderer = new UniqueValueRenderer({
            field: "status"
          });

          for (let property in colors) {
            if (colors.hasOwnProperty(property)) {
              renderer.addUniqueValueInfo({
                value: property,
                symbol: {
                  type: "line-3d",
                  symbolLayers: [
                    {
                      type: "path",
                      profile: options.profile,
                      material: {
                        color: colors[property]
                      },
                      width: options.width,
                      height: options.height,
                      join: options.join,
                      cap: options.cap,
                      anchor: "bottom",
                      profileRotation: options.profileRotation
                    }
                  ]
                }
              });
            }
          }

          tbmTunnelLayer.renderer = renderer;
        }

        renderTransitLayer();

// River Layer:-------------------
        const riverLayer = new FeatureLayer({
          portalItem: {
            id: "5ebdee597f3540d1baed240034532883",
            portal: {
              url: "https://gis.railway-sector.com/portal"
            },
          },
          layerId: 1,
        elevationInfo: {
          mode: "on-the-ground",
          offset: 0
        },
        renderer: {
            type: "simple",
            symbol: {
                type: "polygon-3d",
                symbolLayers: [
                    {
                        type: "water",
                        waveDirection: 260,
                        color: "#005B66", //#005B66, #25427c
                        waveStrength: "moderate",
                        waterbodySize: "medium"
                    }
                ]
            }
        }
        });
        riverLayer.listMode = "hide";
        map.add(riverLayer, 0);

// Station structure: reference only
var stationStructure = new SceneLayer({ //structureLayer
          portalItem: {
            id: "09f1e6d86cf34567bebcd22afcad8b4b",
            portal: {
              url: "https://gis.railway-sector.com/portal"
            }
          },
          definitionExpression: "Type = 1",
          popupEnabled: false,
            elevationInfo: {
                mode: "absolute-height",
                offset: 0
            },
            title: "Station Structure",
            outFields: ["*"]
            // when filter using date, example below. use this format
            //definitionExpression: "EndDate = date'2020-6-3'"
        });
        stationStructure.listMode = "hide";
        map.add(stationStructure, 1);

// Bridge Layer:-------------------        
        var bridgeLayer = new SceneLayer({
          portalItem: {
            id: "33801e0fd57a420e8f2dfc814b4fbf96", //8d867de4d0034e08afed516372f8dd86
            portal: {
                url: "https://gis.railway-sector.com/portal"
            },
          },
          /*
          portalItem: {
          id: "e01d0321d29f4239a383be1ba056d2aa",  
          portal: {
            url: "https://mmspgc-gis.mmspgc.local/portal"
          }
          },
          */
          elevationInfo: {
            mode: "absolute-height",
            offset: 0
          },
          title: "Monitoring Bridge",
          outFields: ["*"],
        });
        map.add(bridgeLayer, 0);

        function renderBridgeLayer() {
          const renderer = new UniqueValueRenderer({
            field: "Rating",
            legendOptions: {
            title: "Rating for Defects"
            }
          });

          for (let property in colorsBridge) {
            if (colorsBridge.hasOwnProperty(property)) {
              renderer.addUniqueValueInfo({
                value: property,
                symbol: {
                  type: "mesh-3d",
                  symbolLayers: [
                    {
                      type: "fill",
                      material: {
                        color: colorsBridge[property],
                        colorMixMode: "replace"
                      },
                      edges: {
                        type: "solid", // autocasts as new SolidEdges3D()
                        color: [225, 225, 225, 0.3]
                        }
                    }
                  ]
                 }
              });
            }
          }

          bridgeLayer.renderer = renderer;
        }

        renderBridgeLayer();


// Monitored Buildings:-----------
        /*****************************************************************
         * Set each unique value directly in the renderer's constructor.
         * At least one field must be used (in this case the "DESCLU" field).
         * The label property of each unique value will be used to indicate
         * the field value and symbol in the legend.
         *
         * The size visual variable sets the height of each building as it
         * exists in the real world according to the "ELEVATION" field.
         *****************************************************************/
var obstructionLayer = new FeatureLayer({
    portalItem: {
            id: "5ebdee597f3540d1baed240034532883",
            portal: {
              url: "https://gis.railway-sector.com/portal"
            },
          },
          layerId: 2,
          elevationInfo: {
            mode: "on-the-ground",
            offset: 0
          },
          title: "Monitoring Structures",
          labelingInfo: [monitorBuillabelClass],
          renderer: obstructionRenderer,
          popupTemplate: {
            // autocasts as new PopupTemplate()
            title: "{Rating}",
            content: [
              {
                type: "fields",
                fieldInfos: [
                  {
                    fieldName: "Type",
                    label: "Type of Building"
                  },
                  {
                    fieldName: "Score",
                    label: "Score"
                  },
                  {
                    fieldName: "Rating",
                    label: "Rating"
                  }
                ]
              }
            ]
          },
          outFields: ["*"],
          definitionExpression: "Remarks IS NULL" // show only buildings with height, 
        });
        map.add(obstructionLayer, 0);

// Dilapidation survey Extent line
var dilapSurveyExtent = new FeatureLayer({
  portalItem: {
    id: "30cdb9f9775146308a05dd17cfbfa87a",
    portal: {
        url: "https://gis.railway-sector.com/portal"
    },
  },
  layerId: 2,
        /*
          portalItem: {
          id: "8f53ab5eed324f5d9272a09b243198a6",
          portal: {
            url: "https://mmspgc-gis.mmspgc.local/portal"
          }
          },
          */
          elevationInfo: {
            mode: "on-the-ground",
            offset: 0
          },
          title: "Survey Extent Line"
        });
        map.add(dilapSurveyExtent, 0);

// TBM Alignment reference line:--------------
let defaultTBMAlign = {
                type: "simple-line",
                color: [211, 211, 211, 0.5],
                style: "solid",
                width: 0.5
};

let tbmAlignRenderer = {
    type: "unique-value",
    field: "LAYER",
    defaultSymbol: defaultTBMAlign
};

// Add graphics Layer
var graphicsLayer = new GraphicsLayer({
  elevationInfo: {
    mode: "relative-to-ground",
    featureExpressionInfo: {
        expression: "Geometry($feature).z * -0.5"
    },
    unit: "meters"
  },
  screenSizePerspectiveEnabled: true,
  outFields: ["*"],
  title: "TBM Spot"
});

map.add(graphicsLayer);
//*******************************//
//      Progress Chart           //
//*******************************//
const totalProgressTitleDiv = document.getElementById("totalProgressTitleDiv");
const totalProgressDiv = document.getElementById("totalProgressDiv");

// Find current position of TBM
// The current position refers to the spot of minimum segment No.

var query = tbmTunnelLayer.createQuery();
query.returnGeometry = true;
query.where = "tbmSpot = 1"; // to be constructed
query.groupByFieldsForStatistics = ["line"];

tbmTunnelLayer.queryFeatures(query).then(function(response) {
    stats = response.features;   

    stats.forEach((result, index) => {
        const attributes = result.attributes;
        const lineType = attributes.line;
        const segmentNo = attributes.segmentno;
        const vertex = result.geometry.paths[0];
        
        const long = (vertex[0][0] + vertex[1][0]) / 2;
        const lat = (vertex[0][1] + vertex[1][1]) / 2;
        // longitude: vertex[0][0]
        // latitude: vertex[0][1]

            view.graphics.add({
                geometry: {
                    spatialReference: spatialReference,
                    type: "point",
                    x: long,
                    y: lat,
                    z: -0.1
                },
                symbol: {
                type: "point-3d",
                symbolLayers: [
                    {
                        type: "icon",
                        resource: {
                          href: "https://EijiGorilla.github.io/Symbols/TBM_LOGO2.png"
                        },
                        size: 30
                        //resource: {primitive: "circle"},
                        //material: {color: "green"}
                    }
                ],
                verticalOffset: {
                    screenLength: 100,
                    maxWorldLength: 500,
                    minWorldLength: 40
                },
                callout: {
                    type: "line",
                    size: 1.5,
                    color: "#E83618",
                    border: {
                        color: "#E83618"
                    }
                },
                maxScale: 1000,
                minScale: 25000000
            }
            });


    });

});

// Total progress //
function totalProgressTBM() {

  var total_complete = {
  onStatisticField: "CASE WHEN status = 4 THEN 1 ELSE 0 END",
  outStatisticFieldName: "total_complete",
  statisticType: "sum"
};

var total_obs = {
  onStatisticField: "status",
  outStatisticFieldName: "total_obs",
  statisticType: "count"
};

var query = tbmTunnelLayer.createQuery();
query.outStatistics = [total_complete, total_obs];
query.returnGeometry = true;

return tbmTunnelLayer.queryFeatures(query).then(function(response) {
  var stats = response.features[0].attributes;

  const total_complete = stats.total_complete;
  const total_obs = stats.total_obs;

  const totalperc = (total_complete/total_obs)*100;
  //totalProgressDiv.innerHTML = totalperc.toFixed(0) + " %";

  tbmTunnelArray = [total_obs, total_complete];

  return tbmTunnelArray;
});
}

function totalProgressNATM(tbmTunnelArray) {
  var total_complete = {
  onStatisticField: "CASE WHEN status = 4 THEN 1 ELSE 0 END",
  outStatisticFieldName: "total_complete",
  statisticType: "sum"
};

var total_obs = {
  onStatisticField: "status",
  outStatisticFieldName: "total_obs",
  statisticType: "count"
};

var query = natmLayer.createQuery();
query.outStatistics = [total_complete, total_obs];
query.returnGeometry = true;

natmLayer.queryFeatures(query).then(function(response) {
  var stats = response.features[0].attributes;

  const total_complete = stats.total_complete;
  const total_obs = stats.total_obs;

  const grandTotal = tbmTunnelArray[0] + total_obs;
  const grandComp = tbmTunnelArray[1] + total_complete;

  const totalperc = (grandComp/grandTotal)*100;
  totalProgressDiv.innerHTML = totalperc.toFixed(0) + " %";
});

}
function totalProgessAllTunnel() {
  totalProgressTBM()
  .then(totalProgressNATM);
}




/////////////////////////////////////



/* Function for zooming to selected layers */
function zoomToLayer(layer) {
  return layer.queryExtent().then(function(response) {
    view.goTo(response.extent, { //response.extent
      speedFactor: 2
    }).catch(function(error) {
      if (error.name != "AbortError") {
        console.error(error);
      }
    });
  });
}

var highlightSelect;



 // Create a Bar chart to calculate % completion for each viaduct sample
am4core.ready(function() {
am4core.useTheme(am4themes_animated);

// Default
function defaultRender(){
  tbmTunnelLayer.definitionExpression = null;
  natmLayer.definitionExpression = null;
  //stationStructure.definitionExpression = "Section = 'PO'";
  tbmChart();
  natmChart();
  totalProgessAllTunnel();
}
defaultRender();

// Add Section and tunnel type to drop-down lists
/// 1. Section
function sectionTypeValues() {
  var sectionArray = [];
  var query = tbmTunnelLayer.createQuery();
  query.outField = ["Section"];
  query.where = "Section IS NOT NULL";
  query.returnGeometry = true;
  return tbmTunnelLayer.queryFeatures(query).then(function(response) {
    var stats = response.features;
    stats.forEach((result, index) => {
      var attributes = result.attributes;
      const SectionValues = attributes.Section;
      sectionArray.push(SectionValues);
    });
    return sectionArray;
  });
}

function getUniqueValueSection(values) {
  var uniqueValues = [];
  values.forEach(function(item, i) {
    if ((uniqueValues.length < 1 || uniqueValues.indexOf(item) === -1) && item !== "") {
        uniqueValues.push(item);
    }
});
return uniqueValues;
}

function addToSelectSection(values) {
  values.sort();
  //values.unshift('None');
  values.forEach(function(value) {
    var option = document.createElement("option");
    option.text = value;
    sectionSelect.add(option);
  });
}
function sectionListQuery(){
  sectionTypeValues()
    .then(getUniqueValueSection)
    .then(addToSelectSection)
}
sectionListQuery();

/// 2. Tunnel Type

function filterForTunnelType(sectionValue) {
  
    if (sectionValue === 'PO' || sectionValue === undefined) {
      allArray = ['TBM'];

    } else if (sectionValue === 'Remaining') {
      allArray = ['TBM','NATM'];
    }

  var uniqueValues2 = [];
  allArray.forEach(function(item, i) {
        if ((uniqueValues2.length < 1 || uniqueValues2.indexOf(item) === -1) && item !== "") {
            uniqueValues2.push(item);
        }
    });

  tunnelSelect.options.length = 0;
  uniqueValues2.sort();
  uniqueValues2.unshift('None');
  uniqueValues2.forEach(function(value) {
    var option = document.createElement("option");
      option.text = value;
      tunnelSelect.add(option);
  });
}



function sectionOnlyExpression(sectionValue) {
  if (sectionValue === 'None') {
    tbmTunnelLayer.definitionExpression = null;
    natmLayer.definitionExpression = null;
  } else {
    tbmTunnelLayer.definitionExpression = "Section = '" + sectionValue + "'";
    natmLayer.definitionExpression = "Section = '" + sectionValue + "'";
  }
}

function sectionTunnelTypeExpression(sectionValue, tunnelValue) {
  if (sectionValue === 'None' && tunnelValue === 'None') {
    tbmTunnelLayer.definitionExpression = null;
    natmLayer.definitionExpression = null;

  } else if (sectionValue !== 'None' && tunnelValue === 'None') {
    tbmTunnelLayer.definitionExpression = "Section = '" + sectionValue + "'";
    natmLayer.definitionExpression = "Section = '" + sectionValue + "'";

  } else if (sectionValue === 'None' && tunnelValue === 'TBM') {
    tbmTunnelLayer.definitionExpression = null;
    natmLayer.visible = false;

  } else if (sectionValue === 'None' && tunnelValue === 'NATM') {
    tbmTunnelLayer.visible = false;
    natmLayer.visible = true;
    natmLayer.definitionExpression = null;

  } else if (sectionValue === 'PO' && tunnelValue === 'TBM') {
    tbmTunnelLayer.definitionExpression = "Section = '" + sectionValue + "'";
    natmLayer.visible = false;

  } else if (sectionValue === 'Remaining' && tunnelValue === 'NATM') {
    tbmTunnelLayer.visible = false;
    natmLayer.visible = true;
    natmLayer.definitionExpression = null;
  
} else if (sectionValue === 'Remaining' && tunnelValue === 'TBM') {
    tbmTunnelLayer.visible = "Section = '" + sectionValue + "'";
    natmLayer.visible = false;
  }

}



function filterTbm() {
  var query2 = tbmTunnelLayer.createQuery();
  query2.where = tbmTunnelLayer.definitionExpression; // use filtered municipality. is this correct?

}

function filterNatm() {
  var query2 = natmLayer.createQuery();
  query2.where = natmLayer.definitionExpression; // use filtered municipality. is this correct?

}

// Dropdown List
/// 1. Section dropdown list ('PO', 'Remaining')
sectionSelect.addEventListener("change", function() {
  var sectionType = event.target.value;
  //headerTitleDiv.innerHTML = sectionType;

  filterForTunnelType(sectionType);
  sectionOnlyExpression(sectionType);

  tbmChart();
  natmChart();
  SurveyChart();
  totalProgessAllTunnel();

  filterTbm();
  filterNatm();

});


/// 2. Tunnel Type dropdown list ('TBM', 'NATM')
tunnelSelect.addEventListener("change", function() {
  var tunnelType = event.target.value;
  var sectionType = sectionSelect.value;

  sectionTunnelTypeExpression(sectionType, tunnelType);

  if (tunnelType === 'TBM') {
    zoomToLayer(tbmTunnelLayer);
  } else if (tunnelType === 'NATM') {
    zoomToLayer(natmLayer);
  }

  tbmChart();
  natmChart();
  SurveyChart();
  totalProgessAllTunnel();
  

  filterTbm();
  filterNatm();
});


///////// PIE CHART /////////
// 1. TBM
function tbmChart() {
    var total_tobeC = {
        onStatisticField: "CASE WHEN status = 1 THEN 1 ELSE 0 END",
        outStatisticFieldName: "total_tobeC",
        statisticType: "sum"
    }

    var total_complete = {
        onStatisticField: "CASE WHEN status = 4 THEN 1 ELSE 0 END",
        outStatisticFieldName: "total_complete",
        statisticType: "sum"
    }

    var query = tbmTunnelLayer.createQuery();
    query.outStatistics = [total_tobeC, total_complete];
    query.returnGeometry = true;
    
    tbmTunnelLayer.queryFeatures(query).then(function(response) {
      var stats = response.features[0].attributes;

      const tbm_incomp = stats.total_tobeC;
      const tbm_comp = stats.total_complete;

      var chart = am4core.create("chartTbmDiv",  am4charts.XYChart);

      // Responsive to screen size
      chart.responsive.enabled = true;
      chart.responsive.useDefault = false
      chart.responsive.rules.push({
        relevant: function(target) {
          if (target.pixelWidth <= 400) {
            return true;
          }
            return false;
          },
          state: function(target, stateId) {
            
            if (target instanceof am4charts.Chart) {
              var state = target.states.create(stateId);
              state.properties.paddingTop = 0;
              state.properties.paddingRight = 15;
              state.properties.paddingBottom = 5;
              state.properties.paddingLeft = 15;
              return state;
            }
            
            if (target instanceof am4charts.Legend) {
              var state = target.states.create(stateId);
              state.properties.paddingTop = 0;
              state.properties.paddingRight = 0;
              state.properties.paddingBottom = 0;
              state.properties.paddingLeft = 0;
              state.properties.marginLeft = 0;
              return state;
            }
            
            if (target instanceof am4charts.AxisRendererY) {
              var state = target.states.create(stateId);
              state.properties.inside = false;
              state.properties.maxLabelPosition = 0.99;
              return state;
            }
            
            if ((target instanceof am4charts.AxisLabel) && (target.parent instanceof am4charts.AxisRendererY)) { 
              var state = target.states.create(stateId);
              state.properties.dy = 0;
              state.properties.paddingTop = 3;
              state.properties.paddingRight = 5;
              state.properties.paddingBottom = 3;
              state.properties.paddingLeft = 5;
              
              // Create a separate state for background
              // target.setStateOnChildren = true;
              // var bgstate = target.background.states.create(stateId);
              // bgstate.properties.fill = am4core.color("#fff");
              // bgstate.properties.fillOpacity = 0;
      
              return state;
            }
            
            // if ((target instanceof am4core.Rectangle) && (target.parent instanceof am4charts.AxisLabel) && (target.parent.parent instanceof am4charts.AxisRendererY)) { 
            //   var state = target.states.create(stateId);
            //   state.properties.fill = am4core.color("#f00");
            //   state.properties.fillOpacity = 0.5;
            //   return state;
            // }
    
               return null;
              }
            });
            
            chart.hiddenState.properties.opacity = 0;
            
            chart.data = [
            {
                category: "TBM",
                value1: tbm_comp,
                value2: tbm_incomp
            }
        ];

        // Define chart setting
        chart.colors.step = 2;
        chart.padding(0, 0, 0, 0);
        
        // Axis Setting
        /// Category Axis
        var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
        categoryAxis.dataFields.category = "category";
        categoryAxis.renderer.grid.template.location = 0;
        categoryAxis.renderer.labels.template.fontSize = 0;
        categoryAxis.renderer.labels.template.fill = "#ffffff";
        categoryAxis.renderer.minGridDistance = 5; //can change label
        categoryAxis.renderer.grid.template.strokeWidth = 0;
        
        /// Value Axis
        var valueAxis = chart.xAxes.push(new am4charts.ValueAxis());
        valueAxis.min = 0;
        valueAxis.max = 100;
        valueAxis.strictMinMax = true;
        valueAxis.calculateTotals = true;
        valueAxis.renderer.minWidth = 50;
        valueAxis.renderer.labels.template.fontSize = 0;
        valueAxis.renderer.labels.template.fill = "#ffffff";
        valueAxis.renderer.grid.template.strokeWidth = 0;
        
        // Layerview and Expand
        function createSeries(field, name) {
            var series = chart.series.push(new am4charts.ColumnSeries());
            series.calculatePercent = true;
            series.dataFields.valueX = field;
            series.dataFields.categoryY = "category";
            series.stacked = true;
            series.dataFields.valueXShow = "totalPercent";
            series.dataItems.template.locations.categoryY = 0.5;
            
            // Bar chart line color and width
            series.columns.template.stroke = am4core.color("#FFFFFF"); //#00B0F0
            series.columns.template.strokeWidth = 0.5;
            series.name = name;
            
            var labelBullet = series.bullets.push(new am4charts.LabelBullet());
            
            if (name == "Incomplete"){
                series.fill = am4core.color("#FF000000");
                labelBullet.locationX = 0.5;
                labelBullet.label.text = "";
                labelBullet.label.fill = am4core.color("#FFFFFFFF");
                labelBullet.interactionsEnabled = false;
                labelBullet.label.fontSize = 0;
                labelBullet.locationX = 0.5;
            
            } else {
                series.fill = am4core.color("#00B0F0"); // Completed
                labelBullet.locationX = 0.5;
                labelBullet.label.text = "{valueX.totalPercent.formatNumber('#.')}%";
                labelBullet.label.fill = am4core.color("#ffffff");
                labelBullet.interactionsEnabled = false;
                labelBullet.label.fontSize = 10;
                labelBullet.locationX = 0.5;
            }
            
            series.columns.template.width = am4core.percent(60);
            series.columns.template.tooltipText = "[font-size:15px]{name}: {valueX.value.formatNumber('#.')} ({valueX.totalPercent.formatNumber('#.')}%)"
            
            // Click chart and filter, update maps
            const chartElement = document.getElementById("chartPanel");
            series.columns.template.events.on("hit", filterByChart, this);

            function filterByChart(ev) {
                const selectedC = ev.target.dataItem.component.name;
                const selectedP = ev.target.dataItem.categoryY;
                
                // Layer
                if (selectedC === "Incomplete") {
                    selectedStatus = 1;
                } else if (selectedC === "Complete") {
                    selectedStatus = 4;
                } else {
                    selectedLayer = null;
                }
                
         view.when(function() {
          view.whenLayerView(tbmTunnelLayer).then(function (layerView) {
            chartLayerView = layerView;
            chartElement.style.visibility = "visible";
            
            tbmTunnelLayer.queryFeatures().then(function(results) {
              const RESULT_LENGTH = results.features;
              const ROW_N = RESULT_LENGTH.length;

              let objID = [];
              for (var i=0; i < ROW_N; i++) {
                  var obj = results.features[i].attributes.OBJECTID;
                  objID.push(obj);
              }

              var queryExt = new Query({
                 objectIds: objID
              });

              tbmTunnelLayer.queryExtent(queryExt).then(function(result) {
                  if (result.extent) {
                      view.goTo(result.extent)
                  }
              });

              if (highlightSelect) {
                  highlightSelect.remove();
              }
              highlightSelect = layerView.highlight(objID);

              view.on("click", function() {
                layerView.filter = null;
                highlightSelect.remove();
              });
            }); // End of queryFeatures
            layerView.filter = {
              where: "status = " + selectedStatus
            }
          }); // End of view.whenLayerView
        }); // End of view.when
      } // End of filterByChart
    } // End of createSlices function
    
    createSeries("value1", "Complete");
    createSeries("value2", "Incomplete");

}); // end of queryFeatures
} // end of updateChartWater

// 2. NATM
function natmChart() {
    var total_tobeC = {
        onStatisticField: "CASE WHEN status = 1 THEN 1 ELSE 0 END",
        outStatisticFieldName: "total_tobeC",
        statisticType: "sum"
    }

    var total_complete = {
        onStatisticField: "CASE WHEN status = 4 THEN 1 ELSE 0 END",
        outStatisticFieldName: "total_complete",
        statisticType: "sum"
    }

    var query = natmLayer.createQuery();
    query.outStatistics = [total_tobeC, total_complete];
    query.returnGeometry = true;
    
    natmLayer.queryFeatures(query).then(function(response) {
      var stats = response.features[0].attributes;

      const tbm_incomp = stats.total_tobeC;
      const tbm_comp = stats.total_complete;

      var chart = am4core.create("chartNatmDiv",  am4charts.XYChart);

      // Responsive to screen size
      chart.responsive.enabled = true;
      chart.responsive.useDefault = false
      chart.responsive.rules.push({
        relevant: function(target) {
          if (target.pixelWidth <= 400) {
            return true;
          }
            return false;
          },
          state: function(target, stateId) {
            
            if (target instanceof am4charts.Chart) {
              var state = target.states.create(stateId);
              state.properties.paddingTop = 0;
              state.properties.paddingRight = 15;
              state.properties.paddingBottom = 5;
              state.properties.paddingLeft = 15;
              return state;
            }
            
            if (target instanceof am4charts.Legend) {
              var state = target.states.create(stateId);
              state.properties.paddingTop = 0;
              state.properties.paddingRight = 0;
              state.properties.paddingBottom = 0;
              state.properties.paddingLeft = 0;
              state.properties.marginLeft = 0;
              return state;
            }
            
            if (target instanceof am4charts.AxisRendererY) {
              var state = target.states.create(stateId);
              state.properties.inside = false;
              state.properties.maxLabelPosition = 0.99;
              return state;
            }
            
            if ((target instanceof am4charts.AxisLabel) && (target.parent instanceof am4charts.AxisRendererY)) { 
              var state = target.states.create(stateId);
              state.properties.dy = 0;
              state.properties.paddingTop = 3;
              state.properties.paddingRight = 5;
              state.properties.paddingBottom = 3;
              state.properties.paddingLeft = 5;
              
              // Create a separate state for background
              // target.setStateOnChildren = true;
              // var bgstate = target.background.states.create(stateId);
              // bgstate.properties.fill = am4core.color("#fff");
              // bgstate.properties.fillOpacity = 0;
      
              return state;
            }
            
            // if ((target instanceof am4core.Rectangle) && (target.parent instanceof am4charts.AxisLabel) && (target.parent.parent instanceof am4charts.AxisRendererY)) { 
            //   var state = target.states.create(stateId);
            //   state.properties.fill = am4core.color("#f00");
            //   state.properties.fillOpacity = 0.5;
            //   return state;
            // }
    
               return null;
              }
            });
            
            chart.hiddenState.properties.opacity = 0;
            
            chart.data = [
            {
                category: "TBM",
                value1: tbm_comp,
                value2: tbm_incomp
            }
        ];

        // Define chart setting
        chart.colors.step = 2;
        chart.padding(0, 0, 0, 0);
        
        // Axis Setting
        /// Category Axis
        var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
        categoryAxis.dataFields.category = "category";
        categoryAxis.renderer.grid.template.location = 0;
        categoryAxis.renderer.labels.template.fontSize = 0;
        categoryAxis.renderer.labels.template.fill = "#ffffff";
        categoryAxis.renderer.minGridDistance = 5; //can change label
        categoryAxis.renderer.grid.template.strokeWidth = 0;
        
        /// Value Axis
        var valueAxis = chart.xAxes.push(new am4charts.ValueAxis());
        valueAxis.min = 0;
        valueAxis.max = 100;
        valueAxis.strictMinMax = true;
        valueAxis.calculateTotals = true;
        valueAxis.renderer.minWidth = 50;
        valueAxis.renderer.labels.template.fontSize = 0;
        valueAxis.renderer.labels.template.fill = "#ffffff";
        valueAxis.renderer.grid.template.strokeWidth = 0;
        
        // Layerview and Expand
        function createSeries(field, name) {
            var series = chart.series.push(new am4charts.ColumnSeries());
            series.calculatePercent = true;
            series.dataFields.valueX = field;
            series.dataFields.categoryY = "category";
            series.stacked = true;
            series.dataFields.valueXShow = "totalPercent";
            series.dataItems.template.locations.categoryY = 0.5;
            
            // Bar chart line color and width
            series.columns.template.stroke = am4core.color("#FFFFFF"); //#00B0F0
            series.columns.template.strokeWidth = 0.5;
            series.name = name;
            
            var labelBullet = series.bullets.push(new am4charts.LabelBullet());
            
            if (name == "Incomplete"){
                series.fill = am4core.color("#FF000000");
                labelBullet.locationX = 0.5;
                labelBullet.label.text = "";
                labelBullet.label.fill = am4core.color("#FFFFFFFF");
                labelBullet.interactionsEnabled = false;
                labelBullet.label.fontSize = 0;
                labelBullet.locationX = 0.5;
            
            } else {
                series.fill = am4core.color("#00B0F0"); // Completed
                labelBullet.locationX = 0.5;
                labelBullet.label.text = "{valueX.totalPercent.formatNumber('#.')}%";
                labelBullet.label.fill = am4core.color("#ffffff");
                labelBullet.interactionsEnabled = false;
                labelBullet.label.fontSize = 10;
                labelBullet.locationX = 0.5;
            }
            
            series.columns.template.width = am4core.percent(60);
            series.columns.template.tooltipText = "[font-size:15px]{name}: {valueX.value.formatNumber('#.')} ({valueX.totalPercent.formatNumber('#.')}%)"
            
            // Click chart and filter, update maps
            const chartElement = document.getElementById("chartPanel");
            series.columns.template.events.on("hit", filterByChart, this);

            function filterByChart(ev) {
                const selectedC = ev.target.dataItem.component.name;
                const selectedP = ev.target.dataItem.categoryY;
                
                // Layer
                if (selectedC === "Incomplete") {
                    selectedStatus = 1;
                } else if (selectedC === "Complete") {
                    selectedStatus = 4;
                } else {
                    selectedLayer = null;
                }
                
         view.when(function() {
          view.whenLayerView(natmLayer).then(function (layerView) {
            chartLayerView = layerView;
            chartElement.style.visibility = "visible";
            
            natmLayer.queryFeatures().then(function(results) {
              const RESULT_LENGTH = results.features;
              const ROW_N = RESULT_LENGTH.length;

              let objID = [];
              for (var i=0; i < ROW_N; i++) {
                  var obj = results.features[i].attributes.OBJECTID;
                  objID.push(obj);
              }

              var queryExt = new Query({
                 objectIds: objID
              });

              natmLayer.queryExtent(queryExt).then(function(result) {
                  if (result.extent) {
                      view.goTo(result.extent)
                  }
              });

              if (highlightSelect) {
                  highlightSelect.remove();
              }
              highlightSelect = layerView.highlight(objID);

              view.on("click", function() {
                layerView.filter = null;
                highlightSelect.remove();
              });
            }); // End of queryFeatures
            layerView.filter = {
              where: "status = " + selectedStatus
            }
          }); // End of view.whenLayerView
        }); // End of view.when
      } // End of filterByChart
    } // End of createSlices function
    
    createSeries("value1", "Complete");
    createSeries("value2", "Incomplete");

}); // end of queryFeatures
} // 


// 3. Dilapidation Survey
// 2. NATM
function SurveyChart() {
    var total_dilap = {
        onStatisticField: "CASE WHEN Rating = 'Dilapidated' THEN 1 ELSE 0 END",
        outStatisticFieldName: "total_dilap",
        statisticType: "sum"
    }

    var total_survey = {
        onStatisticField: "Rating",
        outStatisticFieldName: "total_survey",
        statisticType: "count"
    }


    var query = obstructionLayer.createQuery();
    query.outStatistics = [total_dilap, total_survey];
    query.returnGeometry = true;
    query.outFields = ["Rating"];
    
    obstructionLayer.queryFeatures(query).then(function(response) {
      var stats = response.features[0].attributes;

      const dilap = stats.total_dilap;

      var chart = am4core.create("chartSurveyDiv",  am4charts.XYChart);

      // Responsive to screen size
      chart.responsive.enabled = true;
      chart.responsive.useDefault = false
      chart.responsive.rules.push({
        relevant: function(target) {
          if (target.pixelWidth <= 400) {
            return true;
          }
            return false;
          },
          state: function(target, stateId) {
            
            if (target instanceof am4charts.Chart) {
              var state = target.states.create(stateId);
              state.properties.paddingTop = 0;
              state.properties.paddingRight = 15;
              state.properties.paddingBottom = 5;
              state.properties.paddingLeft = 15;
              return state;
            }
            
            if (target instanceof am4charts.Legend) {
              var state = target.states.create(stateId);
              state.properties.paddingTop = 0;
              state.properties.paddingRight = 0;
              state.properties.paddingBottom = 0;
              state.properties.paddingLeft = 0;
              state.properties.marginLeft = 0;
              return state;
            }
            
            if (target instanceof am4charts.AxisRendererY) {
              var state = target.states.create(stateId);
              state.properties.inside = false;
              state.properties.maxLabelPosition = 0.99;
              return state;
            }
            
            if ((target instanceof am4charts.AxisLabel) && (target.parent instanceof am4charts.AxisRendererY)) { 
              var state = target.states.create(stateId);
              state.properties.dy = 0;
              state.properties.paddingTop = 3;
              state.properties.paddingRight = 5;
              state.properties.paddingBottom = 3;
              state.properties.paddingLeft = 5;
              
              // Create a separate state for background
              target.setStateOnChildren = true;
              var bgstate = target.background.states.create(stateId);
              bgstate.properties.fill = am4core.color("#fff");
              bgstate.properties.fillOpacity = 0;
      
              return state;
            }
            
            if ((target instanceof am4core.Rectangle) && (target.parent instanceof am4charts.AxisLabel) && (target.parent.parent instanceof am4charts.AxisRendererY)) { 
               var state = target.states.create(stateId);
               state.properties.fill = am4core.color("#f00");
               state.properties.fillOpacity = 0.5;
               return state;
             }
    
               return null;
              }
            });
            
            chart.hiddenState.properties.opacity = 0;
            
            chart.data = [
            {
                category: "Dilapidated",
                value1: dilap,
                value2: 0
            }
        ];

        // Define chart setting
        chart.colors.step = 2;
        chart.padding(0, 0, 0, 0);
        
        // Axis Setting
        /// Category Axis
        /// Category Axis
        var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
        categoryAxis.dataFields.category = "category";
        categoryAxis.renderer.grid.template.location = 0;
        categoryAxis.renderer.labels.template.fontSize = 0;
        categoryAxis.renderer.labels.template.fill = "#ffffff";
        categoryAxis.renderer.minGridDistance = 5; //can change label
        categoryAxis.renderer.grid.template.strokeWidth = 0;
        
        /// Value Axis
        var valueAxis = chart.xAxes.push(new am4charts.ValueAxis());
        valueAxis.strictMinMax = true;
        valueAxis.calculateTotals = true;
        valueAxis.renderer.labels.template.fontSize = 0;
        valueAxis.renderer.labels.template.fill = "#ffffff";
        valueAxis.renderer.grid.template.strokeWidth = 0;
        
        // Layerview and Expand
        function createSeries(field, name) {
            var series = chart.series.push(new am4charts.ColumnSeries());
            series.dataFields.valueX = field;
            series.dataFields.categoryY = "category";
            series.stacked = true;
            series.dataItems.template.locations.categoryY = 0.5;
            
            // Bar chart line color and width
            series.columns.template.stroke = am4core.color("#00000000"); //#00B0F0
            series.columns.template.strokeWidth = 0.5;
            series.name = name;
            
            var labelBullet = series.bullets.push(new am4charts.LabelBullet());

            if (name === "Dilapidated"){
              series.fill = am4core.color("#00000000");
              labelBullet.locationX = 0.5;
              labelBullet.label.text = "{valueX.formatNumber('#.')}";
              //labelBullet.label.fill = am4core.color("#00FFFFFF");
              labelBullet.label.fill = am4core.color("#FF0000");
              labelBullet.interactionsEnabled = false;
              labelBullet.label.fontSize = 50;
              labelBullet.locationX = 0.5;

            } else if (name === "temp") {
              series.fill = am4core.color("#00000000");
            labelBullet.locationX = 0.5;
            //labelBullet.label.fill = am4core.color("#00FFFFFF");
            labelBullet.label.fill = am4core.color("#FFFFFF");
            labelBullet.interactionsEnabled = false;
            labelBullet.label.fontSize = 19;
            labelBullet.locationX = 0.5;
            }

            series.columns.template.width = am4core.percent(60);
            
            // Click chart and filter, update maps
            const chartElement = document.getElementById("chartPanel");
            series.columns.template.events.on("hit", filterByChart, this);

            function filterByChart(ev) {
                const selectedC = ev.target.dataItem.component.name;
                const selectedP = ev.target.dataItem.categoryY;
                
         view.when(function() {
          view.whenLayerView(obstructionLayer).then(function (layerView) {
            chartLayerView = layerView;
            chartElement.style.visibility = "visible";
            
            obstructionLayer.queryFeatures().then(function(results) {
              const RESULT_LENGTH = results.features;
              const ROW_N = RESULT_LENGTH.length;

              let objID = [];
              for (var i=0; i < ROW_N; i++) {
                  var obj = results.features[i].attributes.OBJECTID;
                  objID.push(obj);
              }

              var queryExt = new Query({
                 objectIds: objID
              });

              obstructionLayer.queryExtent(queryExt).then(function(result) {
                  if (result.extent) {
                      view.goTo(result.extent)
                  }
              });

              if (highlightSelect) {
                  highlightSelect.remove();
              }
              highlightSelect = layerView.highlight(objID);

              view.on("click", function() {
                layerView.filter = null;
                highlightSelect.remove();
              });
            }); // End of queryFeatures
            layerView.filter = {
              where: "Rating = '" + selectedC + "'"
            }
          }); // End of view.whenLayerView
        }); // End of view.when
      } // End of filterByChart
    } // End of createSlices function
    
    createSeries("value1", "Dilapidated");
    createSeries("value2", "temp")

}); // end of queryFeatures
} // end of updateChartWater
SurveyChart();



}); // end am4core.ready()

//////////////////////////////////////////////////////
///////////////////////////////////////////////////////

//*****************************//
//      LayerList             //
//*****************************//
var layerList = new LayerList({
            view: view,
            listItemCreatedFunction: function(event) {
              const item = event.item;
              if (item.title === "Monitoring Structures" ||
                  item.title === "Monitoring Bridge" ||
                  item.title === "Soil Profile" ||
                  item.title === "Survey Extent Line" ||
                  item.title === "OpenStreetMap 3D Buildings"){
                item.visible = false
              }
            }
          });

var layerListExpand = new Expand ({
  view: view,
  content: layerList,
  expandIconClass: "esri-icon-visible",
  group: "top-right"
});
view.ui.add(layerListExpand, {
  position: "top-right"
});
        // End of LayerList
        // End of LayerList
  
view.ui.empty("top-left");

// Legend
var legend = new Legend({
  view: view,
  container: document.getElementById("legendDiv"),
  layerInfos: [
  {
      layer: tbmTunnelLayer,
      title: "TBM Tunnel"
    },
    {
      layer: geotech,
      title: "Soil Profile"
    },
    {
      layer: obstructionLayer,
      title: "OBS Structure"
    },
    {
      layer: bridgeLayer,
      title: "OBS Bridge"
    },
    {
      layer: riverLayer,
      title: "Creek or River"
    },
    {
        layer: natmLayer,
        title: "NATM"
    }
  ]
});

var legendExpand = new Expand({
    view: view,
    content: legend,
    expandIconClass: "esri-icon-legend",
    group: "top-right"
});
view.ui.add(legendExpand, {
    position: "top-right"
});

// Compass Widget
var compass = new Compass({
  view: view});
  // adds the compass to the top left corner of the MapView
  view.ui.add(compass, "top-right");
          
// Full Screen Widget
view.ui.add(
  new Fullscreen({
    view: view,
  }),
  "top-right"
  );

// See-through-Ground        
view.when(function() {
    // allow navigation above and below the ground
    map.ground.navigationConstraint = {
        type: "none"
    };
    // the webscene has no basemap, so set a surfaceColor on the ground
    map.ground.surfaceColor = "#fff";
    // to see through the ground, set the ground opacity to 0.4
    map.ground.opacity = 0.9; //
});
          
document
    .getElementById("opacityInput")
    .addEventListener("change", function(event) {
    //map.ground.opacity = event.target.checked ? 0.1 : 0.9;
    map.ground.opacity = event.target.checked ? 0.1 : 0.6;
});
view.ui.add("menu", "bottom-right");


//////////
      });
    </script>
  </head>
  <div id="viewDiv">
  <body class="sassy-theme">
    <div id="headerTitleDiv">MMSP TUNNEL</div>
    <div class="dateDiv">As of xx, 2022</div>
    <div class="esri-widget" id="dropdownDiv">
      <label for="sel-options">Section:</label>
      <select id="sectionSelect" class="esri-widget"></select>
      <label for="sel-options">Tunnel</label>
      <select id="tunnelSelect" class="esri-widget"></select>
    </div>
    <div id="boxTBM">
      <div id="labelTbm">TBM</div>
      <div class="lowerPanelBox">
        <div id="logoDiv">
          <img src="https://EijiGorilla.github.io/Symbols/TBM.png">
        </div>
        <div id="chartPanel">
          <div id="chartTbmDiv"></div>
        </div>
      </div>
    </div>
    <div id="boxNATM">
      <div id="labelNatm">NATM</div>
      <div class="lowerPanelBox">
        <div id="logoDiv">
          <img src="https://EijiGorilla.github.io/Symbols/NATM_Logo.png">
        </div>
        <div id="chartPanel">
          <div id="chartNatmDiv"></div>
        </div>
      </div>
    </div>
    <div id="boxTotal">
          <div id="labelTotalDiv">TOTAL</div>
          <div class="lowerPanelBox">
            <div id="totalProgressDiv"></div>
          </div>
    </div>
    <div id="boxSurvey">
      <div id="labelSurvey">DILAPIDATED</div>
      <div class="lowerPanelBox">
        <div id="logoDiv">
          <img src="https://EijiGorilla.github.io/Symbols/Broken_House_Logo.png">
        </div>
        <div id="chartPanel">
          <div id="chartSurveyDiv"></div>
        </div>
      </div>
    </div>
    <div id="menu" class="esri-widget">
      <input type="checkbox" id="opacityInput" unchecked />
      <label for="opacityInput">See through ground</label>
    </div>
    </div>
  </body>
</html>