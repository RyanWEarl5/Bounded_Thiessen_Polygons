# Bounded_Thiessen_Polygons
This arcgis tool takes a csv of xy coordinate points broken up by sheet block. It does this by finding the cross median of point clusters, calculates the convex hull for the entirety of the system of points, defines the vertices of the convex hull, calculates thiessen polygons between median points, and bounds these polygons using by creating a shapefile from the vertices of the convex hull and clipping the polygon regions to it.