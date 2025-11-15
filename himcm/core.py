"""Core functions for hiMCM sustainability scoring.

This module contains the main scoring pipeline and analysis helpers.
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import json
from pathlib import Path


def _minmax_normalize(series, higher_is_better=True):
    """Min-max normalize a pandas Series to 0-100. If the column is constant,
    return 50 for all values to avoid division by zero.
    """
    if series.isnull().all():
        return pd.Series(50, index=series.index)
    s = series.astype(float)
    mn = s.min()
    mx = s.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
        return pd.Series(50, index=s.index)
    norm = (s - mn) / (mx - mn) * 100
    if not higher_is_better:
        norm = 100 - norm
    return norm


def compute_env_condition_metric(df, row, env_component_weights=None):
    """
    Compute a single environment-conditions metric (0-100) per row combining:
      - energy ratio (derived from Renewable_Energy_Pct when non-renewable not present)
      - water indicator (column names: 'Water', 'Water_Score', 'Water_Availability', prefer higher better)
      - air indicator (column name 'Air_ug_m3' or 'Air' or 'Air_Quality'; lower is better)
      - carbon emissions (column 'Carbon_Emissions' in metric million tonnes; lower is better)

    If specific columns are missing, they are skipped and weights re-normalized.
    """
    # sensible default subweights
    default_weights = {'energy': 0.4, 'water': 0.2, 'air': 0.2, 'carbon': 0.2}
    weights = default_weights if env_component_weights is None else env_component_weights.copy()

    # Collect available components and their normalized values
    components = {}

    # Energy ratio: try to use Renewable_Energy_Pct and optionally NonRenewable_Energy_Pct
    if 'Renewable_Energy_Pct' in df.columns:
        ren_norm = _minmax_normalize(df['Renewable_Energy_Pct'], higher_is_better=True)
        components['energy'] = ren_norm.loc[row.name]

    # Water: prefer plausible column names
    water_cols = [c for c in df.columns if c.lower().startswith('water')]
    if water_cols:
        wc = water_cols[0]
        components['water'] = _minmax_normalize(df[wc], higher_is_better=True).loc[row.name]

    # Air quality: lower ug/m3 is better
    air_cols = [c for c in df.columns if 'air' in c.lower() or 'pm2' in c.lower() or 'pm10' in c.lower()]
    if air_cols:
        ac = air_cols[0]
        components['air'] = _minmax_normalize(df[ac], higher_is_better=False).loc[row.name]

    # Carbon emissions: lower is better
    carbon_cols = [c for c in df.columns if 'carbon' in c.lower() or 'emissions' in c.lower()]
    if carbon_cols:
        cc = carbon_cols[0]
        components['carbon'] = _minmax_normalize(df[cc], higher_is_better=False).loc[row.name]

    # Re-normalize weights to available components
    present = [k for k in weights.keys() if k in components]
    if not present:
        return 50.0
    total_w = sum(weights[k] for k in present)
    score = 0.0
    for k in present:
        w = weights[k] / total_w
        score += components[k] * w

    return float(np.round(score, 2))


def _load_rubric(path=None):
    """Load a JSON rubric mapping categorical values to numeric scores.

    The rubric file is optional. If `path` is None or the file is missing/malformed
    the function returns an empty dict and the caller should fall back to built-in
    defaults.
    """
    if path is None:
        path = Path.cwd() / 'config' / 'rubric.json'
    else:
        path = Path(path)

    if not path.exists():
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _map_with_rubric(value, rubric_map):
    """Map a categorical value to a numeric score using a rubric map.

    The rubric_map is expected to be a dict mapping lowercase keys to numeric
    scores, and may contain a special key 'default' to return if nothing matches.
    Matching is case-insensitive and uses substring containment to allow flexible
    labels (e.g. 'Gold Certified' -> matches 'gold'). If rubric_map is empty,
    return None to indicate no mapping was applied.
    """
    if not rubric_map or value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value).lower()
    # exact key match first
    for k, v in rubric_map.items():
        if k == 'default':
            continue
        if k == s:
            return v
    # substring match
    for k, v in rubric_map.items():
        if k == 'default':
            continue
        if k in s:
            return v
    # fallback to provided default in rubric
    if 'default' in rubric_map:
        return rubric_map['default']
    return None


def calculate_sustainability_scores(df, user_weights=None, env_component_weights=None, env_overall_weight=0.4, rubric_path=None):
    """
    Calculate sustainability scores for the DataFrame `df`.

    Parameters
    - user_weights: dict mapping variable names to importance weight (these will be re-normalized).
    - env_component_weights: subweights for energy/water/air/carbon within the environment composite
    - env_overall_weight: how much of overall score is contributed by the environment composite (0-1)

    Returns df with added columns: 'Env_Conditions', 'Raw_Score', 'Sustainability_Z', 'Sustainability_Z_Scaled'
    """
    df = df.copy()

    # Default weights for variables (before normalization). These are relative importances.
    default_weights = {
        'Times_Hosted': 0.05,
        'Last_Hosted_Year': 0.02,
        'Stadium_Type': 0.08,
        'Stadium_leed_cert': 0.05,
        'Waste_Management': 0.03,
        'Future_Developments': 0.03,
        'Avg_Feb_Temp_F': 0.05,
        'Alltransit_Score': 0.15,
        'Renewable_Energy_Pct': 0.10,
        'Waste_Diversion_Pct': 0.10,
        'Green_Legacy_Projects': 0.10,
        'Carbon_Offset_Programs': 0.05,
        # 'Env_Conditions' will be added and set to env_overall_weight
        'Env_Conditions': 0.25
    }

    # Allow user override
    if user_weights:
        for k, v in user_weights.items():
            default_weights[k] = v

    # Make sure Env_Conditions gets the env_overall_weight (user can still override)
    default_weights['Env_Conditions'] = env_overall_weight

    # Normalize default_weights so they sum to 1
    total = sum(default_weights.values())
    for k in default_weights:
        default_weights[k] = default_weights[k] / total

    # Compute environment composite for each row
    df['Env_Conditions'] = df.apply(lambda r: compute_env_condition_metric(df, r, env_component_weights), axis=1)

    # Load rubric (optional JSON file) to map categorical labels -> numeric scores
    rubric = _load_rubric(rubric_path)

    # Prepare normalized columns dictionary (0-100), handle existence flexibly
    norm_cols = {}
    col_map = {
        'Times_Hosted': ('Times_Hosted', True),
        'Last_Hosted_Year': ('Last_Hosted_Year', True),
        'Avg_Feb_Temp_F': ('Avg_Feb_Temp_F', False),  # milder temps in Feb often preferable (assumption)
        'Alltransit_Score': ('Alltransit_Score', True),
        'Renewable_Energy_Pct': ('Renewable_Energy_Pct', True),
        'Waste_Diversion_Pct': ('Waste_Diversion_Pct', True),
        'Green_Legacy_Projects': ('Green_Legacy_Projects', True),
        'Carbon_Offset_Programs': ('Carbon_Offset_Programs', True)
    }

    for key, (col, hi_better) in col_map.items():
        if col in df.columns:
            norm_cols[key] = _minmax_normalize(df[col], higher_is_better=hi_better)
        else:
            # If column missing, create a neutral 50 series
            norm_cols[key] = pd.Series(50, index=df.index)

    # Stadium type scoring (categorical) - try rubric first, then fallback heuristic
    if 'Stadium_Type' in df.columns:
        stadium_rub = {k.lower(): v for k, v in rubric.get('Stadium_Type', {}).items()} if rubric else {}
        def _stad_map(v):
            m = _map_with_rubric(v, stadium_rub)
            if m is not None:
                return m
            s = str(v).lower()
            return 100 if s in ['dome', 'retractable roof', 'retractable'] else 50
        stadium_scores = df['Stadium_Type'].apply(_stad_map)
    else:
        stadium_scores = pd.Series(50, index=df.index)

    # Stadium leed cert mapping: prefer rubric, else use built-in mapping
    if 'Stadium_leed_cert' in df.columns:
        leed_rub = {k.lower(): v for k, v in rubric.get('Stadium_leed_cert', {}).items()} if rubric else {}
        def _map_leed(x):
            m = _map_with_rubric(x, leed_rub)
            if m is not None:
                return m
            if pd.isna(x):
                return 0
            s = str(x).lower()
            if 'platinum' in s:
                return 100
            if 'gold' in s:
                return 80
            if 'silver' in s:
                return 60
            if 'certified' in s:
                return 50
            return 30
        leed_scores = df['Stadium_leed_cert'].apply(_map_leed)
    else:
        leed_scores = pd.Series(50, index=df.index)

    # Waste management (qualitative) - map using rubric if present, else neutral
    if 'Waste_Management' in df.columns:
        waste_rub = {k.lower(): v for k, v in rubric.get('Waste_Management', {}).items()} if rubric else {}
        def _map_waste(x):
            m = _map_with_rubric(x, waste_rub)
            if m is not None:
                return m
            return 50
        waste_scores = df['Waste_Management'].apply(_map_waste)
    else:
        waste_scores = pd.Series(50, index=df.index)

    # Future developments (qualitative) - map using rubric if present, else neutral
    if 'Future_Developments' in df.columns:
        future_rub = {k.lower(): v for k, v in rubric.get('Future_Developments', {}).items()} if rubric else {}
        def _map_future(x):
            m = _map_with_rubric(x, future_rub)
            if m is not None:
                return m
            return 50
        future_scores = df['Future_Developments'].apply(_map_future)
    else:
        future_scores = pd.Series(50, index=df.index)

    # Assemble raw score per row
    raw_scores = []
    for idx in df.index:
        s = 0.0
        # Stadium type
        s += default_weights.get('Stadium_Type', 0) * stadium_scores.loc[idx]
        # Stadium leed
        s += default_weights.get('Stadium_leed_cert', 0) * leed_scores.loc[idx]
        # Waste management
        s += default_weights.get('Waste_Management', 0) * waste_scores.loc[idx]
        # Future developments
        s += default_weights.get('Future_Developments', 0) * future_scores.loc[idx]

        # Numeric normalized fields
        for key in ['Times_Hosted', 'Last_Hosted_Year', 'Avg_Feb_Temp_F', 'Alltransit_Score',
                    'Renewable_Energy_Pct', 'Waste_Diversion_Pct', 'Green_Legacy_Projects', 'Carbon_Offset_Programs']:
            s += default_weights.get(key, 0) * norm_cols[key].loc[idx]

        # Env composite
        s += default_weights.get('Env_Conditions', 0) * df.loc[idx, 'Env_Conditions']

        raw_scores.append(s)

    df['Raw_Score'] = np.round(raw_scores, 3)

    # Z-score normalization across Raw_Score
    mean = df['Raw_Score'].mean()
    std = df['Raw_Score'].std()
    if std == 0 or np.isnan(std):
        df['Sustainability_Z'] = 0.0
    else:
        df['Sustainability_Z'] = (df['Raw_Score'] - mean) / std

    # Optional scaled Z (mean 50, sd 10) for easier human interpretation
    df['Sustainability_Z_Scaled'] = df['Sustainability_Z'] * 10 + 50

    return df


def analyze_previous_hosts(df):
    """Analyze cities that have previously hosted Super Bowl using scaled Z score"""
    previous_hosts = ['Inglewood', 'Glendale', 'Las Vegas', 'New Orleans', 'Santa Clara', 'Atlanta']
    previous_hosts_df = df[df['City'].isin(previous_hosts)].copy()

    previous_hosts_ranked = previous_hosts_df.sort_values('Sustainability_Z_Scaled', ascending=False)

    print("=== PART 3a: PREVIOUS HOST CITIES RANKING (by scaled Z score) ===")
    print(previous_hosts_ranked[['City', 'State', 'Sustainability_Z_Scaled']])

    # Visualize previous hosts
    plt.figure(figsize=(10, 6))
    sns.barplot(data=previous_hosts_ranked, x='Sustainability_Z_Scaled', y='City')
    plt.title('Previous Super Bowl Host Cities Ranked by Sustainability (scaled Z)')
    plt.xlabel('Scaled Z Score (mean 50, sd 10)')
    plt.tight_layout()
    plt.show()

    return previous_hosts_ranked


def analyze_new_hosts(df):
    """Analyze cities that have never hosted Super Bowl using scaled Z score"""
    previous_host_cities = ['New Orleans', 'Miami', 'Los Angeles', 'Tampa', 'Phoenix',
                           'Glendale', 'Atlanta', 'Houston', 'San Diego', 'Santa Clara',
                           'Inglewood', 'Las Vegas']

    new_hosts_df = df[~df['City'].isin(previous_host_cities)].copy()
    new_hosts_ranked = new_hosts_df.sort_values('Sustainability_Z_Scaled', ascending=False)

    print("=== PART 3b: NEW POTENTIAL HOST CITIES RANKING (by scaled Z score) ===")
    print(new_hosts_ranked[['City', 'State', 'Sustainability_Z_Scaled']].head(10))

    # Visualize top new potential hosts
    plt.figure(figsize=(10, 6))
    top_new_hosts = new_hosts_ranked.head(8)
    sns.barplot(data=top_new_hosts, x='Sustainability_Z_Scaled', y='City')
    plt.title('Top New Potential Host Cities Ranked by Sustainability (scaled Z)')
    plt.xlabel('Scaled Z Score (mean 50, sd 10)')
    plt.tight_layout()
    plt.show()

    return new_hosts_ranked


def comprehensive_analysis(df):
    """Perform comprehensive analysis and create visualizations using the new columns"""

    # 1. Overall ranking of all cities by scaled Z
    all_cities_ranked = df.sort_values('Sustainability_Z_Scaled', ascending=False)

    print("=== COMPREHENSIVE RANKING OF ALL CITIES (by scaled Z) ===")
    print(all_cities_ranked[['City', 'State', 'Sustainability_Z_Scaled']].head(10))

    # 2. Correlation analysis: choose available numeric columns
    numeric_candidates = ['Raw_Score', 'Sustainability_Z', 'Sustainability_Z_Scaled', 'Avg_Feb_Temp_F',
                          'Alltransit_Score', 'Renewable_Energy_Pct', 'Waste_Diversion_Pct']
    available_numeric_cols = [c for c in numeric_candidates if c in df.columns]

    if len(available_numeric_cols) >= 2:
        plt.figure(figsize=(10, 8))
        correlation_matrix = df[available_numeric_cols].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, square=True)
        plt.title('Correlation Matrix of Sustainability Factors')
        plt.tight_layout()
        plt.show()

    # 3. Sustainability score distribution (use scaled Z)
    if 'Sustainability_Z_Scaled' in df.columns:
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.hist(df['Sustainability_Z_Scaled'], bins=15, alpha=0.7, edgecolor='black')
        plt.xlabel('Scaled Z Score')
        plt.ylabel('Frequency')
        plt.title('Distribution of Scaled Z Scores')

        plt.subplot(1, 2, 2)
        df.boxplot(column='Sustainability_Z_Scaled')
        plt.title('Box Plot of Scaled Z Scores')
        plt.tight_layout()
        plt.show()

    return all_cities_ranked


def save_analysis_results(df, previous_hosts_ranked, new_hosts_ranked, all_ranked):
    """Save all analysis results to CSV files (updated to new column names)"""

    df.to_csv('super_bowl_with_sustainability_scores.csv', index=False)
    previous_hosts_ranked.to_csv('previous_hosts_ranked.csv', index=False)
    new_hosts_ranked.to_csv('new_potential_hosts_ranked.csv', index=False)
    all_ranked.to_csv('all_cities_sustainability_ranked.csv', index=False)

    # Save summary statistics of relevant numeric columns
    summary_cols = [c for c in ['Raw_Score', 'Sustainability_Z_Scaled', 'Alltransit_Score', 'Renewable_Energy_Pct', 'Waste_Diversion_Pct'] if c in df.columns]
    if summary_cols:
        summary_stats = df[summary_cols].describe()
        summary_stats.to_csv('sustainability_metrics_summary.csv')

    print("Analysis results saved to CSV files:")
    print("- super_bowl_with_sustainability_scores.csv")
    print("- previous_hosts_ranked.csv")
    print("- new_potential_hosts_ranked.csv")
    print("- all_cities_sustainability_ranked.csv")
    print("- sustainability_metrics_summary.csv")


def expand_model_for_multisport(df, extra_weights=None):
    """
    Expand the sustainability model for multi-sport events by adjusting weights.
    This re-runs the calculate_sustainability_scores with modified user_weights.
    """
    # Example: increase weights for infrastructure & legacy projects
    base_override = {
        'Green_Legacy_Projects': 0.20,
        'Alltransit_Score': 0.25,
        'Renewable_Energy_Pct': 0.25,
        'Env_Conditions': 0.20
    }
    if extra_weights:
        base_override.update(extra_weights)

    multisport_df = calculate_sustainability_scores(df, user_weights=base_override, env_overall_weight=0.25)
    multisport_ranked = multisport_df.sort_values('Sustainability_Z_Scaled', ascending=False)

    print("=== MULTI-SPORT EVENT RANKING (by scaled Z) ===")
    print(multisport_ranked[['City', 'State', 'Sustainability_Z_Scaled']].head(10))

    comparison = multisport_df[['City', 'State', 'Sustainability_Z_Scaled']].head(10)
    print("\nTop comparison for multi-sport scenario:")
    print(comparison)

    return multisport_ranked
