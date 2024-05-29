import io

import pandas as pd
import shapely.wkb


def deserialize_wkb(df):
    """deserialize wkb expected in df.geom, intended use in df.pipe(load_wkbs)"""
    load_wkb = lambda x: shapely.wkb.load(io.BytesIO(x))
    return df.assign(geom=df.geom.apply(load_wkb))


def get_geometries():
    points = pd.read_parquet("/data/tier2/points").pipe(deserialize_wkb)
    marks = pd.read_parquet("/data/tier2/marks")
    regions = pd.read_parquet("/data/tier2/regions").pipe(deserialize_wkb)
    return marks, points, regions
