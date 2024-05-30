![alt text](https://github.com/gabrieldernbach/cell-niches/blob/main/spots.png)

Introduction
============
This code accompanies the publication 

**Multimodal AI-powered spatial cellomics enhances risk stratification in non-small cell lung cancer.**

Data is available at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.11389863.svg)](https://doi.org/10.5281/zenodo.11389863)

Data is structured in 
=====================
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

RUN
===
* in your home, crete a folder for the experiment `mkdir ~/cell_niches && cd $_`
* clone repoistory `git clone https://github.com/gabrieldernbach/cell_niches repo`
* start environment `docker-compose run container`
* fetch data `python download.py`
* start computation `python main.py`


FAQ
=====
**Q: I don't have docker-compose, can I still run the code?**

**A**: If you don't have docker-compose available you can start the container and manually

bind the directories `-v` and set the working directory `-w`
```
  docker run -it \
  -v ~/crete_heraklion/data:/data \
  -v ~/crete_hearklion/repo:/repo \
  -w /src \
  gabrieldernbach/cell_niches:cellomics \
  python src/main.py
```
**Q I have a different platform (arm/x86) and can't use the public container, how can I rebuild it?**

**A** You can make a local build by**

`cd ~/cell_niches/ && docker build -tag cellomics .`

**Q I don't have docker**

**A** You can setup python3.11 manually and run pip

`pip install -r requirements.txt`

