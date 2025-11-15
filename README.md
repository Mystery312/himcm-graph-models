hiMCM sustainability scoring

This project provides a small scoring pipeline to evaluate city environmental sustainability for event hosting.

Quickstart

1. Install dependencies:

```bash
````markdown
hiMCM sustainability scoring

This project provides a small scoring pipeline to evaluate city environmental sustainability for event hosting.

Quickstart

1. Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the analysis (requires a CSV `super_bowl_sustainability_data.csv` in the project root):

```bash
python3 "himcm_graph_models.py"
```

3. To import core functions in another script or tests:

```python
from himcm.core import calculate_sustainability_scores

df = pd.read_csv('super_bowl_sustainability_data.csv')
df = calculate_sustainability_scores(df)
```

Custom weights example

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

Running tests

```bash
pytest -q
```

Files
- `himcm/core.py` — scoring and analysis functions.
- `himcm_graph_models.py` — thin script that loads CSV and runs analysis when executed as main.
- `tests/` — pytest unit tests and synthetic validation.

Colab (Google Colaboratory)
---------------------------

You can run this project easily on Google Colab. Below are two simple workflows: clone the repo in Colab, or upload files manually.

1) Clone the repository and run the script

```python
# In a Colab notebook cell — clone, install, and run
!git clone <YOUR_GITHUB_REPO_URL> himcm_repo
%cd himcm_repo
!pip install -r requirements.txt
!python3 himcm_graph_models.py
```

Replace `<YOUR_GITHUB_REPO_URL>` with your repository URL (e.g. `https://github.com/username/repo.git`). Make sure your CSV (e.g. `super_bowl_sustainability_data.csv`) is present in the repo root or upload it to the Colab session.

2) Upload dataset and run interactively

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

3) Mount Google Drive (optional)

If you'd like to persist outputs to Drive, mount it first:

```python
from google.colab import drive
drive.mount('/content/drive')
# then copy or save files under /content/drive/MyDrive/...
```

Notes
- If you use the rubric configuration (`config/rubric.json`), ensure it is present in the working directory or pass a path to `calculate_sustainability_scores(..., rubric_path='path/to/rubric.json')`.
- Colab sessions are ephemeral; mount Drive to keep outputs or download files from the session using `files.download()`.

Running tests in Colab
----------------------

If your local Python environment has conflicts (e.g., the Anaconda 3.13 parsing bug), you can run the test suite in a clean Colab environment using the included notebook `colab_run_tests.ipynb` or by running the commands below in a Colab cell.

Quick paste (single cell):

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

Or open `colab_run_tests.ipynb` (included in the repo) via Colab: File → Open notebook → GitHub → paste your repo URL and select `colab_run_tests.ipynb`.

This runs the tests in a fresh environment (no Anaconda/Python 3.13 issues) and saves the pytest output for download.

````
