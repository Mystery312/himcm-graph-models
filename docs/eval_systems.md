# Sustainability Score Evaluation System

## Overview

This document explains how the hiMCM sustainability scoring program evaluates and computes the final sustainability score for each city. The system uses a **modular, multi-step pipeline** that normalizes data, maps categorical variables, aggregates metrics, and standardizes outputs for easy interpretation.

---

## Step 1: Data Normalization (0–100 Scale)

All numeric variables are normalized to a **0–100 range** using min-max normalization to make different metrics comparable.

### Min-Max Normalization Formula

$$\text{Normalized Score} = \frac{\text{Value} - \text{Min}}{\text{Max} - \text{Min}} \times 100$$

Where:
- **Value** = the city's metric value
- **Min** = minimum value across all cities
- **Max** = maximum value across all cities

### Special Cases

- **Constant columns** (all values are identical): Default to a neutral score of **50**
- **Missing/empty columns**: Default to **50** if all values are missing
- **Inverse metrics**: For variables where *lower is better* (e.g., air pollution, carbon emissions), the score is inverted: `100 - normalized_score`

### Example

If renewable energy percentages range from 10% to 90% across cities:
- City with 10% → (10 - 10) / (90 - 10) × 100 = **0**
- City with 50% → (50 - 10) / (90 - 10) × 100 = **50**
- City with 90% → (90 - 10) / (90 - 10) × 100 = **100**

---

## Step 2: Categorical Mapping (via JSON Rubric)

Qualitative variables like stadium type, LEED certification, waste management programs, and future developments are converted to numeric scores using an **interactive JSON rubric**.

### Rubric File Structure

The rubric is stored in `config/rubric.json` and uses this structure:

```json
{
  "Stadium_Type": {
    "dome": 100,
    "open-air": 50,
    "retractable": 75,
    "default": 50
  },
  "Stadium_leed_cert": {
    "platinum": 100,
    "gold": 80,
    "silver": 60,
    "default": 30
  },
  "Waste_Management": {
    "comprehensive": 90,
    "basic": 40,
    "default": 30
  },
  "Future_Developments": {
    "green_infrastructure": 85,
    "renewable_energy_expansion": 80,
    "default": 40
  }
}
```

### Matching Strategy

The program uses **case-insensitive substring matching**:
- "LEED Platinum" matches "platinum" → 100
- "leed gold certified" matches "gold" → 80
- "Platinum Certification" matches "platinum" → 100
- Unknown values fall back to the `"default"` entry

### Example Mappings

| Input Value | Matched Key | Score |
|-------------|-------------|-------|
| LEED Platinum | platinum | 100 |
| LEED Gold | gold | 80 |
| LEED Silver | silver | 60 |
| Not Certified | (no match) | 30 (default) |
| Dome Stadium | dome | 100 |
| Open-Air Stadium | open-air | 50 |

---

## Step 3: Environment Composite Metric

The program creates a single **Environment Conditions score** by combining four environmental sub-metrics into a weighted average.

### Sub-Metrics and Weights

| Component | Variable(s) | Default Weight | Description |
|-----------|-------------|-----------------|-------------|
| **Energy** | `Renewable_Energy_Pct` | 40% | Percentage of energy from renewable sources |
| **Water** | `Water_Score` (if available) | 20% | Water quality or conservation score |
| **Air** | `Air_ug_m3` (inverted) | 20% | Air pollution level (µg/m³); lower is better |
| **Carbon** | `Carbon_Emissions` (inverted) | 20% | Carbon emissions; lower is better |

### Calculation

$$\text{Env\_Conditions} = \frac{40\% \times \text{Energy} + 20\% \times \text{Water} + 20\% \times \text{Air} + 20\% \times \text{Carbon}}{100}$$

**Note**: If a component is missing, its weight is redistributed proportionally to available components.

### Example

If a city has:
- Renewable Energy: 65/100
- Water Score: 70/100
- Air Quality: 60/100
- Carbon: 55/100

$$\text{Env\_Conditions} = \frac{0.40 \times 65 + 0.20 \times 70 + 0.20 \times 60 + 0.20 \times 55}{100} = \frac{26 + 14 + 12 + 11}{100} = \frac{63}{100} = 63$$

---

## Step 4: Weighted Score Aggregation

The program combines all normalized factors and the environment composite into a **Raw_Score** using a **flexible weighting system**.

