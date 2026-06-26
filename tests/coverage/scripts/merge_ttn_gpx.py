import pandas as pd
import numpy as np
from pathlib import Path

# ==========================================
SCRIPT_DIR = Path(__file__).resolve().parent

TTN_FILE = SCRIPT_DIR / 'ttn_log.csv'
GPX_FILE = SCRIPT_DIR / 'combined_gpx.csv'
OUTPUT_FILE = SCRIPT_DIR / 'ttn_with_gps_final.csv'

TTN_TIMESTAMP_COL = 'timestamp'          
GPX_TIMESTAMP_COL = 'timestamp'    

GPX_GPS_CHECK_COL = 'latitude'
# ==========================================

print("Lade Datensätze...")
df_ttn = pd.read_csv(TTN_FILE)
df_gpx = pd.read_csv(GPX_FILE)

print("Konvertiere Zeitstempel in Datetime-Objekte...")
# pd.to_datetime verarbeitet ISO-Strings sowie Epoch/Unix-Zeitstempel automatisch
df_ttn['match_time'] = pd.to_datetime(df_ttn[TTN_TIMESTAMP_COL])
df_gpx['match_time'] = pd.to_datetime(df_gpx[GPX_TIMESTAMP_COL])

# <-- ÄNDERUNG 1: Entferne die originale GPX-Zeitstempelspalte vor dem Merge,
# damit sie im finalen Datensatz nicht als Duplikat (z.B. 'time_gpx') auftaucht.
if GPX_TIMESTAMP_COL in df_gpx.columns and GPX_TIMESTAMP_COL != 'match_time':
    df_gpx = df_gpx.drop(columns=[GPX_TIMESTAMP_COL])

# WICHTIG: Beide DataFrames MÜSSEN für merge_asof nach der Zeit sortiert sein!
df_ttn = df_ttn.sort_values('match_time')
df_gpx = df_gpx.sort_values('match_time')

print("Merging dataframes by matching timestamps")
final_df = pd.merge_asof(
    df_ttn,
    df_gpx,
    on='match_time',
    direction='nearest',
    tolerance=pd.Timedelta('120s'),  # Maximal 10 Sekunden Versatz erlaubt
    suffixes=('', '_gpx')           # Verhindert Namenskonflikte bei doppelten Spalten
)

# Delete auxiliary column
final_df = final_df.drop(columns=['match_time'])

# Delete rows with no gps and ttn match
original_row_count = len(final_df)
final_df = final_df.dropna(subset=[GPX_GPS_CHECK_COL])
deleted_rows = original_row_count - len(final_df)

# Speichern
final_df.to_csv(OUTPUT_FILE, index=False)

print("\n=== ERFOLG ===")
print(f"Das originale TTN-DataFrame hatte {len(df_ttn)} Zeilen.")
print(f"Das finale DataFrame hat exakt dieselbe Anzahl: {len(final_df)} Zeilen.")
print(f"Datei erfolgreich gespeichert unter: {OUTPUT_FILE}")