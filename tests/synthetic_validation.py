import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import importlib.util

# Load the module by file path because workspace path contains spaces
module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'himcm_graph_models.py'))
spec = importlib.util.spec_from_file_location('himcm_graph_models', module_path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Create synthetic data
data = [
    {
        'City': 'Alpha', 'State': 'A', 'Times_Hosted': 1, 'Last_Hosted_Year': 2010,
        'Stadium_Name': 'Alpha Stadium', 'Stadium_Type': 'Dome', 'Avg_Feb_Temp_F': 45,
        'Alltransit_Score': 80, 'Renewable_Energy_Pct': 60, 'Waste_Diversion_Pct': 50,
        'Green_Legacy_Projects': 2, 'Carbon_Offset_Programs': 1, 'Stadium_leed_cert': 'Gold',
        'Water_Score': 70, 'Air_ug_m3': 12, 'Carbon_Emissions': 2.5
    },
    {
        'City': 'Beta', 'State': 'B', 'Times_Hosted': 0, 'Last_Hosted_Year': 0,
        'Stadium_Name': 'Beta Field', 'Stadium_Type': 'Open', 'Avg_Feb_Temp_F': 55,
        'Alltransit_Score': 60, 'Renewable_Energy_Pct': 20, 'Waste_Diversion_Pct': 30,
        'Green_Legacy_Projects': 0, 'Carbon_Offset_Programs': 0, 'Stadium_leed_cert': 'Certified',
        'Water_Score': 50, 'Air_ug_m3': 25, 'Carbon_Emissions': 5.0
    },
    {
        'City': 'Gamma', 'State': 'C', 'Times_Hosted': 2, 'Last_Hosted_Year': 2022,
        'Stadium_Name': 'Gamma Dome', 'Stadium_Type': 'Retractable', 'Avg_Feb_Temp_F': 35,
        'Alltransit_Score': 90, 'Renewable_Energy_Pct': 80, 'Waste_Diversion_Pct': 70,
        'Green_Legacy_Projects': 5, 'Carbon_Offset_Programs': 3, 'Stadium_leed_cert': 'Platinum',
        'Water_Score': 80, 'Air_ug_m3': 8, 'Carbon_Emissions': 1.2
    }
]

df_test = pd.DataFrame(data)

# Run scoring with a custom weight emphasizing Env_Conditions
user_weights = {
    'Alltransit_Score': 0.2,
    'Renewable_Energy_Pct': 0.15,
    'Waste_Diversion_Pct': 0.15,
    'Green_Legacy_Projects': 0.15,
    'Carbon_Offset_Programs': 0.05,
    'Env_Conditions': 0.25
}

# Compute scores
result = mod.calculate_sustainability_scores(df_test, user_weights=user_weights, env_component_weights={'energy':0.5,'water':0.2,'air':0.2,'carbon':0.1}, env_overall_weight=0.35)

out_dir = os.path.join(os.path.dirname(__file__), 'outputs')
os.makedirs(out_dir, exist_ok=True)

# Save CSV
csv_path = os.path.join(out_dir, 'synthetic_results.csv')
result.to_csv(csv_path, index=False)
print('Saved synthetic results to', csv_path)

# Create a simple barplot and save
ranked = result.sort_values('Sustainability_Z_Scaled', ascending=False)
plt.figure(figsize=(6,4))
sns = mod.__dict__.get('sns') or __import__('seaborn')
sns.barplot(data=ranked, x='Sustainability_Z_Scaled', y='City', palette='viridis')
plt.title('Synthetic Top Cities (Scaled Z)')
plot_path = os.path.join(out_dir, 'synthetic_barplot.png')
plt.tight_layout()
plt.savefig(plot_path)
print('Saved barplot to', plot_path)

# Save heatmap of numeric correlations
numeric_cols = [c for c in ['Raw_Score', 'Sustainability_Z', 'Sustainability_Z_Scaled', 'Avg_Feb_Temp_F', 'Alltransit_Score', 'Renewable_Energy_Pct', 'Waste_Diversion_Pct'] if c in result.columns]
if len(numeric_cols) >= 2:
    plt.figure(figsize=(6,5))
    sns.heatmap(result[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0)
    heatmap_path = os.path.join(out_dir, 'synthetic_heatmap.png')
    plt.tight_layout()
    plt.savefig(heatmap_path)
    print('Saved heatmap to', heatmap_path)

print('Synthetic validation complete.')
