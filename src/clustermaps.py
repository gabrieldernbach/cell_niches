"""
Module for hierarchical clustering and visualization of tissue spot data.

This module processes tissue spot data to perform hierarchical clustering on both rows (spots) 
and columns (features) using distance metrics and linkage methods. It visualizes the clustered 
data as a clustermap with dendrograms and generates output images.

Main Components:
- `load_and_preprocess_data`: Loads data from a parquet file and adjusts its structure for clustering.
- `log_normalize`: Applies logarithmic normalization to the data to compress dynamic ranges.
- `calculate_linkage`: Computes the hierarchical linkage matrix for clustering using specified method and metric.
- `extract_clusters`: Extracts flat clusters from a linkage matrix based on the maximum number of clusters.
- `apply_color_map`: Applies a color map to the cluster labels to visualize groupings.
- `create_clustermap`: Generates a clustermap with hierarchical dendrograms for rows and columns, visualizing clusters.
- `run`: Main function that handles the full pipeline from loading data to clustering and saving clustermaps.

The module is designed to work without a graphical frontend (via `mpl.use('Agg')`), generating files directly.
"""
import colorcet as cc
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import ListedColormap
from scipy.cluster import hierarchy
from scipy.spatial import distance

mpl.use('Agg')  # use without front-end interactive windows, only create files


def load_and_preprocess_data(filepath):
    """
    Loads tissue spot data from a parquet file and prepares it for clustering.
    
    The index of the data is renamed to "individual tissue spot" to get descriptive labels 
    of the axis during plotting, and column names, originally starting from 0, are incremented by 1.

    Args:
        filepath (str): The path to the input parquet file containing tissue spot data.

    Returns:
        pd.DataFrame: The loaded and preprocessed DataFrame with adjusted index and column names.
    """
    data = pd.read_parquet(filepath)
    data.index.name = "individual tissue spot"
    data.columns = data.columns.astype(int) + 1
    return data


def log_normalize(data, factor=10):
    """
    Apply logarithmic normalization to compress the dynamic range of the data.
    The log-compression mitigates the impact of individual high-scoring entities on the clustering.

    Args:
        data (pd.DataFrame): The input data to be normalized.
        factor (float, optional): The scaling factor for normalization. Default is 10.

    Returns:
        np.ndarray: Logarithmically normalized data.
    """
    return np.log1p(data / factor)


def calculate_linkage(data, method='complete', metric='euclidean', axis=0):
    """
    Calculate hierarchical linkage for clustering using the specified method and metric.
    
    The linkage is calculated on either rows or columns of the data based on the axis parameter.

    Args:
        data (pd.DataFrame): Input data for clustering.
        method (str, optional): The linkage method to use (e.g., 'complete', 'average'). Default is 'complete'.
        metric (str, optional): The distance metric to use (e.g., 'euclidean', 'cosine'). Default is 'euclidean'.
        axis (int, optional): Axis to calculate linkage on (0 = columns, 1 = rows). Default is 0.

    Returns:
        np.ndarray: Linkage matrix for hierarchical clustering.
    """
    if axis == 1:
        data = data.T # Transpose if clustering on rows
    # Compute pairwise distances between data points
    distances = distance.pdist(data)
    # Generate linkage matrix based on method and metric
    return hierarchy.linkage(distances, method=method, metric=metric)


def extract_clusters(linkage, max_clusters=15):
    """
    Generates flat clusters from the hierarchical clustering results by cutting the 
    dendrogram at the specified number of clusters.

    Args:
        linkage (np.ndarray): The linkage matrix from hierarchical clustering.
        max_clusters (int, optional): The desired number of clusters to extract. Default is 15.

    Returns:
        np.ndarray: An array of cluster labels indicating the cluster assignment for each data point.
    """
    return hierarchy.fcluster(linkage, t=max_clusters, criterion='maxclust')


def apply_color_map(cluster_labels, palette=cc.glasbey_category10):
    """
    Maps cluster labels to specific colors using the provided color palette.

    Args:
        cluster_labels (np.ndarray): An array of cluster labels.
        palette (list, optional): The color palette to use for visualizing clusters. Default is 'glasbey_category10'.

    Returns:
        np.ndarray: Array of colors mapped to each cluster label.
    """
    return ListedColormap(palette)(cluster_labels)


def create_clustermap(data, row_linkage, col_linkage, cluster_colors, figsize=(13, 6)):
    """
    Creates a clustermap with hierarchical clustering on both rows and columns, and applies 
    the provided colors to represent flattened column clusters.
    The clustermap visualizes hierarchical relationships between rows and columns as dendrograms.

    Args:
        data (pd.DataFrame): The input data to visualize in the clustermap.
        row_linkage (np.ndarray): Linkage matrix for rows (spots).
        col_linkage (np.ndarray): Linkage matrix for columns (features).
        cluster_colors (np.ndarray): Color-coded clusters for columns.
        figsize (tuple, optional): The size of the output figure. Default is (13, 6).

    Returns:
        sns.ClusterGrid: The clustermap object that can be used for further customization or saving.
    """
    g = sns.clustermap(
        data,
        figsize=figsize,
        xticklabels=False, # Disable x-axis labels to avoid clutter by spot-uuids
        z_score=1, # Normalize data by standardizing rows (z-score normalization)
        dendrogram_ratio=(0.02, 0.1), # Control size ratio of row/column dendrograms
        cbar_pos=None, # Disable the color bar
        col_colors=cluster_colors,  # Color for columns based on flat-cluster assignments
        row_linkage=row_linkage, # Linkage for rows (spots)
        col_linkage=col_linkage, # Linkage for columns (features)
    )
    return g


def run():
    """
    Executes the full pipeline: loading data, normalization, clustering, and clustermap creation.

    The function processes tissue spot data for each specified entity, applying hierarchical 
    clustering and generating clustermap visualizations. The clustermaps are saved as PNG files.

    For each entity:
    1. Loads and preprocesses data from a parquet file.
    2. Applies logarithmic normalization to the data.
    3. Performs hierarchical clustering on both rows and columns.
    4. Generates and saves clustermap images with dendrograms and color-coded clusters.
    """
    for entity in ["LUAD", "LUSC"]:
        # Load and preprocess data specific to the entity
        data_path = f"/data/tier3/publication_all_spots_niche_loading_{entity}.parquet"
        raw_data = load_and_preprocess_data(data_path)
        normalized_data = log_normalize(raw_data)
        
        # Perform hierarchical clustering on both columns (features) and rows (spots)
        col_linkage = calculate_linkage(normalized_data, axis=0)
        row_linkage = calculate_linkage(normalized_data, axis=1)
        
        # Extract clusters for columns and apply color mapping
        col_clusters = extract_clusters(col_linkage)
        col_colors = apply_color_map(col_clusters)

        # Create clustermap and save as PNG file
        g = create_clustermap(normalized_data.T, row_linkage, col_linkage, col_colors)
        g.savefig(f"/data/tier4/{entity}_clustermap.png")
        plt.clf();
        plt.cla()


if __name__ == "__main__":
    run()
