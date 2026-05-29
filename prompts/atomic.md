# Atomic Caption Generation

This document describes the multi-stage pipeline for generating structured atomic captions that describe the visual content of each image in a problem. Atomic captions serve as the foundation for downstream tasks (Tier 1 question generation, Tier 2 text pruning, and Tier 3 diagram formalization).

The pipeline has four stages: (1) initial extraction, (2) conversion to structured JSON, (3) cross-model feedback, and (4) aggregation and revision.

---

## Stage 1: Initial Extraction

Given an image and the associated problem question, a VLM produces a structured caption with four sections: a problem summary, exact values from the text, topological relationships from the figure, and visual estimates.

**Input:** `[image]`, `{{question}}`

```
{{question}}

Do not solve the problem. Output four sections:

Section 0: Problem Summary Write 2-3 sentences describing: what kind of diagram or figure this is (geometry, chemistry reaction, graph, etc.), what the problem is asking you to find or determine, and any key constraints or conditions stated.

Section 1: Exact Values (from problem text) List every coordinate, equation, length, angle, and geometric relationship explicitly stated in the problem text. These are ground truth.

Section 2: Topology (from figure) Describe relationships as chains and intersections, not isolated facts. For each element state:
- What it passes through or lies on, in order (e.g. Line L passes through A, then X, then B from left to right)
- What it intersects and where in the sequence (e.g. Line L and Line M intersect at X, which is between A and B on Line L)
- Every arrow in the diagram: what it points FROM and TO, its direction (left/right/up/down), and its position relative to other elements
- Every labeled region, box, or enclosed area and what it contains
- Every connection, bond, or edge between elements and what they link
- Spatial ordering: left-to-right or top-to-bottom ordering of all major elements

Section 3: Visual Estimates (figure only) For anything not covered above:
- Relative sizes: which segment/region appears longer, larger, or smaller than another
- Approximate angles: describe each visible angle as acute, right, obtuse, or reflex
- Approximate ratios: e.g. segment AB appears roughly twice as long as segment CD
- Relative positions: e.g. point P appears closer to the left edge than the right edge
- Any spatial property not otherwise described
```

---

## Stage 2: Convert to JSON

The raw captions from Stage 1 are reformatted into a structured JSON array of atomic fact objects, where each item in the Content list is a single verifiable atomic fact.

**Input:** `{{raw_captions}}`

```
{{raw_captions}}

Your task is to change the format of the above captions to make them more easy-to-parse.

To be specific, you should convert the above captions into a JSON array of objects (do not overly paraphrase), where each item in the Content list should be a single verifiable atomic fact. Example output format:
[
    {
        'Section': 1,
        'Description': 'Exact Values (from problem text)',
        'Content': [
            ...
            'C is the intersection of line PA with the line y = -1/2 x + 3',
            ...
        ]
    },
    {
        'Section': 2,
        'Description': 'Topology (from figure)',
        'Content': [
            ...
            'Along line PB (from upper-left toward lower-right): P → Q → B → D → (extension)',
            ...
        ]
    },
    {
        'Section': 3,
        'Description': 'Visual Estimates (figure only)',
        'Content': [
            ...
            'A ≈ (-3.3, 0)',
            ...
        ]
    }
]

Your output should only contain the JSON array, without any additional text or explanation. If the original captions are in Chinese, please output the Chinese values with English keys (e.g. "Section", "Description", "Content") as shown above.
```

---

## Stage 3: Cross-Model Feedback

Multiple expert VLMs independently verify and correct the structured atomic captions against the figure and the question. Each expert produces feedback identifying errors and missing content.

**Input:** `[image]`, `{{question}}`, `{{part1_items}}`, `{{part2_items}}`, `{{part3_items}}`

```
You are given a question, and one figure related to the question. Also, human annotated atomic captions are provided. Your task is to verify and correct the atomic captions based on the figure and the question.

[Question Begin]
{{question}}
[Question End]

[Atomic Captions Begin]
Part 1: Exact Values (from problem text), {{num_part1_items}} items
{{part1_items}}

Part 2: Topology (from figure), {{num_part2_items}} items
{{part2_items}}

Part 3: Visual Estimates (figure only), {{num_part3_items}} items
{{part3_items}}
[Atomic Captions End]

You should check:
- Whether each caption is not a fact (e.g., "The figure looks complicated") and suggest to remove it if so.
- Whether each caption is consistent with the figure and the question. If not, suggest a correction.
- Whether all the content in the figure is covered by the captions. If not, suggest new captions to add.
- Need to consider the source of each caption (problem text vs figure) when verifying its correctness. For example, if a caption is about the exact value of a point, it should be consistent with the problem text; if a caption is about the topology, it should be consistent with the figure. When you suggest to add new captions, please also specify which part they belong to (exact values, topology, or visual estimates).

Special instructions for corrections:
- Your should only focus on the correctness. If a caption is mostly correct but has minor issues (e.g., "A is approximately (-3.3, 0)" → "A is approximately (-3.2, 0)"), you should ignore it and make your suggestions concise. Do not mention minor issues or suggest to keep sth as-is.
- Your output format should be like this:
[Caption Feedback Begin]
Part {part_id} Caption {caption_id}: {suggestion}
Part {part_id} New Caption: {suggestion}
...
[Caption Feedback End]
```

---

## Stage 4: Aggregate Feedback and Revise

A VLM aggregates the feedback from multiple experts and produces a revised set of atomic captions. Contradictory feedback is resolved by judging reasoning quality.

**Input:** `[image]`, `{{question}}`, `{{part1_items}}`, `{{part2_items}}`, `{{part3_items}}`, `{{expert_feedbacks}}`

```
You are given a question, and one figure related to the question. Original annotated atomic captions used to decribe the figure are provided. And, expert feedbacks on the captions are also provided. Your task is to revise the atomic captions based on the figure, the question, and the expert feedbacks.

[Question Begin]
{{question}}
[Question End]

[Atomic Captions Begin]
Part 1: Exact Values (from problem text), {{num_part1_items}} items
{{part1_items}}

Part 2: Topology (from figure), {{num_part2_items}} items
{{part2_items}}

Part 3: Visual Estimates (figure only), {{num_part3_items}} items
{{part3_items}}
[Atomic Captions End]

{{expert_feedbacks}}

You should check:
- If the feedbacks are reasonble and revise the captions. You cannot propose revisions that are not included in the feedbacks. If the feedbacks are contradictory, you should make a judgement on which feedback to follow based on the reasoning quality and then revise the captions accordingly.

Special instructions:
- You should also calculate the number of items in each part before revision, the number of items revised, and the number of new items added, and include this information in your output.
- You output format should be a JSON array without any additional text. The format should be like this:
[
    {
        'Section': 1,
        'Description': 'Exact Values (from problem text)',
        'Number of items before revision': {an integer},
        'Number of revised items': {an integer},
        'Number of new items added': {an integer},
        'Content': [
            ...
            'C is the intersection of line PA with the line y = -1/2 x + 3',
            ...
        ]
    },
    {
        'Section': 2,
        'Description': 'Topology (from figure)',
        'Number of items before revision': {an integer},
        'Number of revised items': {an integer},
        'Number of new items added': {an integer},
        'Content': [
            ...
            'Along line PB (from upper-left toward lower-right): P → Q → B → D → (extension)',
            ...
        ]
    },
    {
        'Section': 3,
        'Description': 'Visual Estimates (figure only)',
        'Number of items before revision': {an integer},
        'Number of revised items': {an integer},
        'Number of new items added': {an integer},
        'Content': [
            ...
            'A ≈ (-3.3, 0)',
            ...
        ]
    }
]
```
