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
    print("Cargando datos para insights de HACINAMIENTO...")
    try:
        gdf = gpd.read_file(INPUT_FILE)
    except Exception as e:
        print(f"Error cargando gpkg: {e}")
        return

    # Check columns
    required = ['n_viv_hacinadas', 'n_vp', 'COMUNA']
    
    if not all(c in gdf.columns for c in required):
        print(f"Faltan columnas necesarias. Tenemos: {gdf.columns.tolist()}")
        return

    # Ponderado correcto: Suma de viviendas hacinadas / Suma de viviendas totales
    stats = gdf.groupby('COMUNA')[['n_viv_hacinadas', 'n_vp']].sum().reset_index()
    
    # Evitar div por cero si n_vp es 0 (no deberia en comunas agregadas pero por seguridad)
    stats = stats[stats['n_vp'] > 0]
    
    stats['pct_hacinamiento'] = (stats['n_viv_hacinadas'] / stats['n_vp']) * 100
        
    stats['AREA_METRO'] = stats['COMUNA'].apply(assign_metro_area)
    stats_metro = stats.dropna(subset=['AREA_METRO'])

    print("\n" + "="*40)
    print(" 🏠 INSIGHTS: HACINAMIENTO CRÍTICO 🏠")
    print("="*40 + "\n")

    for area in ['Gran Santiago', 'Gran Valparaíso', 'Gran Concepción']:
        df = stats_metro[stats_metro['AREA_METRO'] == area]
        if df.empty: continue
        
        # Rankings (Mayor porcentaje es peor)
        # Menor hacinamiento (Mejor)
        best_1 = df.loc[df['pct_hacinamiento'].idxmin()] 
        # Mayor hacinamiento (Peor)
        worst_1 = df.loc[df['pct_hacinamiento'].idxmax()] 
        
        print(f"📍 {area.upper()}")
        print(f"   ✅ Menor Hacinamiento: {best_1.COMUNA} ({best_1.pct_hacinamiento:.1f}%)")
        print(f"   ❌ Mayor Hacinamiento: {worst_1.COMUNA} ({worst_1.pct_hacinamiento:.1f}%)")
        print(f"   ⚠️ Diferencia:         {(worst_1.pct_hacinamiento - best_1.pct_hacinamiento):.1f} pts")
        print("-" * 30)

if __name__ == "__main__":
    main()
