# Tier 2: Text Pruning Pipeline

This document describes the four-stage pipeline for producing pruned questions that remove visually-redundant text. The goal is to identify and remove textual information that is already conveyed by the image(s), so that a model must actually rely on visual perception to solve the problem.

The pipeline stages are: (1) mask visually-redundant spans, (2) attempt to recover the original from the masked version, (3) verify recovery quality, and (4) classify fact coverage. Stages 2–3 serve as a self-consistency check — if the masked content can be recovered from the image and captions alone, the masking was valid.

---

## Stage 1: Masking

A VLM identifies phrases in the question that can be recovered from the image(s) and atomic captions, replaces them with `<MASK>` tags, and then rewrites the masked question into a naturally readable pruned question.

**Input:** `[image(s)]`, `{{question}}`, `{{atomic_captions}}`

```
You are given a multimodal question with {{num_images}} image(s) and atomic captions of the image(s).

Produce two outputs:

1. Masked Question:
Replace any phrase that can be recovered from the image(s)-only or atomic captions with `<MASK ...>`. After masking, the resulting question should still be logically consistent and solvable.
- Each mask should include a short hint about the role of the missing content, so that an expert can recover it from the image(s) and atomic captions without ambiguity.
- The hint should describe the type or function of the masked content, not restate the answer itself.
- The goal of masking is to help reduce the redundancy, leading to a better pruned question (see later). 

Example:
"... Darlnim adds point $A$, which is on $\overline{BE}$ ..."
->
"... Darlnim adds point $A$, <MASK: relationship between $A$ and the segment it lies on> ..."

**Allowed:**
- If the text is already minimized, you can leave it as is without adding a `<MASK>`.
- Mask the visual relationships that are explicitly depicted in the image(s).

**Not allowed:**
- Masking the phrase that gives exact numbers. E.g., 1) $A$ = (1, 2) if (1,2) is not shown in the image(s)
- Masking the target, e.g., "Find $m \angle 7$."
- Break a phrase into too many pieces, only mask the entire phrase or logical unit as a whole.

2. Pruned Question:
Rewrite the Masked Question into a naturally readable question without `<MASK>`.

- The Pruned Question should preserve roughly the same meaning and information as the Masked Question, while avoiding explicit mention of content that can be recovered from the image(s) or atomic captions.
- That means, if a sentence contains no remaining information after masking, consider removing it.
- It should read as a complete, natural question that can be given directly to a student as a standalone problem.
- Do not leave behind broken references to removed content.

Requirements:
- Always keep the original logic and ordering of the question.
- Always preserve every `<image_N>` tag exactly in its original position.
- The Pruned Question should be readable on its own, not a broken sentence with masks removed.
- You may rewrite lightly for fluency.

[Original Question Begin]
{{question}}
[Original Question End]

[Atomic Captions Begin]
{{atomic_captions}}
[Atomic Captions End]

Your output should strictly follow the format below:
[Masked Question Begin]
Your masked question here. It should be the same as the original question but replaced some text with <MASK>.
[Masked Question End]

[Pruned Question Begin]
Your pruned question here. It should be a naturally readable question without <MASK>, and should preserve roughly the same meaning and information as the Masked Question.
[Pruned Question End]
```

---

## Stage 2: Recovery

A separate VLM attempts to recover the original question from the masked version using only the image(s) and atomic captions. This tests whether the masked content is truly recoverable from visual information.

**Input:** `[image(s)]`, `{{atomic_captions}}`, `{{masked_question}}`

