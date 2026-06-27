"""
Description:
This script automates the retrieval of high-resolution Digital Surface Model (DOM/DSM) 
data tiles provided by the Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin.
It targets the official INSPIRE ATOM sub-feed containing 2km x 2km grid tiles with a 1m resolution.
The DOM database contains 297 zip files representing the 297 2kmx2km raster tiles that cover the entirety
of Berlin. For an overview of the files, visit:
https://fbinter.stadt-berlin.de/fb/atom//Blattschnitte/2X2_EPSG_25833.gif
"""

import os
import requests
import xml.etree.ElementTree as ET

# Define namespaces found in INSPIRE ATOM feeds
namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'georss': 'http://www.georss.org/georss'
}

# The actual ATOM feed connect point for the Berlin DOM service
ATOM_URL = "https://gdi.berlin.de/data/dom/atom/0.atom" 
output_folder = "./berlin_dom_tiles"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

print("Fetching ATOM Feed metadata...")
response = requests.get(ATOM_URL)
if response.status_code != 200:
    print(f"Failed to fetch ATOM feed. Status: {response.status_code}")
    exit()

# Parse XML
root = ET.fromstring(response.content)

# Find all entry links that correspond to zip or txt files
download_links = []
for entry in root.findall('atom:entry', namespaces):
    for link in entry.findall('atom:link', namespaces):
        href = link.get('href')
        # Filter for download archives/tiles (usually .zip, .gz, or .txt)
        if href and any(ext in href.lower() for ext in ['.zip', '.txt', '.tar', '.gz']):
            download_links.append(href)

# Remove duplicates
download_links = list(set(download_links))
print(f"Found {len(download_links)} grid tiles to download.")

# Download sequentially
for i, url in enumerate(download_links, 1):
    filename = url.split('/')[-1]
    file_path = os.path.join(output_folder, filename)
    
    print(f"[{i}/{len(download_links)}] Downloading {filename}...")
    try:
        file_response = requests.get(url, stream=True)
        if file_response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print(f"Error downloading {filename}: Status {file_response.status_code}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")

print("All downloads complete!")

"""
Postprocessing Pipeline Overview (Executed in WSL/Linux Terminal after running this script):
1. EXTRACT: Unzip all 297 downloaded archives into a flat directory.
   Command: for f in berlin_dom_tiles/*.zip; do unzip -j "$f" -d ~/berlin_dom_txt; done
2. RENAME: Change the file extension from .txt to .xyz to comply with standard GIS point cloud/grid formats.
   Command: 
3. for file in *.xyz; 
        # adjust NS resolution 
        do echo "$file"; gdalwarp -t_srs EPSG:25833 -overwrite "$file" "$(basename "$file" .xyz).tif" && rm "$file"
   done
4. VIRTUALIZE: Build a GDAL Virtual Raster (VRT) to stitch all 297 grid tiles into a single seamless map layer without memory overhead.
   Command: gdalbuildvrt berlin_dom_complete.vrt *.tif
5. GIS IMPORT: Load the .vrt file into QGIS using the official Berlin coordinate reference system: EPSG:25833 (ETRS89 / UTM Zone 33N).
"""