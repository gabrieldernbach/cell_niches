![alt text](https://github.com/gabrieldernbach/cell-niches/blob/main/spots.png)

Introduction
============
This code accompanies the publication 

**Multimodal AI-powered spatial cellomics enhances risk stratification in non-small cell lung cancer.**

Data is available at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11389863.svg)](https://doi.org/10.5281/zenodo.11389863)

RUN
===
* in your home, crete a folder for the experiment `mkdir ~/cell_niches && cd $_`
* clone repoistory `git clone https://github.com/gabrieldernbach/cell_niches repo`
* build environment `docker build -t cellomics . `
* start environment
```
  docker run -it \
  -v ~/cell_niches/data:/data \
  -v ~/cell_niches/repo:/repo \
  -w /src \
  gabrieldernbach/cell_niches:cellomics
```
* fetch data `python download.py`
* start computation `python main.py`


Data is structured into
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
  * abundance of niche type with in each spot
* TIER 4 (to be computed)
  * plot for each spot with cells assigned to niches
  * cell-omics cluster-map

TIER 1 and TIER2 data can be retrieved from DOI `10.5281/zenodo.11369540`.