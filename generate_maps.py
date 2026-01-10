import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from matplotlib.colors import ListedColormap
import mapclassify
import contextily as cx # Librería necesaria para el mapa base

# --- CONFIGURACIÓN ---
INPUT_FILE = 'Manzanas_Indicadores.gpkg'
OUTPUT_DIR = 'mapas_finales_instagram'
DPI = 300
FIG_SIZE = (3.6, 3.6) # Formato cuadrado para IG (1080x1080 px aprox)

# Estilo Neon Dark High Contrast
BACKGROUND_COLOR = '#111111' 
TEXT_COLOR = '#FFFFFF'

# Paleta Discreta (5 Clases) - Estilo "Plasma/Magma" High Contrast
NEON_COLORS = ['#3d0859', '#7f0e8f', '#cf326e', '#fa8146', '#fce82e']
NEON_CMAP = ListedColormap(NEON_COLORS)

def setup_plot():
    """Configura el estilo global de matplotlib"""
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'sans-serif'
    # Intenta usar fuentes modernas si están disponibles
    plt.rcParams['font.sans-serif'] = ['Bahnschrift', 'Arial Narrow', 'Arial', 'DejaVu Sans']
    plt.rcParams['axes.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['figure.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['text.color'] = TEXT_COLOR

def create_custom_legend(ax, gdf, column, scheme='FisherJenks', k=5):
    """Crea una leyenda discreta manual y estética"""
    try:
        valid_data = gdf[column].dropna()
        if valid_data.empty: return

        unique_vals = valid_data.nunique()
        if unique_vals < k: k = unique_vals
            
        classifier = mapclassify.FisherJenks(valid_data, k=k)
        bins = classifier.bins
        
        patches = []
        lower_bound = valid_data.min()
        
        current_colors = NEON_COLORS
        if k < 5:
             indices = [int(i * (len(NEON_COLORS)-1) / (k-1)) for i in range(k)]
             current_colors = [NEON_COLORS[i] for i in indices]

        for i, upper_bound in enumerate(bins):
            if str(upper_bound) == 'nan': continue
            color = current_colors[i] if i < len(current_colors) else NEON_COLORS[-1]
            # Formato de etiqueta
            label = f"{int(lower_bound)} - {int(upper_bound)}%"
            patch = mpatches.Patch(color=color, label=label)
            patches.append(patch)
            lower_bound = upper_bound

        # Añadir leyenda
        legend = ax.figure.legend(
            handles=patches, 
            loc='lower center', 
            bbox_to_anchor=(0.5, 0.05), # Posición fija
            ncol=k, 
            frameon=False, 
            fontsize=4.0, 
            handlelength=0.8, 
            handleheight=0.8,
            bbox_transform=ax.figure.transFigure,
            borderaxespad=0
        )
        
        for text in legend.get_texts():
            text.set_color(TEXT_COLOR)
            text.set_fontweight('bold')
    except Exception as e:
        print(f"Error creating legend: {e}")

def generate_commune_map(gdf, commune_name, column, title, filename, description=""):
    """Genera y guarda el mapa estático con estilo Neon y Basemap"""
    print(f"  -> Generando mapa para {commune_name} ({column})...")
    
    commune_gdf = gdf[gdf['COMUNA'] == commune_name].copy()
    if commune_gdf.empty: return

    # CRUCIAL: Convertir a Web Mercator (EPSG:3857) para Contextily
    commune_gdf_toplot = commune_gdf.to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    
    # 1. PLOT DE DATOS (Capa Superior - Zorder 2)
    try:
        commune_gdf_toplot.plot(
            column=column,
            ax=ax,
            cmap=NEON_CMAP,
            scheme='FisherJenks', 
            k=5,
            legend=False, 
            alpha=0.6,          # Transparencia para ver el mapa base debajo
            edgecolor='#ffffff',# Borde blanco fino para efecto neon
            linewidth=0.1,      # Grosor del borde
            zorder=2            # IMPORTANTE: Dibuja esto ENCIMA del mapa base
        )
    except Exception as e:
        print(f"Fallback to continuous plot: {e}")
        commune_gdf_toplot.plot(column=column, ax=ax, cmap=NEON_CMAP, legend=False, alpha=0.6, zorder=2)

    # 2. AÑADIR MAPA BASE (Capa Inferior - Zorder 1)
    try:
        # Usamos DarkMatterNoLabels para que sea limpio (sin nombres de calles que molesten)
        cx.add_basemap(
            ax, 
            crs=commune_gdf_toplot.crs.to_string(), 
            source=cx.providers.CartoDB.DarkMatterNoLabels, 
            attribution=False,
            zorder=1 # IMPORTANTE: Dibuja esto DEBAJO de los datos
        )
    except Exception as e:
        print(f"    WARN: No se pudo añadir basemap (Check internet connection): {e}")

    # Fondo de seguridad (por si falla el basemap)
    ax.set_facecolor(BACKGROUND_COLOR)
    
    # 3. AJUSTE DE ZOOM
    minx, miny, maxx, maxy = commune_gdf_toplot.total_bounds
    margin_x = (maxx - minx) * 0.1 # 10% de margen
    margin_y_top = (maxy - miny) * 0.2
    margin_y_bottom = (maxy - miny) * 0.2 
    
    ax.set_xlim(minx - margin_x, maxx + margin_x)
    ax.set_ylim(miny - margin_y_bottom, maxy + margin_y_top)

    # 4. TITULOS Y TEXTOS
    # Título principal
    plt.text(0.5, 0.94, title.upper(), transform=fig.transFigure, 
             ha="center", fontsize=16, fontweight='bold', color=TEXT_COLOR)
    
    # Subtítulo (Nombre Comuna)
    plt.text(0.5, 0.88, commune_name, transform=fig.transFigure,
             ha="center", fontsize=14, fontweight='light', color=TEXT_COLOR)

    # Descripción
    if description:
        plt.text(0.5, 0.088, description, transform=fig.transFigure,
                 ha="center", fontsize=5, fontweight='normal', color=TEXT_COLOR, alpha=0.9)

    # Leyenda
    create_custom_legend(ax, commune_gdf_toplot, column, k=5)

    # Fuente
    plt.text(0.5, 0.010, "Fuente: INE - Censo 2024 • @conmapas", transform=fig.transFigure,
             ha="center", fontsize=4, color=TEXT_COLOR, alpha=0.5)

    # Logo (Opcional)
    try:
        if os.path.exists('conmapas.png'):
            logo = plt.imread('conmapas.png')
            # [left, bottom, width, height]
            logo_ax = fig.add_axes([0.88, 0.02, 0.1, 0.1], zorder=10)
            logo_ax.imshow(logo)
            logo_ax.axis('off')
    except Exception as e:
        pass

    ax.set_axis_off()
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    out_path = os.path.join(OUTPUT_DIR, f"{filename}_{commune_name}.png")
    
    # Guardar
    plt.savefig(out_path, dpi=DPI, facecolor=BACKGROUND_COLOR, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f"    Guardado: {out_path}")

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
    setup_plot()
    print(f"Cargando datos: {INPUT_FILE}...")
    
    # Verificación simple de archivo
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: No se encuentra el archivo '{INPUT_FILE}'. Verifica la ruta.")
        return

    gdf = gpd.read_file(INPUT_FILE)
    
    # Definición de indicadores
    indicadores_config = [
        ('pct_internet', 'Brecha Digital', 'internet', '% Hogares con conexión fija', 'n_internet', 'n_hog'),       
        ('pct_hacinamiento', 'Hacinamiento Crítico', 'hacinamiento', '% Viviendas con >2.5 personas/dorm.', 'n_viv_hacinadas', 'n_vp'),
        ('pct_inmigrantes', 'Población Migrante', 'inmigrantes', '% Población nacida en el extranjero', 'n_inmigrantes', 'n_per'),
        ('pct_deficit_agua', 'Crisis Hídrica', 'agua', '% Viviendas sin agua potable de red', 'pct_deficit_agua', None), 
    ]
    
    # Check para agua
    cols_agua = ['n_fuente_agua_camion', 'n_fuente_agua_rio', 'n_fuente_agua_pozo']
    has_agua_cols = all(c in gdf.columns for c in cols_agua)

    print("Calculando estadísticas metropolitanas...")
    if 'COMUNA' not in gdf.columns:
        print("ERROR: Falta columna COMUNA en el archivo.")
        return

    # 1. Agrupar sumarizando
    agg_cols = ['n_internet', 'n_hog', 'n_viv_hacinadas', 'n_vp', 'n_inmigrantes', 'n_per']
    if has_agua_cols: agg_cols += cols_agua
    agg_cols = [c for c in agg_cols if c in gdf.columns]
    
    stats_raw = gdf.groupby(['COMUNA'])[agg_cols].sum().reset_index()
    
    # 2. Asignar Área Metro
    stats_raw['AREA_METRO'] = stats_raw['COMUNA'].apply(assign_metro_area)
    stats = stats_raw.dropna(subset=['AREA_METRO']).copy()
    
    if stats.empty:
        print("CRITICAL: Ninguna comuna matcheó con las listas de Áreas Metro.")
        return

    # 3. Calcular porcentajes
    if 'n_internet' in stats and 'n_hog' in stats:
        stats['pct_internet'] = (stats['n_internet'] / stats['n_hog']) * 100
        
    if 'n_viv_hacinadas' in stats and 'n_vp' in stats:
        stats['pct_hacinamiento'] = (stats['n_viv_hacinadas'] / stats['n_vp']) * 100
        
    if 'n_inmigrantes' in stats and 'n_per' in stats:
        stats['pct_inmigrantes'] = (stats['n_inmigrantes'] / stats['n_per']) * 100
        
    if has_agua_cols and 'n_vp' in stats:
        stats['pct_deficit_agua'] = ((stats['n_fuente_agua_camion'] + stats['n_fuente_agua_rio'] + stats['n_fuente_agua_pozo']) / stats['n_vp']) * 100
    else:
         # Fallback simple
         print("WARN: Fallback promedio simple para agua")
         aux = gdf.groupby('COMUNA')['pct_deficit_agua'].mean().reset_index()
         stats = stats.merge(aux, on='COMUNA', suffixes=('', '_simple'))
         stats['pct_deficit_agua'] = stats['pct_deficit_agua'].fillna(stats['pct_deficit_agua_simple'])

    print(f"Comunas analizadas: {len(stats)}")

    # 4. Loop Generación
    for col, title, fname_base, desc, _, _ in indicadores_config:
        if col not in stats.columns: 
            print(f"Saltando {col} (no existe en datos)")
            continue
        
        print(f"Analizando indicador: {title}...")

        for area in stats['AREA_METRO'].unique():
            df_area = stats[stats['AREA_METRO'] == area]
            if df_area.empty: continue
            
            # Caso "Alto" (Máximo valor)
            max_row = df_area.loc[df_area[col].idxmax()]
            fname_max = f"{fname_base}_MAX_{area.replace(' ','')}"
            generate_commune_map(gdf, max_row['COMUNA'], col, title, fname_max, desc)
            
            # Caso "Bajo" (Mínimo valor)
            min_row = df_area.loc[df_area[col].idxmin()]
            fname_min = f"{fname_base}_MIN_{area.replace(' ','')}"
            generate_commune_map(gdf, min_row['COMUNA'], col, title, fname_min, desc)

    print("¡Generación finalizada con éxito!")

if __name__ == "__main__":
    main()