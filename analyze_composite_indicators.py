"""
Análisis Exploratorio de Variables del Censo 2024
Objetivo: Entender correlaciones para construir indicadores compuestos significativos
"""
import geopandas as gpd
import pandas as pd
import numpy as np

# Cargar datos crudos con todas las columnas
INPUT_FILE = 'Cartografia_censo2024_Pais.gpkg'
print(f"Cargando {INPUT_FILE}...")

# Leer ambas capas
layers = ['Manzanas_CPV24', 'Entidades_CPV24']
gdfs = []
for layer in layers:
    print(f"  > Leyendo capa: {layer}...")
    try:
        temp_gdf = gpd.read_file(INPUT_FILE, layer=layer)
        if 'MZ_BASE_CENSO' in temp_gdf.columns:
            temp_gdf = temp_gdf[temp_gdf['MZ_BASE_CENSO'] == 1]
        gdfs.append(temp_gdf)
    except Exception as e:
        print(f"    Error: {e}")

gdf = pd.concat(gdfs, ignore_index=True)
print(f"Total registros: {len(gdf)}")

# Filtrar Región Metropolitana
gdf = gdf[gdf['REGION'].astype(str).str.contains('METROPOLITANA', case=False, na=False)].copy()
print(f"Registros RM: {len(gdf)}")

# ============================================
# AGREGAR A NIVEL COMUNAL
# ============================================
# Definir todas las columnas numéricas relevantes
numeric_cols = [
    # Universos
    'n_per', 'n_hog', 'n_vp',
    # Demografía
    'n_hombres', 'n_mujeres',
    'n_edad_0_5', 'n_edad_6_13', 'n_edad_14_17', 'n_edad_18_24', 
    'n_edad_25_44', 'n_edad_45_59', 'n_edad_60_mas',
    'n_inmigrantes',
    # Estado Civil
    'n_estcivcon_casado', 'n_estcivcon_conviviente', 'n_estcivcon_conv_civil',
    'n_estcivcon_anul_sep_div', 'n_estcivcon_viudo', 'n_estcivcon_soltero',
    # Educación
    'n_cine_primaria', 'n_cine_secundaria', 'n_cine_terciaria_maestria_doctorado',
    'n_analfabet',
    # Trabajo
    'n_ocupado', 'n_desocupado', 'n_fuera_fuerza_trabajo',
    'n_cise_rec_independientes', 'n_cise_rec_dependientes',
    # Transporte
    'n_transporte_auto', 'n_transporte_publico', 'n_transporte_camina', 
    'n_transporte_bicicleta', 'n_transporte_motocicleta',
    # Hogares
    'n_hog_unipersonales', 'n_hog_60', 'n_hog_menores', 'n_jefatura_mujer',
    # Tenencia Vivienda
    'n_tenencia_propia_pagada', 'n_tenencia_propia_pagandose',
    'n_tenencia_arrendada_contrato', 'n_tenencia_arrendada_sin_contrato',
    'n_tenencia_cedida_trabajo', 'n_tenencia_cedida_familiar', 'n_tenencia_otro',
    # Tipo Vivienda
    'n_tipo_viv_casa', 'n_tipo_viv_depto', 'n_tipo_viv_mediagua', 'n_tipo_viv_pieza',
    # Calidad Vivienda
    'n_viv_hacinadas', 'n_viv_irrecuperables', 'n_deficit_cuantitativo',
    # Servicios
    'n_serv_compu', 'n_internet',
    # Combustible
    'n_comb_cocina_gas', 'n_comb_cocina_lena', 'n_comb_calefaccion_lena',
    # Agua y Saneamiento
    'n_fuente_agua_publica', 'n_fuente_agua_pozo', 'n_fuente_agua_camion', 'n_fuente_agua_rio',
    'n_serv_hig_alc_dentro', 'n_serv_hig_fosa', 'n_serv_hig_no_tiene',
]

# Filtrar columnas que existen
numeric_cols = [c for c in numeric_cols if c in gdf.columns]
print(f"Columnas numéricas disponibles: {len(numeric_cols)}")

# Agregar por comuna
stats = gdf.groupby('COMUNA')[numeric_cols].sum().reset_index()

# Evitar división por cero
stats['n_per'] = stats['n_per'].replace(0, np.nan)
stats['n_hog'] = stats['n_hog'].replace(0, np.nan)
stats['n_vp'] = stats['n_vp'].replace(0, np.nan)

# ============================================
# CALCULAR TODOS LOS PORCENTAJES
# ============================================
print("\nCalculando indicadores porcentuales...")

