"""
Module for generating spatial niche overlay plots from parquet data.

This module processes spatial point data and niche IDs from parquet files, and creates scatter plots
for each WSI (Whole Slide Image) showing the spatial distribution of niches. The plots are saved as
high-resolution PNG files.

Main Components:
- `make_legend`: Creates a legend for the niche IDs using a predefined color map.
- `get_xy`: Extracts the x and y coordinates from the geometry data in the DataFrame.
- `plot`: Generates a scatter plot for the spatial data and saves the plot as a PNG image.
- `run`: The main pipeline that loads niche and spatial data, applies plotting for each WSI, and saves the results.
"""

from pathlib import Path

import duckdb
import matplotlib as mpl
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from src.utils import deserialize_wkb

# Use non-interactive backend for matplotlib to save figures without opening a window
mpl.use('Agg')


def make_legend(ax):
    """
    Adds a legend to the plot with predefined colors corresponding to the niche IDs.

    The legend displays ten niche categories, with each niche assigned a unique color 
    from the 'tab10' color map.

    Args:
        ax (matplotlib.axes.Axes): The axes on which to place the legend.
    """
    colors = plt.cm.tab10(np.linspace(0, 1, 9))
    patches = [mpatches.Patch(color=colors[i], label=f'Niche {i + 1}') for i in range(9)]
    ax.legend(handles=patches, title="Niche IDs", loc=(1.04, 0.3))


def get_xy(df):
    """
    Extracts the x and y coordinates from the geometry column of the DataFrame.

    The coordinates are extracted by applying lambda functions that access the 
    x and y attributes of the geometric points.

    Args:
        df (pd.DataFrame): DataFrame containing a 'geom' column with shapely geometric points.

    Returns:
        np.ndarray: A 2D array of shape (n_samples, 2) with x and y coordinates.
    """
    coords = np.c_[
        df.geom.apply(lambda point: point.x),
        df.geom.apply(lambda point: point.y),
    ]
    return coords


def plot(id_df):
    """
    Creates and saves a scatter plot of the spatial niche overlay for a given WSI.

    This function generates a scatter plot of the x and y coordinates of each point, 
    colored by the 'niche_id'. The plot is saved as a high-resolution PNG image.

    Args:
        id_df (tuple): A tuple containing the WSI UUID and a DataFrame with spatial and niche data.
                       The DataFrame must include 'geom' (geometry) and 'niche_id' columns.
    """
    base_path = "/data/tier4/niche_spot_overlay"
    # Ensure the output directory exists
    Path("/data/tier4/niche_spot_overlay").mkdir(parents=True, exist_ok=True)
    # Unpack WSI UUID and corresponding DataFrame
    wsi_uuid, df = id_df
    # Extract x and y coordinates from the 'geom' column
    coords = get_xy(df)

    # Create the plot figure and axes
    fig, ax = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=(5.8, 4.1)  # shape of DIN-A6 in inches
    )
    # Plot the data as a scatter plot, with points colored by 'niche_id'
    ax.scatter(
        *coords.T, # Transpose coordinates to separate x and y
        c=df.niche_id,  # Use 'niche_id' to color the points
        marker='.', # Use the dot marker
        cmap="tab10", # Use the 'tab10' colormap for coloring
        s=1. # Set relatively large marker size
    )
    ax.axis("equal") # Ensure equal scaling on both axes to keep aspect ratio constant
    ax.axis("off") # Hide axis labels and ticks for cleaner visual
    
    make_legend(ax) # Apply the custom the legend
    fig.savefig(
        f"{base_path}/{wsi_uuid}.png",
        bbox_inches="tight",  # Ensures to include the legend in the output
        dpi=600,  # Set the resolution to 600 DPI (retina quality)
    )
    plt.close(fig)


def run():
    """
    Loads niche assignment and spatial point data from parquet files and generates overlay plots.
    
    This function loads the data using DuckDB SQL, joins niche IDs with spatial points, 
    and processes the data for each WSI by generating spatial niche scatter plots. The 
    resulting plots are saved as high-resolution images.
    """
    niche_points = duckdb.sql("""
    select cn.niche_id, p.geom, p.wsi_uuid
    from read_parquet('/data/tier3/cell_niche_assignment/*/*.parquet') cn
    join read_parquet('/data/tier2/points/*/*.parquet') p 
        on cn.wsi_uuid = p.wsi_uuid and cn.polygon_uuid = p.polygon_uuid
    """).df()
    # Deserialize the geometry data from Well-Known Binary (WKB) format to usable geometric objects
    niche_points = niche_points.pipe(deserialize_wkb)
    # Generate niche overlay plots for each WSI (grouped by 'wsi_uuid')
    [plot(i) for i in tqdm(niche_points.groupby("wsi_uuid"), desc="Plotting spot niche overlays")]


if __name__ == "__main__":
    run()
