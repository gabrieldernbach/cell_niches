"""
Module for loading and deserializing spatial geometry data.

This module is responsible for loading spatial data (e.g., points, regions) and associated metadata 
from Parquet files, and converting serialized Well-Known Binary (WKB) geometries into usable geometric 
objects. The resulting DataFrames are used for spatial analysis.

Main Components:
- `deserialize_wkb`: Deserializes WKB geometries from a DataFrame column into shapely geometry objects.
- `get_geometries`: Loads spatial point, marker, and region data from Parquet files, and deserializes the WKB geometries.
"""

import io

import pandas as pd
import shapely.wkb


def deserialize_wkb(df):
    """
    Deserializes Well-Known Binary (WKB) geometry data from a DataFrame column into shapely geometry objects.
    
    The function expects the WKB-encoded geometries to be stored in the 'geom' column of the DataFrame. 
    Each WKB entry is deserialized into a shapely geometry object (e.g., Point, Polygon) to enable 
    spatial operations.

    Args:
        df (pd.DataFrame): The input DataFrame containing a 'geom' column with WKB-encoded geometries.

    Returns:
        pd.DataFrame: A DataFrame with the 'geom' column replaced by shapely geometry objects.
    
    Example:
        The function is typically used in a pipeline, such as:
        
        df = pd.read_parquet("points.parquet").pipe(deserialize_wkb)
    """
    # Lambda function to deserialize each WKB entry using shapely.wkb
    load_wkb = lambda x: shapely.wkb.load(io.BytesIO(x))
    # Apply the deserialization to the 'geom' column and return the modified DataFrame
    return df.assign(geom=df.geom.apply(load_wkb))


def get_geometries():
    """
    Loads spatial points, marker data, and region geometries from Parquet files and deserializes the WKB geometries.
    
    This function reads spatial and non-spatial data from Parquet files, including:
    - Points: Spatial data representing individual points (e.g., cell positions).
    - Marks: Non-spatial data representing cell markers or other metadata.
    - Regions: Spatial data representing defined regions (e.g., tissue sections or areas of interest).

    The point and region geometries are serialized in WKB format and are deserialized into shapely geometry objects 
    for spatial operations. The deserialized geometries are stored in the 'geom' column of the resulting DataFrames.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: A tuple of three DataFrames:
        - marks: DataFrame containing cell marker data.
        - points: DataFrame containing point geometries (deserialized shapely objects) and associated metadata.
        - regions: DataFrame containing region geometries (deserialized shapely objects) and associated metadata.

    Example:
        marks, points, regions = get_geometries()
    """
    points = pd.read_parquet("/data/tier2/points").pipe(deserialize_wkb)
    marks = pd.read_parquet("/data/tier2/marks")
    regions = pd.read_parquet("/data/tier2/regions").pipe(deserialize_wkb)
    return marks, points, regions