### Default Weights

| Factor | Default Weight |
|--------|-----------------|
| `Env_Conditions` (composite) | 40% |
| `Alltransit_Score` | 15% |
| `Renewable_Energy_Pct` | 15% |
| `Waste_Diversion_Pct` | 15% |
| `Green_Legacy_Projects` | 15% |

### Raw Score Formula

$$\text{Raw\_Score} = \sum (\text{Weight}_i \times \text{Normalized\_Score}_i)$$

### Custom Weights

Users can override default weights without editing code:

```python
user_weights = {
    'Alltransit_Score': 0.25,        # Increase from 15% to 25%
    'Env_Conditions': 0.35,          # Decrease from 40% to 35%
    'Renewable_Energy_Pct': 0.15,
    'Waste_Diversion_Pct': 0.10,     # Decrease from 15% to 10%
    'Green_Legacy_Projects': 0.15
}

df = calculate_sustainability_scores(df, user_weights=user_weights)
```

**Automatic Normalization**: The program automatically re-normalizes custom weights so they sum to 1.0.

### Example Calculation

Given a city with normalized scores:
- Env_Conditions: 63/100
- Alltransit_Score: 75/100
- Renewable_Energy_Pct: 65/100
- Waste_Diversion_Pct: 70/100
- Green_Legacy_Projects: 55/100

Using **default weights**:

$$\text{Raw\_Score} = 0.40 \times 63 + 0.15 \times 75 + 0.15 \times 65 + 0.15 \times 70 + 0.15 \times 55$$
$$= 25.2 + 11.25 + 9.75 + 10.5 + 8.25 = 64.95 \approx 65.0$$

---

## Step 5: Z-Score Standardization

The raw score is converted to a **Z-score**, which measures how many standard deviations a city's score is from the mean.

### Z-Score Formula

$$z = \frac{\text{Raw\_Score} - \text{Mean(Raw\_Scores)}}{\text{Standard\_Deviation(Raw\_Scores)}}$$

### Interpretation

- **z = 0**: City is at the average sustainability level
- **z > 0**: City is above average (more sustainable)
- **z < 0**: City is below average (less sustainable)
- **z = 1**: City is one standard deviation above average (very sustainable)
- **z = −1**: City is one standard deviation below average (not very sustainable)

### Example

If the dataset has:
- Mean raw score: 60
- Standard deviation: 8

For a city with raw score 65:

$$z = \frac{65 - 60}{8} = \frac{5}{8} = 0.625$$

This city is **0.625 standard deviations above the mean**.

---

## Step 6: Scaled Z-Score (User-Friendly Output)

The Z-score is scaled to a **0–100 range** centered around 50 for easier interpretation.

### Scaling Formula

$$\text{Sustainability\_Z\_Scaled} = 50 + (z \times 10)$$

### Interpretation Scale

| Scaled Score | Z-Score Range | Interpretation |
|-------------|---------------|----|
| **70+** | z > +2 | Exceptional sustainability |
| **60–70** | z = +1 to +2 | Above average |
| **50–60** | z = 0 to +1 | Average |
| **40–50** | z = −1 to 0 | Below average |
| **<40** | z < −1 | Poor sustainability |

### Example

From the previous example:
- Raw score: 65
- Z-score: 0.625

$$\text{Sustainability\_Z\_Scaled} = 50 + (0.625 \times 10) = 50 + 6.25 = 56.25$$

This city scores **56.25**, which is **slightly above average** (between 50 and 60).

---

## Step 7: City Segmentation

The program splits cities into two groups based on their **`Times_Hosted`** value for separate analysis and visualization.

### Groups

| Group | Condition | Purpose |
|-------|-----------|---------|
| **Previous Hosts** | `Times_Hosted > 0` | Cities that have previously hosted the event; used for benchmarking and repeat-host suitability |
| **Future Candidates** | `Times_Hosted = 0` | Cities that have never hosted; used for identifying promising new venues |

### Separate Analysis

Each group's scores are analyzed independently:
- Summary statistics (mean, median, std dev, min, max)
- Correlation analysis
- Visualizations

---

## Step 8: Visualization and Ranking

The program creates two **bar charts** (one for each city group) showing cities ranked by their `Sustainability_Z_Scaled` scores.

### Previous Hosts Chart

