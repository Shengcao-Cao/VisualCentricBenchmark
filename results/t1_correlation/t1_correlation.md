# Tier 1 Perception → Reasoning Correlation Analysis

## Research Question

Does a model's Tier 1 visual perception accuracy predict its downstream reasoning performance on the original problem and Tier 2 (pruned text)?

## Method

**Per-problem analysis (binned bar chart).**
For each (problem, model) pair, we compute the model's Tier 1 score—the fraction of perception sub-questions answered correctly—and bin it into three categories: ≤1/3, 2/3, and 3/3. Most problems have exactly 3 sub-questions (1,964 / 2,711); for items with more or fewer, the continuous average is mapped to the nearest bin. We then compute reasoning accuracy within each bin, pooling across all 10 models.

**Model-level analysis (scatter plot).**
For each model, we compute its mean Tier 1 accuracy (across all 2,710 problems) and its mean reasoning accuracy on the original problems (2,710 items) and Tier 2 pruned problems (1,035 items). We plot these 10 model-level points and report Pearson r and Spearman ρ. Models are distinguished by color and marker shape: circle/green = GPT, square/blue = Gemini, triangle/orange = Claude, plus/purple = Qwen, diamond/teal = Gemma, X/gray = Kimi.

## Data Sources

| Data | File | Items |
|------|------|-------|
| Tier 1 predictions | `data/*_tier1+2_clean_tier1_{slug}.json` | 2,710 per model |
| Original judgments | `data/*_hard_{slug}_judged.json` | 2,710 per model |
| Tier 2 judgments | `data/*_tier1+2_clean_tier2_{slug}_judged.json` | 1,035 per model |

**Models (10):** GPT-5.4, GPT-5.4 mini, Gemini 3.1 Pro, Gemini 3.1 Flash-Lite, Claude Opus 4.6, Claude Sonnet 4.6, Qwen3.5-397B-A17B, Qwen3-VL-235B-A22B, Gemma 4 31B, Kimi K2.5. (Nova 2 Lite excluded.)

## Outputs

### `t1_correlation_binned.{pdf,png}`

Two-panel bar chart. Left: original problem accuracy by perception score bin. Right: Tier 2 (pruned) accuracy by perception score bin. Each bar is labeled with accuracy (%) and sample count. Data is pooled across all 10 models.

**Key finding:** Both panels show a monotonic trend—higher perception scores correspond to higher reasoning accuracy.
- Original problem: 49.7% (≤1/3) → 53.9% (2/3) → 58.3% (3/3)
- Tier 2 (pruned): 45.2% (≤1/3) → 49.0% (2/3) → 56.0% (3/3)

The trend is steeper for Tier 2, consistent with image reliance being more critical when textual shortcuts are removed.

### `t1_correlation_scatter.{pdf,png}`

Two-panel scatter plot. Each dot is one model, identified by color and marker shape (see legend). Dashed gray line shows the linear fit. Panel subtitles report Pearson r and Spearman ρ.

**Key finding:** At the model level, perception and reasoning are positively correlated:
- Original problem: r = 0.65 (p = 0.042), ρ = 0.58 (p = 0.082)
- Tier 2 (pruned): r = 0.68 (p = 0.031), ρ = 0.59 (p = 0.074)

Qwen3-VL-235B-A22B is a notable outlier—high perception (92.2%) but low reasoning (29.5% original, 27.3% Tier 2).

## Per-Problem Correlation (Not Plotted)

Within any single model, Tier 1 score is essentially uncorrelated with reasoning correctness (|r| < 0.09 for all models). This is because most models score >90% on Tier 1 on average, leaving very little variance at the per-problem level. The predictive signal emerges only at the model level: models that perceive better also reason better, but knowing a specific model got 3/3 perception on a specific problem does not meaningfully predict whether it solves that problem.

## How to Reproduce

```bash
conda activate dataset
python results/analysis/t1_correlation.py
```
