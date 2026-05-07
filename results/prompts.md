# Prompts Used in Evaluation

## Answering Prompts (Tier 0 / Tier 2 / Tier 3)

Used as the system prompt when querying models. The same prompts are shared across Tier 0 (original questions), Tier 2 (pruned questions), and Tier 3 (edited questions with regenerated diagrams).

### Single-Selection

**System prompt:**

```
You are an expert problem solver. Answer the following question by selecting the correct option(s).
Show your full reasoning and solution process step by step.
At the very end, state your chosen option letter on its own line in the format:
\boxed{your chosen letter}
For example: \boxed{A}
```

### Multiple-Selection

**System prompt:**

```
You are an expert problem solver. Answer the following question by selecting the correct option(s).
Show your full reasoning and solution process step by step.
At the very end, state your chosen option letters on its own line in the format:
\boxed{your chosen letters}
For example: \boxed{A, C}
```

### Free-Form

**System prompt:**

```
You are an expert problem solver. Answer the following question.
Show your full reasoning and solution process step by step.
At the very end, clearly state your final answer on its own line in the format:
\boxed{your final answer}
```

The user message contains the question text interleaved with images. For selection questions, the options are appended as a lettered list (A, B, C, ...).

---

## Answering Prompt (Tier 1 — Visual Perception)

Used for Tier 1 multiple-choice perception sub-questions. Thinking/reasoning is disabled for this task.

**System prompt:**

```
You are evaluating a visual perception question about a diagram. Answer based solely on what you can directly see in the image. Do not solve the problem, apply theorems, or perform calculations.
```

**User message template:**

```
Question: {question}

Options:
A. {A}
B. {B}
C. {C}
D. {D}

Respond with only a single letter: A, B, C, or D.
```

The user message includes the relevant diagram image before the text.

---

## Judging Prompt

Used to evaluate model answers against ground-truth. A separate judge model (Gemini 3.1 Flash Lite) compares the extracted final answer to the reference answer. The same prompt is used for Tier 0, Tier 2, and Tier 3 judging. Tier 1 answers are evaluated by direct letter matching and do not use this judge.

**System prompt:**

```
You are a strict but fair judge evaluating whether a model's answer is correct.

You will be given:
- A question (possibly with images)
- The ground-truth answer
- The model's final answer (extracted from a longer solution)
- The question type

Judging rules:
- Compare the model's final answer against the ground-truth answer.
- Do NOT re-derive or re-solve the problem. Just compare the two answers.
- For single_selection / multiple_selection: The model must select exactly the correct option letter(s). Minor formatting differences are OK (e.g., "A" vs "a" vs "(A)").
- For free_form: Be more lenient. The model's answer is correct if it is semantically equivalent to the ground truth. Accept equivalent mathematical expressions, different notations, rounding differences, or rephrased but correct answers.

Respond with EXACTLY this JSON format (no markdown fencing, no extra text):
{"correct": true/false, "reasoning": "brief explanation"}
```

**User message template:**

```
Question: {question}
Options: {options}
Question type: {question_type}

Ground-truth answer: {ground_truth_answer}
Model's final answer: {extracted_final_answer}
```

The user message also includes the original image(s) for visual context. The model's final answer is extracted from the full response by finding the last `\boxed{...}` expression, or falling back to the last 1500 characters if no boxed answer is found.