- **File**: `previous_hosts_sustainability.png`
- **Colors**: Coolwarm palette (blue = lower scores, red = higher scores)
- **Order**: Sorted by `Sustainability_Z_Scaled` (highest to lowest)
- **Use**: Compare sustainability improvements over time or across repeat venues

### Future Candidates Chart

- **File**: `future_hosts_sustainability.png`
- **Colors**: Viridis palette (purple = lower scores, yellow = higher scores)
- **Order**: Sorted by `Sustainability_Z_Scaled` (highest to lowest)
- **Use**: Identify the most sustainable new cities for event hosting

---

## Step 9: Results Export

The program exports results in multiple formats for further analysis and decision-making.

### Output Files

- **CSV with all scores**: Original data + `Raw_Score`, `Sustainability_Z`, `Sustainability_Z_Scaled` columns
- **Previous hosts analysis CSV**: Filtered and summarized for repeat venues
- **Future candidates analysis CSV**: Filtered and summarized for new venues
- **PNG visualizations**: Two bar charts (see Step 8)

---

## Complete Example Walkthrough

### Input Data (Single City)

| Field | Value |
|-------|-------|
| City | Springfield |
| Times_Hosted | 0 |
| Avg_Feb_Temp_F | 45 |
| Alltransit_Score | 72 |
| Renewable_Energy_Pct | 35 |
| Waste_Diversion_Pct | 55 |
| Green_Legacy_Projects | 2 |
| Stadium_Type | Dome |
| Stadium_leed_cert | Gold |
| Water_Score | 60 |
| Air_ug_m3 | 25 |
| Carbon_Emissions | 2.5 |

### Processing Steps

**Step 1: Normalization**
- Alltransit_Score: 72 → 72/100 (assuming 0–100 range) = **72**
- Renewable_Energy_Pct: 35 → **35**
- Waste_Diversion_Pct: 55 → **55**
- Green_Legacy_Projects: 2 → (assuming 0–5 range) → (2−0)/(5−0) × 100 = **40**

**Step 2: Categorical Mapping**
- Stadium_Type (Dome) → **100**
- Stadium_leed_cert (Gold) → **80**

**Step 3: Environment Composite**
- Energy (Renewable 35) → **35**
- Water → **60**
- Air (25 µg/m³, inverted) → **75** (assuming 0–50 range, lower is better)
- Carbon (2.5 MT, inverted) → **60** (assuming 0–5 range)
- Env_Conditions = (0.4×35 + 0.2×60 + 0.2×75 + 0.2×60) / 100 = **56**

**Step 4: Raw Score Aggregation**
$$\text{Raw\_Score} = 0.40 \times 56 + 0.15 \times 72 + 0.15 \times 35 + 0.15 \times 55 + 0.15 \times 40$$
$$= 22.4 + 10.8 + 5.25 + 8.25 + 6.0 = 52.7$$

**Step 5–6: Standardization & Scaling**
- Assume dataset mean = 58, std dev = 9
- Z-score = (52.7 − 58) / 9 = **−0.59**
- Scaled Z = 50 + (−0.59 × 10) = **44.1**

**Step 7: Segmentation**
- Times_Hosted = 0 → **Future Candidate** group

### Output

| Field | Value |
|-------|-------|
| Raw_Score | 52.7 |
| Sustainability_Z | −0.59 |
| Sustainability_Z_Scaled | 44.1 |
| Group | Future Candidate |

**Interpretation**: Springfield is a **future candidate** with **below-average sustainability** (44.1 < 50). It would benefit from improving renewable energy capacity and environmental quality before hosting.

---

## Key Insights

1. **Flexibility**: Users can adjust weights to match their priorities without code changes.
2. **Transparency**: Each score breaks down into interpretable components (raw, z, scaled).
3. **Comparability**: Z-score standardization allows fair comparison across different metrics and datasets.
4. **Segmentation**: Separating previous hosts from future candidates enables targeted analysis.
5. **Accessibility**: The scaled Z-score (0–100, centered at 50) is intuitive for non-technical stakeholders.

---

## Configuration

To customize the evaluation:

1. **Change category mappings**: Edit `config/rubric.json`
2. **Adjust factor weights**: Pass `user_weights` parameter to `calculate_sustainability_scores()`
3. **Modify environment sub-weights**: Pass `env_component_weights` parameter
4. **Change overall environment importance**: Pass `env_overall_weight` parameter

All changes take effect without modifying source code.
