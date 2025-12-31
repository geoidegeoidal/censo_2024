import geopandas as gpd
import pandas as pd

# Configuración
INPUT_FILE = 'Cartografia_censo2024_Pais.gpkg'
LAYER_NAME = 'Manzanas_CPV24'

def inspect_columns():
    print(f"Inspeccionando capa: {LAYER_NAME} en {INPUT_FILE}...")
    try:
        # Leemos solo 1 fila para ver las columnas
        gdf = gpd.read_file(INPUT_FILE, layer=LAYER_NAME, rows=1)
        
        print("\n--- COLUMNAS DISPONIBLES ---")
        cols = list(gdf.columns)
        # Imprimimos ordenado para facilitar lectura
        for i, c in enumerate(sorted(cols)):
            print(f"{i}: {c}")
            
        print("\n--- BUSQUEDA DE 'n_viv_part' ---")
        matches = [c for c in cols if 'viv' in c.lower() or 'part' in c.lower()]
        print(f"Posibles coincidencias: {matches}")
        
    except Exception as e:
        print(f"Error al leer: {e}")

if __name__ == "__main__":
    inspect_columns()
