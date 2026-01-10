import geopandas as gpd
import pandas as pd
import numpy as np
import os

# Configuración
INPUT_FILE = 'Cartografia_censo2024_Pais.gpkg'
OUTPUT_FILE = 'Manzanas_Indicadores.gpkg'
LAYER_NAME = 'Manzanas_CPV24' # O el nombre correcto de la capa de manzanas

def process_data():
    print(f"Leyendo archivo: {INPUT_FILE}...")
    
    layers = ['Manzanas_CPV24', 'Entidades_CPV24']
    gdfs = []
    
    for layer in layers:
        print(f"  > Leyendo capa: {layer}...")
        try:
            # Intentar filtro SQL simple para optimizar
            # Asumimos que amblas capas tienen MZ_BASE_CENSO o equivalente para filtrar validez
            # En entidades a veces todas son validas, pero aplicamos el filtro por consistencia si existe la columna
            # Si falla, leemos todo y concatenamos.
            temp_gdf = gpd.read_file(INPUT_FILE, layer=layer)
            if 'MZ_BASE_CENSO' in temp_gdf.columns:
                 temp_gdf = temp_gdf[temp_gdf['MZ_BASE_CENSO'] == 1]
            gdfs.append(temp_gdf)
        except Exception as e:
            print(f"    Error leyendo {layer}: {e}")
            
    if not gdfs:
        print("CRITICAL: No se pudo cargar ninguna capa.")
        return

    print("Fusionando capas urbana (Manzanas) y rural (Entidades)...")
    gdf = pd.concat(gdfs, ignore_index=True)
    print(f"Total registros cargados: {len(gdf)}")

    # 2. Manejo de Nulos en Indicadores
    # Las columnas n_* pueden venir como NaN si fueron suprimidas. Reemplazamos por 0 para calculos agregados,
    # PERO, para visualización honesta, quizás deberíamos dejarlas fuera opcionalmente.
    # Para el mapa, asumiremos 0 para poder pintar, o mantendremos NaN si el indicador resulta inválido.
    # Vamos a llenar con 0 las columnas n_ antes de calcular.
    
    n_cols = [c for c in gdf.columns if c.startswith('n_')]
    gdf[n_cols] = gdf[n_cols].fillna(0)

    # 3. Cálculo de Indicadores
    print("Calculando indicadores...")

    # Evitar division por cero
    # n_per (personas) y n_vp (viviendas particulares) son los denominadores principales
    gdf['n_per'] = gdf['n_per'].replace(0, np.nan) 
    gdf['n_vp'] = gdf['n_vp'].replace(0, np.nan)
    gdf['n_hog'] = gdf['n_hog'].replace(0, np.nan)

    # --- DEMOGRAFÍA ---
    # Índice de Envejecimiento: (60+ / Total) * 100
    gdf['pct_adulto_mayor'] = (gdf['n_edad_60_mas'] / gdf['n_per']) * 100
    
    # Dependencia Juvenil (0-14 aprox, aqui 0-13 segun columnas): ((0-5 + 6-13) / Total) * 100
    gdf['pct_infancia'] = ((gdf['n_edad_0_5'] + gdf['n_edad_6_13']) / gdf['n_per']) * 100
    
    # Inmigración
    gdf['pct_inmigrantes'] = (gdf['n_inmigrantes'] / gdf['n_per']) * 100
    
    # --- CALIDAD DE VIDA ---
    # Hacinamiento
    gdf['pct_hacinamiento'] = (gdf['n_viv_hacinadas'] / gdf['n_vp']) * 100
    
    # Déficit Hídrico (Sin red pública: camión + río + pozo)
    # Ajustar nombres de columnas segun lo visto en el output anterior del usuario
    gdf['pct_deficit_agua'] = ((gdf['n_fuente_agua_camion'] + gdf['n_fuente_agua_rio'] + gdf['n_fuente_agua_pozo']) / gdf['n_vp']) * 100

    # Calefacción a Leña (Contaminación)
    gdf['pct_lena'] = (gdf['n_comb_calefaccion_lena'] / gdf['n_vp']) * 100

    # --- CONECTIVIDAD ---
    # Internet Fijo (Brecha Digital)
    # Usamos n_internet (que parece ser el total con internet) sobre n_hog (hogares)
    gdf['pct_internet'] = (gdf['n_internet'] / gdf['n_hog']) * 100

    # 4. Limpieza Final y Exportación
    # Seleccionamos solo columnas relevantes para el mapa ligero
    # IMPORTANTE: Incluimos las columnas 'n_...' raw para poder recalcular 
    # promedios ponderados por comuna en el script de visualización.
    keep_cols = [
        'MANZENT', 'CUT', 'REGION', 'PROVINCIA', 'COMUNA',  # Identificadores
        'geometry', 'MZ_BASE_CENSO',                        # Geometria y filtro
        'n_per', 'n_vp', 'n_hog',                           # Universos
        'pct_adulto_mayor', 'pct_infancia', 'pct_inmigrantes', 
        'pct_hacinamiento', 'pct_deficit_agua', 'pct_lena', 
        'pct_internet',
        # Variables base para ponderación
        'n_internet', 'n_viv_hacinadas', 'n_inmigrantes',
        'n_fuente_agua_camion', 'n_fuente_agua_rio', 'n_fuente_agua_pozo',
        'n_hog_unipersonales', # Para indicador Forever Alone
        'n_transporte_bicicleta', # Para Ciclistas Furiosos
        'n_tenencia_propia_pagandose', # Para Hipotecados
        'n_estcivcon_anul_sep_div' # Para Club de los Ex
    ]
    
    # Filtrar solo columnas que existen (por si acaso algun ID geogrfico tiene otro nombre)
    final_cols = [c for c in keep_cols if c in gdf.columns]
    output_gdf = gdf[final_cols]
    
    # Reemplazar infinitos o NaNs resultantes de division por cero con -1 (para pintar 'Sin Datos') o 0
    # Para visualización continua, 0 suele ser mas seguro, o Null. Dejemos Null.
    # output_gdf = output_gdf.fillna(-9999) # Opcional

    print(f"Guardando {OUTPUT_FILE}...")
    output_gdf.to_file(OUTPUT_FILE, driver='GPKG')
    
    print("¡Proceso completado con éxito!")
    print(f"Archivo generado: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    process_data()
