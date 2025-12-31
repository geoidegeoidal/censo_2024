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
    print("Cargando datos para insights...")
    try:
        gdf = gpd.read_file(INPUT_FILE)
    except Exception as e:
        print(f"Error cargando gpkg: {e}")
        return

    # Check columns
    required = ['n_internet', 'n_hog', 'COMUNA']
    if not all(c in gdf.columns for c in required):
        print("Faltan columnas n_internet o n_hog para calcular brecha.")
        return

    # Agrupar por comuna
    stats = gdf.groupby('COMUNA')[['n_internet', 'n_hog']].sum().reset_index()
    
    # Calcular %
    stats['pct_internet'] = (stats['n_internet'] / stats['n_hog']) * 100
    
    # Asignar Area Metro
    stats['AREA_METRO'] = stats['COMUNA'].apply(assign_metro_area)
    stats_metro = stats.dropna(subset=['AREA_METRO'])

    print("\n" + "="*40)
    print(" 🚨 INSIGHTS: BRECHA DIGITAL (INTERNET) 🚨")
    print("="*40 + "\n")

    for area in ['Gran Santiago', 'Gran Valparaíso', 'Gran Concepción']:
        df = stats_metro[stats_metro['AREA_METRO'] == area]
        if df.empty: continue
        
        # Rankings
        top_1 = df.loc[df['pct_internet'].idxmax()]
        bottom_1 = df.loc[df['pct_internet'].idxmin()]
        brecha = top_1.pct_internet - bottom_1.pct_internet
        
        print(f"📍 {area.upper()}")
        print(f"   ✅ Mejor Conectividad: {top_1.COMUNA} ({top_1.pct_internet:.1f}%)")
        print(f"   ❌ Peor Conectividad:  {bottom_1.COMUNA} ({bottom_1.pct_internet:.1f}%)")
        print(f"   ⚠️ Brecha Digital:     {brecha:.1f} puntos de diferencia")
        print("-" * 30)

if __name__ == "__main__":
    main()
