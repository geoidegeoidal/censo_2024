import geopandas as gpd
import pandas as pd
import numpy as np

# Load Data
INPUT_FILE = 'Manzanas_Indicadores.gpkg'
print(f"Loading {INPUT_FILE}...")
gdf = gpd.read_file(INPUT_FILE)

# Filter Ñuñoa
nunoa = gdf[gdf['COMUNA'] == 'ÑUÑOA'].copy()
print(f"Ñuñoa blocks: {len(nunoa)}")

# Calculate Target Variable
nunoa['pct_ex'] = (nunoa['n_estcivcon_anul_sep_div'] / nunoa['n_per']) * 100

# Calculate Explanatory Variables
# 1. Housing Type (Departamentos)
nunoa['pct_depto'] = (nunoa['n_tipo_viv_depto'] / nunoa['n_hog']) * 100

# 2. Education (Proxy for professionals/status)
# prom_escolaridad18 is already numeric
# Or Calculate % with Higher Ed
nunoa['pct_superior'] = (nunoa['n_asistencia_superior'] / nunoa['n_per']) * 100 # This might be currently attending?
# Use 'n_cine_terciaria_maestria_doctorado' if applicable, but description says 'n_cine_...'
# Let's check n_cine cols. 'n_cine_terciaria_maestria_doctorado'.
nunoa['pct_profesional'] = (nunoa['n_cine_terciaria_maestria_doctorado'] / nunoa['n_per']) * 100

# 3. Household Head (Female Headship)
nunoa['pct_jefa_hogar'] = (nunoa['n_jefatura_mujer'] / nunoa['n_hog']) * 100

# 4. Household Size (Unipersonal)
nunoa['pct_unipersonal'] = (nunoa['n_hog_unipersonales'] / nunoa['n_hog']) * 100

# 5. Age Groups
nunoa['pct_25_44'] = (nunoa['n_edad_25_44'] / nunoa['n_per']) * 100
nunoa['pct_45_59'] = (nunoa['n_edad_45_59'] / nunoa['n_per']) * 100
nunoa['pct_60_mas'] = (nunoa['n_edad_60_mas'] / nunoa['n_per']) * 100

# 6. Tenure (Renters vs Owners)
nunoa['pct_arriendo'] = ((nunoa['n_tenencia_arrendada_contrato'] + nunoa['n_tenencia_arrendada_sin_contrato']) / nunoa['n_hog']) * 100
nunoa['pct_propietario'] = ((nunoa['n_tenencia_propia_pagada'] + nunoa['n_tenencia_propia_pagandose']) / nunoa['n_hog']) * 100

# 7. Children (Absence of children?)
nunoa['pct_ninos'] = (nunoa['n_edad_0_5'] + nunoa['n_edad_6_13']) / nunoa['n_per'] * 100

# Correlation Analysis
cols_to_corr = [
    'pct_ex', 
    'pct_depto', 
    'pct_profesional', 
    'prom_escolaridad18',
    'pct_jefa_hogar', 
    'pct_unipersonal',
    'pct_25_44', 
    'pct_45_59',
    'pct_60_mas',
    'pct_arriendo',
    'pct_propietario',
    'pct_ninos',
    'prom_per_hog',
    'n_per' # Density proxy if area is roughly const or checking size
]

# Drop NaNs created by division by zero
valid_nunoa = nunoa[cols_to_corr].dropna()

corr_matrix = valid_nunoa.corr()
print("\n--- Correlations with pct_ex ---")
print(corr_matrix['pct_ex'].sort_values(ascending=False))

# Spatial Analysis: Where are the top 10% blocks?
top_10_thresh = nunoa['pct_ex'].quantile(0.90)
top_blocks = nunoa[nunoa['pct_ex'] >= top_10_thresh]
print(f"\n--- Top 10% Blocks Analysis (Threshold: {top_10_thresh:.2f}%) ---")
print(f"Number of blocks: {len(top_blocks)}")
print("Average attributes in Top 10% blocks vs Rest:")
compare = pd.DataFrame({
    'Top 10%': top_blocks[cols_to_corr].mean(),
    'Rest': nunoa[nunoa['pct_ex'] < top_10_thresh][cols_to_corr].mean()
})
print(compare)

# Determine location of top blocks relative to commune center or specific landmarks?
# Calculating centroid of top blocks
centroids = top_blocks.geometry.centroid
avg_x = centroids.x.mean()
avg_y = centroids.y.mean()
print(f"\nCentroid of Top Blocks: {avg_x}, {avg_y}")
# Rough check if it's north/south/east/west relative to all ñuñoa
center_all = nunoa.geometry.centroid
all_x = center_all.x.mean()
all_y = center_all.y.mean()

print(f"Ñuñoa Center: {all_x}, {all_y}")
if avg_y > all_y: print("Trend: NORTH")
else: print("Trend: SOUTH")
if avg_x > all_x: print("Trend: EAST")
else: print("Trend: WEST")
