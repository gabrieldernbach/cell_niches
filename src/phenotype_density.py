import pathlib
from itertools import product

import pandas as pd
from shapely.prepared import prep
from tqdm import tqdm

from src.utils import get_geometries

pd.set_option('future.no_silent_downcasting', True)  # accept future behaviour


def extract(pattern, column, df):
    """extract regex `pattern` from `column` of `df` and let result take its place"""
    df = df.copy()  # avoid side-effects (no inplace operations)
    tmp = df[column].str.extract(pattern)
    return df.join(tmp).drop(column, axis=1)


def parse_tag_string_to_multi_hot_vector(marks):
    marks = marks.drop_duplicates().reset_index(drop=True)
    # fix names white-spaces
    marks["tag_name"] = marks.tag_name.str.replace(" ", "_")
    # convert names into indications
    marks = extract("(?P<tag>.*)_(?P<value>.*)", "tag_name", marks)
    marks["value"] = marks.value.map(dict(negative=0, positive=1))
    # records format to features format (unmelt/unpivot)
    marks = marks.groupby("polygon_id").apply(
        lambda x: x.set_index("tag")["value"])
    return marks


def multilabel_to_phenotype(marks, lookup):
    column_sort = lambda df: df.reindex(sorted(df.columns), axis=1)
    marks = column_sort(marks)
    lookup = column_sort(lookup)
    assert all(marks.columns == lookup.columns)

    row2str = lambda x: str(x.values)
    marks = marks.apply(row2str, axis=1)
    lookup = lookup.apply(row2str, axis=1)

    lookup = {v: k for k, v in lookup.items()}
    return marks.map(lookup).fillna("Other")


def column_names_replace_whitespace(df):
    df.columns = df.columns.str.replace(" ", "_")
    return df


def clean_conflicting(marks):
    """immuno cells cannot express CK, in these cases, we let CK win against more noisy signals"""
    marks.loc[marks[marks.CD3 == 1].index, "CK"] = 0
    marks.loc[marks[marks.CD20 == 1].index, "CK"] = 0
    marks.loc[marks[marks.CD68 == 1].index, "CK"] = 0
    marks.loc[marks[marks.CD163 == 1].index, "CK"] = 0
    return marks


def phenotyping(marks, granularity: str):
    """
    Each row in `marks` represents a cell with a multi-hot-vector of marker activations,
    the phenotyping maps the set of multi-hot-vectors to expert-curated-names,
    the `granularity={"medium", "fine"} determines the number of labels assigned.
    """

    marks = clean_conflicting(marks)

    xls = pd.ExcelFile("/data/tier2/metadata/phenotyping.xlsx")
    assert granularity in xls.sheet_names, f"must be one of {xls.sheet_names}"
    lookup = pd.read_excel(xls, sheet_name=granularity)
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
    """evaluate ALL phenotype x region combinations"""

    def density(points, marks, regions):
        """evaluate ONE phenotype x region combination"""

        def wrapped(ids):
            marker_id, region_id = ids
            joined = points.merge(marks.to_frame("mark"), on="polygon_uuid")
            subset = joined[joined.mark == marker_id]
            region = regions.query("region==@region_id").geom.item()
            pregion = prep(region)
            return subset.geom.apply(lambda x: pregion.contains(x)).sum() / region.area

        return wrapped

    combinations = list(product(phenotypes.unique(), regions.region.tolist()))
    combinations = pd.DataFrame(combinations, columns=["marker", "region"])
    combinations["density"] = combinations.apply(density(points, phenotypes, regions), axis=1)
    return combinations.query("marker!='Other'").assign(wsi_uuid=points.wsi_uuid.unique()[0])


def run():
    pathlib.Path("/data/tier3/").mkdir(parents=True, exist_ok=True)
    marks, points, regions = get_geometries()
    phenotypes = phenotyping(marks.set_index(["polygon_uuid", "wsi_uuid"]), "medium")
    wsi_uuids = points.wsi_uuid.drop_duplicates()

    outcome = []
    for wsi_uuid in tqdm(wsi_uuids, "Computing density of phenotype x in region y"):
        outcome.append(densities(
            points.query("wsi_uuid==@wsi_uuid"),
            phenotypes.loc[:, wsi_uuid],
            regions.query("wsi_uuid==@wsi_uuid")
        ))
    outcome = pd.concat(outcome)
    outcome.to_parquet("/data/tier3/densities.parquet")


if __name__ == "__main__":
    run()
