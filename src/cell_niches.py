import pathlib

import duckdb
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
from sklearn.cluster import MiniBatchKMeans
from tqdm import tqdm

from src.utils import get_geometries


class Neighbourhood:
    def __init__(self, radius=0.034):
        self.radius = radius

    def __call__(self, points, marks):
        df = points.merge(marks, on=["wsi_uuid", "polygon_uuid"], validate="one_to_one")
        xy = np.c_[df.geom.apply(lambda point: point.x), df.geom.apply(lambda point: point.y)]

        multihot = df.drop("geom", axis=1)
        neighbours = KDTree(xy).query_ball_point(xy, r=self.radius)
        aggregated = np.stack([multihot.iloc[n].sum(0) for n in neighbours])
        aggregated = pd.DataFrame(
            aggregated,
            index=multihot.index,
            columns=multihot.columns
        )
        return aggregated


def run_neighbourhood_aggregation():
    marks, points, regions = get_geometries()
    wsi_uuids = points.wsi_uuid.drop_duplicates()

    outcome = []
    for wsi_uuid in tqdm(wsi_uuids, desc="Aggregating neighbourhood of each cell"):
        outcome.append(Neighbourhood(0.034)(
            points.query("wsi_uuid==@wsi_uuid").set_index(["polygon_uuid", "wsi_uuid"]),
            marks.query("wsi_uuid==@wsi_uuid").set_index(["wsi_uuid", "polygon_uuid"])
        ))
    outcome = pd.concat(outcome)
    outcome.reset_index().to_parquet("/data/tier3/cell_neighbourhoods", partition_cols=["wsi_uuid"])


def gethist(df):
    df = df.fillna(0)
    df = np.log1p(df)
    vals = df.values
    vals = vals / (vals.sum(-1, keepdims=True) + 1e-6)
    return vals


def columns2strings(df):
    df.columns = df.columns.astype("str")
    return df


def cluster(df):
    # normalize (sum to one) and log-compress
    hists = gethist(df)
    # use mini-batch, as we have millions of neighbourhoods
    kms = MiniBatchKMeans(
        n_clusters=10,
        random_state=0,
        n_init="auto",
        verbose=10,
        batch_size=8000,
        max_no_improvement=200
    )
    cluster_ids = pd.Series(kms.fit_predict(hists), index=df.index)
    prototypes = pd.DataFrame(kms.cluster_centers_, columns=df.columns)
    return cluster_ids, prototypes


def run_clustering():
    for entity in ["LUAD", "LUSC"]:
        # metadata contains the entity
        # join with neighbourhoods subset ("LUAD/LUSC")
        neighbourhoods = duckdb.execute("""
        with wsi_uuid_to_entity as (select parent, first(ENTITY) as entity
        from read_csv('/data/tier1/metadata/he_to_mif.csv')
        group by parent)
        select cn.*
        from read_parquet('/data/tier3/cell_neighbourhoods/*/*.parquet') cn
        join wsi_uuid_to_entity w2e on cn.wsi_uuid = w2e.parent
        where entity=$entity
        """, parameters=dict(entity=entity))
        neighbourhoods = neighbourhoods.df().set_index(["polygon_uuid", "wsi_uuid"])

        cluster_ids, prototypes = cluster(neighbourhoods)
        (  # for each cell, store which niche it was assigned to
            cluster_ids
            .to_frame("niche_id")
            .reset_index()
            .to_parquet(f"/data/tier3/cell_niche_assignment", partition_cols=["wsi_uuid"])
        )
        (  # for each spot, count how many cells were assignet to a given niche
            cluster_ids
            .to_frame("niche_id")
            .groupby("wsi_uuid")
            .niche_id
            .value_counts()
            .unstack()
            .fillna(0)
            .to_parquet(f"/data/tier3/spot_niche_loading", partition_cols=["wsi_uuid"])
        )
        (  # each niche comes with a prototypical neighbourhood (expression)
            prototypes
            .to_parquet(f"/data/tier3/{entity}_niche_prototypes.parquet")
        )


def run():
    pathlib.Path("/data/tier3/").mkdir(parents=True, exist_ok=True)
    run_neighbourhood_aggregation()
    run_clustering()


if __name__ == "__main__":
    run()
