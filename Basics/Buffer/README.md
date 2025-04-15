# BUFFER ANALYSIS
## Table of Content
* What is Buffer Analysis
* Use Cases
* The objective of this project
* Data Required
* Steps Involved
* Output

  ## What is Buffer Analysis
  Buffer is defined as a region or an area created around or within a geographic feature such as a point, line, or polygon.
  It is used to determine features that falls within a particular geographic features as specified by the buffer radius and also it can use to determine the number of features that falls outside a particular geographic feature.

  Buffer can be in different forms such as :
      * Point Buffer: it has to deal with the creating a circle around a geographic feature which is defined by the radius of the buffer. When the points are that close tho each other it  can overlap and as such it may be necessary to dissolve them to form one complex feature.
      * Line Buffer: This kind of buffer deals with creating an area around a linear feature such as a road in order to know whether certain features falls within such range or not. For  instance, in constructing a road a buffer can be performed on a road to determine the number of buildings that falls within that area and the necessary safety measures will be  adheard to.
    * Polygon Buffer: polygonal buffer looks at creating an area around a polygonal feature in order.
    * Multi-Ring Buffer: This kind is where you create multiple rings of buffer around a geographic feature which could be either point, line and polygon.
## Use Cases
1. Buffer can be used for gas explosion analysis, where the radius around the gas station will determine the extent of explosion.
2. Buffer can be used in the conservation of ecologically sensitive areas such as Parks, ponds. It helps us to know the extent to which some actives such as deforetation can be carried without having a negative influence on the work

## The objective of this project.
The objective of this project is to assess the number of buildings that will be affected by gas explosion in the Accra New Town Community.
The hypothetical gas station that was used for thsi project was the total energy gas station found in Accra New Town.
The kind of buffer that was used in this project was the Multi-Ring Buffer Type.


## Data Required and Software:
  1. The first data was the shapefile of the gas station.
  2. The Shapefile of the Open Street Maps buildings (OSM)
  3. ArcGIS Pro 

## Steps Involved
1. Launch ArcGIS pro
2. Bring in the two data sets into the ArcGIS environment
3. Change the Coordinate System of the project to UTM Zone 30N
4. Search for "Buffer". Choose the analysis one
5. Buffer Tool:
   * input feature  = the gas_station layer
   * output feature class = Any name of interest and it should be save at your preferred directory.
   * Distance [value or field]: Enter 0.5, make sure linear unit is selected and choose kilometers
   * Side Type = Full
   * End Type = Round
   * Method = Planer
   * Dissolve Type = No Dissolve
6. Once all the parameters are specified, click on run
7. Do the same for buffer for 1km, 1.5km and 2km
8. Second thing to do again is Clip all the buildings that falls within each buffer zone
     1. Search for Clip  from the search bar and select the analysis one
     2. input features = osm building dataset
     3. clip features = 0.5km buffered polygon
     4. output features = any name and saved it in your directory
     5. Click "Run"
     6. Do same for the 3 other buffer rings
9. Counting the number of buildings within each buffer:
      * The first approach is to use to select the cliffed building of interest, right click and select "opent attribute table"
      * You will see "0 of a number is selected" at the button lift side. The number is is the the total number of buildings within that buffer from the gas station.
      * The second approach is to use arcpy to count it:
          * ```
            import arcpy
             #Counting the number of affected buildings in each zone
            Z1_Buildings = int(arcpy.GetCount_management("Z1 Buildings").getOutput(0))
             print(f'The total Buildings affected within Zone 1 is {Z1_Buildings} buildings')  ```
    
