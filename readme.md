![alt text](https://github.com/gabrieldernbach/cell-niches/blob/main/spots.png)

Introduction
============
This code accompanies the publication

**Multimodal AI-powered spatial cellomics enhances risk stratification in non-small cell lung cancer.**

Data is available
at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11395885.svg)](https://doi.org/10.5281/zenodo.11395885)
and automatically downloaded by the provided scripts.

> Risk stratification remains a critical challenge in non-small cell lung cancer (NSCLC) patients for optimal therapy
> selection. In this study, we developed an AI-powered spatial cellomics approach that combines histology, multiplex
> immunofluorescence imaging and multimodal machine learning to decipher the complex cellular relationships of 43 cell
> phenotypes in the tumor microenvironment (TME) in a real-world cohort of 1,168 NSCLC patients from two large German
> cancer centers. The AI model identified TME cell niches associated with survival and allowed for an improved risk
> stratification combining niche patterns with conventional (UICC8) cancer staging. Our results showed that complex
> immune
> cell niche patterns identify potentially undertreated high risk patients qualifying for adjuvant therapy. Our approach
> highlights the potential of AI-powered multiplex imaging analyses to better understand the contribution of the TME to
> cancer progression and to improve risk stratification and treatment selection in NSCLC.



RUN
===

* in your home, crete a folder for the experiment <br> `mkdir ~/cell_niches && cd $_`
* clone repoistory <br> `git clone https://github.com/gabrieldernbach/cell_niches repo && cd repo`
* build environment <br> `docker build -t cellomics . `
* start environment <br> `docker run -it -v ~/cell_niches/data:/data -v ~/cell_niches/repo:/repo -w /repo/src cellomics`
* fetch data <br> `python download.py`
* start computation <br> `python main.py`

OUTCOME
=======
The code will aggregate the phenotypes within each region for each spot, results are placed in `/data/tier3`.

The neighbourhood aggregation will result in a per-cell statistic to be found int `/data/tier3/cell_neighbourhoods`.

The niche clustering will produce a niche-assignment for each cell `/data/iter3/cell_niche_assignment`,
the cluster prototypes `/data/iter3/{entity}/niche_prototypes` and will summarize for each spot, how many of its cells
have been assigned to a given prototype `/data/iter3/spot_niche_loading`.

The plots of the spots with niches overlayed (color coded categories) is written to `/data/tier4/nicht_spot_overaly`.

We include cohort wide spot-niche-loading in `publication_all_spots_niche_loading_{entity}.parquet`, and recreate
the clustermaps in `/data/tier4/{entity}_clustermap.png`.

Data structure overview
=======================

* TIER 1 (provided)
    * raw H&E images
    * registered raw mIF images
* TIER 2 (provided)
    * segmentation polygon (regions)
    * nuclei detection coordinates (points)
    * nuclei classification (marks)
* TIER 3 (to be computed)
    * density of phenotyped cells within region
    * niche prototypes
    * niche assignment of each cell
    * abundance of niche type within each spot
* TIER 4 (to be computed)
    * plot for each spot with cells assigned to niches
    * cell-omics cluster-map