# hiMCM Sustainability Scoring

This project provides a modular scoring pipeline to evaluate city environmental sustainability for event hosting.

## Quickstart

1. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the analysis (requires a CSV `super_bowl_sustainability_data.csv` in the project root):

```bash
python3 himcm_graph_models.py
```

3. To import core functions in another script or tests:

```python
from himcm.core import calculate_sustainability_scores

df = pd.read_csv('super_bowl_sustainability_data.csv')
df = calculate_sustainability_scores(df)
```

## Custom Weights Example

```python
user_weights = {
    'Alltransit_Score': 0.25,
    'Env_Conditions': 0.35,
    'Renewable_Energy_Pct': 0.15,
    'Waste_Diversion_Pct': 0.10,
    'Green_Legacy_Projects': 0.15
}

df = calculate_sustainability_scores(df, user_weights=user_weights, env_overall_weight=0.35)
```

## Running Tests

```bash
pytest -q
```

## Files

- `himcm/core.py` — scoring and analysis functions.
- `himcm_graph_models.py` — thin script that loads CSV and runs analysis when executed as main.
- `tests/` — pytest unit tests and synthetic validation.
- `config/rubric.json` — interactive configuration for categorical variable mappings.
- `docs/RUBRIC.md` — rubric file format documentation.
- `docs/eval_systems.md` — detailed explanation of the sustainability score evaluation system.
- `examples/sample_super_bowl.csv` — sample data for testing.

## Colab (Google Colaboratory)

You can run this project easily on Google Colab. Below are two simple workflows: clone the repo in Colab, or upload files manually.

### 1) Clone the Repository and Run

```python
# In a Colab notebook cell — clone, install, and run
!git clone https://github.com/YOUR_USERNAME/himcm-graph-models.git himcm_repo
%cd himcm_repo
!pip install -r requirements.txt
!python3 himcm_graph_models.py
```

Replace `https://github.com/YOUR_USERNAME/himcm-graph-models.git` with your repository URL. Ensure your CSV (e.g., `super_bowl_sustainability_data.csv`) is in the repo root or upload it to Colab.

### 2) Upload Dataset and Run Interactively

```python
# In Colab: upload a file interactively
from google.colab import files
uploaded = files.upload()  # choose your CSV

import io, pandas as pd
df = pd.read_csv(io.BytesIO(next(iter(uploaded.values()))))

# Use the core functions directly
from himcm.core import calculate_sustainability_scores
df_out = calculate_sustainability_scores(df)
df_out.head()
```

### 3) Mount Google Drive (Optional)

If you'd like to persist outputs to Drive, mount it first:

```python
from google.colab import drive
drive.mount('/content/drive')
# then copy or save files under /content/drive/MyDrive/...
```

### Notes

- If you use the rubric configuration (`config/rubric.json`), ensure it is present in the working directory or pass a path: `calculate_sustainability_scores(..., rubric_path='path/to/rubric.json')`.
- Colab sessions are ephemeral; mount Drive to keep outputs or download files using `files.download()`.

## Running Tests in Colab

If your local Python environment has conflicts (e.g., Anaconda 3.13 parsing bug), run the test suite in a clean Colab environment.

### Quick Paste (Single Cell)

```python
%env MPLBACKEND=Agg
!git clone https://github.com/YOUR_USERNAME/himcm-graph-models.git repo || true
%cd repo
!pip install -q -r requirements.txt
!pip install -q pytest
!pytest -q --maxfail=1 | tee pytest_output.txt
from google.colab import files
files.download('pytest_output.txt')
```

Or open `colab_run_tests.ipynb` (in the repo) via Colab: **File → Open notebook → GitHub → paste your repo URL → select `colab_run_tests.ipynb`**.

This runs tests in a fresh environment and saves pytest output for download.

## Rubric Configuration

The project uses an interactive JSON rubric (`config/rubric.json`) to map categorical variables (e.g., stadium type, LEED certification) to numeric scores without editing code.

**Example rubric snippet:**

```json
{
  "Stadium_Type": {
    "dome": 100,
    "open-air": 50,
    "default": 50
  },
  "Stadium_leed_cert": {
    "platinum": 100,
    "gold": 80,
    "silver": 60,
    "default": 30
  }
}
```

