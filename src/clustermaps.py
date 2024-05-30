import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster import hierarchy
from scipy.spatial import distance
from matplotlib.colors import ListedColormap
import colorcet as cc
import seaborn as sns


def load_and_preprocess_data(filepath):
    data = pd.read_parquet(filepath)
    data.index.name = "individual tissue spot"
    data.columns = data.columns.astype(int) + 1
    return data


def log_normalize(data, factor=10):
    return np.log1p(data / factor)


def calculate_linkage(data, method='complete', metric='euclidean', axis=0):
    if axis == 1:
        data = data.T
    distances = distance.pdist(data)
    return hierarchy.linkage(distances, method=method, metric=metric)


def extract_clusters(linkage, max_clusters=15):
    return hierarchy.fcluster(linkage, t=max_clusters, criterion='maxclust')


def apply_color_map(cluster_labels, palette=cc.glasbey_category10):
    return ListedColormap(palette)(cluster_labels)


def create_clustermap(data, row_linkage, col_linkage, cluster_colors, figsize=(13, 6)):
    g = sns.clustermap(
        data,
        figsize=figsize,
        xticklabels=False,
        z_score=1,
        dendrogram_ratio=(0.02, 0.1),
        cbar_pos=None,
        col_colors=cluster_colors,
        row_linkage=row_linkage,
        col_linkage=col_linkage,
    )
    return g


def run():
    for entity in ["LUAD", "LUSC"]:
        data_path = f"/data/tier3/publication_all_spots_niche_loading_{entity}.parquet"
        raw_data = load_and_preprocess_data(data_path)
        normalized_data = log_normalize(raw_data)

        col_linkage = calculate_linkage(normalized_data, axis=0)
        row_linkage = calculate_linkage(normalized_data, axis=1)

        col_clusters = extract_clusters(col_linkage)
        col_colors = apply_color_map(col_clusters)

        g = create_clustermap(normalized_data.T, row_linkage, col_linkage, col_colors)
        g.savefig(f"/data/tier4/{entity}_clustermap.png")
        plt.clf(); plt.cla()


if __name__ == "__main__":
    run()