"""
Module for neighbourhood aggregation and clustering of spatial data.

This module processes spatial points and corresponding marks to compute neighbourhood features 
within a defined radius. It then performs clustering on these aggregated neighbourhoods 
using MiniBatchKMeans, assigning each point to a niche and generating prototypical neighbourhoods 
for each cluster.

Main Components:
- `Neighbourhood`: A class to aggregate spatial marks based on proximity using KDTree.
- `run_neighbourhood_aggregation`: Function to apply neighbourhood aggregation for multiple WSI UUIDs.
- `cluster`: Function to perform MiniBatchKMeans clustering on aggregated neighbourhood data.
- `run_clustering`: Function to execute the clustering process for different entities.
- `run`: Main function that coordinates the neighbourhood aggregation and clustering workflow.
"""

import pathlib

import duckdb
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
from sklearn.cluster import MiniBatchKMeans
from tqdm import tqdm

from src.utils import get_geometries


class Neighbourhood:
    """
    This class represents a Neighbourhood, which aggregates marks from spatial points within a certain radius.
    
    Attributes:
        radius (float): The radius within which neighbours are aggregated.
    """
    def __init__(self, radius=0.034):
        """
        Initializes the Neighbourhood with a specified radius.

        Args:
            radius (float): The distance within which to search for neighbours. Default is 0.034 µm
                and corresponds to the size of the radius of a lymphocyte added to the diameter of a large macrophage.
        """

        self.radius = radius

    def __call__(self, points, marks):
        """
        Aggregate marks for each point based on neighbouring points within the defined radius.

        Args:
            points (pd.DataFrame): DataFrame containing spatial points (includes columns like 'wsi_uuid', 'polygon_uuid', and 'geom').
            marks (pd.DataFrame): DataFrame containing marks corresponding to the points.

        Returns:
            pd.DataFrame: Aggregated marks with neighbourhood features.
        """
        # Merge points and marks on 'wsi_uuid' and 'polygon_uuid'
        df = points.merge(marks, on=["wsi_uuid", "polygon_uuid"], validate="one_to_one")
        # Extract x, y coordinates from geometry
        xy = np.c_[df.geom.apply(lambda point: point.x), df.geom.apply(lambda point: point.y)]

        # Drop geometry from the dataframe
        multihot = df.drop("geom", axis=1)
        # Build KDTree to find neighbours within the radius
        neighbours = KDTree(xy).query_ball_point(xy, r=self.radius)
        # Aggregate the marks for each point based on its neighbours
        aggregated = np.stack([multihot.iloc[n].sum(0) for n in neighbours])
        aggregated = pd.DataFrame(
            aggregated,
            index=multihot.index,
            columns=multihot.columns
        )
        return aggregated


def run_neighbourhood_aggregation():
    """
    Runs the neighbourhood aggregation for each whole slide image (WSI) UUID.
    
    This function reads geometries (marks, points, regions) and iteratively applies the Neighbourhood class 
    to aggregate marks for each point, saving the results to a parquet file.
    """
    # Retrieve geometry data (marks, points, regions)
    marks, points, regions = get_geometries()
    # Get unique WSI UUIDs
    wsi_uuids = points.wsi_uuid.drop_duplicates()

    outcome = []
    # Loop through each WSI UUID and aggregate the neighbourhood data
    for wsi_uuid in tqdm(wsi_uuids, desc="Aggregating neighbourhood of each cell"):
        outcome.append(Neighbourhood(0.034)(
            points.query("wsi_uuid==@wsi_uuid").set_index(["polygon_uuid", "wsi_uuid"]),
            marks.query("wsi_uuid==@wsi_uuid").set_index(["wsi_uuid", "polygon_uuid"])
        ))
    # Concatenate all results and save to parquet
    outcome = pd.concat(outcome)
    outcome.reset_index().to_parquet("/data/tier3/cell_neighbourhoods", partition_cols=["wsi_uuid"])


def gethist(df):
    """
    Log-compresses and normalizes the densities in the dataframe for further processing.
    
    Args:
        df (pd.DataFrame): The input DataFrame to be normalized and log-compressed.
    
    Returns:
        np.ndarray: The normalized and log-compressed values from the input DataFrame.
    """
    df = df.fillna(0) # Fill missing values with 0, if no cell is observed we call it 0 density
    df = np.log1p(df) # Apply log compression to mitigate distribution skew typically observed in densities
    vals = df.values # Keep an array of values only 
    vals = vals / (vals.sum(-1, keepdims=True) + 1e-6)  # Normalize (sum to 1)
    return vals


def columns2strings(df):
    """
    Convert column names of the DataFrame to string type.

    Args:
        df (pd.DataFrame): DataFrame whose columns need conversion to string.

    Returns:
        pd.DataFrame: DataFrame with columns converted to strings.
    """
    df.columns = df.columns.astype("str")
    return df


def cluster(df):
    """
    Perform clustering on the neighbourhoods using MiniBatchKMeans.
    
    Args:
        df (pd.DataFrame): The input DataFrame representing the neighbourhood features.

    Returns:
        pd.Series: Cluster assignments for each neighbourhood.
        pd.DataFrame: Prototypical neighbourhood features for each cluster.
    """
    # normalize (sum to one) and log-compress
    hists = gethist(df)
    # Initialize MiniBatchKMeans for clustering
    kms = MiniBatchKMeans(
        n_clusters=10,
        random_state=0,
        n_init="auto",
        verbose=10,
        batch_size=8000,
        max_no_improvement=200
    )
    # Fit the model and get cluster IDs
    cluster_ids = pd.Series(kms.fit_predict(hists), index=df.index)
    # Extract prototypical neighbourhoods (cluster centers)
    prototypes = pd.DataFrame(kms.cluster_centers_, columns=df.columns)
    return cluster_ids, prototypes


def run_clustering():
    """
    Executes the clustering process for each entity ('LUAD', 'LUSC') by joining metadata and neighbourhood data.
    
    Saves the cluster assignments, niche loading, and prototypical neighbourhoods as parquet files.
    """
    for entity in ["LUAD", "LUSC"]:
        # metadata contains the entity
        # join with neighbourhoods subset ("LUAD/LUSC")
        
        # Join metadata with neighbourhood data based on WSI UUID and entity
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

        # Perform clustering
        cluster_ids, prototypes = cluster(neighbourhoods)
        # Store the results
        # For each cell, store which niche it was assigned to
        (  
            cluster_ids
            .to_frame("niche_id")
            .reset_index()
            .to_parquet(f"/data/tier3/cell_niche_assignment", partition_cols=["wsi_uuid"])
        )
        # For each spot, count how many cells were assigned to each niche
        (
            cluster_ids
            .to_frame("niche_id")
            .groupby("wsi_uuid")
            .niche_id
            .value_counts()
            .unstack()
            .fillna(0)
            .to_parquet(f"/data/tier3/spot_niche_loading", partition_cols=["wsi_uuid"])
        )
        # Save the prototypical neighbourhoods for each niche
        (  
            prototypes
            .to_parquet(f"/data/tier3/{entity}_niche_prototypes.parquet")
        )


def run():
    """
    Main function to execute the full pipeline: 
    - Neighbourhood aggregation
    - Clustering
    """
    # Ensure the output directory exists
    pathlib.Path("/data/tier3/").mkdir(parents=True, exist_ok=True)
    # Run neighbourhood aggregation
    run_neighbourhood_aggregation()
    # Run clustering on the aggregated neighbourhoods
    run_clustering()


if __name__ == "__main__":
    run()
