"""
Module for downloading and extracting ZIP archives from URLs.

This module facilitates the download of large files from the web and the extraction of 
ZIP archives into a specified local directory. It supports progress tracking to monitor 
the download and extraction processes in real time.

Main Components:
- `load_url`: Downloads content from a URL with progress tracking and writes it to a specified destination.
- `extract_zip`: Extracts the contents of a ZIP archive from a binary stream to a specified directory, showing extraction progress.
- `load_extract`: Downloads a ZIP archive from a URL, extracts its contents, and saves them to a local directory.
"""
import io
import zipfile
from typing import BinaryIO

import requests
from tqdm import tqdm



def load_url(url, destination, description):
    """
    Downloads content from the specified URL and writes it to the destination stream with progress tracking.
    
    The function streams the file in chunks to efficiently handle large files, using `tqdm` to provide a 
    progress bar that shows the download progress.

    Args:
        url (str): The URL of the file to be downloaded.
        destination (BinaryIO): The in-memory binary stream or file object to write the downloaded content to.
        description (str): A description for the progress bar to indicate the current download task.

    Returns:
        BinaryIO: The destination stream containing the downloaded content.
    """
    response = requests.get(url, stream=True)
    # Get total file size for progress bar
    total_size = int(response.headers.get("content-length", 0)) 
    # Set up a progress bar with total file size in unit bytes
    with tqdm(total=total_size, unit="B", unit_scale=True, desc=description) as progress_bar:
         # Download in chunks of 1024 bytes
        for data in response.iter_content(1024):
            # Update progress bar with chunk size
            progress_bar.update(len(data))
            # Write chunk to destination stream
            destination.write(data)
    return destination


def extract_zip(source: BinaryIO, destination: str, description: str):
    """
    Extracts the contents of a ZIP archive from a binary stream and saves them to the specified directory, 
    with progress tracking for each file in the archive.

    Args:
        source (BinaryIO): The binary stream containing the ZIP archive.
        destination (str): The directory path where the extracted files will be saved.
        description (str): A description for the progress bar to indicate the current extraction task.

    Returns:
        None
    """
    with zipfile.ZipFile(source) as zf:
        # Iterate over all files in the ZIP archive and extract each, showing progress with tqdm
        for member in tqdm(zf.infolist(), desc=description):
            # Extract the current file to the destination
            zf.extract(member, destination)


def load_extract(url, directory, name):
    """
    Downloads a ZIP archive from the given URL, extracts its contents, and saves them to a specified directory.
    
    The function combines downloading and extraction processes, showing progress for both operations. The ZIP archive 
    is streamed into memory, and its contents are extracted without requiring any intermediate file on disk.

    Args:
        url (str): The URL of the ZIP file to be downloaded.
        directory (str): The directory where the extracted files will be saved.
        name (str): A name for the task used in progress bar descriptions.

    Returns:
        None
    """
    stream = load_url(url, io.BytesIO(), f"loading {name}")
    extract_zip(stream, directory, f"extracting {name}")

# Base URL for the web files
web_base_path = "https://zenodo.org/records/11395885/files"
# Download and extract the specified ZIP files into the '/data' directory
load_extract(f"{web_base_path}/tier3.zip", "/data", "spatial")
load_extract(f"{web_base_path}/tier2.zip", "/data", "geometries")
load_extract(f"{web_base_path}/tier1_metadata_only.zip", "/data", "whole_slide_images")
