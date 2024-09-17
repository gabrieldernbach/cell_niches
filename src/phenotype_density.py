"""
Module for cell phenotyping and density computation in spatial regions.

This module processes cell marker data to assign phenotypes based on expert-curated criteria, 
and computes densities for combinations of phenotypes and spatial regions. The results are 
saved as parquet files for further analysis.

Main Components:
- `extract`: Extracts regex matches from a DataFrame column and replaces the original column with the result.
- `parse_tag_string_to_multi_hot_vector`: Converts tag strings into a multi-hot vector representing marker presence.
- `multilabel_to_phenotype`: Maps multi-hot vectors to predefined phenotypes based on a lookup table.
- `clean_conflicting`: Resolves conflicts between immuno markers and CK expression.
- `phenotyping`: Assigns phenotypes to cells based on marker combinations using different levels of granularity.
- `densities`: Computes phenotype densities for all phenotype-region combinations.
- `run`: Executes the full workflow from loading data to phenotyping and density computation.
"""
import pathlib
from itertools import product

import pandas as pd
from shapely.prepared import prep
from tqdm import tqdm

from src.utils import get_geometries

# Accept future behavior for downcasting warnings
pd.set_option('future.no_silent_downcasting', True)

def extract(pattern, column, df):
    """
    Extracts regular expression matches from a specified column and replaces the original column with the result.

    Args:
        pattern (str): The regex pattern to apply.
        column (str): The name of the column in which to search for regex matches.
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: A DataFrame with the extracted matches replacing the original column.
    """

    df = df.copy()  # avoid side-effects (no inplace operations)
    tmp = df[column].str.extract(pattern) # Extract regex matches
    return df.join(tmp).drop(column, axis=1) # Replace original column with extracted results


def parse_tag_string_to_multi_hot_vector(marks):
    """
    Converts tag strings into a multi-hot vector representation of marker presence/absence.

    Each tag string is split into marker names and their values (positive/negative), and the result 
    is unpivoted to form a multi-hot vector where 1 indicates marker presence and 0 indicates absence.

    Args:
        marks (pd.DataFrame): DataFrame containing the 'tag_name' column to be converted.

    Returns:
        pd.DataFrame: A DataFrame where each row represents a cell and each column a marker, with values as 0 or 1.
    """
    # Remove duplicates and reset index
    marks = marks.drop_duplicates().reset_index(drop=True)
    # Replace spaces with underscores in tag names
    marks["tag_name"] = marks.tag_name.str.replace(" ", "_")
    # Extract marker and value from tag names
    marks = extract("(?P<tag>.*)_(?P<value>.*)", "tag_name", marks)
    # Map marker values to 0 or 1
    marks["value"] = marks.value.map(dict(negative=0, positive=1))
    # Convert DataFrame from records format (long) to Features format (wide) by performing an unpivot operation
    # This is implemented by a group by over 'polygon_id' and converting tag to an index, only keeping value
    marks = marks.groupby("polygon_id").apply(lambda x: x.set_index("tag")["value"])
    return marks


def multilabel_to_phenotype(marks, lookup):
    """
    Maps multi-hot vectors of marker activations to predefined phenotypes using a lookup table.

    Args:
        marks (pd.DataFrame): Multi-hot vectors representing marker activations for each cell.
        lookup (pd.DataFrame): A lookup table mapping marker combinations to phenotypes.

    Returns:
        pd.Series: A series mapping each cell to its corresponding phenotype, with 'Other' for unmatched combinations.
    """
    # Sort columns alphabetically
    column_sort = lambda df: df.reindex(sorted(df.columns), axis=1)
    marks = column_sort(marks) # Sort columns in the marker DataFrame
    lookup = column_sort(lookup) # Sort columns in the lookup DataFrame
    assert all(marks.columns == lookup.columns),  "Columns in marks and lookup must match."

    # Convert each row (multi-hot vector) to a string for comparison
    row2str = lambda x: str(x.values)
    marks = marks.apply(row2str, axis=1)
    lookup = lookup.apply(row2str, axis=1)

    # Create a dictionary that maps string representations of marker combinations to phenotypes
    lookup = {v: k for k, v in lookup.items()}
    # Map markers to phenotypes, defaulting to "Other"
    return marks.map(lookup).fillna("Other")


