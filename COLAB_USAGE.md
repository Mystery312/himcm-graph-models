# How to Use the Colab Notebook

The corrupted notebook has been fixed and pushed to GitHub. Here's how to use it in Google Colab:

## Option 1: Open from GitHub (Recommended)

1. Go to https://colab.research.google.com
2. Click **File** → **Open notebook** → **GitHub**
3. Paste your repo URL: `https://github.com/Mystery312/himcm-graph-models`
4. Select `colab_demo_edit_rubric.ipynb` from the dropdown
5. Click the notebook to open it

## Option 2: Clone and Run

In a Colab cell, run:

```python
!git clone https://github.com/Mystery312/himcm-graph-models.git
%cd himcm-graph-models
```

Then run the remaining cells in order.

## What the Notebook Does

The notebook demonstrates a simple workflow:

1. **Setup**: Install dependencies and check/create `config/rubric.json`
2. **Score Before**: Run `calculate_sustainability_scores()` on synthetic data
3. **Edit Rubric**: Change gold certification score (80 → 40)
4. **Score After**: Re-run scoring and show the difference

Each cell is independent and the notebook is Colab-optimized.

## Troubleshooting

If you get "Unable to read file" error:
- Make sure you're using the latest version of the notebook from GitHub
- Clear your browser cache and try again
- Try opening in an incognito/private tab

The notebook is now **valid JSON** and should load without errors.
