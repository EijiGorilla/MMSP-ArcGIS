# MMSP-ArcGIS


## How To Use ESRI's World Imagery and OpenStreeMap for Offline Use in Collector for ArcGIS

* World Imagery
1. GO to https://www.arcgis.com/home/search.html?q=for%20export&t=content&focus=layers&start=1&sortOrder=true&sortField=relevance
2. Choose World Imagery (for Export)
3. Open it in a web map of ArcGIS Online
4. Add feature of your interest
5. Save As

* OpenStreetMap
1. Go to the link above and search "OpenStreetMap" and choose "Tile Layer" (Do NOT choose Layer Package: you will not be able to use as a basemap)
2. Open the OpenStreetMap in a web map of ArcGIS Online
3. Add feature class (shape files)
4. Save As

* Upload to Collector for ArcGIS
1. Open the Collector
2. Choose a Map you saved in Content of ArcGIS Online

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
