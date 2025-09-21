import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import ListedColormap
import matplotlib as mpl

# Set global matplotlib parameters for publication quality
mpl.rcParams['font.family'] = 'Arial'
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['ps.fonttype'] = 42
mpl.rcParams['font.size'] = 13
mpl.rcParams['axes.linewidth'] = 1.5
mpl.rcParams['axes.labelsize'] = 14
mpl.rcParams['xtick.major.width'] = 1.5
mpl.rcParams['ytick.major.width'] = 1.5
mpl.rcParams['xtick.major.size'] = 5
mpl.rcParams['ytick.major.size'] = 5

# Function to normalize data
def normalize(data, max_val, min_val):
    normal = (data - min_val)/(max_val-min_val)
    normal = np.clip(normal, 0, 1)
    return normal

# Read the data
# Replace these paths with your actual file paths
lst = pd.read_csv(r'C:\pyGUCA\SensitivityAnalysis\LST_Statistics\maskedUrban\LST_MaxDay_maskedNonUrb_Summer.csv')
uhi = pd.read_csv(r'C:\pyGUCA\SensitivityAnalysis\UHI_Statistics\UHI_warm_months.csv')
hw = pd.read_excel(r'C:\pyGUCA\SensitivityAnalysis\Heatwave\Heatwave_Max_5D_cityMetrics.xlsx')

# Prepare the dataframes
dfLST = lst.loc[:,['Name', 'Mean']].rename(columns={'Name': 'City', 'Mean': 'meanLST'}).set_index('City')
dfUHI = uhi.loc[:,['Name', 'mean']].rename(columns={'Name': 'City', 'mean': 'meanUHI'}).set_index('City')
dfHW = hw.loc[:, ['City','HW Index']].rename(columns={'WeightedIndex': 'HW_i'}).set_index('City')

# Combine dataframes
dfHI = pd.concat([dfLST, dfUHI, dfHW], axis=1)

# Normalize the data
max_lst, min_lst = 50, 30
max_UHI, min_UHI = 5, 0

dfHI.loc[:, "LST_N"] = normalize(dfHI['meanLST'], max_lst, min_lst)
dfHI.loc[:, "UHI_N"] = normalize(dfHI['meanUHI'], max_UHI, min_UHI)
dfHI.loc[:, "HW_N"] = normalize(dfHI['HW_i'], 1, 0)

# Create weight combinations with 0.1 increments
n_steps = 11
w1_range = np.linspace(0, 1, n_steps)
w2_range = np.linspace(0, 1, n_steps)[::-1]  # Reverse w2_range for visualization

# Create matrices to store HHI values and rankings for each weight combination
hhi_matrix = {}
ranking_matrix = {}
for city in dfHI.index:
    hhi_matrix[city] = np.full((n_steps, n_steps), np.nan)
    ranking_matrix[city] = np.full((n_steps, n_steps), np.nan)


# # Create a matrix to store rankings for each weight combination
# ranking_matrix = {}
# for city in dfHI.index:
#     ranking_matrix[city] = np.full((n_steps, n_steps), np.nan)

# Calculate HHI values and rankings for each weight combination
valid_combinations = 0
for i, w1 in enumerate(w1_range):
    for j, w2 in enumerate(w2_range):
        w3 = 1 - w1 - w2
        if w3 >= 0:
            valid_combinations += 1
           
            # Calculate HHI for each city
            hhi_values = (dfHI['LST_N'] * w1 +
                          dfHI['UHI_N'] * w2 +
                          dfHI['HW_N'] * w3)
           
            # Case 1: Check if ALL cities have zero values or the same value
            if (hhi_values == 0).all() or hhi_values.nunique() == 1:
                for city in dfHI.index:
                    hhi_matrix[city][j, i] = -999  # Special marker for "all zeros or same value"
                    ranking_matrix[city][j, i] = -999  # Keep ranking matrix for sorting
           
            # Case 2: Check for ties at zero within rankings
            elif (hhi_values == 0).any():
                # Get regular rankings first
                rankings = hhi_values.rank(ascending=False, method='min')
               
                # Store values and rankings in the matrices
                for city in dfHI.index:
                    if hhi_values[city] == 0:
                        # Mark tied zero values with the same special marker
                        hhi_matrix[city][j, i] = -999
                        ranking_matrix[city][j, i] = -999
                    else:
                        hhi_matrix[city][j, i] = hhi_values[city]
                        ranking_matrix[city][j, i] = rankings[city]
           
            else:
                # Normal case (no zeros) - store actual HHI values and rankings
                rankings = hhi_values.rank(ascending=False, method='min')
               
                # Store HHI values and rankings in the matrices
                for city in dfHI.index:
                    hhi_matrix[city][j, i] = hhi_values[city]
                    ranking_matrix[city][j, i] = rankings[city]

