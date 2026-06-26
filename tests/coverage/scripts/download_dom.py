import os
import requests
import xml.etree.ElementTree as ET

# Define namespaces found in INSPIRE ATOM feeds
namespaces = {
    'atom': 'http://www.w3.org/2005/Atom',
    'georss': 'http://www.georss.org/georss'
}

# The actual ATOM feed connect point for the Berlin DOM service
ATOM_URL = "https://gdi.berlin.de/data/dom/atom/0.atom" # or bdom/atom/bdom.xml depending on exact metadata endpoint
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