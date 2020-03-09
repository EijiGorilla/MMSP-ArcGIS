# MMSP-ArcGIS


## How To Use ESRI's World Imagery and OpenStreeMap for Offline Use in Collector for ArcGIS

* World Imagery
1. Open ArcGIS Pro
2. Click Catalogue and Portal (All Portal).
3. Search for World Image (for export)
4. Drag and drop the Image into the current map.
5. Click Download File in the Offline panel
6. Choose scale of your interest
7. Once the imagery is shown in the Content, right-click the Imagery file, go to Share, and choose "Share As Web Layer"
8. Make sure to choose "tile" when Publish.
9. Open ArcGIS Online and go to Content
10. Find the Imagery, click "View item details" and Settings.
11. Adjust the Visible Range
12. Build Tiles (Make sure to build tiles and % complete is 100%; otherwise, you fail to use the imagery as a basemap)
13. Make sure to check "Offline"
14. Open Map Viewer and create a New Map.
15. Click Add Layer and My Content.
16. Click the Imagery name and choose "Add a Basemap" (note: if you do not see this option. Something is wrong)
17. Add feature of your interest for Collector for ArcGIS
18. Save as
FYI: https://www.arcgis.com/home/search.html?q=for%20export&t=content&focus=layers&start=1&sortOrder=true&sortField=relevance

* Refer to the following link for Offline Use in Collector for ArcGIS
https://doc.arcgis.com/en/arcgis-online/manage-data/take-maps-offline.htm

## 本プロジェクトで使用する座標系
*座標系に関する情報
他企業と使用する標高値の基準が異なっていたため、標高値に差異が生じていました。フィリピン国では１つの基準点に対して３つの座標系が存在します。
1. WGS84(楕円体経緯度表記)
2. WGS84 UTM(楕円体座標値表記)
3. PRS92 PTM(平面直角座標値表記)

他企業が基準とした標高値は1、当プロジェクトは3における平均海面標高値です。設計を行うために使用する座標系は3です。また、標高値は平均海面の標高値を基準にすることが一般的です。

当プロジェクトの標高にあわせ、他企業が作成した平面図の標高値を変換しました。変換後のCADデータは団内サーバに格納済です。設計は、標高値に相対的な問題が無かった為、標高値の差分のみ考慮すれば可能です。

*GIS SpecialistのMike CAULANの情報と合わせると、MMSPで使用する座標系は：
1. WGS84 UTM Zone 51N (Projected Coordinate System：ArcGIS)
2. WGS84 (Geographic Coordinate System：ArcGIS)
3. PRS1992 Philippine Zone III.prj (CADで使用する座標系）

## Height Conversion: PRS 1992 Philippine Zone III to EGM2008 Geoid
*Vertical Coordinate System (VCS)  
VCS defines the origin for height or depth and is referenced to two types of a surface: Spheroid (ellipsoid) or Gravity-based (geoid).
1. Spheroid (e.g., WGS84)
2. Gravity-based (EGM2008)

*Geoid  
The geoid is an equipotential, or level, surface of the earth’s gravity field.
![Geoid](https://github.com/EijiGorilla/MMSP-ArcGIS/blob/master/Geoid%20Height.gif)  
In the illustration above, the green line represents the geoid surface. It roughly curves to follow the topography. The dashed line represents the surface of the spheroid. The **h is the height above the spheroid, or ellipsoid (HAE)**. In this case, the height is a negative value. **Geoid undulation, N**, is the distance between the spheroid and geoid surface. The **orthometric height, H**" is related to the spheroid height by the following:

*Conversion from PRS 1992 Philippine Zone III to EGM2008    
EGM2008 is geoid (gravity-based), and ArcGIS Pro has conversion equation for EGM2008. However, there is no direct way of converting PRS 1992 to EGM2008 Geiod. As such, PRS1992 must be first converted to WGS84 and then to EGM2008. Please refer to steps below using ArcGIS Pro.  
![Conversion Figure](https://github.com/EijiGorilla/MMSP-ArcGIS/blob/master/Illustration%20of%20VCS%20PRS92%20to%20EGM2008Geoid.png =10x10)  