# Calculate global statistics for consistent colorbar
# Find global min and max HHI values (excluding special markers)
all_hhi_values = []
for city in dfHI.index:
    valid_values = hhi_matrix[city][hhi_matrix[city] != -999]
    valid_values = valid_values[~np.isnan(valid_values)]
    all_hhi_values.extend(valid_values)

global_min_hhi = min(all_hhi_values)
global_max_hhi = max(all_hhi_values)

# Calculate rank statistics for sorting
city_stats = {}
for city in dfHI.index:
    # Only consider valid and non-special ranks
    valid_ranks = ranking_matrix[city][(~np.isnan(ranking_matrix[city])) &
                                      (ranking_matrix[city] > 0)]
   
    city_stats[city] = {
        'median_rank': np.median(valid_ranks) if len(valid_ranks) > 0 else np.nan,
        'min_rank': np.min(valid_ranks) if len(valid_ranks) > 0 else np.nan,
        'max_rank': np.max(valid_ranks) if len(valid_ranks) > 0 else np.nan,
        'rank_range': np.max(valid_ranks) - np.min(valid_ranks) if len(valid_ranks) > 0 else np.nan
    }

# Sort cities by median rank for plotting (maintain same order as before)
# sorted_cities = sorted(city_stats.items(), key=lambda x: x[1]['median_rank'])
# sorted_city_names = [city for city, _ in sorted_cities]

# Create a custom colormap for HHI values - red (high HHI) to blue (low HHI)
custom_cmap = sns.color_palette("RdBu_r", as_cmap=True)  # Reversed to make red=high, blue=low

# Create a figure with subplots for each city
fig = plt.figure(figsize=(18, 9))

