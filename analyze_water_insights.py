import geopandas as gpd
import pandas as pd
import sys

# Configuración
INPUT_FILE = 'Manzanas_Indicadores.gpkg'

def assign_metro_area(commune):
    """Asigna área metropolitana basada en la comuna"""
    c = str(commune).upper().strip()
    
    # Gran Valparaíso
    if c in ['VALPARAISO', 'VIÑA DEL MAR', 'CONCÓN', 'QUILPUÉ', 'VILLA ALEMANA']:
        return 'Gran Valparaíso'
        
    # Gran Concepción
    if c in ['CONCEPCIÓN', 'TALCAHUANO', 'CHIGUAYANTE', 'SAN PEDRO DE LA PAZ', 'HUALPÉN', 'PENCO', 'TOMÉ', 'CORONEL', 'LOTA', 'HUALQUI']:
        return 'Gran Concepción'
        
    # Gran Santiago
    santiago_communes = [
        'SANTIAGO', 'CERRILLOS', 'CERRO NAVIA', 'CONCHALÍ', 'EL BOSQUE', 'ESTACIÓN CENTRAL', 'HUECHURABA', 'INDEPENDENCIA', 
        'LA CISTERNA', 'LA FLORIDA', 'LA GRANJA', 'LA PINTANA', 'LA REINA', 'LAS CONDES', 'LO BARNECHEA', 'LO ESPEJO', 
        'LO PRADO', 'MACUL', 'MAIPÚ', 'ÑUÑOA', 'PEDRO AGUIRRE CERDA', 'PEÑALOLÉN', 'PROVIDENCIA', 'PUDAHUEL', 'QUILICURA', 
        'QUINTA NORMAL', 'RECOLETA', 'RENCA', 'SAN JOAQUÍN', 'SAN MIGUEL', 'SAN RAMÓN', 'VITACURA', 'PUENTE ALTO', 'SAN BERNARDO'
    ]
    if c in santiago_communes:
        return 'Gran Santiago'

    return None

def main():
    print("Cargando datos para insights de AGUA...")
    try:
        gdf = gpd.read_file(INPUT_FILE)
    except Exception as e:
        print(f"Error cargando gpkg: {e}")
        return

    # Check columns
    # Sumamos las fuentes precarias: camión, río, pozo
    cols_precario = ['n_fuente_agua_camion', 'n_fuente_agua_rio', 'n_fuente_agua_pozo']
    required = cols_precario + ['n_vp', 'COMUNA']
    
    if not all(c in gdf.columns for c in required):
        print(f"Faltan columnas necesarias. Tenemos: {gdf.columns.tolist()}")
        # Fallback to pct_deficit_agua mean if raw cols missing (though they should be there)
        if 'pct_deficit_agua' in gdf.columns:
             print("Usando pct_deficit_agua pre-calculado (promedio simple, menos preciso)...")
             stats = gdf.groupby('COMUNA')['pct_deficit_agua'].mean().reset_index()
             stats['AREA_METRO'] = stats['COMUNA'].apply(assign_metro_area)
             stats_metro = stats.dropna(subset=['AREA_METRO'])
        else:
             return
    else:
        # Ponderado correcto
        stats = gdf.groupby('COMUNA')[cols_precario + ['n_vp']].sum().reset_index()
        stats['n_sin_agua'] = stats[cols_precario].sum(axis=1)
        stats['pct_deficit_agua'] = (stats['n_sin_agua'] / stats['n_vp']) * 100
        
        stats['AREA_METRO'] = stats['COMUNA'].apply(assign_metro_area)
        stats_metro = stats.dropna(subset=['AREA_METRO'])

    print("\n" + "="*40)
    print(" 💧 INSIGHTS: CRISIS HÍDRICA (DÉFICIT) 💧")
    print("="*40 + "\n")

    for area in ['Gran Santiago', 'Gran Valparaíso', 'Gran Concepción']:
        df = stats_metro[stats_metro['AREA_METRO'] == area]
        if df.empty: continue
        
        # Rankings (Ojo: Aquí "Mejor" es MENOR déficit, "Peor" es MAYOR déficit)
        best_1 = df.loc[df['pct_deficit_agua'].idxmin()] # Menos déficit
        worst_1 = df.loc[df['pct_deficit_agua'].idxmax()] # Más déficit
        
        print(f"📍 {area.upper()}")
        print(f"   ✅ Mejor Acceso (0% Déficit es ideal): {best_1.COMUNA} ({best_1.pct_deficit_agua:.2f}%)")
        print(f"   ❌ Mayor Déficit:                      {worst_1.COMUNA} ({worst_1.pct_deficit_agua:.2f}%)")
        print("-" * 30)

if __name__ == "__main__":
    main()
