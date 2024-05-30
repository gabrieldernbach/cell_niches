import io
import zipfile
from pathlib import Path
from typing import BinaryIO

import requests
from tqdm import tqdm

web_base_path = "https://zenodo.org/records/11389863/files/"

# for i in range(1, 5):
#     Path(f"/data/tier{i}/").mkdir(parents=True, exist_ok=True)
# Path("/data/tier1/wsis").mkdir(parents=True, exist_ok=True)
# Path("/data/tier1/metadata").mkdir(parents=True, exist_ok=True)


def load_url(url, destination, description):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get("content-length", 0))
    with tqdm(total=total_size, unit="B", unit_scale=True, desc=description) as progress_bar:
        for data in response.iter_content(1024):
            progress_bar.update(len(data))
            destination.write(data)
    return destination


def extract_zip(source: BinaryIO, destination: str, description: str):
    with zipfile.ZipFile(source) as zf:
        for member in tqdm(zf.infolist(), desc=description):
            zf.extract(member, destination)

def load_extract(url, directory, name):
    stream = load_url(url, io.BytesIO(), f"loading {name}")
    extract_zip(stream, directory, f"extracting {name}")


load_extract(f"{web_base_path}/tier3.zip", "/data", "spatial")
load_extract(f"{web_base_path}/tier2.zip", "/data", "geometries")
load_extract(f"{web_base_path}/tier1.zip", "/data", "whole_slide_images")