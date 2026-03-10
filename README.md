# Coreset

A curated subset of 1,000 multimodal questions from 12 datasets, annotated with model-generated answers, correctness judgments, difficulty ratings, and image captions via an automated pipeline.

## Data

Download the data from [this link](https://drive.google.com/drive/folders/1I3-umV3ZuydBcH7Neyn1r88QyrdXG7y4?usp=sharing).

| File | Description |
|---|---|
| `all_data.json` | Full merged dataset from all source datasets |
| `all_figures/` | All referenced images (shared by all JSON files) |
| `sampled_1000.json` | Stratified sample of 1,000 questions with model annotations |
| `sampled_100.json` | Further subsampled 100 questions (harder questions prioritized) |

### Schema

Each item in the sampled JSON files:

```jsonc
{
  "id": "MathVerse-testmini-502",
  "dataset": "MathVerse",
  "split": "testmini",
  "question": "As shown in the figure... <image_1>",        // <image_N> = placeholder for Nth image
  "options": ["54°", "64°", "27°", "37°"],                  // null for free_form
  "answer": "C",                                            // string or list of strings
  "images": ["all_figures/MathVerse_testmini_502.png"],     // paths relative to this directory
  "question_type": "single_selection",                      // single_selection | multiple_selection | free_form
  "domain": "Math",
  "subdomain": "Geometry",
  "extra": { ... },                                         // dataset-specific metadata
  "model": {
    "gpt-5.4": {
      "answer": "Step 1: ... \\boxed{C}",                   // full solution with boxed final answer
      "judge": {"correct": true, "reasoning": "..."},       // correctness judgment
      "difficulty": {"difficulty": 3, "reasoning": "..."},  // 1-5 scale
      "captions": ["* The image shows ...\n* ..."]          // per-image factual captions
    }
  }
}
```

### Coverage

**Datasets** (12): EMMA, Geometry3k, HumanityLastExam, MME_Reasoning, MMMU, MathVerse, MathVision, MathVista, OlympiadBench, OlympicArena, PuzzleVQA, SUPERChem

**Domains**: Math (400), Physics (200), Chemistry (150), Puzzle (100), Computer Science (60), Biology (40), Geography (30), Engineering (20)

**Question types**: single_selection (526), free_form (471), multiple_selection (3)

## Pipeline

The evaluation pipeline runs four tasks, each adding a field under `question["model"]["<model_name>"]`:

| Task | Field | Description |
|---|---|---|
| `answer` | `["answer"]` | Full step-by-step solution with `\boxed{...}` final answer |
| `judge` | `["judge"]` | `{"correct": bool, "reasoning": str}` — correctness vs ground truth |
| `difficulty` | `["difficulty"]` | `{"difficulty": 1-5, "reasoning": str}` — calibrated difficulty rating |
| `caption` | `["captions"]` | List of per-image factual captions (one per image in the question) |

### Usage

Run individual tasks (chainable — output of one is input to the next):

```bash
python run_pipeline.py answer     -i sampled_1000.json -o sampled_1000.json --model-name gpt-5.4
python run_pipeline.py judge      -i sampled_1000.json -o sampled_1000.json --model-name gpt-5.4
python run_pipeline.py difficulty -i sampled_1000.json -o sampled_1000.json --model-name gpt-5.4
python run_pipeline.py caption    -i sampled_1000.json -o sampled_1000.json --model-name gpt-5.4
```

Or run all tasks at once (`answer → judge → difficulty → caption`):

```bash
python run_pipeline.py all -i sampled_1000.json -o sampled_1000.json --model-name gpt-5.4 --concurrency 50
```

**CLI arguments:**

| Argument | Description |
|---|---|
| `task` | `answer`, `judge`, `caption`, `difficulty`, or `all` |
| `-i` / `--input` | Input JSON path |
| `-o` / `--output` | Output JSON path |
| `--model-name` | Model name (API param + output key, e.g. `gpt-5.4`) |
| `--api-key` | API key (or set `OPENAI_API_KEY` env var) |
| `--base-url` | API base URL override |
| `--base-dir` | Base directory for image paths (default: input file's parent) |
| `--concurrency` | Max parallel requests (default: 10) |

### Code Structure

```
coreset/
├── run_pipeline.py      # CLI entry point
├── client.py            # VLMClient base class + OpenAIClient (extensible to Gemini, Claude)
├── utils.py             # Message building, image encoding, JSON I/O, async batch runner
├── tasks/
│   ├── answer.py        # Task 1: answer questions with full reasoning
│   ├── judge.py         # Task 2: judge correctness
│   ├── difficulty.py    # Task 3: rate difficulty (1-5)
│   └── caption.py       # Task 4: caption each image
├── merge.py             # Merge per-dataset JSONs → all_data.json + all_figures/
├── sample.py            # Stratified sampling: all_data.json → sampled_1000.json
└── sample_100.py        # Subsample: sampled_1000.json → sampled_100.json (harder questions first)
```