def column_names_replace_whitespace(df):
    """
    Replaces spaces in column names with underscores.

    Args:
        df (pd.DataFrame): The input DataFrame whose columns need modification.

    Returns:
        pd.DataFrame: A DataFrame with modified column names.
    """
    df.columns = df.columns.str.replace(" ", "_")
    return df


def clean_conflicting(marks):
    """
    Resolves conflicts between immuno markers and CK (Cytokeratin) expression.

    CK expression is considered more reliable than certain immuno markers (e.g., CD3, CD20),
    so CK is given priority and set to 0 in cells where conflicting immuno markers are present.

    Args:
        marks (pd.DataFrame): DataFrame with marker expressions.

    Returns:
        pd.DataFrame: A modified DataFrame with conflicts resolved.
    """
    marks.loc[marks[marks.CD3 == 1].index, "CK"] = 0
    marks.loc[marks[marks.CD20 == 1].index, "CK"] = 0
    marks.loc[marks[marks.CD68 == 1].index, "CK"] = 0
    marks.loc[marks[marks.CD163 == 1].index, "CK"] = 0
    return marks


def phenotyping(marks, granularity: str):
    """
    Assigns phenotypes to cells based on their marker expressions, using expert-curated phenotype definitions.

    The phenotyping is controlled by `granularity`, which determines the level of detail in the phenotype mapping.
    Available options are "medium" or "fine", which correspond to different phenotype mappings in the lookup table.

    Args:
        marks (pd.DataFrame): DataFrame containing marker expressions for each cell.
        granularity (str): The granularity level for phenotyping, must be one of the sheets in the lookup table.

    Returns:
        pd.Series: A series mapping each cell to its phenotype.
    """
    marks = clean_conflicting(marks)

    # Load the phenotype lookup table from an Excel file
    xls = pd.ExcelFile("/data/tier2/metadata/phenotyping.xlsx")
    assert granularity in xls.sheet_names, f"must be one of {xls.sheet_names}"
    lookup = pd.read_excel(xls, sheet_name=granularity)

    # Process the lookup table: replace values, remove unnecessary columns, and format column names
    lookup = (lookup
              .replace("(+)", 1)
              .replace("(-)", 0)
              .drop(["Number (total)", "Cell phenotype (abbreviation)"], axis=1)
              .query("`Cell phenotype` !='Other'")
              .query("`Cell phenotype` !='Other '")
              .set_index("Cell phenotype")
              .pipe(column_names_replace_whitespace)
              .rename(columns={"FOXP3": "FoxP3"}))

    marks = multilabel_to_phenotype(marks, lookup)
    return marks


