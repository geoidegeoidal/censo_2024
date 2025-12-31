import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from matplotlib.colors import ListedColormap
import mapclassify

# Configuración
INPUT_FILE = 'Manzanas_Indicadores.gpkg'
OUTPUT_DIR = 'mapas_finales_instagram' # Nombre final carpeta
DPI = 300
FIG_SIZE = (3.6, 3.6) # 1080x1080 px

# Estilo Neon Dark High Contrast
BACKGROUND_COLOR = '#111111' 
TEXT_COLOR = '#FFFFFF'

# Paleta Discreta (5 Clases) - Estilo "Plasma/Magma" High Contrast
NEON_COLORS = ['#3d0859', '#7f0e8f', '#cf326e', '#fa8146', '#fce82e']
NEON_CMAP = ListedColormap(NEON_COLORS)

def setup_plot():
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Bahnschrift', 'Arial Narrow', 'Arial', 'DejaVu Sans']
    plt.rcParams['axes.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['figure.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['text.color'] = TEXT_COLOR

def create_custom_legend(ax, gdf, column, scheme='FisherJenks', k=5):
    """Crea una leyenda discreta manual aesthetic"""
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
            label = f"{int(lower_bound)} - {int(upper_bound)}%"
            patch = mpatches.Patch(color=color, label=label)
            patches.append(patch)
            lower_bound = upper_bound
            
        legend = ax.legend(handles=patches, 
                  loc='lower center', 
                  bbox_to_anchor=(0.5, -0.115), 
                  ncol=k, 
                  frameon=False, 
                  fontsize=4.0, 
                  handlelength=0.8, 
                  handleheight=0.8,
                  columnspacing=1.0
                 )
        
        for text in legend.get_texts():
            text.set_color(TEXT_COLOR)
            text.set_fontweight('bold')
    except Exception as e:
        print(f"Error creating legend: {e}")

def generate_commune_map(gdf, commune_name, column, title, filename):
    print(f"  -> Generando mapa para {commune_name} ({column})...")
    
    commune_gdf = gdf[gdf['COMUNA'] == commune_name].copy()
    if commune_gdf.empty: return

    commune_gdf_toplot = commune_gdf.to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    
    # Plot Discreto
    try:
        commune_gdf_toplot.plot(
            column=column,
            ax=ax,
            cmap=NEON_CMAP,
            scheme='FisherJenks', 
            k=5,
            legend=False, 
            alpha=1.0, # Opacidad total (100%)
            edgecolor='none' 
        )
    except Exception as e:
        print(f"Fallback to continuous plot: {e}")
        commune_gdf_toplot.plot(column=column, ax=ax, cmap=NEON_CMAP, legend=False, alpha=1.0)

    # Fondo Sólido Oscuro
    ax.set_facecolor(BACKGROUND_COLOR)
    
    # Zoom
    minx, miny, maxx, maxy = commune_gdf_toplot.total_bounds
    # Margen mínimo (Zoom ajustado)
    margin_x = (maxx - minx) * 0.01 
    margin_y_top = (maxy - miny) * 0.1 
    margin_y_bottom = (maxy - miny) * 0.02 
    
    ax.set_xlim(minx - margin_x, maxx + margin_x)
    ax.set_ylim(miny - margin_y_bottom, maxy + margin_y_top)

    # TITULOS (Mayor espaciado vertical)
    # 1. Título principal (Arriba)
    plt.text(0.5, 0.94, title.upper(), transform=fig.transFigure, 
             ha="center", fontsize=16, fontweight='bold', color=TEXT_COLOR)
    
    # 2. Nombre Comuna (Separado del título)
    plt.text(0.5, 0.88, commune_name, transform=fig.transFigure,
             ha="center", fontsize=14, fontweight='light', color=TEXT_COLOR)

    # 3. Variable (ELIMINADO a pedido del usuario)
    # plt.text(0.5, 0.84, f"Variable: {column}", transform=fig.transFigure,
    #          ha="center", fontsize=6, color=TEXT_COLOR, alpha=0.7)

    # LEYENDA MANUAL
    create_custom_legend(ax, commune_gdf_toplot, column, k=5)

    # Fuente (Abajo bien al borde)
    plt.text(0.5, 0.010, "Fuente: INE - Censo 2024 • @conmapas", transform=fig.transFigure,
             ha="center", fontsize=4, color=TEXT_COLOR, alpha=0.5)

    # Logo Marca de Agua (Esquina Inferior Derecha)
    try:
        if os.path.exists('conmapas.png'):
            logo = plt.imread('conmapas.png')
            # [left, bottom, width, height] en coordenadas de figura (0-1)
            # Ajustado para esquina inferior derecha
            logo_ax = fig.add_axes([0.88, 0.02, 0.1, 0.1], zorder=10)
            logo_ax.imshow(logo)
            logo_ax.axis('off')
    except Exception as e:
        print(f"    WARN: No se pudo cargar el logo: {e}")

    ax.set_axis_off()
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    out_path = os.path.join(OUTPUT_DIR, f"{filename}_{commune_name}.png")
    
    # Guardar EXACTO
    plt.savefig(out_path, dpi=DPI, facecolor=BACKGROUND_COLOR)
    plt.close()
    print(f"    Guardado: {out_path}")

def assign_macrozone(region):
    """Asigna macrozona basada en el nombre de la región"""
    r = str(region).upper()
    if any(x in r for x in ['ARICA', 'TARAPACA', 'ANTOFAGASTA']):
        return 'Norte Grande'
    elif any(x in r for x in ['ATACAMA', 'COQUIMBO']):
        return 'Norte Chico'
    elif any(x in r for x in ['VALPARAISO', 'METROPOLITANA', "O'HIGGINS", 'MAULE']):
        return 'Zona Centro'
    elif any(x in r for x in ['ÑUBLE', 'BIOBIO', 'ARAUCANIA', 'LOS RIOS', 'LOS LAGOS']):
        return 'Zona Sur'
    elif any(x in r for x in ['AYSEN', 'MAGALLANES']):
        return 'Zona Austral'
    return 'Otra'

def main():
    setup_plot()
    print(f"Cargando datos: {INPUT_FILE}...")
    gdf = gpd.read_file(INPUT_FILE)
    
    # Mapas definidos (Nombre Columna, Titulo, Filename Short, Criterio 'Mal' Caso)
    # Nota: Para analisis zonal queremos ambos extremos (Mejor y Peor)
    indicadores = [
        ('pct_internet', 'Brecha Digital', 'internet'),       
        ('pct_hacinamiento', 'Hacinamiento Crítico', 'hacinamiento'),
        ('pct_inmigrantes', 'Población Migrante', 'inmigrantes'),
        ('pct_deficit_agua', 'Crisis Hídrica', 'agua'),
    ]

    print("Calculando estadísticas zonales...")
    if 'COMUNA' not in gdf.columns or 'REGION' not in gdf.columns:
        print("ERROR: Faltan columnas COMUNA o REGION.")
        return

    # Agrupar por Comuna y Region para mantener la geografía
    stats = gdf.groupby(['COMUNA', 'REGION'])[
        ['pct_internet', 'pct_hacinamiento', 'pct_inmigrantes', 'pct_adulto_mayor', 'pct_deficit_agua']
    ].mean().reset_index()
    
    # Asignar Macrozona
    stats['MACROZONA'] = stats['REGION'].apply(assign_macrozone)
    
    # Filtrar solo macrozonas validas
    stats = stats[stats['MACROZONA'] != 'Otra']
    
    for col, title, fname_base in indicadores:
        print(f"Analizando: {title}...")
        
        # Por cada macrozona, sacar el Mejor y Peor caso
        for zona in stats['MACROZONA'].unique():
            df_zona = stats[stats['MACROZONA'] == zona]
            if df_zona.empty: continue
            
            # Caso "Alto" (Max valor)
            max_row = df_zona.loc[df_zona[col].idxmax()]
            commune_max = max_row['COMUNA']
            val_max = max_row[col]
            
            # Caso "Bajo" (Min valor)
            min_row = df_zona.loc[df_zona[col].idxmin()]
            commune_min = min_row['COMUNA']
            val_min = min_row[col]
            
            print(f"  [{zona}]")
            print(f"    -> Max: {commune_max} ({val_max:.1f}%)")
            print(f"    -> Min: {commune_min} ({val_min:.1f}%)")
            
            # Generar mapas
            # Sufijo zona para archivo
            suffix_zona = zona.replace(' ', '')
            
            generate_commune_map(gdf, commune_max, col, title, f"{fname_base}_MAX_{suffix_zona}")
            generate_commune_map(gdf, commune_min, col, title, f"{fname_base}_MIN_{suffix_zona}")

    print("¡Generación masiva finalizada!")

if __name__ == "__main__":
    main()
