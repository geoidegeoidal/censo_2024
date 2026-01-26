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
    
    # SOLO MANZANAS (URBANO) - Entidades rurales distorsionan visualización
    layers = ['Manzanas_CPV24'] 
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

    print("Procesando capa urbana (Manzanas)...")
    gdf = pd.concat(gdfs, ignore_index=True)
    print(f"Total registros cargados (Nacional): {len(gdf)}")

    # === 1.5 FILTRO ESTRICTO REGIÓN METROPOLITANA ===
    # Para que los Z-Scores sean locales y metodológicamente relevantes
    print("Filtrando solo REGIÓN METROPOLITANA para análisis relativo local...")
    # Aseguramos que sea string y buscamos 'METROPOLITANA' o codigo '13' (si aplica)
    gdf = gdf[gdf['REGION'].astype(str).str.contains('METROPOLITANA', case=False, na=False)].copy()
    print(f"Registros en RM: {len(gdf)}")
    
    if gdf.empty:
        print("CRITICAL: El filtro RM dejó el dataframe vacío.")
        return

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

    # ==================================================
    # 4. INDICADORES COMPUESTOS ROBUSTOS (Z-SCORES)
    # ==================================================
    print("Calculando indicadores compuestos con Normalización Z-Score...")
    
    # 4.1 Definir variables crudas necesarias
    vars_raw = [
        # Universos
        'n_vp', 'n_hog', 'n_per',
        # Precariedad Dimensión 1: Hacinamiento/Allegamiento
        'n_viv_hacinadas', 'n_hog_allegados', 'n_nucleos_hacinados_allegados', 
        # Precariedad Dimensión 2: Materialidad
        'n_viv_irrecuperables', 'n_tipo_viv_mediagua', 
        'n_mat_paredes_precarios', 'n_mat_techo_precarios', 'n_mat_piso_tierra',
        # Precariedad Dimensión 3: Tenencia/Formalidad
        'n_tenencia_arrendada_sin_contrato', 'n_tenencia_cedida_familiar',
        # Precariedad Dimensión 4: Saneamiento/Agua
        'n_fuente_agua_pozo', 'n_fuente_agua_camion', 'n_fuente_agua_rio',
        'n_serv_hig_fosa', 'n_serv_hig_no_tiene',
        
        # Vulnerabilidad
        'n_desocupado', 'n_ocupado', 'n_analfabet', 'n_jefatura_mujer', 
        'n_internet', # Brecha digital
        
        # Privilegio
        'n_cine_terciaria_maestria_doctorado', 
        'n_transporte_auto', 
        'n_tenencia_propia_pagada',
        'n_serv_internet_fija', 'n_serv_compu', # Calidad Conectividad
        'n_dormitorios_4', 'n_dormitorios_5', 'n_dormitorios_6_o_mas' # Espacio
    ]
    
    # Rellenar Nulos en variables crudas
    for c in vars_raw:
        if c not in gdf.columns:
            gdf[c] = 0 # Fallback si no existe la columna
        else:
            gdf[c] = gdf[c].fillna(0)

    # 4.2 Helper para porcentajes seguros
    def calc_pct(num_col, den_col):
        # Si denominador es 0, retorna 0 (no NaN para no romper Z-score)
        return (gdf[num_col] / gdf[den_col].replace(0, np.nan)).fillna(0) * 100

    # 4.3 Calcular Variables Intermedias (Porcentajes)
    # PRECARIEDAD
    p_hacinamiento  = calc_pct('n_viv_hacinadas', 'n_vp')
    p_allegamiento  = calc_pct('n_hog_allegados', 'n_hog')
    p_irrecup       = calc_pct('n_viv_irrecuperables', 'n_vp')
    p_mediagua      = calc_pct('n_tipo_viv_mediagua', 'n_vp')
    p_mat_precari   = calc_pct('n_mat_paredes_precarios', 'n_vp') + calc_pct('n_mat_techo_precarios', 'n_vp') + calc_pct('n_mat_piso_tierra', 'n_vp')
    p_sin_contrato  = calc_pct('n_tenencia_arrendada_sin_contrato', 'n_hog')
    p_cedida        = calc_pct('n_tenencia_cedida_familiar', 'n_hog')
    p_saneamiento   = calc_pct('n_serv_hig_no_tiene', 'n_vp') + calc_pct('n_fuente_agua_camion', 'n_vp') # Fosas, NoTiene, Camion

    # VULNERABILIDAD
    fuerza_lab = gdf['n_ocupado'] + gdf['n_desocupado']
    p_desempleo     = (gdf['n_desocupado'] / fuerza_lab.replace(0, np.nan)).fillna(0) * 100
    p_analfabet     = calc_pct('n_analfabet', 'n_per')
    p_jefa          = calc_pct('n_jefatura_mujer', 'n_hog')
    p_sin_internet  = 100 - calc_pct('n_internet', 'n_hog')

    # PRIVILEGIO ("Cuestiona tus privilegios")
    p_profesional   = calc_pct('n_cine_terciaria_maestria_doctorado', 'n_per')
    p_propia_pagada = calc_pct('n_tenencia_propia_pagada', 'n_hog')
    p_auto          = calc_pct('n_transporte_auto', 'n_per')
    p_int_fija      = calc_pct('n_serv_internet_fija', 'n_hog') # Internet de Alta Calidad
    p_computador    = calc_pct('n_serv_compu', 'n_hog')
    # Espacio (Casas grandes): 4+ dormitorios
    p_espacio       = calc_pct('n_dormitorios_4', 'n_vp') + calc_pct('n_dormitorios_5', 'n_vp') + calc_pct('n_dormitorios_6_o_mas', 'n_vp')

    # 4.4 Normalización Z-Score (Estandarización)
    # Z = (x - mean) / std.
    # Esto centra las variables en 0 (promedio regional RM) y escala por desviación.
    def z_score(series):
        std = series.std()
        if std == 0: return series * 0
        return (series - series.mean()) / std

    # --- A. ÍNDICE DE PRECARIEDAD HABITACIONAL ROBUSTO ---
    # Promedio de Z-Scores de dimensiones negativas
    z_precariedad = (
        z_score(p_hacinamiento) + 
        z_score(p_allegamiento) + 
        z_score(p_irrecup) + 
        z_score(p_mat_precari) +
        z_score(p_saneamiento) +
        z_score(p_sin_contrato) + 
        z_score(p_cedida) # Cedida contextualizada
    ) / 7.0 
    
    # 4.6 SCALING 0-100 (Min-Max) para legibilidad
    def minmax_scale(series):
        if series.max() == series.min(): return series * 0
        return ((series - series.min()) / (series.max() - series.min())) * 100

    gdf['idx_precariedad_hab'] = minmax_scale(z_precariedad)

    # --- B. ÍNDICE DE VULNERABILIDAD SOCIAL ROBUSTO ---
    z_vulnerabilidad = (
        z_score(p_desempleo) +
        z_score(p_analfabet) +
        z_score(p_sin_internet) +
        z_score(p_jefa)
    ) / 4.0
    gdf['idx_vulnerabilidad_soc'] = minmax_scale(z_vulnerabilidad)

    # --- C. ÍNDICE DE PRIVILEGIO ROBUSTO ("Cuestiona tus privilegios") ---
    # Promedio de Z-Scores de dimensiones positivas
    z_privilegio = (
        z_score(p_profesional) +
        z_score(p_propia_pagada) +
        z_score(p_auto) +
        z_score(p_int_fija) +
        z_score(p_computador) +
        z_score(p_espacio)
    ) / 6.0
    gdf['idx_privilegio'] = minmax_scale(z_privilegio)
    
    # 4.5 Limpieza
    cols_extra = [
         'n_hog_allegados', 'n_nucleos_hacinados_allegados',
         'n_mat_paredes_precarios', 'n_serv_internet_fija', 'n_serv_compu',
         'n_dormitorios_4', 'n_dormitorios_5', 'n_dormitorios_6_o_mas'
    ]
    # Check existence before adding to keep_cols inside the list comp
    available_extra = [c for c in cols_extra if c in gdf.columns]

    # 4. Limpieza Final y Exportación
    # Seleccionamos solo columnas relevantes para el mapa ligero
    # IMPORTANTE: Incluimos las columnas 'n_...' raw para poder recalcular 
    # promedios ponderados por comuna en el script de visualización.
    keep_cols = [
        'MANZENT', 'CUT', 'REGION', 'PROVINCIA', 'COMUNA', 'AREA_C',  # Identificadores
        'geometry', 'MZ_BASE_CENSO',                        # Geometria y filtro
        'n_per', 'n_vp', 'n_hog',                           # Universos
        'n_vp_ocupada',                                     # Viviendas ocupadas (para hacinamiento correcto)
        'pct_adulto_mayor', 'pct_infancia', 'pct_inmigrantes', 
        'pct_hacinamiento', 'pct_deficit_agua', 'pct_lena', 
        'pct_internet',
        # Variables base para ponderación
        'n_internet', 'n_viv_hacinadas', 'n_inmigrantes',
        'n_fuente_agua_camion', 'n_fuente_agua_rio', 'n_fuente_agua_pozo',
        'n_hog_unipersonales', # Para indicador Forever Alone
        'n_transporte_bicicleta', # Para Ciclistas Furiosos
        'n_tenencia_propia_pagandose', # Para Hipotecados
        'n_estcivcon_anul_sep_div', # Para Club de los Ex
        'n_cise_rec_independientes', # Para Mente de Tiburón
        # Estado Civil Completo (para "Aún Sin Anillo" con denominador correcto)
        'n_estcivcon_soltero', 'n_estcivcon_casado', 'n_estcivcon_conviviente', 
        'n_estcivcon_conv_civil', 'n_estcivcon_viudo',
        # Componentes de indices compuestos (para agregación)
        'n_viv_irrecuperables', 'n_tipo_viv_mediagua', 
        'n_tenencia_arrendada_sin_contrato', 'n_tenencia_cedida_familiar',
        'n_desocupado', 'n_ocupado', 'n_analfabet', 'n_jefatura_mujer',
        'n_cine_terciaria_maestria_doctorado', 'n_transporte_auto', 'n_tenencia_propia_pagada', # Para Privilegio
        # Índices Pre-calculados (Z-Scores)
        'idx_precariedad_hab', 'idx_vulnerabilidad_soc', 'idx_privilegio'
    ] + available_extra
    
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