def densities(points, phenotypes, regions):
    """
    Computes the density of each phenotype in each spatial region.

    This function calculates the density of cells expressing a specific phenotype 
    within defined spatial regions. The density is defined as the ratio of the number 
    of cells of a given phenotype contained within a region to the total area of that region. 
    All possible phenotype-region combinations are evaluated, and results are returned as 
    a DataFrame.

    Args:
        points (pd.DataFrame): DataFrame containing the geometric coordinates of each cell.
                               Must include 'geom' (geometric data) and 'polygon_uuid' for matching.
        phenotypes (pd.Series): Series mapping each cell's 'polygon_uuid' to a phenotype.
        regions (pd.DataFrame): DataFrame containing spatial region geometries. 
                                Must include 'region' and 'geom' columns for region identification.

    Returns:
        pd.DataFrame: A DataFrame with computed densities for each phenotype-region combination.
                      The DataFrame includes columns:
                      - 'marker': The phenotype/marker name.
                      - 'region': The name of the spatial region.
                      - 'density': The computed density of the phenotype in the region.
                      - 'wsi_uuid': The UUID of the whole slide image (WSI) the data corresponds to.
    """
    def density(points, marks, regions):
        """
        Computes the density for one phenotype-region combination.

        For each phenotype and region, the function calculates how many cells express the 
        phenotype and are located inside the region. The density is calculated as:
        
        Density = (Number of cells expressing the phenotype inside the region) / (Area of the region)

        Args:
            points (pd.DataFrame): DataFrame of cell coordinates and metadata.
            marks (pd.Series): Series mapping 'polygon_uuid' to phenotypes.
            regions (pd.DataFrame): DataFrame of region geometries.

        Returns:
            Function: A wrapped function that calculates density for one phenotype-region pair.
        """
        def wrapped(ids):
            marker_id, region_id = ids  # Unpack phenotype and region
            # Merge points and phenotype data based on polygon_uuid
            joined = points.merge(marks.to_frame("mark"), on="polygon_uuid")
            subset = joined[joined.mark == marker_id] # Filter to get only cells with the specific phenotype
            region = regions.query("region==@region_id").geom.item() # Get the geometry of the region
            pregion = prep(region) # Prepare the region geometry for efficient spatial queries
            # Check how many cells are contained in the region and compute density
            return subset.geom.apply(lambda x: pregion.contains(x)).sum() / region.area

        return wrapped

    # Generate all possible phenotype-region combinations
    combinations = list(product(phenotypes.unique(), regions.region.tolist()))
    # Create a DataFrame of combinations
    combinations = pd.DataFrame(combinations, columns=["marker", "region"])
    # Apply the density calculation for each combination
    combinations["density"] = combinations.apply(density(points, phenotypes, regions), axis=1)
    # Filter out 'Other' phenotypes (if necessary) and assign WSI UUID
    return combinations.query("marker!='Other'").assign(wsi_uuid=points.wsi_uuid.unique()[0])


def run():
    """
    Executes the full workflow to compute phenotype densities for each WSI (Whole Slide Image) and save the results.

    The run function orchestrates the entire process:
    1. Loads spatial point data, cell marker data, and region geometries using `get_geometries`.
    2. Applies phenotyping to cell marker data to classify each cell according to its marker expressions, 
       using an expert-curated phenotyping table (controlled by the 'medium' granularity).
    3. Iterates through all WSI UUIDs and for each WSI:
       - Filters the points, phenotypes, and regions corresponding to that WSI.
       - Computes the density of each phenotype in each region within the WSI.
    4. Concatenates the density results for all WSIs into a single DataFrame and saves the output as a Parquet file.

    The output Parquet file contains the following information:
    - The density of each phenotype in each spatial region for each WSI.
    - The WSI UUIDs to track which image each result belongs to.

    Output:
        Saves the computed densities as '/data/tier3/densities.parquet'.

    """
    # Ensure the output directory exists
    pathlib.Path("/data/tier3/").mkdir(parents=True, exist_ok=True)
    # Load geometries (marks, points, and regions)
    marks, points, regions = get_geometries()
     # Perform phenotyping
    phenotypes = phenotyping(marks.set_index(["polygon_uuid", "wsi_uuid"]), "medium")
    # Get unique WSI UUIDs
    wsi_uuids = points.wsi_uuid.drop_duplicates()

    outcome = []
    # Iterate through each WSI UUID to compute densities for that WSI
    for wsi_uuid in tqdm(wsi_uuids, "Computing density of phenotype x in region y"):
        # Compute the densities for the current WSI and append the result to the outcome list
        outcome.append(densities(
            points.query("wsi_uuid==@wsi_uuid"),
            phenotypes.loc[:, wsi_uuid],
            regions.query("wsi_uuid==@wsi_uuid"),
        ))
    outcome = pd.concat(outcome)
    # Save the computed densities to a Parquet file for further analysis
    outcome.to_parquet("/data/tier3/densities.parquet")


if __name__ == "__main__":
    run()
