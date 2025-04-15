# BUFFER ANALYSIS
## Table of Content
* What is Buffer Analysis
* Use Cases
* The objective of this project
* Data Required
* Steps Involved
* Output
* Interpretation
* Conclusion

  ## What is Buffer Analysis
  Buffer is defined as a region or an area created around or within a geographic feature such as a point, line, or polygon.
  It is used to determine features that falls within a particular geographic features as specified by the buffer radius and also it can use to determine the number of features that falls outside a particular geographic feature. Buffer analysis as used in this context means the act of making sense out of the buffer that was performed in order to help solve a given spatial problem such as how do we assess the impact of road expansion project on a given location.

  Buffer can be in different forms such as :
    * Point Buffer: it has to deal with creating a circle around a geographic feature which is defined by the radius of the buffer. When the points are that close to each other it  can overlap and as such it may be necessary to dissolve them to form one complex feature.
    * Line Buffer: This kind of buffer deals with creating an area around a linear feature such as a road, river in order to know whether certain features falls within such range or not. For  instance, in constructing a road, a buffer can be performed on a road to determine the number of buildings that falls within that area and the necessary safety measures will be  adheard to.
    * Polygon Buffer: polygonal buffer looks at creating an area around a polygonal feature in order to know the features that falls within the new polygon created.
    * Multi-Ring Buffer: This kind is where you create multiple rings of buffer around a geographic feature which could be either point, line and polygon.
## Use Cases
1. Buffer can be used for gas explosion analysis, where the radius around the gas station will determine the extent of explosion.
2. Buffer can be used in the conservation of ecologically sensitive areas such as Parks, ponds. It helps us to know the extent to which some activities such as deforetation can be carried out without having a negative influence on these ecological zones.

## The objective of this project.
The objective of this project is to assess the number of buildings that will be affected by gas explosion in the Accra New Town Community in Ghana.
The hypothetical gas station that was used for this project was the total energy gas station found in Accra New Town.
The kind of buffer that was used in this project was the Multi-Ring Buffer Type.


## Data Required and Software:
  1. The first data was the shapefile of the gas station, which can be downloaded(Gas_Station)
  2. The Shapefile of the Open Street Maps buildings (OSM), (OSM_Buildings)
  3. ArcGIS Pro 

## Steps Involved
1. Launch ArcGIS pro
2. Bring in the two data sets into the ArcGIS environment
3. The two dataset has already been projected to UTM Zone 30N, if it is your own data, reproject it to projected coordinate system of the area of interest.
4. Search for "Buffer". Choose the analysis one
5. Buffer Tool:
   * input feature  = the gas_station layer
   * output feature class = Any name of interest and it should be save at your preferred directory.
   * Distance [value or field]: Enter 0.5, make sure linear unit is selected and choose kilometers
   * Side Type = Full
   * End Type = Round
   * Method = Planer
   * Dissolve Type = No Dissolve
6. Once all the parameters are specified, click on "Run"
7. Repeat the same buffer process with these different distance [1km, 1.5km and 2km]
8. Second thing to do again is Clip all the buildings that falls within each buffer zone
     1. Search for Clip  from the search bar and select the analysis one
     2. input features = osm building dataset
     3. clip features = 0.5km buffered polygon
     4. output features = any name and saved it in your directory
     5. Click "Run"
     6. Do same for the 3 other buffer rings
9. Counting the number of buildings within each buffer:
      * The first approach is to select the clipped building of interest, right click and select "opent attribute table"
      * You will see "0 of a number is selected" at the button lift side. The number is is the the total number of buildings within that buffer from the gas station.
      * The second approach is to use arcpy to count it:
          * ```
            import arcpy
             #Counting the number of affected buildings in each zone
            Z1_Buildings = int(arcpy.GetCount_management("Z1 Buildings").getOutput(0))
             print(f'The total Buildings affected within Zone 1 is {Z1_Buildings} buildings')
            ```
        * The same can be used to determine the rest of the buildings in each clipped buffer.
        * **Note**: Lets say, we have these clipped buildings A, B , C and D. So far as buffer is concerned, B is the addition of A.
        * To get only B = B - A, and the same way to get C only = C - B
  10. Map Preparation:
        * Create a new layout layer (Architectural C), if you are using the same dataset.
        * Add the map layer
        * Add basemap ("Dark Gray Canvas"
        * Because of it dark nature, make sure most of the labels are changed to white to make it Visible.
        * Add all other map cosmetics
        * Create a bar chart showing the buildings that were affected in each Zone
        * Colors used: 
            * Z1 (#FF0000)
            * Z2 (#FFD37F)
            * Z3 (#FF00C5)
            * Z4 (#38A800)

## Output
The feature below shows the output of the final map produced during the process
![Layout5](https://github.com/user-attachments/assets/aa3a1efd-2a20-473e-8883-281aff45c8a2)

Chart showing the number of buildings affected by each buffer
![Image](https://github.com/user-attachments/assets/16e28902-ae81-4df0-8111-37e35c82a6f7)

## Interpretation
The project made use of terms such as risk zone whichs was basically the distance from the gas station to the distance that was specified. Also, it was based on the distance decay principle which is the farther you are from the gas station the safer you are. Four risk zones were identified, they are: 
  * Z1 = Highly Risky Areas, thus 0.5 km buffer
  * Z2 = Risky Areas, thus 1 km buffer
  * Z3 = Safe Areas, thus 1.5 km buffer
  * Z4 = Highly Safe Areas, thus 2 km buffer

At the end of the project it was found out that, people who are likely to be affected by an explosion of 0.5 km from the gas station in Accra New Town were **2558** buildings, those who will be affected within a 1 km explosion were **4968** buildings. Moreover, there were **7308** buildings that would be affected by an explosion of 1.5 km and lastly, the buildings that were considered highly safe were **6384**.

## Conclusion
The essence of this project was to find out the number of buildings that will be affected by gas explosion. From the interpretation part it can be concluded that the goal of this project was achieved. All said and done, I will conclude by saying that "Buffer is Simple but Powerful"

