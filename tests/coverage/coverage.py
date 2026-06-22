"""
LoRaWAN Coverage Visualizer
============================
Matches GPS track data (.gpx or .kml) with TTN uplink JSON logs by timestamp,
then generates an interactive HTML map showing signal reception quality.

Usage:
    python coverage_map.py --gps track.gpx --ttn uplinks.json
    python coverage_map.py --gps track.kml  --ttn uplinks.json --output map.html

TTN JSON format (from TTN MQTT export or console export):
    A JSON file containing a list of uplink objects, each with:
    {
        "received_at": "2026-04-13T10:23:45.123456789Z",
        "uplink_message": {
            "rx_metadata": [{"rssi": -87, "snr": 7.2}],
            "f_cnt": 42,
            "frm_payload": "..."
        }
    }
    Or a newline-delimited JSON file (one object per line), as exported
    by `mosquitto_sub` piped to a file.

Dependencies:
    pip install gpxpy folium pandas numpy lxml
"""

import argparse
import json
import sys
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import gpxpy
import folium
import pandas as pd
import numpy as np
from folium.plugins import HeatMap, MarkerCluster
from lxml import etree


# ── Timestamp parsing ─────────────────────────────────────────────────────────

def parse_iso(ts: str) -> datetime:
    """
    Parse an ISO-8601 timestamp string into a timezone-aware UTC datetime.
    Handles nanosecond precision from TTN (truncates to microseconds),
    and both 'Z' and '+00:00' UTC designators.
    """
    # Truncate sub-microsecond precision (TTN sends nanoseconds)
    ts = re.sub(r'(\.\d{6})\d+', r'\1', ts)
    ts = ts.replace('Z', '+00:00')
    return datetime.fromisoformat(ts).astimezone(timezone.utc)

# ── GPX loader ────────────────────────────────────────────────────────────────

def load_gpx(path: str) -> pd.DataFrame:
    """
    Parse a .gpx file and return a DataFrame with columns:
        time (datetime, UTC), lat (float), lon (float), ele (float)

    Each row is one trackpoint. Multiple tracks and segments are flattened
    into a single chronologically sorted sequence.
    """
    with open(path, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)

    rows = []
    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                if pt.time is None:
                    continue   # skip points without timestamp
                rows.append({
                    'time': pt.time.astimezone(timezone.utc),
                    'lat':  pt.latitude,
                    'lon':  pt.longitude,
                    'ele':  pt.elevation or 0.0,
                })

    if not rows:
        raise ValueError(f"No timestamped trackpoints found in {path}")

    df = pd.DataFrame(rows).sort_values('time').reset_index(drop=True)
    print(f"[GPX] Loaded {len(df)} trackpoints "
          f"({df['time'].iloc[0]} → {df['time'].iloc[-1]})")
    return df

# ── KML loader ────────────────────────────────────────────────────────────────

def load_kml(path: str) -> pd.DataFrame:
    """
    Parse a .kml file exported from Google Maps, OsmAnd, or similar apps.

    Supports two common KML structures:
      1. <gx:Track> with <when> + <gx:coord> elements (Google Earth timeline)
      2. <LineString><coordinates> (static path, no timestamps – interpolated)

    Returns the same DataFrame schema as load_gpx().
    """
    tree = etree.parse(path)
    root = tree.getroot()

    # XML namespaces used in KML files
    NS  = 'http://www.opengis.net/kml/2.2'
    GX  = 'http://www.google.com/kml/ext/2.2'

    rows = []

    # ── Strategy 1: gx:Track (timestamped) ───────────────────────────────────
    for track in root.iter(f'{{{GX}}}Track'):
        whens  = track.findall(f'{{{GX}}}when')
        coords = track.findall(f'{{{GX}}}coord')

        if len(whens) != len(coords):
            print(f"[KML] Warning: {len(whens)} timestamps vs "
                  f"{len(coords)} coordinates – skipping track")
            continue

        for when_el, coord_el in zip(whens, coords):
            parts = coord_el.text.strip().split()
            if len(parts) < 2:
                continue
            lon, lat = float(parts[0]), float(parts[1])
            ele = float(parts[2]) if len(parts) > 2 else 0.0
            rows.append({
                'time': parse_iso(when_el.text.strip()),
                'lat':  lat,
                'lon':  lon,
                'ele':  ele,
            })

    # ── Strategy 2: LineString (no timestamps – interpolate) ─────────────────
    if not rows:
        print("[KML] No gx:Track found, trying LineString (no timestamps)...")
        for ls in root.iter(f'{{{NS}}}LineString'):
            coord_el = ls.find(f'{{{NS}}}coordinates')
            if coord_el is None or not coord_el.text:
                continue
            coord_text = coord_el.text.strip()
            for entry in coord_text.split():
                parts = entry.split(',')
                if len(parts) < 2:
                    continue
                rows.append({
                    'time': None,   # will be interpolated below
                    'lat':  float(parts[1]),
                    'lon':  float(parts[0]),
                    'ele':  float(parts[2]) if len(parts) > 2 else 0.0,
                })

        if rows:
            # Interpolate timestamps: assume 1 point per second starting now
            # (best effort – tell the user to use a timestamped format)
            base = datetime.now(timezone.utc)
            for i, row in enumerate(rows):
                row['time'] = base + timedelta(seconds=i)
            print(f"[KML] Warning: LineString has no timestamps. "
                  f"Interpolated {len(rows)} points at 1 pt/s. "
                  f"Timestamp matching will be approximate.")

    if not rows:
        raise ValueError(f"No trackpoints found in {path}. "
                         f"Export as gx:Track KML for best results.")

    df = pd.DataFrame(rows).sort_values('time').reset_index(drop=True)
    print(f"[KML] Loaded {len(df)} trackpoints "
          f"({df['time'].iloc[0]} → {df['time'].iloc[-1]})")
    return df