Edit `config/rubric.json` to change category→score mappings, then re-run the analysis. For more details, see `docs/RUBRIC.md`.

---

## Program Summary (Plain English)

**What does this program do?** It helps event organizers (like Super Bowl organizers) choose which city is best for hosting a major event based on how **sustainable** that city is. Sustainability means being friendly to the environment—having clean air, renewable energy, good public transportation, and waste reduction programs.

**How does it work? (Step by step)**

1. **Load the data**: You provide a spreadsheet (CSV file) with information about different cities (e.g., temperature, renewable energy %, public transit scores, waste recycling percentage).

2. **Clean the data**: The program verifies that all numbers are valid and in the correct format.

3. **Measure individual factors**: For each city, the program measures how good it is in each area (e.g., renewable energy %, waste diversion %, public transit score, etc.). All scores are scaled to a 0–100 range so they're easy to compare.

4. **Calculate environment health**: The program combines energy, water quality, air quality, and carbon emissions into a single "environment score" for each city (0–100).

5. **Create a final score**: The program combines all measurements—environment, transit, renewable energy, waste management, green projects, etc.—into one final **sustainability score** for each city. You can adjust how important each factor is (weighting system).

6. **Standardize the score**: The final score is converted to a **Z-score** (a statistical measure) and then scaled to be centered around 50, making scores easier to understand and compare.

7. **Split cities into groups**: The program separates cities into two groups:
   - **Previous hosts**: Cities that have hosted the event before (Times_Hosted > 0)
   - **Future candidates**: Cities that have never hosted (Times_Hosted = 0)

8. **Rank and visualize**: The program creates two colored bar charts:
   - One showing previous hosts ranked by sustainability (coolwarm colors)
   - One showing future candidates ranked by sustainability (viridis colors)
   - These images are saved as PNG files.

9. **Save the results**: The program exports results to CSV files and spreadsheets for review, sharing, or further analysis.

**Key features:**

- **Flexible weighting**: Decide how important each factor is. For example, if renewable energy is critical, give it more weight than waste management.
- **Interactive rubric**: Edit a simple JSON file (`config/rubric.json`) to change how categories (like "LEED platinum" or "dome stadium") map to scores. No Python coding needed.
- **Z-score standardization**: Scores are automatically converted to a standard scale (mean 50, standard deviation 10) so they're comparable across metrics.
- **Two visualization modes**: Separate charts for previous hosts vs. future candidates help you spot patterns in each group.
- **Colab-ready**: Run the entire analysis in Google Colab for free, no local installation required.

**Sample input (CSV):**

| City | Times_Hosted | Renewable_Energy_Pct | Alltransit_Score | Waste_Diversion_Pct | Stadium_Type |
|------|--------------|----------------------|------------------|---------------------|--------------|
| City A | 2 | 45 | 75 | 60 | Dome |
| City B | 0 | 30 | 50 | 40 | Open-Air |
| City C | 1 | 80 | 90 | 75 | Dome |

**Sample output (added columns to CSV):**

| City | Raw_Score | Sustainability_Z | Sustainability_Z_Scaled |
|------|-----------|------------------|-------------------------|
| City A | 62.5 | 0.50 | 55.0 |
| City B | 42.0 | −1.20 | 38.0 |
| City C | 78.5 | 1.80 | 68.0 |

**Who is this for?**

- **Event organizers** (Super Bowl, Olympics, etc.) who want to make data-driven decisions about host cities.
- **Urban planners** who want to benchmark their city's sustainability.
- **Sustainability researchers** who want to score and compare multiple locations.
- **Non-technical managers** who can edit the rubric JSON and re-run the program without writing code.

**Getting started:**

1. Prepare a CSV file with your city data (see `examples/sample_super_bowl.csv` for a template).
2. Place it in the project folder or upload to Google Colab.
3. Run `python3 himcm_graph_models.py` (or run in Colab).
4. Check the output PNG charts and CSV files.
5. To tune weights or category mappings, edit `config/rubric.json` or pass custom weights to the function—no code changes needed.
