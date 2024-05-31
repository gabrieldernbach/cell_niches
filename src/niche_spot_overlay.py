from pathlib import Path

import duckdb
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from src.utils import deserialize_wkb


def make_legend(ax):
    colors = plt.cm.tab10(np.linspace(0, 1, 9))
    patches = [mpatches.Patch(color=colors[i], label=f'Niche {i + 1}') for i in range(9)]
    ax.legend(handles=patches, title="Niche IDs", loc=(1.04, 0.3))


def get_xy(df):
    coords = np.c_[
        df.geom.apply(lambda point: point.x),
        df.geom.apply(lambda point: point.y),
    ]
    return coords


def plot(id_df):
    base_path = "/data/tier4/niche_spot_overlay"
    Path("/data/tier4/niche_spot_overlay").mkdir(parents=True, exist_ok=True)
    wsi_uuid, df = id_df
    coords = get_xy(df)
    fig, ax = plt.subplots(
        nrows=1,
        ncols=1,
        figsize=(5.8, 4.1)  # shape of DIN-A6 in inches
    )
    ax.scatter(
        *coords.T,
        c=df.niche_id,
        marker='.',
        cmap="tab10",
        s=1.
    )
    ax.axis("equal")
    ax.axis("off")
    # make_legend(ax)
    fig.savefig(
        f"{base_path}/{wsi_uuid}.png",
        bbox_inches="tight",  # include legend
        dpi=600,  # retina resolution
    )
    plt.clf(); plt.cla()


def run():
    niche_points = duckdb.sql("""
    select cn.niche_id, p.geom, p.wsi_uuid
    from read_parquet('/data/tier3/cell_niche_assignment/*/*.parquet') cn
    join read_parquet('/data/tier2/points/*/*.parquet') p 
        on cn.wsi_uuid = p.wsi_uuid and cn.polygon_uuid = p.polygon_uuid
    """).df()
    niche_points = niche_points.pipe(deserialize_wkb)
    [plot(i) for i in tqdm(niche_points.groupby("wsi_uuid"), desc="Plotting spot niche overlays")]

if __name__ == "__main__":
    run()