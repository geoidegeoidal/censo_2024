import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
from matplotlib.colors import ListedColormap
import mapclassify
import seaborn as sns # Para graficos estadisticos bonitos
import matplotlib.patheffects as path_effects # Para efectos de brillo (Glow)

# --- CONFIGURACIÓN ---
INPUT_FILE = 'Manzanas_Indicadores.gpkg'
OUTPUT_DIR = 'mapas_finales_instagram'
DPI = 300
FIG_SIZE = (3.6, 3.6) # Formato cuadrado para IG (1080x1080 px aprox)

# Estilo Cyberpunk Dark High Contrast
BACKGROUND_COLOR = '#050510' # Azul muy oscuro casi negro
TEXT_COLOR = '#E0E0E0'

# Paleta Cyberpunk Puro (Para Infografías)
CYBER_CYAN = '#00f3ff'
CYBER_MAGENTA = '#ff00ff'
CYBER_YELLOW = '#fce82e'
CYBER_GREEN = '#00ff41'
CYBER_PURPLE = '#bc13fe'

# Paleta Viridis (Standard Matplotlib)
import matplotlib.cm as cm
NEON_CMAP = cm.viridis

def setup_plot():
    """Configura el estilo global de matplotlib"""
    plt.style.use('dark_background')
    plt.rcParams['font.family'] = 'sans-serif'
    # Intenta usar fuentes modernas si están disponibles
    plt.rcParams['font.sans-serif'] = ['Bahnschrift', 'Arial Narrow', 'Arial', 'DejaVu Sans']
    plt.rcParams['axes.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['figure.facecolor'] = BACKGROUND_COLOR
    plt.rcParams['text.color'] = TEXT_COLOR

def create_custom_legend(ax, gdf, column, scheme='FisherJenks', k=5, bins=None, context=None):
    """Crea una leyenda discreta manual y estética"""
    try:
        if bins is None:
            if gdf is None or column is None: return
            valid_data = gdf[column].dropna()
            if valid_data.empty: return

            unique_vals = valid_data.nunique()
            if unique_vals < k: k = unique_vals
                
            classifier = mapclassify.FisherJenks(valid_data, k=k)
            bins = classifier.bins
        else:
            k = len(bins)

        patches = []
        # Para leyenda global, 'lower_bound' es implícito del bin anterior.
        # Asumiremos min=0 para el primer bin en porcentajes si no tenemos data,
        # o usamos logicamente el bin anterior + 1.
        # En FisherJenks bins son el limite SUPERIOR.
        
        # Caso manual (bins pasados) - Aproximacion
        lower_bound = 0 
        
        # Muestrear colores del Colormap (Matplotlib Viridis u otro)
        current_colors = [NEON_CMAP(i / (k - 1)) for i in range(k)]

        for i, upper_bound in enumerate(bins):
            if str(upper_bound) == 'nan': continue
            color = current_colors[i] 
            # Formato de etiqueta limpio (solo numeros)
            label = f"{int(lower_bound)} - {int(upper_bound)}"
            patch = mpatches.Patch(color=color, label=label)
            patches.append(patch)
            lower_bound = upper_bound

        # Añadir leyenda (Bajada para dar espacio al texto de contexto arriba)
        legend = ax.figure.legend(
            handles=patches, 
            loc='lower center', 
            bbox_to_anchor=(0.5, 0.04),
            ncol=k, 
            frameon=False, 
            fontsize=5.0, 
            handlelength=0.8, 
            handleheight=0.8,
            bbox_transform=ax.figure.transFigure,
            borderaxespad=0
        )
        
        for text in legend.get_texts():
            text.set_color(TEXT_COLOR)
            text.set_fontweight('bold')

        # Etiquetas de contexto ENCIMA de la leyenda (línea separada)
        if context:
            ctx_lower = context.lower()
            suffix = "Intensidad"
            if "privilegio" in ctx_lower: suffix = "Privilegio"
            elif "precariedad" in ctx_lower: suffix = "Precariedad"
            elif "vulnerabilidad" in ctx_lower: suffix = "Vulnerabilidad"
            
            # Línea superior con gradiente visual (texto en extremos)
            ax.figure.text(0.25, 0.085, f"< Menor {suffix}", ha='center', va='center', 
                          fontsize=6, fontweight='bold', color=TEXT_COLOR, alpha=0.9)
            
            ax.figure.text(0.75, 0.085, f"Mayor {suffix} >", ha='center', va='center', 
                          fontsize=6, fontweight='bold', color=TEXT_COLOR, alpha=0.9)
            
            # Línea visual conectora (opcional, comentada si no gusta)
            # ax.figure.text(0.5, 0.075, "─────────────────────", ha='center', va='center', 
            #               fontsize=6, color=TEXT_COLOR, alpha=0.3)
    except Exception as e:
        print(f"Error creating legend: {e}")

def generate_commune_map(gdf, commune_name, column, title, filename, description="", bins=None):
    """Genera y guarda el mapa estático con estilo Neon y Basemap"""
    print(f"  -> Generando mapa para {commune_name} ({column})...")
    
    commune_gdf = gdf[gdf['COMUNA'] == commune_name].copy()
    if commune_gdf.empty: return

    # CRUCIAL: Convertir a Web Mercator (EPSG:3857) para Contextily
    commune_gdf_toplot = commune_gdf.to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    
    # 1. ESTABLECER LÍMITES PRIMERO
    minx, miny, maxx, maxy = commune_gdf_toplot.total_bounds
    margin_x = (maxx - minx) * 0.1 
    margin_y = (maxy - miny) * 0.1
    ax.set_xlim(minx - margin_x, maxx + margin_x)
    ax.set_ylim(miny - margin_y, maxy + margin_y)
    
    # 2. FONDO DARK
    ax.set_facecolor(BACKGROUND_COLOR)
    
    # 3. PLOT DE DATOS (encima del basemap)
    try:
        plot_args = {
            'column': column,
            'ax': ax,
            'cmap': NEON_CMAP,
            'legend': False,
            'alpha': 0.7,
            'edgecolor': 'none',
            'linewidth': 0.0,
        }
        
        if bins is not None:
             plot_args['scheme'] = 'UserDefined'
             plot_args['classification_kwds'] = {'bins': bins}
        else:
             plot_args['scheme'] = 'FisherJenks'
             plot_args['k'] = 5
             
        commune_gdf_toplot.plot(**plot_args)

    except Exception as e:
        print(f"Fallback to continuous plot: {e}")
        commune_gdf_toplot.plot(column=column, ax=ax, cmap=NEON_CMAP, legend=False, alpha=0.7)

    ax.set_aspect('equal')

    # 4. TITULOS Y TEXTOS (Ajustados manualmente para centrado visual)
    # Título principal
    plt.text(0.5, 0.93, title.upper(), transform=fig.transFigure, 
             ha="center", fontsize=15, fontweight='bold', color=TEXT_COLOR)
    
    # Subtítulo (Nombre Comuna)
    plt.text(0.5, 0.89, commune_name, transform=fig.transFigure,
             ha="center", fontsize=13, fontweight='light', color=TEXT_COLOR)

    # Descripción (MOVIDA ARRIBA para limpiar el footer)
    if description:
        plt.text(0.5, 0.85, description, transform=fig.transFigure,
                 ha="center", fontsize=6, fontweight='normal', color=TEXT_COLOR, alpha=0.7)

    # Leyenda (Footer despejado)
    if bins is not None:
         # Hack: pasamos el gdf entero o un dummy con los rangos correctos?
         create_custom_legend(ax, None, None, bins=bins, context=title)
    else:
         create_custom_legend(ax, commune_gdf_toplot, column, context=title)

    # Fuente (Bien abajo)
    plt.text(0.5, 0.01, "Fuente: INE - Censo 2024 • @conmapas", transform=fig.transFigure,
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
    
    # Guardar SIN bbox_inches='tight' para respetar tamaño fijo y layout
    plt.savefig(out_path, dpi=DPI, facecolor=BACKGROUND_COLOR) 
    plt.close()
    print(f"    Guardado: {out_path}")

def generate_infographic(df, column, title, filename_base, description, area_name):
    """Genera una infografía estilo 'Dataviz Pro' de 1080x1080"""
    print(f"  -> Generando dashboard Pro para {title}...")
    
    # Filtrar datos validos
    try:
        valid_df = df.dropna(subset=[column]).sort_values(by=column, ascending=False)
        if valid_df.empty: return
    except KeyError:
        return

    # --- CONFIG STYLE ---
    # Colores más sofisticados
    BG_COLOR = '#0f111a' # Dark Navy/Black aesthetic
    ACCENT_COLOR = CYBER_MAGENTA # Mantenemos la identidad pero usada con elegancia
    SEC_COLOR = CYBER_CYAN
    TEXT_MAIN = '#ffffff'
    TEXT_SUB = '#8b9bb4' # Blue-gray for subtitles

    plt.rcParams['font.family'] = 'sans-serif' 
    plt.rcParams['font.weight'] = 'normal'

    fig = plt.figure(figsize=FIG_SIZE)
    fig.patch.set_facecolor(BG_COLOR)
    
    # GRID LAYOUT MEJORADO
    # Row 0: Header (15%)
    # Row 1: Content (Top 7 + Stats) (50%)
    # Row 2: Distribution (35%)
    gs = fig.add_gridspec(3, 1, height_ratios=[0.15, 0.50, 0.35], hspace=0.3)
    
    # --- 1. HEADER ---
    ax_header = fig.add_subplot(gs[0, 0])
    ax_header.axis('off')
    
    # Titulo Limpio y Grande
    ax_header.text(0.5, 0.55, title.upper(), ha='center', va='center', 
                   color=TEXT_MAIN, fontsize=20, fontweight='bold')
    
    # Subtitulo Elegante
    ax_header.text(0.5, 0.25, description, ha='center', va='center', 
                   color=SEC_COLOR, fontsize=9, fontweight='medium', alpha=0.9)
    
    # Linea separadora sutil
    ax_header.plot([0.3, 0.7], [0.1, 0.1], color=TEXT_SUB, linewidth=0.5, alpha=0.5)



    # --- 2. MAIN SECTION ---
    gs_mid = gs[1].subgridspec(1, 2, width_ratios=[1.3, 0.7], wspace=0.15)
    
    # A. TOP 7 RANKING (Horizontal Bar Chart)
    ax_bars = fig.add_subplot(gs_mid[0])
    top_7 = valid_df.head(7).iloc[::-1] # Top 7 invertido
    
    # Barras Sólidas con Gradiente simulado (Color plano + alpha)
    bars = ax_bars.barh(top_7['COMUNA'], top_7[column], color=ACCENT_COLOR, alpha=1.0, height=0.5)
    
    # Etiquetas de Valor (Clean, sin glow borroso)
    for bar in bars:
        width = bar.get_width()
        ax_bars.text(width + (valid_df[column].max()*0.02), bar.get_y() + bar.get_height()/2 - 0.02, 
                     f'{width:.1f}%', 
                     ha='left', va='center', color=TEXT_MAIN, fontsize=10, fontweight='bold', fontfamily='monospace')

    # Etiquetas de Categoría (Comunas)
    # Las ponemos en el eje Y, asegurando color y tamaño
    ax_bars.set_yticks(range(len(top_7)))
    ax_bars.set_yticklabels(top_7['COMUNA'], color=TEXT_MAIN, fontsize=9, fontweight='medium')
    ax_bars.tick_params(axis='y', length=0, pad=8) # Separacion del texto
    
    # Titulo de sección
    ax_bars.set_title("TOP 7 COMUNAS", color=TEXT_SUB, fontsize=8, loc='left', pad=10, fontweight='bold')
    
    # Clean up
    ax_bars.spines['top'].set_visible(False)
    ax_bars.spines['right'].set_visible(False)
    ax_bars.spines['bottom'].set_visible(False) # Sin eje X abajo
    ax_bars.spines['left'].set_color(TEXT_SUB)
    ax_bars.spines['left'].set_linewidth(0.5)
    ax_bars.xaxis.set_visible(False)
    ax_bars.set_xlim(0, valid_df[column].max() * 1.25) # Margen derecho para números


    # B. KPI CARD (Stats)
    ax_stat = fig.add_subplot(gs_mid[1])
    ax_stat.axis('off')
    
    avg_val = valid_df[column].mean()
    max_val = valid_df[column].max()
    
    # Calculate key points for distribution markers
    max_row = valid_df.iloc[0]  # Already sorted descending
    min_row = valid_df.iloc[-1]
    # Find 2 communes closest to the average
    valid_df_temp = valid_df.copy()
    valid_df_temp['_diff_avg'] = abs(valid_df_temp[column] - avg_val)
    near_avg_rows = valid_df_temp.nsmallest(1, '_diff_avg')

    # Contenedor visual (Linea vertical izquierda)
    ax_stat.axvline(x=0.1, ymin=0.1, ymax=0.9, color=TEXT_SUB, linewidth=0.5, alpha=0.5)
    
    # MAXIMO
    ax_stat.text(0.2, 0.80, "MÁXIMO", ha='left', color=SEC_COLOR, fontsize=9, fontweight='bold')
    ax_stat.text(0.2, 0.62, f"{max_val:.1f}%", ha='left', color=TEXT_MAIN, fontsize=26, fontweight='bold', fontfamily='monospace')
    
    # PROMEDIO
    ax_stat.text(0.2, 0.40, "PROMEDIO RM", ha='left', color=TEXT_SUB, fontsize=8, fontweight='bold')
    ax_stat.text(0.2, 0.25, f"{avg_val:.1f}%", ha='left', color=TEXT_SUB, fontsize=16, fontweight='bold', fontfamily='monospace')


    # --- 3. DISTRIBUTION (Footer) ---
    ax_dist = fig.add_subplot(gs[2, 0])
    
    # Clean KDE
    try:
        sns.kdeplot(valid_df[column], ax=ax_dist, color=CYBER_GREEN, fill=True, alpha=0.2, linewidth=1.5, clip=(0, 100))
    except:
        pass

    # Linea de Promedio
    ax_dist.axvline(avg_val, color=TEXT_MAIN, linestyle=':', linewidth=1, alpha=0.7)
    ax_dist.text(avg_val + (valid_df[column].max()*0.02), ax_dist.get_ylim()[1]*0.8, "AVG", color=TEXT_MAIN, fontsize=7)

    # Style Axis
    ax_dist.set_title("DISTRIBUCIÓN DE CASOS", color=TEXT_SUB, fontsize=8, loc='left', pad=5, fontweight='bold')
    ax_dist.spines['top'].set_visible(False)
    ax_dist.spines['right'].set_visible(False)
    ax_dist.spines['left'].set_visible(False)
    ax_dist.spines['bottom'].set_color(TEXT_SUB)
    
    ax_dist.set_xlim(0, max_val * 1.1) # Limitar eje X al maximo real + 10% margen
    ax_dist.ticklabel_format(style='plain', axis='x') # Evitar notacion cientifica
    
    ax_dist.tick_params(axis='x', colors=TEXT_SUB, labelsize=8)
    ax_dist.yaxis.set_visible(False)
    ax_dist.set_xlabel("", color=TEXT_SUB)
    ax_dist.set_ylabel("")

    # --- KEY POINTS MARKERS ---
    marker_y = ax_dist.get_ylim()[1] * 0.15  # Position above the x-axis
    label_y = ax_dist.get_ylim()[1] * 0.30
    
    # Max Point (Red) - Bold for hierarchy
    ax_dist.scatter([max_row[column]], [marker_y], color='#ff4444', s=25, zorder=5, marker='o')
    ax_dist.text(max_row[column], label_y, max_row['COMUNA'], color='#ff4444', fontsize=6, ha='center', fontweight='bold')
    
    # Min Point (Blue)
    ax_dist.scatter([min_row[column]], [marker_y], color=CYBER_CYAN, s=25, zorder=5, marker='o')
    ax_dist.text(min_row[column], label_y, min_row['COMUNA'], color=CYBER_CYAN, fontsize=6, ha='center', fontweight='medium')
    
    # Near Average Point (Yellow)
    for _, row in near_avg_rows.iterrows():
        ax_dist.scatter([row[column]], [marker_y], color=CYBER_YELLOW, s=25, zorder=4, marker='o')
        ax_dist.text(row[column], label_y, row['COMUNA'], color=CYBER_YELLOW, fontsize=6, ha='center', fontweight='medium')


    # --- BRANDING ---
    plt.text(0.5, 0.03, "FUENTE: INE CENSO 2024 • VISUALIZACIÓN: @CONMAPAS", transform=fig.transFigure,
             ha="center", fontsize=7, color=TEXT_SUB, alpha=0.6)

    # Padding manual para asegurar bordes limpios
    plt.subplots_adjust(left=0.15, right=0.90, top=0.92, bottom=0.08)

    # Guardar
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    out_path = os.path.join(OUTPUT_DIR, f"{filename_base}_DASH_{area_name.replace(' ','')}.png")
    
    plt.savefig(out_path, dpi=DPI, facecolor=BG_COLOR)
    plt.close()
    print(f"    Guardado Dash Pro: {out_path}")

    # --- EXPORTAR COMPONENTES INDIVIDUALES (TRANSPARENTE) ---
    print(f"    Exportando elementos individuales...")
    
    # 1. RANKING INDIVIDUAL
    fig_rank = plt.figure(figsize=(6, 4.5)) # Rectangular optimizado
    fig_rank.patch.set_alpha(0.0) # Transparente
    ax_r = fig_rank.add_subplot(111)
    
    bars_r = ax_r.barh(top_7['COMUNA'], top_7[column], color=ACCENT_COLOR, alpha=1.0, height=0.5)
    
    for bar in bars_r:
        width = bar.get_width()
        ax_r.text(width + (valid_df[column].max()*0.02), bar.get_y() + bar.get_height()/2 - 0.02, 
                     f'{width:.1f}%', 
                     ha='left', va='center', color=TEXT_MAIN, fontsize=10, fontweight='bold', fontfamily='monospace')

    ax_r.set_yticks(range(len(top_7)))
    ax_r.set_yticklabels(top_7['COMUNA'], color=TEXT_MAIN, fontsize=9, fontweight='medium')
    ax_r.tick_params(axis='y', length=0, pad=8)
    
    # Titulo descriptivo para contexto (CENTRADO EN LA IMAGEN)
    # Usamos fig.text en lugar de set_title para centrar respecto al lienzo total, no solo las barras
    fig_rank.text(0.5, 0.92, f"TOP 7: {title.upper()}", ha='center', va='center', 
                  color=TEXT_MAIN, fontsize=14, fontweight='bold')
    
    fig_rank.text(0.5, 0.85, description, ha='center', va='center', 
                  color=SEC_COLOR, fontsize=10, fontweight='medium')

    ax_r.spines['top'].set_visible(False)
    ax_r.spines['right'].set_visible(False)
    ax_r.spines['bottom'].set_visible(False)
    ax_r.spines['left'].set_color(TEXT_SUB)
    ax_r.xaxis.set_visible(False)
    ax_r.set_xlim(0, valid_df[column].max() * 1.3)
    ax_r.set_facecolor('none') # Eje transparente

    plt.tight_layout(rect=[0, 0, 1, 0.82]) # Dejar espacio arriba para los titulos
    path_rank = os.path.join(OUTPUT_DIR, f"{filename_base}_ELEM_RANK.png")
    plt.savefig(path_rank, dpi=DPI, transparent=True)
    plt.close()

    # 2. STATS INDIVIDUAL
    fig_stat = plt.figure(figsize=(4, 3)) # Tarjeta compacta
    fig_stat.patch.set_alpha(0.0)
    ax_s = fig_stat.add_subplot(111)
    ax_s.axis('off')
    
    ax_s.text(0.5, 0.85, title.upper(), ha='center', color=TEXT_MAIN, fontsize=14, fontweight='bold')
    
    # Card like layout
    ax_s.text(0.5, 0.65, "MÁXIMO REGIONAL", ha='center', color=SEC_COLOR, fontsize=10, fontweight='bold')
    ax_s.text(0.5, 0.50, f"{max_val:.1f}%", ha='center', color=TEXT_MAIN, fontsize=40, fontweight='bold', fontfamily='monospace')
    
    ax_s.plot([0.3, 0.7], [0.4, 0.4], color=TEXT_SUB, linewidth=1, alpha=0.5)

    ax_s.text(0.5, 0.30, "PROMEDIO RM", ha='center', color=TEXT_SUB, fontsize=10, fontweight='bold')
    ax_s.text(0.5, 0.15, f"{avg_val:.1f}%", ha='center', color=TEXT_SUB, fontsize=24, fontweight='bold', fontfamily='monospace')

    plt.tight_layout()
    path_stat = os.path.join(OUTPUT_DIR, f"{filename_base}_ELEM_STATS.png")
    plt.savefig(path_stat, dpi=DPI, transparent=True)
    plt.close()

    # 3. DISTRIBUTION INDIVIDUAL
    fig_dist = plt.figure(figsize=(6, 2.5)) # Panorámico bajito
    fig_dist.patch.set_alpha(0.0)
    ax_d = fig_dist.add_subplot(111)
    
    try:
        sns.kdeplot(valid_df[column], ax=ax_d, color=CYBER_GREEN, fill=True, alpha=0.4, linewidth=2, clip=(0, 100))
    except:
        pass

    ax_d.axvline(avg_val, color=TEXT_MAIN, linestyle=':', linewidth=1.5, alpha=0.9)
    ax_d.text(avg_val, ax_d.get_ylim()[1]*0.95, " PROMEDIO", color=TEXT_MAIN, fontsize=8)

    ax_d.set_title(f"DISTRIBUCIÓN: {title.upper()}", color=TEXT_MAIN, fontsize=10, pad=10, fontweight='bold')
    ax_d.set_facecolor('none')
    
    ax_d.spines['top'].set_visible(False)
    ax_d.spines['right'].set_visible(False)
    ax_d.spines['left'].set_visible(False)
    ax_d.spines['bottom'].set_color(TEXT_SUB)
    
    ax_d.set_xlim(0, max_val * 1.1) # Limitar eje X al maximo real + 10% margen
    ax_d.ticklabel_format(style='plain', axis='x') # Evitar notacion cientifica (ese "1" raro)
    
    ax_d.tick_params(axis='x', colors=TEXT_MAIN)
    ax_d.yaxis.set_visible(False)
    ax_d.set_ylabel("")
    ax_d.set_xlabel("Porcentaje (%)", color=TEXT_SUB)

    # --- KEY POINTS MARKERS ---
    marker_y_d = ax_d.get_ylim()[1] * 0.15
    label_y_d = ax_d.get_ylim()[1] * 0.30
    
    # Max Point (Red) - Bold for hierarchy
    ax_d.scatter([max_row[column]], [marker_y_d], color='#ff4444', s=35, zorder=5, marker='o')
    ax_d.text(max_row[column], label_y_d, max_row['COMUNA'], color='#ff4444', fontsize=8, ha='center', fontweight='bold')
    
    # Min Point (Blue)
    ax_d.scatter([min_row[column]], [marker_y_d], color=CYBER_CYAN, s=35, zorder=5, marker='o')
    ax_d.text(min_row[column], label_y_d, min_row['COMUNA'], color=CYBER_CYAN, fontsize=8, ha='center', fontweight='medium')
    
    # Near Average Point (Yellow)
    for _, row in near_avg_rows.iterrows():
        ax_d.scatter([row[column]], [marker_y_d], color=CYBER_YELLOW, s=35, zorder=4, marker='o')
        ax_d.text(row[column], label_y_d + (ax_d.get_ylim()[1] * 0.08), row['COMUNA'], color=CYBER_YELLOW, fontsize=8, ha='center', fontweight='medium')


    plt.tight_layout()
    path_dist = os.path.join(OUTPUT_DIR, f"{filename_base}_ELEM_DIST.png")
    plt.savefig(path_dist, dpi=DPI, transparent=True)
    plt.close()

    # 4. LOLLIPOP CHART (Todas las comunas)
    print(f"    Generando Lollipop Chart...")
    fig_lol = plt.figure(figsize=(6, 8))
    fig_lol.patch.set_alpha(0.0)
    ax_lol = fig_lol.add_subplot(111)
    
    # Ordenar todas las comunas de menor a mayor
    all_sorted = valid_df.sort_values(by=column, ascending=True)
    y_pos = range(len(all_sorted))
    
    # Líneas horizontales (lollipop stems)
    ax_lol.hlines(y=y_pos, xmin=0, xmax=all_sorted[column], color=TEXT_SUB, alpha=0.4, linewidth=1)
    
    # Puntos (lollipop heads) - color basado en valor
    colors = [CYBER_MAGENTA if v == max_val else (CYBER_CYAN if v == all_sorted[column].min() else CYBER_GREEN) for v in all_sorted[column]]
    ax_lol.scatter(all_sorted[column], y_pos, color=colors, s=40, zorder=3)
    
    # Etiquetas de comunas
    ax_lol.set_yticks(y_pos)
    ax_lol.set_yticklabels(all_sorted['COMUNA'], fontsize=6, color=TEXT_MAIN)
    
    # Línea de promedio
    ax_lol.axvline(avg_val, color=CYBER_YELLOW, linestyle='--', linewidth=1.5, alpha=0.8, label=f'Promedio: {avg_val:.1f}%')
    
    # Estilo
    ax_lol.set_title(f"RANKING COMUNAS: {title.upper()}", color=TEXT_MAIN, fontsize=11, fontweight='bold', pad=10)
    ax_lol.set_xlabel("Porcentaje (%)", color=TEXT_SUB, fontsize=9)
    ax_lol.set_facecolor('none')
    ax_lol.spines['top'].set_visible(False)
    ax_lol.spines['right'].set_visible(False)
    ax_lol.spines['left'].set_color(TEXT_SUB)
    ax_lol.spines['bottom'].set_color(TEXT_SUB)
    ax_lol.tick_params(axis='x', colors=TEXT_SUB)
    ax_lol.tick_params(axis='y', length=0)
    ax_lol.legend(loc='lower right', fontsize=8, frameon=False, labelcolor=TEXT_MAIN)
    
    plt.tight_layout()
    path_lol = os.path.join(OUTPUT_DIR, f"{filename_base}_LOLLIPOP.png")
    plt.savefig(path_lol, dpi=DPI, transparent=True)
    plt.close()


def assign_metro_area(commune):
    """Asigna área metropolitana (Simplificado solo RM)"""
    # Como ya filtramos por Región Metropolitana y Urbano, 
    # clasificamos todo lo resultante como 'Gran Santiago' para el loop de generación.
    return 'Gran Santiago'

def main():
    setup_plot()
    print(f"Cargando datos: {INPUT_FILE}...")
    
    # Verificación simple de archivo
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: No se encuentra el archivo '{INPUT_FILE}'. Verifica la ruta.")
        return

    gdf = gpd.read_file(INPUT_FILE)
    
    # --- FILTRO REGION METROPOLITANA ---
    # Filtrar por substring para evitar problemas de encoding exacto
    if 'REGION' in gdf.columns:
        print("Filtrando solo REGIÓN METROPOLITANA...")
        # Normalizar y buscar 'METROPOLITANA'
        gdf = gdf[gdf['REGION'].astype(str).str.contains('METROPOLITANA', case=False, na=False)].copy()
        print(f"Registros en RM: {len(gdf)}")
    else:
        print("ERROR: No se encontró columna REGION.")
        return

    # --- FILTRO URBANO ---
    # User requested "Toda la región", removing urban filter to simplify.
    # if 'AREA_C' in gdf.columns:
    #     print("Filtrando solo áreas URBANAS (AREA_C = 1)...")
    #     gdf['AREA_C'] = gdf['AREA_C'].astype(str)
    #     gdf = gdf[gdf['AREA_C'] == '1'].copy()
    #     print(f"Registros Urbanos: {len(gdf)}")
    # else:
    #     print("WARN: No se encontró columna AREA_C.")
    
    # Definición de indicadores (SOLO LOS SELECCIONADOS)
    indicadores_config = [
        # Nuevos indicadores compuestos (Humor cargado de Realidad + Sátira al Privilegio)
        # Escala 0-100 (Min-Max sobre Z-Score)
        ('idx_precariedad_hab', 'Precariedad Habitacional', 'precariedad_hab', 'Variables: Hacinamiento, Allegamiento, Calidad Viv., Saneamiento, Tenencia Inf.', 'n_viv_hacinadas', 'n_vp'),
        ('idx_vulnerabilidad_soc', 'Vulnerabilidad Social', 'vulnerabilidad_soc', 'Variables: Desempleo, Analfabetismo, Brecha Digital, Jefatura Fem.', 'n_desocupado', 'n_per'),
        ('idx_privilegio', 'Cuestiona tus privilegios perro', 'cuestiona_privilegios', 'Variables: Educ. Sup., Auto, Casa Pagada, Internet Fija, Alto Estándar, Espacio', 'n_cine_terciaria_maestria_doctorado', 'n_per'),
    ]
    
    # Check para agua (Legacy, se puede ignorar si no se usa)
    cols_agua = ['n_fuente_agua_camion', 'n_fuente_agua_rio', 'n_fuente_agua_pozo']
    has_agua_cols = all(c in gdf.columns for c in cols_agua)

    print("Calculando estadísticas metropolitanas...")
    if 'COMUNA' not in gdf.columns:
        print("ERROR: Falta columna COMUNA en el archivo.")
        return

    # 0. CALCULAR INDICADORES EN GDF (NIVEL MANZANA) PARA EL PLOT
    # Esto faltaba y por eso fallaba el ploteo ("Fallback to continuous...")
    print("  Calculando indicadores a nivel manzana...")
    if 'n_hog_unipersonales' in gdf and 'n_hog' in gdf:
        gdf['pct_alone'] = (gdf['n_hog_unipersonales'] / gdf['n_hog']) * 100
    
    if 'n_transporte_bicicleta' in gdf and 'n_per' in gdf:
        gdf['pct_ciclistas'] = (gdf['n_transporte_bicicleta'] / gdf['n_per']) * 100
        
    if 'n_tenencia_propia_pagandose' in gdf and 'n_hog' in gdf:
        gdf['pct_hipotecados'] = (gdf['n_tenencia_propia_pagandose'] / gdf['n_hog']) * 100
        
    if 'n_estcivcon_anul_sep_div' in gdf and 'n_per' in gdf:
        gdf['pct_ex'] = (gdf['n_estcivcon_anul_sep_div'] / gdf['n_per']) * 100
    
    if 'n_tenencia_cedida_familiar' in gdf and 'n_hog' in gdf:
         # Eliminamos pct_hotel_mama
         pass
    
    # Rellenar indices compuestos si vienen nulos (ya calculados en process)
    if 'idx_precariedad_hab' in gdf.columns:
        gdf['idx_precariedad_hab'] = gdf['idx_precariedad_hab'].fillna(0)
    if 'idx_vulnerabilidad_soc' in gdf.columns:
        gdf['idx_vulnerabilidad_soc'] = gdf['idx_vulnerabilidad_soc'].fillna(0)
    if 'idx_privilegio' in gdf.columns:
        gdf['idx_privilegio'] = gdf['idx_privilegio'].fillna(0)
    
    # Rellenar NaNs con 0 para evitar huecos en el mapa
    for col, _, _, _, _, _ in indicadores_config:
        if col in gdf.columns:
            gdf[col] = gdf[col].fillna(0)

    # 1. Agrupar sumarizando (Para ranking comunal)
    # Lista exhaustiva de componentes para Z-Score
    agg_cols = ['n_hog', 'n_per', 'n_vp', 'n_hog_unipersonales', 'n_transporte_bicicleta', 
                'n_tenencia_propia_pagandose', 'n_estcivcon_anul_sep_div', 
                # Precariedad
                'n_viv_hacinadas', 'n_hog_allegados', 'n_viv_irrecuperables', 'n_tipo_viv_mediagua',
                'n_mat_paredes_precarios', 'n_mat_techo_precarios', 'n_mat_piso_tierra',
                'n_tenencia_arrendada_sin_contrato', 'n_tenencia_cedida_familiar',
                'n_fuente_agua_pozo', 'n_fuente_agua_camion', 'n_serv_hig_no_tiene',
                # Vulnerabilidad
                'n_desocupado', 'n_ocupado', 'n_analfabet', 'n_jefatura_mujer', 'n_internet',
                # Privilegio
                'n_cine_terciaria_maestria_doctorado', 'n_transporte_auto', 'n_tenencia_propia_pagada',
                'n_serv_internet_fija', 'n_serv_compu', 
                'n_dormitorios_4', 'n_dormitorios_5', 'n_dormitorios_6_o_mas'
                ]
    
    agg_cols = [c for c in agg_cols if c in gdf.columns]
    
    stats_raw = gdf.groupby(['COMUNA'])[agg_cols].sum().reset_index()
    
    # 2. Asignar Área Metro
    stats_raw['AREA_METRO'] = stats_raw['COMUNA'].apply(assign_metro_area)
    stats = stats_raw.dropna(subset=['AREA_METRO']).copy()
    
    # FILTER: Filtro de robustez estadística
    if 'n_hog' in stats and 'n_per' in stats:
         before_count = len(stats)
         stats = stats[(stats['n_per'] > 1000) & (stats['n_hog'] > 300)].copy()
         print(f"Filtradas comunas pequeñas (n_per<1000): {before_count - len(stats)} eliminadas.")
    
    if stats.empty:
        print("CRITICAL: Ninguna comuna cumple criterios.")
        return

    # 3. Calcular porcentajes (NIVEL COMUNA - Para el Ranking)
    if 'n_hog_unipersonales' in stats and 'n_hog' in stats:
        stats['pct_alone'] = (stats['n_hog_unipersonales'] / stats['n_hog']) * 100

    if 'n_transporte_bicicleta' in stats and 'n_per' in stats: 
        stats['pct_ciclistas'] = (stats['n_transporte_bicicleta'] / stats['n_per']) * 100

    if 'n_tenencia_propia_pagandose' in stats and 'n_hog' in stats:
        stats['pct_hipotecados'] = (stats['n_tenencia_propia_pagandose'] / stats['n_hog']) * 100

    if 'n_estcivcon_anul_sep_div' in stats and 'n_per' in stats:
        stats['pct_ex'] = (stats['n_estcivcon_anul_sep_div'] / stats['n_per']) * 100

    # RECALCULO DE ÍNDICES COMPUESTOS A NIVEL COMUNAL (Z-SCORES) --
    
    # Helper seguro calculo
    def calc_pct_stats(num, den):
        if num in stats and den in stats:
             return (stats[num] / stats[den].replace(0, 1)) * 100
        return 0 # Si no existe, asume 0
    
    def z_score_stats(series):
        std = series.std()
        if std == 0: return series * 0
        return (series - series.mean()) / std

    # --- Precariedad Habitacional ---
    p_hacinamiento = calc_pct_stats('n_viv_hacinadas', 'n_vp')
    p_allegamiento = calc_pct_stats('n_hog_allegados', 'n_hog')
    p_irrecuperable = calc_pct_stats('n_viv_irrecuperables', 'n_vp')
    p_mediagua = calc_pct_stats('n_tipo_viv_mediagua', 'n_vp')
    
    # Materialidad Sumada
    # Asegurar que existan (cols_extra)
    mat_sum = 0
    for c in ['n_mat_paredes_precarios', 'n_mat_techo_precarios', 'n_mat_piso_tierra']:
        if c in stats: mat_sum += calc_pct_stats(c, 'n_vp')
    p_mat_precari = mat_sum
    
    p_sin_contrato = calc_pct_stats('n_tenencia_arrendada_sin_contrato', 'n_hog')
    p_cedida = calc_pct_stats('n_tenencia_cedida_familiar', 'n_hog')
    
    san_sum = 0
    for c in ['n_serv_hig_no_tiene', 'n_fuente_agua_camion']:
        if c in stats: san_sum += calc_pct_stats(c, 'n_vp')
    p_saneamiento = san_sum

    # --- Helper MinMax ---
    def minmax_scale(series):
        if series.max() == series.min(): return series * 0
        return ((series - series.min()) / (series.max() - series.min())) * 100

    stats['idx_precariedad_hab'] = minmax_scale((
        z_score_stats(p_hacinamiento) + z_score_stats(p_allegamiento) +
        z_score_stats(p_irrecuperable) + z_score_stats(p_mediagua) +
        z_score_stats(p_mat_precari) + z_score_stats(p_saneamiento) +
        z_score_stats(p_sin_contrato) + z_score_stats(p_cedida)
    ) / 8.0)

    # --- Vulnerabilidad Social ---
    p_analfabeto = calc_pct_stats('n_analfabet', 'n_per')
    p_jefa = calc_pct_stats('n_jefatura_mujer', 'n_hog')
    
    if 'n_ocupado' in stats and 'n_desocupado' in stats:
        fl = stats['n_ocupado'] + stats['n_desocupado']
        p_desempleo = (stats['n_desocupado'] / fl.replace(0, 1)) * 100
    else: p_desempleo = 0 # Series 0
        
    if 'n_internet' in stats and 'n_hog' in stats:
        pct_internet = (stats['n_internet'] / stats['n_hog'].replace(0,1)) * 100
        p_sin_internet = 100 - pct_internet
    else: p_sin_internet = 0
        
    stats['idx_vulnerabilidad_soc'] = minmax_scale((
        z_score_stats(p_desempleo) + z_score_stats(p_analfabeto) + 
        z_score_stats(p_sin_internet) + z_score_stats(p_jefa)
    ) / 4.0)

    # --- Privilegio ---
    p_profesional = calc_pct_stats('n_cine_terciaria_maestria_doctorado', 'n_per')
    p_propia_pagada = calc_pct_stats('n_tenencia_propia_pagada', 'n_hog')
    p_auto = calc_pct_stats('n_transporte_auto', 'n_per')
    p_int_fija = calc_pct_stats('n_serv_internet_fija', 'n_hog')
    p_computador = calc_pct_stats('n_serv_compu', 'n_hog')
    
    esp_sum = 0
    for c in ['n_dormitorios_4', 'n_dormitorios_5', 'n_dormitorios_6_o_mas']:
        if c in stats: esp_sum += calc_pct_stats(c, 'n_vp')
    p_espacio = esp_sum

    stats['idx_privilegio'] = minmax_scale((
        z_score_stats(p_profesional) +
        z_score_stats(p_propia_pagada) +
        z_score_stats(p_auto) +
        z_score_stats(p_int_fija) +
        z_score_stats(p_computador) +
        z_score_stats(p_espacio)
    ) / 6.0)





    print(f"Comunas analizadas (raw): {len(stats)}")
    
    # 4. Loop Generación
    for col, title, fname_base, desc, _, _ in indicadores_config:
        if col not in stats.columns: 
            print(f"Saltando {col} (no existe en datos)")
            continue
        
        print(f"Analizando indicador: {title}...")

        # 4.1 Filter Urban Only within the stats (if possible) or just for the Jenks calculation?
        # User said: "concentrate en el urbano".
        # We assume dataset has 'AREA_C'. If not, we skip filter.
        valid_data_for_bins = stats[col].dropna()
        # If we have commune granularity, AREA_C is likely not here but in the geometry.
        # But 'stats' is aggregated by COMUNA.
        # The filter should happen at the MANZANA level (in generate_commune_map) or we should assume
        # the indicator itself aggregates urban? 
        # Actually, if we filter gdf in main, the 'stats' should also be filtered?
        # NO. 'stats' is aggregated from gdf. We need to filter gdf BEFORE aggregation.
        # So we must move the filter up.
        
        # 4.2 CÁLCULO DE LEYENDA GLOBAL (Unified Legend)
        # Usamos todos los valores válidos del dataset (ya filtrado por Urbano)
        try:
            global_classifier = mapclassify.FisherJenks(valid_data_for_bins, k=5)
            global_bins = global_classifier.bins
            print(f"  Bins Globales para {col}: {global_bins}")
        except Exception as e:
            print(f"  Error calculando bins globales: {e}")
            global_bins = None

        for area in stats['AREA_METRO'].unique():
            df_area = stats[stats['AREA_METRO'] == area]
            if df_area.empty: continue
            
            # Caso "Alto" (Máximo valor) - SOLO ESTE
            try:
                max_row = df_area.loc[df_area[col].idxmax()]
                fname_max = f"{fname_base}_MAX_{area.replace(' ','')}"
                # Pasamos 'global_bins'
                generate_commune_map(gdf, max_row['COMUNA'], col, title, fname_max, desc, bins=global_bins)
                
                # --- GENERAR INFOGRAFÍA (SOLO UNA POR ÁREA/INDICADOR) ---
                # Usamos el dataframe 'df_area' que contiene las estadísticas de todas las comunas del área
                generate_infographic(df_area, col, title, fname_base, desc, area)

            except Exception as e:
                print(f"Error generando max para {area}: {e}")

    print("¡Generación finalizada con éxito!")

if __name__ == "__main__":
    main()