# Plot heatmaps in order of median rank
# for idx, city in enumerate(sorted_city_names, 1):
for idx, city in enumerate(dfHI.index, 1):
#    print(idx, ' ',  city)
    ax = plt.subplot(3, 3, idx)
   
    # Create masks for different special cases
    special_mask = hhi_matrix[city] == -999  # All zeros/special cases use same marker
   
    # Create a mask for invalid combinations
    invalid_mask = np.isnan(hhi_matrix[city])
   
    # Create a mask for regular values (neither special case nor invalid)
    regular_mask = ~(special_mask | invalid_mask)
   
    # Create arrays for the different types of cells
    regular_data = np.where(regular_mask, hhi_matrix[city], np.nan)
   
    # Plot HHI values without annotations first (we'll add them manually with smaller font)
    hm = sns.heatmap(regular_data,
                     xticklabels=[f'{x:.1f}' for x in w1_range],
                     yticklabels=[f'{x:.1f}' for x in w2_range],
                     cmap=custom_cmap,
                     vmin=global_min_hhi,
                     vmax=global_max_hhi,
                     cbar=True,
                     annot=False,  # Don't automatically annotate
                     cbar_kws={'orientation': 'vertical', 'shrink': 0.8})
   
    # Modify colorbar for HHI values
    colorbar = hm.collections[0].colorbar
    colorbar.set_ticks(np.linspace(0, 1, 6))
    colorbar.set_ticklabels([f'{x:.1f}' for x in np.linspace(0, 1, 6)])
    colorbar.ax.tick_params(labelsize=10)
   
    # Plot black cells for special_mask locations (no annotations)
    if np.any(special_mask):
        # Create a mesh for the cell centers
        x, y = np.meshgrid(np.arange(0.5, special_mask.shape[1] + 0.5),
                           np.arange(0.5, special_mask.shape[0] + 0.5))
        # Plot black squares for each special cell
        for yi, xi in zip(y[special_mask], x[special_mask]):
            ax.add_patch(plt.Rectangle((xi-0.5, yi-0.5), 1, 1, fill=True, color='black'))
   
    # Add text annotations with smaller font size
    #for i in range(hhi_matrix[city].shape[0]):
        # for j in range(hhi_matrix[city].shape[1]):
        #     if regular_mask[i, j]:
        #         # Add manual annotation with proper color and smaller font size
        #         hhi_val = regular_data[i, j]
        #         norm_val = (hhi_val - global_min_hhi) / (global_max_hhi - global_min_hhi)
        #         # Use white text for darker cells (higher HHI), black for lighter cells
        #         text_color = 'white' if norm_val >= 0.7 or norm_val <= 0.3 else 'black'
               
        #         # Use smaller font size (7pt) and simplify format (1 decimal place)
        #         plt.text(j + 0.5, i + 0.5, f'{hhi_val:.1f}',
        #                  ha='center', va='center',
        #                  color=text_color, fontweight='bold', fontsize=7)
   
    # Add city name to title with proper formatting
    plt.title(city, fontsize=16, pad=10, fontweight='bold')
   
    # Add journal-quality axis labels with proper padding
    plt.xlabel('W1 (LST)', fontsize=14, labelpad=10, fontweight='bold')
    plt.ylabel('W2 (UHI)', fontsize=14, labelpad=10, fontweight='bold')
   
    # Rotate y-axis tick labels for better readability
    plt.yticks(rotation=0)  # Horizontal orientation for y-ticks
   
    # Increase tick label sizes
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
   
    # # Add colorbar label only to the last subplot in each row
    # if idx % 4 == 0:  # Last subplot in each row
    #     colorbar.set_label('HHI Value', fontsize=14, fontweight='bold', labelpad=10)

# Ensure proper spacing between subplots
plt.tight_layout(rect=[0, 0.08, 1, 1.0])  # Increased bottom margin for legend

# Create a separate axis for the legend at the bottom to avoid overlap
legend_ax = fig.add_axes([0.3, 0.045, 0.4, 0.02], frameon=False)  # [x, y, width, height]
legend_ax.axis('off')  # Hide axis

# Add legend to the separate axis
legend_elements = [
    plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='black',
              markersize=12, label='HHI = 0: Zero values for this weight combination')
]
legend = legend_ax.legend(handles=legend_elements, loc='center',
                   ncol=1, fontsize=14, frameon=True, framealpha=0.9,
                   title='Special Cases', title_fontsize=16)
legend.get_frame().set_linewidth(1.5)

# Add a note about W3 and metadata with better formatting, positioned at the very bottom
note_text = (
    'Note: W3 (Heatwave) = 1 - W1 - W2     |     '
    f'Analysis based on {valid_combinations} valid weight combinations'
)
fig.text(0.5, 0.002, note_text, ha='center', fontsize=14,
         bbox=dict(facecolor='white', alpha=0.7, boxstyle="round,pad=0.3"))

# # Save the figure in high resolution with proper dimensions for journal submission
# plt.savefig('city_hhi_values_heatmap_smallfont.png', dpi=600, bbox_inches='tight')

# plt.show()

# Save the figure in high resolution with proper dimensions for journal submission
plt.savefig(r'C:\pyGUCA\SensitivityAnalysis\Fig\city_HHI_value_heatmap_final2.png',
           dpi=600, bbox_inches='tight')

plt.show()
