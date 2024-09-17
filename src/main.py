"""
Main script for executing spatial analysis workflows.

This script runs the complete analysis pipeline, including phenotype density computation, 
cell niche identification, niche overlay visualization, and clustering heatmaps.

Modules:
- `phenotype_density`: Computes phenotype densities within spatial regions.
- `cell_niches`: Identifies and categorizes cell niches.
- `niche_spot_overlay`: Visualizes cell niches on spatial regions.
- `clustermaps`: Produces heatmaps and clustering visualizations based on niche data.
"""


from src import cell_niches
from src import clustermaps
from src import niche_spot_overlay
from src import phenotype_density

if __name__ == "__main__":
    """
    Main script to sequentially execute the spatial analysis workflows.
    
    This script serves as an entry point to run multiple analytical modules in sequence. Each module processes 
    a specific aspect of the spatial data and generates results, such as phenotype densities, cell niche 
    identification, spatial overlays, and cluster visualizations. The modules are designed to be executed 
    in the order as follows
    """
    phenotype_density.run()
    cell_niches.run()
    niche_spot_overlay.run()
    clustermaps.run()