# ── TTN JSON loader ───────────────────────────────────────────────────────────

def load_ttn(path: str) -> pd.DataFrame:
    """
    Load TTN uplink records from a JSON file.

    Accepts two formats:
      - A JSON array:              [ {...}, {...}, ... ]
      - Newline-delimited JSON:    {...}\n{...}\n...
        (as produced by mosquitto_sub -v ... > uplinks.json)

    Extracts per-uplink:
        time    – received_at timestamp (UTC)
        rssi    – best gateway RSSI (dBm)
        snr     – best gateway SNR (dB)
        fcnt    – uplink frame counter
        payload – raw frm_payload (base64 string)
        gw_count – number of gateways that received the packet
    """
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read().strip()

    # Try JSON array first, then newline-delimited
    try:
        records = json.loads(raw)
        if isinstance(records, dict):
            records = [records]   # single object
    except json.JSONDecodeError:
        records = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # mosquitto_sub prepends "topic " before the payload
            if line.startswith('{'):
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            else:
                # Try stripping a leading "topic_name " prefix
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    try:
                        records.append(json.loads(parts[1]))
                    except json.JSONDecodeError:
                        pass

    if not records:
        raise ValueError(f"Could not parse any TTN records from {path}")

    rows = []
    for rec in records:
        try:
            received_at = parse_iso(rec['received_at'])
        except (KeyError, ValueError) as e:
            print(f"[TTN] Skipping record – bad timestamp: {e}")
            continue

        msg      = rec.get('uplink_message', rec)   # handle flat exports too
        rx_meta  = msg.get('rx_metadata', [])
        gw_count = len(rx_meta)

        # Use the best (highest RSSI) gateway metadata
        best_rssi = None
        best_snr  = None
        if rx_meta:
            best = max(rx_meta, key=lambda g: g.get('rssi', -999))
            best_rssi = best.get('rssi')
            best_snr  = best.get('snr')

        rows.append({
            'time':     received_at,
            'rssi':     best_rssi,
            'snr':      best_snr,
            'fcnt':     msg.get('f_cnt'),
            'payload':  msg.get('frm_payload', ''),
            'gw_count': gw_count,
        })

    if not rows:
        raise ValueError("No valid TTN uplink records found")

    df = pd.DataFrame(rows).sort_values('time').reset_index(drop=True)
    print(f"[TTN] Loaded {len(df)} uplinks "
          f"(RSSI range: {df['rssi'].min()} to {df['rssi'].max()} dBm)")
    return df

# ── Timestamp matching ────────────────────────────────────────────────────────

