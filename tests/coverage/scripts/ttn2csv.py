"""
TTN Storage API → CSV Converter
=================================
Converts the newline-delimited JSON returned by TTN's Storage Integration
API into a flat CSV file with one row per uplink, ready to import into
GPSVisualizer, QGIS, Excel, or any other timestamp-matching tool.

Usage:
    python ttn2csv.py ttn_data/msg_log.json --output my_uplinks.csv

Output CSV columns:
    timestamp   - ISO 8601 UTC (matches GPS track timestamps)
    epoch       - number of milliseconds from a certain date, derived from timestamp
    rssi        - dBm, from the gateway with strongest signal
    snr         - dB, from the same gateway
    fcnt        - LoRaWAN frame counter
    gw_count    - number of gateways that received this packet
    gateway_id  - ID of the gateway used for rssi/snr (best one)
    payload_b64 - raw payload, base64 (decode separately if needed)
"""

import argparse
import json
import csv
import re
import sys
from datetime import datetime

def clean_iso(ts: str) -> str:
    """Truncate TTN's nanosecond timestamps to microseconds for portability."""
    return re.sub(r'(\.\d{6})\d+Z?$', r'\1Z', ts)


def convert(input_path: str, output_path: str) -> int:
    rows_written = 0

    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:

        writer = csv.writer(outfile)
        writer.writerow([
            'timestamp', 'epoch', 'rssi', 'snr', 'fcnt',
            'gw_count', 'gateway_id', 'payload_b64'
        ])

        for line_num, line in enumerate(infile, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                print(f"  Skipping malformed line {line_num}", file=sys.stderr)
                continue

            # TTN storage API wraps each record under "result"
            rec = rec.get('result', rec)

            received_at = rec.get('received_at')
            if not received_at:
                continue

            try:
                # Schneidet ggf. Nanosekunden ab, ersetzt Z durch +00:00 für sauberes Parsen
                clean_ts = clean_iso(received_at).replace('Z', '+00:00')
                # ISO-String in datetime-Objekt umwandeln und Epochen-Sekunden als Integer berechnen
                epoch_val = int(datetime.fromisoformat(clean_ts).timestamp())
            except Exception:
                epoch_val = ''

            msg = rec.get('uplink_message', {})
            rx_metadata = msg.get('rx_metadata', [])

            best_rssi, best_snr, best_gw = None, None, None
            if rx_metadata:
                best = max(rx_metadata, key=lambda g: g.get('rssi', -999))
                best_rssi = best.get('rssi')
                best_snr  = best.get('snr')
                best_gw   = best.get('gateway_ids', {}).get('gateway_id', '')

            writer.writerow([
                clean_iso(received_at),
                epoch_val,
                best_rssi,
                best_snr,
                msg.get('f_cnt', ''),
                len(rx_metadata),
                best_gw,
                msg.get('frm_payload', ''),
            ])
            rows_written += 1

    return rows_written


def main():
    parser = argparse.ArgumentParser(
        description='Convert TTN Storage API NDJSON export to CSV.'
    )
    parser.add_argument('input', help='Path to TTN NDJSON file')
    parser.add_argument('--output', default='ttn_uplinks.csv',
                        help='Output CSV path (default: ttn_uplinks.csv)')
    args = parser.parse_args()

    count = convert(args.input, args.output)
    print(f"Done: {count} uplinks written to {args.output}")
    print(f"You can now import this CSV alongside your GPX/KML track "
          f"into GPSVisualizer, QGIS, or Excel for timestamp matching.")


if __name__ == '__main__':
    main()