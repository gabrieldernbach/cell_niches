![alt text](https://github.com/gabrieldernbach/cell-niches/blob/main/spots.png)


# Data is structured in 
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

# RUN
* choose a location for the experiment `mkdir ~/cretehearklion && cd $_`
* fetch TIER 1 and TIER 2 data `curl {zendo_link} ~/creteheraklion/data`
* clone repoistory `git clone {github link} ~/creteheraklion/repo`
* start environment `docker-compose run container`
* start experiment `python main.py`


# FAQ container
If you don't have docker-compose available you can manually do
```
  docker run -it \
  -v ~/crete_heraklion/data:/data \
  -v ~/crete_hearklion/repo:/repo \
  gabrieldernbach/crete_heraklion:cellomics \
  python src/main.py
```
If you don't have connection to dockerhub you can build the image locally
`cd /your/local/dir/repo/ && docker build -tag crete_heraklion .`
If you don't have docker, you can setup python3.11 manually and run pip
`pip install -r requirements.txt`
