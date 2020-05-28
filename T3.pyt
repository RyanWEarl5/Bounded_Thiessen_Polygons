import arcpy
import scipy
import os
import numpy as np
import pandas as pd  
from scipy.spatial import ConvexHull

class Toolbox(object):
    def __init__(self):

        self.label = "T3"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [BoundedThiessen]


class BoundedThiessen(object):

    def __init__(self):
        self.label = "Bounded Thiessen Polygons"
        self.description = "Finds the cross median of point clusters, creates Thiessen Polygons from them and bounds the polygons to the extent of the points"
        self.canRunInBackground = False
    
    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName = "Input xy table path",
            name = "xy_data",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input"
        )
        param1 = arcpy.Parameter(
            displayName = "Output GDB Path",
            name = "GDBFolder",
            datatype = "DEFolder",
            parameterType = "Required",
            direction = "Input"
        )
        param3 = arcpy.Parameter(
            displayName = 'Output Name',
            name = 'OutName',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input'
        )
        params = [param0, param1, param2, param3]
        return params


    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):

        # read csv as df
        df = pd.read_csv(parameters[0].valueAsText)
        gdb_path = parameters[1].valueAsText
        points = df[['lat', 'lon']]

        ## potential outlier detection with nearest neighbors goes here ## 

        # get median location of points within sheet block 
        sb = df.groupby('sb1', as_index=False)['lon','lat'].median()
        sb.to_csv(gdb_path + "\\sb.csv")

        # calculate the convex hull of input points 
        hull = ConvexHull(points)
        vertices = points.iloc[hull.vertices].reset_index(drop=True)

        # create geometry for boundary shapefile using vertices of convex hull
        coordinates = []
        for lat, lon in zip(vertices.lat, vertices.lon): 
            coordinates.append((lon, lat))   

        # Set workspace, create file gdb
        env.workspace = gdb_path
        
        # create point shapefile form sheet block csv
        arcpy.management.XYTableToPoint(
            gdb_path + "\\sb.csv",
            "sheet_blocks",
            x_field = "lon",
            y_field = "lat",
            coordinate_system = arcpy.SpatialReference(4326)
        )

        # define extent of thiessen polygons
        xmin = points['lon'].min()
        ymin = points['lat'].min()
        xmax = points['lon'].max()
        ymax = points['lat'].max()
        arcpy.env.extent = arcpy.Extent(xmin, ymin, xmax, ymax)

        # construt Thiessen polygons from sheet block locations
        arcpy.CreateThiessenPolygons_analysis("sheet_blocks", "sb_poly", "ALL")
        arcpy.en.extent = "MAXOF"

        # create empty boundary feature class
        result = arcpy.management.CreateFeatureclass(
            out_path=gdb_path, 
            out_name="boundary", 
            geometry_type="POLYGON", 
            spatial_reference=4326)
        feature_class = result[0]

        # write geometry to feature class
        with arcpy.da.InsertCursor(feature_class, ['SHAPE@']) as cursor:
            cursor.insertRow([coordinates])
        
        # clip polygons to point boundaries
        arcpy.analysis.Clip("sb_poly", "boundary", parameter[2].valueAsText, None)

        return 