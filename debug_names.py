
import geopandas as gpd
import pandas as pd

INPUT_FILE = 'Manzanas_Indicadores.gpkg'

try:
    gdf = gpd.read_file(INPUT_FILE)
    print("Columns:", gdf.columns)
    if 'COMUNA' in gdf.columns:
        print("Unique Comunas (first 20):", sorted(gdf['COMUNA'].unique())[:20])
    if 'REGION' in gdf.columns:
        print("Unique Regions:", gdf['REGION'].unique())
        
    # Check if Santiago matches
    if 'COMUNA' in gdf.columns:
        print("Santiago check:", 'SANTIAGO' in gdf['COMUNA'].unique())
        print("Puente Alto check:", 'PUENTE ALTO' in gdf['COMUNA'].unique())

except Exception as e:
    print(f"Error: {e}")
