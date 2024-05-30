from src import cell_niches
from src import phenotype_density
from src import niche_spot_overlay
from src import clustermaps

# execute in this order
if __name__ == "__main__":
    phenotype_density.run()
    cell_niches.run()
    niche_spot_overlay.run()
    clustermaps.run()