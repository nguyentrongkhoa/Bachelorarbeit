"""
GPX → CSV Converter (with Unix Epoch Column)
============================================
Extracts track points (<trkpt>) from a GPX file and converts them into a 
flat CSV file containing latitude, longitude, elevation, timestamp, and 
the calculated Unix epoch in seconds for easy matching.

Usage:
    python gpx2csv.py gps_data/combined.gpx --output combined_gpx.csv
"""

import argparse
import csv
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime


def clean_iso(ts: str) -> str:
    """Normalize timestamp formats by replacing Z with UTC offset for parsing."""
    return re.sub(r'Z$', r'+00:00', ts.strip())


def convert_gpx(input_path: str, output_path: str) -> int:
    rows_written = 0

    if not os.path.exists(input_path):
        print(f"Fehler: Die Datei '{input_path}' existiert nicht.")
        return 0

    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Fehler beim Parsen der GPX-Datei: {e}")
        return 0

    # GPX-Dateien nutzen XML-Namespaces (z.B. http://www.topografix.com/GPX/1/1)
    # Wir extrahieren den Namespace dynamisch, damit das Skript mit jeder Version funktioniert
    ns_match = re.match(r'\{.*\}', root.tag)
    ns = ns_match.group(0) if ns_match else ''

    with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile)
        
        # Header-Definition (Struktur analog zum TTN-Skript)
        writer.writerow(['timestamp', 'epoch', 'latitude', 'longitude', 'elevation_m'])

        # Suche nach allen Trackpoints (<trkpt>) im XML-Baum
        for trkpt in root.findall(f'.//{ns}trkpt'):
            lat = trkpt.get('lat')
            lon = trkpt.get('lon')
            
            # Höhenmeter extrahieren (<ele>)
            ele_elem = trkpt.find(f'{ns}ele')
            ele = ele_elem.text if ele_elem is not None else ''
            
            # Zeitstempel extrahieren (<time>)
            time_elem = trkpt.find(f'{ns}time')
            if time_elem is None or not time_elem.text:
                continue
                
            raw_timestamp = time_elem.text.strip()
            
            # Epochen-Berechnung
            try:
                clean_ts = clean_iso(raw_timestamp)
                # Parsen des ISO-Strings und Umwandlung in Integer-Sekunden
                epoch_val = int(datetime.fromisoformat(clean_ts).timestamp())
            except Exception:
                epoch_val = ''

            writer.writerow([
                raw_timestamp,
                epoch_val,
                lat,
                lon,
                ele
            ])
            rows_written += 1

    return rows_written


def main():
    parser = argparse.ArgumentParser(
        description='Convert GPX track export to CSV including Unix Epoch.'
    )
    parser.add_argument('input', help='Path to the input GPX file')
    parser.add_argument('--output', default='gps_track.csv',
                        help='Output CSV path (default: gps_track.csv)')
    args = parser.parse_args()

    count = convert_gpx(args.input, args.output)
    if count > 0:
        print(f"Fertig: {count} GPS-Punkte wurden in '{args.output}' geschrieben.")
        print("Du kannst diese CSV nun direkt für das Timestamp-Matching nutzen.")


if __name__ == '__main__':
    main()