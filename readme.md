![alt text](https://github.com/gabrieldernbach/cell-niches/blob/main/spots.png)

Introduction
============
This code accompanies the publication

**Multimodal AI-powered spatial cellomics enhances risk stratification in non-small cell lung cancer.**

A subset (15GB) of the data used in the study is available at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11395885.svg)](https://doi.org/10.5281/zenodo.11395885) and is automatically downloaded by the provided scripts.


> Risk stratification remains a critical challenge in non-small cell lung cancer (NSCLC) patients for optimal therapy
> selection. In this study, we developed an AI-powered spatial cellomics approach that combines histology, multiplex
> immunofluorescence imaging, and multimodal machine learning to decipher the complex cellular relationships of 43 cell
> phenotypes in the tumor microenvironment (TME) in a real-world cohort of 1,168 NSCLC patients from two large German
> cancer centers. The AI model identified TME cell niches associated with survival and allowed for an improved risk
> stratification combining niche patterns with conventional (UICC8) cancer staging. Our results showed that complex
> immune
> cell niche patterns identify potentially undertreated high-risk patients qualifying for adjuvant therapy. Our approach
> highlights the potential of AI-powered multiplex imaging analyses to understand better the contribution of the TME to
> cancer progression and to improve risk stratification and treatment selection in NSCLC.
>


This repository provides a computational pipeline for the spatial analysis performed in the publication, allowing users to replicate the study or apply the methods to their own datasets.

# Project Structure

- `src/phenotype_density.py`: Computes the density of phenotypes in spatial regions.
- `src/cell_niches.py`: Identifies and categorizes cell niches based on phenotype and proximity.
- `src/niche_spot_overlay.py`: Generates visual overlays for niches on spatial regions.
- `src/clustermaps.py`: Creates clustering heatmaps and visualizations based on niche data.

# Run Instructions
To run the analysis pipeline, follow these steps:

* in your home, create a folder for the experiment <br> `mkdir ~/cell_niches && cd $_`
* clone the repository <br> `git clone https://github.com/gabrieldernbach/cell_niches repo && cd repo`
* build the docker environment <br> `docker build -t cellomics . `
* start the docker environment <br> `docker run -it -v ~/cell_niches/data:/data -v ~/cell_niches/repo:/repo -w /repo/src cellomics`
* fetch the data <br> `python download.py`
* start the computation <br> `python main.py`

# Usage
The pipeline can also be run module by module, allowing for greater flexibility and debugging. Below are examples of how to run individual modules:

* To compute phenotype densities: <br> `python -m src.phenotype_density`
* To identify cell niches: <br> `python -m src.cell_niches`
* To generate niche overlays: <br> `python -m src.niche_spot_overlay`
* To create clustering heatmaps: <br> `python -m src.clustermaps`

# Outcome
The following outputs will be generated during the analysis:

* Phenotype Density: The densities of cell phenotypes within each region will be saved to `/data/tier3/densities.parquet`.
* Cell Neighborhoods: Per-cell statistics from neighborhood aggregation will be stored in `/data/tier3/cell_neighbourhoods`.
* Niche Assignment: Niche clustering will assign niches to each cell, which will be stored in `/data/tier3/cell_niche_assignment`. Cluster prototypes will be saved in `/data/tier3/{entity}/niche_prototypes`, and a summary of how many cells in each spot are assigned to a given prototype will be saved in `/data/tier3/spot_niche_loading`.
* Niche Overlay Plots: Visual plots showing niche overlays for each spot will be written to `/data/tier4/niche_spot_overlay`.
* Clustermaps: Cohort-wide spot-niche-loading data will be saved in `publication_all_spots_niche_loading_{entity}.parquet`, and clustermaps will be generated and saved to `/data/tier4/{entity}_clustermap.png`.

# Data structure overview

The data in the repository is divided into tiers:

* TIER 1 (provided)
    * raw H&E images.
    * registered raw multiplex immunofluorescence (mIF) images.
* TIER 2 (provided)
    * segmentation polygon (regions).
    * nuclei detection coordinates (points).
    * nuclei classification (marks).
* TIER 3 (to be computed)
    * density of phenotyped cells within regions.
    * niche prototypes.
    * niche assignment of each cell.
    * abundance of niche types within each spot.
* TIER 4 (to be computed)
    * plot for each spot with cells assigned to niches.
    * cell-omics cluster-map.

# Customization

## Data Inputs
The following input files are expected:

* Points: Located in `/data/tier2/points`, must contain columns for:
   * polygon_uuid (unique identifier for each cell).
   * wsi_uuid (identifier for the whole slide image).
   * geom (geometry of the cell in Well-Known Binary (WKB) format).
* Marks: Located in `/data/tier2/marks`, contains classification or marker data for each cell.
* Regions: Located in `/data/tier2/regions`, must contain columns for:
   * region (region name or identifier).
   * geom (geometry of the region in WKB format).

## Adjusting Parameters

Users can adjust several parameters within the scripts to customize the analysis:

Phenotyping Granularity: The level of granularity for phenotype classification can be modified in the phenotype_density module. For example:
```python
granularity = "medium"  # Can also be set to "fine"
```
New phenotype definitions can be introduced by appending new sheets in the xslx file `/data/tier2/metadata/phenotyping.xlsx`, which then become available
as additional options in the granularity flag above (replacing the granularity string with the name of the new xls-sheet).