```
You are given a multimodal question with {{num_images}} image(s), atomic captions of the image(s), and a masked version of the original question.

Your task is to recover the original question by filling in every masked span.

Requirements:
- Replace every `<MASK ...>` span with the most likely original content.
- If there is no `<MASK ...>` span in the masked question, return the original question as-is.
- Use the image(s) and atomic captions as the primary evidence.
- Preserve the original wording, mathematical notation, logic, and ordering as much as possible.
- Always preserve every `<image_N>` tag exactly in its original position.
- Return one fully recovered question, not a list of guesses.
- If some local wording is uncertain, provide the most likely faithful reconstruction.

[Atomic Captions Begin]
{{atomic_captions}}
[Atomic Captions End]

[Masked Question Begin]
{{masked_question}}
[Masked Question End]

Your output should strictly follow the format below:
[Recovered Question Begin]
Your recovered question here.
[Recovered Question End]
```

---

## Stage 3: Recovery Verification

A VLM judges whether the recovered question faithfully reconstructs the original question. This determines the quality of the masking — if recovery succeeds, the masked content was indeed visually redundant.

**Labels:**
- **2** — successful reconstruction (same meaning, constraints, answerability)
- **1** — wrong reconstruction, but target is still inferable from image(s)/captions
- **0** — important mismatch, missing info, or altered answerability

**Input:** `[image(s)]`, `{{question}}`, `{{atomic_captions}}`, `{{masked_question}}`, `{{recovered_question}}`

```
You are given a multimodal question with {{num_images}} image(s), atomic captions of the image(s), the original question, the masked question, and a recovered question.

Your task is to judge whether the recovered question is a successful reconstruction of the original question.

Judging standard:
- Output label 2 if the recovered question preserves the same meaning, constraints, entities, mathematical relationships, and answerability as the original question.
- Minor wording differences are allowed if they do not change the meaning.
- Output label 1 if the recovered question is wrong, but you believe the target can be inferred from given the image(s) and atomic captions. The reason for failure mostly lies in the ambiguity of the recovering task, instead of the possibility of faithfully reconstructing the original question.
- Output label 0 if there is any important mismatch, missing key information, wrong entity/object/number/relationship, changed logic, or altered answerability.

Requirements:
- Use the image(s) and atomic captions when needed to verify whether the recovery is faithful.
- Focus on semantic equivalence, not exact string match.
- Give a short explanation that points to the key reason for your judgment.

[Original Question Begin]
{{question}}
[Original Question End]

[Atomic Captions Begin]
{{atomic_captions}}
[Atomic Captions End]

[Masked Question Begin]
{{masked_question}}
[Masked Question End]

[Recovered Question Begin]
{{recovered_question}}
[Recovered Question End]

Your output should strictly follow the format below:
[Binary Label Begin]
0, 1, or 2
[Binary Label End]

[Explanation Begin]
Your explanation here.
[Explanation End]
```

---

## Stage 4: Fact Coverage Verification

A VLM classifies each atomic fact by where it is present — in the text, in the image, in both, implicitly, or in neither. This provides a fine-grained analysis of information distribution between modalities.

**Labels per fact:** `"Text"` | `"Image"` | `"Both"` | `"Implicit"` | `"None"`

**Input:** `[image(s)]`, `{{pruned_question}}`, `{{facts_numbered}}`

```
You are given a multimodal question with {{num_images}} image(s), and a list of atomic facts derived from the problem text.

Your task is to classify each fact by where it is present:
- "Text"  — the fact is explicitly stated or clearly implied in the question
- "Image" — the fact is visible in the image(s) but NOT mentioned in the question
- "Both"  — the fact appears in both the question and the image(s)
- "Implicit" — the fact is implied by the question and the image(s) but not explicitly stated in either
- "None"  — the fact can not be inferred from either the question or the image(s)

Requirements:
- Classify every fact in the list, in order.
- Base your judgment on the question text and the image(s) provided.
- Your output must be a valid JSON array of strings, one entry per fact, each entry being exactly one of: "None", "Image", "Text", "Both", "Implicit".

[Question Begin]
{{pruned_question}}
[Question End]

[Facts Begin]
{{facts_numbered}}
[Facts End]

Your output should strictly follow the format below:
[Labels Begin]
["Text", "Image", "None", ...]
[Labels End]

The JSON array must have exactly {{num_facts}} elements, one per fact above.
```
