Rubric (config/rubric.json)
============================

This project supports a JSON rubric file to map textual/categorical values to numeric scores.

Location

- `config/rubric.json` (default)

Usage

- Edit `config/rubric.json` to change how categorical fields are converted into numeric scores.
- Alternatively pass a custom path to `calculate_sustainability_scores(..., rubric_path='path/to/rubric.json')`.

Supported keys

- `Stadium_Type` — stadium types (e.g. "dome", "retractable roof", "open-air").
- `Stadium_leed_cert` — LEED certification levels ("platinum", "gold", "silver", "certified").
- `Waste_Management` — qualitative descriptions of waste programs.
- `Future_Developments` — planned green investments or future sustainability projects.

Format

Each key maps to an object where keys are lowercase snippets to match against the column value (matching is case-insensitive and substring-based). Include a `default` key to return when nothing matches.

Example

```
{
  "Stadium_Type": {"dome": 100, "open-air": 50, "default": 50},
  "Stadium_leed_cert": {"platinum": 100, "gold": 80, "default": 30}
}
```

Notes

- Matching is flexible: if the rubric contains the key `"gold"`, values like `"Gold Certified"` will match.
- If the rubric file is missing or malformed, the code will fall back to built-in heuristics and neutral defaults.