def match_gps_to_uplinks(gps_df: pd.DataFrame,
                          ttn_df: pd.DataFrame,
                          max_delta_s: float = 10.0) -> pd.DataFrame:
    """
    For each TTN uplink, find the GPS trackpoint whose timestamp is closest.
    Discard uplinks where the nearest GPS point is more than max_delta_s
    seconds away (the GPS logger was off, or the walk hadn't started yet).

    Returns a merged DataFrame with one row per matched uplink, containing
    both the GPS coordinates and the TTN signal metrics.

    Parameters
    ----------
    gps_df      : DataFrame from load_gpx() or load_kml()
    ttn_df      : DataFrame from load_ttn()
    max_delta_s : Maximum acceptable time gap in seconds (default 10s).
                  Increase if your GPS logger has coarse time resolution.
    """
    gps_times = gps_df['time'].values.astype('int64')   # nanoseconds

    matched_rows = []
    skipped = 0

    for _, uplink in ttn_df.iterrows():
        uplink_ns = int(uplink['time'].timestamp() * 1e9)

        # Find index of closest GPS point
        idx = np.searchsorted(gps_times, uplink_ns)
        idx = np.clip(idx, 0, len(gps_times) - 1)

        # Also check the neighbour to handle searchsorted boundary
        candidates = [idx]
        if idx > 0:
            candidates.append(idx - 1)

        best_idx   = min(candidates,
                         key=lambda i: abs(gps_times[i] - uplink_ns))
        delta_ns   = abs(gps_times[best_idx] - uplink_ns)
        delta_s    = delta_ns / 1e9

        if delta_s > max_delta_s:
            skipped += 1
            continue

        gps_row = gps_df.iloc[best_idx]
        matched_rows.append({
            'time':      uplink['time'],
            'lat':       gps_row['lat'],
            'lon':       gps_row['lon'],
            'ele':       gps_row['ele'],
            'delta_s':   round(delta_s, 2),
            'rssi':      uplink['rssi'],
            'snr':       uplink['snr'],
            'fcnt':      uplink['fcnt'],
            'gw_count':  uplink['gw_count'],
            'payload':   uplink['payload'],
        })

    matched = pd.DataFrame(matched_rows)
    print(f"[Match] {len(matched)} uplinks matched, "
          f"{skipped} skipped (gap > {max_delta_s}s)")

    if matched.empty:
        raise ValueError(
            "No uplinks could be matched to GPS points. "
            "Check that the timestamps overlap and consider increasing "
            "--max-delta."
        )

    return matched

# ── Colour mapping ────────────────────────────────────────────────────────────

def rssi_to_colour(rssi: float) -> str:
    """
    Map RSSI (dBm) to a colour for circle markers.

    Thresholds chosen for LoRaWAN at 868 MHz:
        > -100 dBm  : strong signal   → green
        -110 to -100: acceptable      → yellow / orange
        < -110 dBm  : weak signal     → red
        None        : unknown         → grey
    """
    if rssi is None or (isinstance(rssi, float) and np.isnan(rssi)):
        return '#888888'
    if rssi >= -90:
        return '#00cc44'   # strong green
    elif rssi >= -100:
        return '#88cc00'   # yellow-green
    elif rssi >= -110:
        return '#ffaa00'   # amber
    elif rssi >= -120:
        return '#ff5500'   # orange-red
    else:
        return '#cc0000'   # deep red (near sensitivity floor)


# ── Map builder ───────────────────────────────────────────────────────────────

