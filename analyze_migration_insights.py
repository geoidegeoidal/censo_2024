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
    print("Cargando datos para insights de INMIGRACIÓN...")
    try:
        gdf = gpd.read_file(INPUT_FILE)
    except Exception as e:
        print(f"Error cargando gpkg: {e}")
        return

    # Check columns
    required = ['n_inmigrantes', 'n_per', 'COMUNA']
    
    if not all(c in gdf.columns for c in required):
        print(f"Faltan columnas necesarias. Tenemos: {gdf.columns.tolist()}")
        return

    # Ponderado correcto: Suma de inmigrantes / Suma de personas totales
    stats = gdf.groupby('COMUNA')[['n_inmigrantes', 'n_per']].sum().reset_index()
    
    # Evitar div por cero 
    stats = stats[stats['n_per'] > 0]
    
    stats['pct_inmigrantes'] = (stats['n_inmigrantes'] / stats['n_per']) * 100
        
    stats['AREA_METRO'] = stats['COMUNA'].apply(assign_metro_area)
    stats_metro = stats.dropna(subset=['AREA_METRO'])

    print("\n" + "="*40)
    print(" 🌎 INSIGHTS: POBLACIÓN MIGRANTE 🌎")
    print("="*40 + "\n")

    for area in ['Gran Santiago', 'Gran Valparaíso', 'Gran Concepción']:
        df = stats_metro[stats_metro['AREA_METRO'] == area]
        if df.empty: continue
        
        # Rankings 
        # Mayor % Inmigrantes
        highest = df.loc[df['pct_inmigrantes'].idxmax()] 
        # Menor % Inmigrantes
        lowest = df.loc[df['pct_inmigrantes'].idxmin()] 
        
        print(f"📍 {area.upper()}")
        print(f"   ⬆️ Mayor concentración: {highest.COMUNA} ({highest.pct_inmigrantes:.1f}%)")
        print(f"   ⬇️ Menor concentración: {lowest.COMUNA} ({lowest.pct_inmigrantes:.1f}%)")
        print(f"   🔄 Diferencia:          {(highest.pct_inmigrantes - lowest.pct_inmigrantes):.1f} pts")
        print("-" * 30)

if __name__ == "__main__":
    main()