# --- VIVIENDA ---
stats['pct_cedida_familiar'] = (stats['n_tenencia_cedida_familiar'] / stats['n_hog']) * 100
stats['pct_arrendada_sin_contrato'] = (stats['n_tenencia_arrendada_sin_contrato'] / stats['n_hog']) * 100
stats['pct_propia_pagada'] = (stats['n_tenencia_propia_pagada'] / stats['n_hog']) * 100
stats['pct_propia_pagandose'] = (stats['n_tenencia_propia_pagandose'] / stats['n_hog']) * 100
stats['pct_mediagua'] = (stats['n_tipo_viv_mediagua'] / stats['n_vp']) * 100
stats['pct_hacinamiento'] = (stats['n_viv_hacinadas'] / stats['n_vp']) * 100
stats['pct_viv_irrecuperable'] = (stats['n_viv_irrecuperables'] / stats['n_vp']) * 100
stats['pct_deficit_cuanti'] = (stats['n_deficit_cuantitativo'] / stats['n_vp']) * 100

# --- SERVICIOS BÁSICOS ---
stats['pct_sin_agua_red'] = ((stats['n_fuente_agua_pozo'] + stats['n_fuente_agua_camion'] + stats['n_fuente_agua_rio']) / stats['n_vp']) * 100
stats['pct_sin_alcantarillado'] = ((stats['n_serv_hig_fosa'] + stats.get('n_serv_hig_no_tiene', 0)) / stats['n_vp']) * 100
stats['pct_internet'] = (stats['n_internet'] / stats['n_hog']) * 100

# --- DEMOGRAFÍA ---
stats['pct_inmigrantes'] = (stats['n_inmigrantes'] / stats['n_per']) * 100
stats['pct_adulto_mayor'] = (stats['n_edad_60_mas'] / stats['n_per']) * 100
stats['pct_ninos'] = ((stats['n_edad_0_5'] + stats['n_edad_6_13']) / stats['n_per']) * 100
stats['pct_jefa_hogar'] = (stats['n_jefatura_mujer'] / stats['n_hog']) * 100
stats['pct_hog_unipersonal'] = (stats['n_hog_unipersonales'] / stats['n_hog']) * 100

# --- EDUCACIÓN / TRABAJO ---
stats['pct_profesional'] = (stats['n_cine_terciaria_maestria_doctorado'] / stats['n_per']) * 100
stats['pct_analfabeto'] = (stats['n_analfabet'] / stats['n_per']) * 100
stats['pct_desocupado'] = (stats['n_desocupado'] / (stats['n_ocupado'] + stats['n_desocupado'])) * 100
stats['pct_independiente'] = (stats['n_cise_rec_independientes'] / stats['n_per']) * 100

# --- ESTADO CIVIL ---
stats['pct_divorciado'] = (stats['n_estcivcon_anul_sep_div'] / stats['n_per']) * 100
stats['pct_soltero'] = (stats['n_estcivcon_soltero'] / stats['n_per']) * 100
stats['pct_viudo'] = (stats['n_estcivcon_viudo'] / stats['n_per']) * 100

# --- TRANSPORTE ---
stats['pct_auto'] = (stats['n_transporte_auto'] / stats['n_per']) * 100
stats['pct_transporte_publico'] = (stats['n_transporte_publico'] / stats['n_per']) * 100
stats['pct_bicicleta'] = (stats['n_transporte_bicicleta'] / stats['n_per']) * 100
stats['pct_camina'] = (stats['n_transporte_camina'] / stats['n_per']) * 100

# ============================================
# ANÁLISIS: CORRELACIONES CON VIVIENDA CEDIDA
# ============================================
print("\n" + "="*60)
print(" ANÁLISIS: ¿QUÉ SIGNIFICA 'VIVIENDA CEDIDA POR FAMILIAR'?")
print("="*60)

# Seleccionar columnas de porcentaje para correlación
pct_cols = [c for c in stats.columns if c.startswith('pct_')]
corr_target = 'pct_cedida_familiar'

corr_matrix = stats[pct_cols].corr()
correlations = corr_matrix[corr_target].drop(corr_target).sort_values(ascending=False)

print(f"\n📊 Correlaciones con '{corr_target}':")
print("-" * 50)
for var, corr in correlations.head(10).items():
    emoji = "🔺" if corr > 0 else "🔻"
    print(f"  {emoji} {var:35} {corr:+.3f}")
print("...")
for var, corr in correlations.tail(10).items():
    emoji = "🔺" if corr > 0 else "🔻"
    print(f"  {emoji} {var:35} {corr:+.3f}")