def build_map(gps_df: pd.DataFrame,
              matched: pd.DataFrame,
              output_path: str) -> None:
    """
    Build a Folium interactive HTML map with three layers:

    1. GPS Track         – thin polyline showing the full walked route
    2. RSSI Circle Markers – colour-coded dots at each uplink location
    3. RSSI Heatmap      – continuous heatmap of signal strength
       (weighted by RSSI shifted to positive range for folium HeatMap)

    The map has a layer control so the user can toggle layers on/off.
    """
    # Centre map on the GPS track centroid
    centre_lat = gps_df['lat'].mean()
    centre_lon = gps_df['lon'].mean()

    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=15,
        tiles='CartoDB positron',
    )

    # ── Layer 1: GPS track ────────────────────────────────────────────────────
    track_coords = list(zip(gps_df['lat'], gps_df['lon']))
    folium.PolyLine(
        locations=track_coords,
        color='#3388ff',
        weight=2,
        opacity=0.6,
        tooltip='GPS track',
    ).add_to(folium.FeatureGroup(name='GPS Track', show=True).add_to(m))

    # ── Layer 2: RSSI circle markers ─────────────────────────────────────────
    marker_group = folium.FeatureGroup(name='Uplinks (RSSI colour)', show=True)
    for _, row in matched.iterrows():
        rssi_val = row['rssi']
        colour   = rssi_to_colour(rssi_val)

        rssi_str = f"{rssi_val:.0f} dBm" if rssi_val is not None else "N/A"
        snr_str  = (f"{row['snr']:.1f} dB"
                    if row['snr'] is not None else "N/A")

        popup_html = f"""
        <div style="font-family: monospace; font-size: 12px; min-width: 180px">
            <b>Uplink #{int(row['fcnt']) if row['fcnt'] else '?'}</b><br>
            <b>RSSI:</b> {rssi_str}<br>
            <b>SNR:</b>  {snr_str}<br>
            <b>Gateways:</b> {int(row['gw_count'])}<br>
            <b>Time:</b> {row['time'].strftime('%H:%M:%S UTC')}<br>
            <b>GPS Δt:</b> {row['delta_s']:.1f} s<br>
            <b>Lat/Lon:</b> {row['lat']:.6f}, {row['lon']:.6f}
        </div>
        """

        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=7,
            color=colour,
            fill=True,
            fill_color=colour,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"RSSI {rssi_str}",
        ).add_to(marker_group)

    marker_group.add_to(m)

    # ── Layer 3: RSSI heatmap ─────────────────────────────────────────────────
    # HeatMap expects [lat, lon, weight]. Weight must be positive,
    # so we shift RSSI: weight = RSSI + 150 (maps -150…0 → 0…150).
    heat_data = []
    for _, row in matched.iterrows():
        if row['rssi'] is not None and not np.isnan(row['rssi']):
            weight = float(row['rssi']) + 150.0   # shift to positive
            heat_data.append([row['lat'], row['lon'], max(weight, 0.1)])

    heatmap_group = folium.FeatureGroup(name='RSSI Heatmap', show=False)
    HeatMap(
        heat_data,
        min_opacity=0.3,
        max_zoom=18,
        radius=20,
        blur=15,
        gradient={
            0.0:  '#cc0000',   # weak  (RSSI < -120 dBm)
            0.35: '#ff5500',
            0.55: '#ffaa00',
            0.75: '#88cc00',
            1.0:  '#00cc44',   # strong (RSSI > -90 dBm)
        },
    ).add_to(heatmap_group)
    heatmap_group.add_to(m)

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px; right: 30px;
        z-index: 1000;
        background: white;
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 12px 16px;
        font-family: monospace;
        font-size: 12px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
    ">
        <b>RSSI (dBm)</b><br>
        <span style="color:#00cc44">&#9632;</span> &gt; -90 &nbsp; Strong<br>
        <span style="color:#88cc00">&#9632;</span> -90 to -100<br>
        <span style="color:#ffaa00">&#9632;</span> -100 to -110<br>
        <span style="color:#ff5500">&#9632;</span> -110 to -120<br>
        <span style="color:#cc0000">&#9632;</span> &lt; -120 &nbsp; Weak<br>
        <span style="color:#888888">&#9632;</span> Unknown
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # ── Statistics box ────────────────────────────────────────────────────────
    rssi_vals = matched['rssi'].dropna()
    stats_html = f"""
    <div style="
        position: fixed;
        top: 30px; right: 30px;
        z-index: 1000;
        background: white;
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 12px 16px;
        font-family: monospace;
        font-size: 12px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
        min-width: 180px;
    ">
        <b>Session Summary</b><br>
        Uplinks matched: {len(matched)}<br>
        RSSI mean: {rssi_vals.mean():.1f} dBm<br>
        RSSI min:  {rssi_vals.min():.1f} dBm<br>
        RSSI max:  {rssi_vals.max():.1f} dBm<br>
        Track pts: {len(gps_df)}<br>
        Start: {gps_df['time'].iloc[0].strftime('%H:%M UTC')}<br>
        End:   {gps_df['time'].iloc[-1].strftime('%H:%M UTC')}
    </div>
    """
    m.get_root().html.add_child(folium.Element(stats_html))

    # ── Layer control ─────────────────────────────────────────────────────────
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(output_path)
    print(f"[Map] Saved to {output_path}")
    print(f"Open in any browser: file://{os.path.abspath(output_path)}")

# ── CSV export ────────────────────────────────────────────────────────────────

def export_csv(matched: pd.DataFrame, output_path: str) -> None:
    """Export matched data to CSV for further analysis (e.g. in pandas or R)."""
    csv_path = output_path.replace('.html', '_data.csv')
    matched.to_csv(csv_path, index=False)
    print(f"[CSV] Data exported to {csv_path}")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent

    # Load GPS
    gps_path = script_dir/"gps_data"/"20260616-162909-rev-a-1.gpx"
    gps_df = load_gpx(gps_path)
    # Load TTN
    ttn_path = script_dir/"ttn_data"/"20260616-162909-rev-a-1.json"
    ttn_df = load_ttn(ttn_path)
    print(ttn_path.exists())

    # ── Timestamp overlap check ───────────────────────────────────────────────
    gps_start = gps_df['time'].iloc[0]
    gps_end   = gps_df['time'].iloc[-1]
    ttn_start = ttn_df['time'].iloc[0]
    ttn_end   = ttn_df['time'].iloc[-1]

    print(f"\n[Info] GPS  window: {gps_start} → {gps_end}")
    print(f"[Info] TTN  window: {ttn_start} → {ttn_end}")

    overlap_start = max(gps_start, ttn_start)
    overlap_end   = min(gps_end,   ttn_end)

    if overlap_start >= overlap_end:
        print("\nWarning: GPS and TTN timestamps do not overlap.")
        print("  Check that both files are from the same measurement session")
        print("  and that your device clock and GPS clock are in sync (UTC).")
        # Continue anyway – matching will report 0 matches and raise ValueError