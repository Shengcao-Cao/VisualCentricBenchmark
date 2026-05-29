# Tier 1: Visual Perception Question Generation

This document describes the prompt used to generate Tier 1 multiple-choice questions that test visual perception ability. For each image in a problem, exactly 3 questions are generated — one per type (A, B, C). These questions must be answerable by looking at the image alone, with no calculation or reasoning required.

The VLM receives the image, the original problem question (for context about what the figure depicts), and the atomic caption (to ground what is visually present). Three separate calls are made per image, one for each question type.

---

## System Prompt

The following system prompt is shared across all three question types:

```
You are given an image from a test problem, along with the original question and a set of atomic captions describing the image.
Questions must never require calculation, algebraic solving, theorem application, or multi-step reasoning.
Your task is to generate exactly 3 single-selection multiple-choice questions that test visual perception ability only.
```

---

## Context Assembly

Before the type-specific prompt, the following context is prepended as the user message (alongside the image):

```
Original problem question:
{{question}}

Structured image description:
{{atomic_caption}}

---

```

This context is followed by the type-specific prompt below.

---

## Type A: Entity Recognition

Type A questions ask about labeled or marked entities that are directly visible in the image.

```
Generate EXACTLY 1 multiple-choice question of Type A (Entity Recognition).

Type A questions ask about labeled or marked entities that are DIRECTLY VISIBLE in the image, such as:
- labeled points (e.g. A, B, P, Q)
- shown numerical values or coordinates
- visible equations or expressions written in the diagram
- equal-length tick markings on segments
- angle arc markings
- any other directly labeled elements

Rules:
- The question must be answerable by reading the image alone — no calculation, no reasoning, no inference
- Exactly 4 answer choices: A, B, C, D
- Exactly 1 correct answer
- Distractors must be plausible (things that look similar or could be confused)
- Do NOT ask about anything that requires solving or inferring hidden values
- Do NOT ask about subjective or ambiguous properties (e.g., "wider", "narrower", "larger", "brighter") unless the difference is stark and unambiguous. Do NOT require domain knowledge, calculation, or multi-step reasoning.

Return ONLY a valid JSON array containing exactly 1 object — no markdown fences, no extra text:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "answer": "A"
  }
]

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
```

---

## Type B: Topology

Type B questions ask about spatial relationships and geometric configurations that are directly visible.

```
Generate EXACTLY 1 multiple-choice question of Type B (Topology).

Type B questions ask about spatial relationships and geometric configurations that are DIRECTLY VISIBLE, such as:
- which point lies inside, outside, or on the boundary of a shape
- whether two segments or lines intersect (and where)
- whether lines appear parallel or perpendicular based on visible markings
- how points or segments are connected (path, triangle, loop)
- which regions are enclosed or adjacent

Rules:
- The question must be answerable by visual inspection alone — no calculation, no measurement, no reasoning beyond what is directly observable
- Exactly 4 answer choices: A, B, C, D
- Exactly 1 correct answer
- Distractors must be plausible spatial alternatives
- Do NOT ask about anything requiring exact measurement or algebraic solving

Return ONLY a valid JSON array containing exactly 1 object — no markdown fences, no extra text:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "answer": "B"
  }
]

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
```

---

## Type C: Measurement and Relative Position

Type C questions ask about approximate visual properties that can be judged from appearance without exact numerical extraction.

```
Generate EXACTLY 1 multiple-choice question of Type C (Measurement and Relative Position).

Type C questions ask about approximate visual properties that can be judged from appearance without requiring exact numerical extraction, such as:
- where a point sits relative to a shape (top-left corner, center, on the edge)
- what category of angle is shown (acute, right, obtuse, reflex)
- the approximate ratio of two lengths (roughly 1:1, 2:1, 3:1)
- rough relative ordering or closeness of two quantities
- coarse relative size (about twice as large, roughly equal)

Rules:
- The question must be answerable from appearance — no exact measurements, no impossible precision, no calculation
- Exactly 4 answer choices: A, B, C, D
- Exactly 1 correct answer
- Choices must span the realistic range so the correct one is distinguishable by appearance but not trivially obvious
- Do NOT ask for exact coordinates or precise numerical answers

Return ONLY a valid JSON array containing exactly 1 object — no markdown fences, no extra text:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "answer": "C"
  }
]

IMPORTANT: In the "options" array, provide only the option TEXT without letter prefixes. Do NOT include "A. ", "B. ", etc. in the option strings. The "answer" field should be the letter (A/B/C/D) of the correct option.
```
