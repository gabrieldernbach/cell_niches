"""
Main execution script for running multiple spatial analysis pipelines.

This script coordinates the execution of various analysis modules related to spatial data, phenotyping, 
niche identification, clustering, and visualization. Each module is responsible for a specific 
aspect of the analysis, and the results are generated sequentially by calling the `run` function 
from each module.

Modules:
- `phenotype_density`: Computes the density of specific phenotypes within spatial regions.
- `cell_niches`: Identifies cell niches based on phenotypes and spatial proximity.
- `niche_spot_overlay`: Generates visual overlays of cell niches on spatial regions.
- `clustermaps`: Creates hierarchical clustering heatmaps based on cell niche data.
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
    in the following order:
    
    1. `phenotype_density.run()`: Computes the density of various cell phenotypes within defined spatial regions.
    2. `cell_niches.run()`: Identifies niches based on phenotype and spatial proximity, categorizing cells into different niches.
    3. `niche_spot_overlay.run()`: Generates visual overlays of cell niches on top of spatial regions for visualization purposes.
    4. `clustermaps.run()`: Produces hierarchical clustering heatmaps based on niche data to identify spatial patterns.

    This script allows for the automation of a full analysis pipeline, starting from the computation of 
    phenotype densities to generating final visualizations of clustered cell niches.
    """
    phenotype_density.run()
    cell_niches.run()
    niche_spot_overlay.run()
    clustermaps.run()