# ============================================
# ANÁLISIS ESPECÍFICO: LO ESPEJO vs COMUNAS ACOMODADAS
# ============================================
print("\n" + "="*60)
print(" COMPARACIÓN: LO ESPEJO vs COMUNAS ACOMODADAS")
print("="*60)

# Comunas a comparar
comunas_vulnerables = ['LO ESPEJO', 'LA PINTANA', 'SAN RAMÓN', 'CERRO NAVIA', 'RENCA']
comunas_acomodadas = ['VITACURA', 'LAS CONDES', 'LO BARNECHEA', 'PROVIDENCIA', 'LA REINA']

vars_clave = [
    'pct_cedida_familiar', 'pct_hacinamiento', 'pct_viv_irrecuperable',
    'pct_mediagua', 'pct_profesional', 'pct_internet', 'pct_propia_pagada',
    'pct_arrendada_sin_contrato', 'pct_desocupado', 'pct_analfabeto'
]

df_vuln = stats[stats['COMUNA'].isin(comunas_vulnerables)][['COMUNA'] + vars_clave]
df_acom = stats[stats['COMUNA'].isin(comunas_acomodadas)][['COMUNA'] + vars_clave]

print("\n🔴 COMUNAS VULNERABLES:")
print(df_vuln.to_string(index=False))

print("\n🟢 COMUNAS ACOMODADAS:")
print(df_acom.to_string(index=False))

print("\n📈 PROMEDIOS COMPARADOS:")
print("-" * 50)
for var in vars_clave:
    avg_vuln = df_vuln[var].mean()
    avg_acom = df_acom[var].mean()
    diff = avg_vuln - avg_acom
    print(f"  {var:35} Vuln: {avg_vuln:6.2f}%  Acom: {avg_acom:6.2f}%  Δ: {diff:+6.2f}")

# ============================================
# PROPUESTA DE INDICADORES COMPUESTOS
# ============================================
print("\n" + "="*60)
print(" PROPUESTA: INDICADORES COMPUESTOS")
print("="*60)

# 1. ÍNDICE DE PRECARIEDAD HABITACIONAL
# Combina: hacinamiento + vivienda irrecuperable + mediagua + arrendada sin contrato + cedida familiar
stats['idx_precariedad_hab'] = (
    stats['pct_hacinamiento'] * 0.25 +
    stats['pct_viv_irrecuperable'] * 0.25 +
    stats['pct_mediagua'] * 0.20 +
    stats['pct_arrendada_sin_contrato'] * 0.15 +
    stats['pct_cedida_familiar'] * 0.15
)

# 2. ÍNDICE DE VULNERABILIDAD SOCIAL
# Combina: desempleo + analfabetismo + sin internet + jefatura femenina (proxy monoparental)
stats['idx_vulnerabilidad'] = (
    stats['pct_desocupado'].fillna(0) * 0.30 +
    stats['pct_analfabeto'] * 0.25 +
    (100 - stats['pct_internet']) * 0.25 +  # Inverso: sin internet
    stats['pct_jefa_hogar'] * 0.20
)

# 3. ÍNDICE DE PRIVILEGIO
# Combina: educación terciaria + internet + vivienda propia pagada + auto
stats['idx_privilegio'] = (
    stats['pct_profesional'] * 0.30 +
    stats['pct_internet'] * 0.20 +
    stats['pct_propia_pagada'] * 0.30 +
    stats['pct_auto'] * 0.20
)

# Mostrar ranking
print("\n🏚️ TOP 10 PRECARIEDAD HABITACIONAL:")
print(stats.nsmallest(10, 'idx_precariedad_hab')[['COMUNA', 'idx_precariedad_hab']].to_string(index=False))
print("\n... BOTTOM 10 (MÁS PRECARIOS):")
print(stats.nlargest(10, 'idx_precariedad_hab')[['COMUNA', 'idx_precariedad_hab']].to_string(index=False))

print("\n⚠️ TOP 10 VULNERABILIDAD SOCIAL:")
print(stats.nlargest(10, 'idx_vulnerabilidad')[['COMUNA', 'idx_vulnerabilidad']].to_string(index=False))

print("\n💎 TOP 10 PRIVILEGIO:")
print(stats.nlargest(10, 'idx_privilegio')[['COMUNA', 'idx_privilegio']].to_string(index=False))

# Guardar para análisis
stats.to_csv('analisis_correlaciones_rm.csv', index=False)
print("\n✅ Análisis guardado en 'analisis_correlaciones_rm.csv'")
