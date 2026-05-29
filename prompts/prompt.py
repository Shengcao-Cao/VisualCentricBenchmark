"""
prompt.py — Centralised prompt builders
"""

# ---------------------------------------------------------------------------
# tier 2
# ---------------------------------------------------------------------------

def build_Tier_2_Masking(num_images: int, question: str, atomic_caption_text: str) -> str:
    """
    Stage 1 (testall.py): Mask visually-redundant spans and produce a pruned question.

    Args:
        num_images: number of images referenced in the question.
        question: the original question text.
        atomic_caption_text: pre-formatted atomic captions string.
    """
    return (
        f'''You are given a multimodal question with {num_images} image(s) and atomic captions of the image(s).'''
        + r'''

Produce two outputs:

1. Masked Question:
Replace any phrase that can be recovered from the image(s)-only or atomic captions with `<MASK ...>`. After masking, the resulting question should still be logically consistent and solvable.
- Each mask should include a short hint about the role of the missing content, so that an expert can recover it from the image(s) and atomic captions without ambiguity.
- The hint should describe the type or function of the masked content, not restate the answer itself.
- The goal of masking is to help reduce the redundancy, leading to a better pruned question (see later). 

Example:
"... Darlnim adds point $A$, which is on $\\overline{BE}$ ..."
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
- You may rewrite lightly for fluency.'''
        + f'''

[Original Question Begin]
{question}
[Original Question End]

[Atomic Captions Begin]
{atomic_caption_text}
[Atomic Captions End]'''
        + r'''

Your output should strictly follow the format below:
[Masked Question Begin]
Your masked question here. It should be the same as the original question but replaced some text with <MASK>.
[Masked Question End]

[Pruned Question Begin]
Your pruned question here. It should be a naturally readable question without <MASK>, and should preserve roughly the same meaning and information as the Masked Question.
[Pruned Question End]
'''
    )


def build_Tier_2_Recovery(num_images: int, atomic_caption_text: str, masked_question: str) -> str:
    """
    Stage 2 (testall.py): Recover the original question from a masked version.

    Args:
        num_images: number of images referenced in the question.
        atomic_caption_text: pre-formatted atomic captions string.
        masked_question: the masked question produced in stage 1.
    """
    return (
        f'''You are given a multimodal question with {num_images} image(s), atomic captions of the image(s), and a masked version of the original question.

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
{atomic_caption_text}
[Atomic Captions End]

[Masked Question Begin]
{masked_question}
[Masked Question End]
'''
        + r'''
Your output should strictly follow the format below:
[Recovered Question Begin]
Your recovered question here.
[Recovered Question End]
'''
    )


def build_Tier_2_Recovery_Verification(
    num_images: int,
    question: str,
    atomic_caption_text: str,
    masked_question: str,
    recovered_question: str,
) -> str:
    """
    Stage 3 (testall.py): Judge whether the recovered question faithfully reconstructs
    the original question.

    Labels:
        2 — successful reconstruction (same meaning, constraints, answerability).
        1 — wrong reconstruction, but target is still inferable from image(s)/captions.
        0 — important mismatch, missing info, or altered answerability.

    Args:
        num_images: number of images referenced in the question.
        question: the original question text.
        atomic_caption_text: pre-formatted atomic captions string.
        masked_question: masked question from stage 1.
        recovered_question: recovered question from stage 2.
    """
    return (
        f'''You are given a multimodal question with {num_images} image(s), atomic captions of the image(s), the original question, the masked question, and a recovered question.

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
{question}
[Original Question End]

[Atomic Captions Begin]
{atomic_caption_text}
[Atomic Captions End]

[Masked Question Begin]
{masked_question}
[Masked Question End]

[Recovered Question Begin]
{recovered_question}
[Recovered Question End]
'''
        + r'''
Your output should strictly follow the format below:
[Binary Label Begin]
0, 1, or 2
[Binary Label End]

[Explanation Begin]
Your explanation here.
[Explanation End]
'''
    )


def build_Tier_2_Fact_Coverage_Verification(
    num_images: int,
    pruned_question: str,
    facts_numbered: str,
    num_facts: int,
) -> str:
    """
    Stage 4 (testall.py): Classify each atomic fact by where it is present.

    Labels per fact: "Text" | "Image" | "Both" | "Implicit" | "None"

    Args:
        num_images: number of images referenced in the question.
        pruned_question: pruned question produced in stage 1.
        facts_numbered: newline-separated numbered list of facts, e.g. "1. ...\n2. ..."
        num_facts: total number of facts (must equal the length of the JSON array returned).
    """
    return f'''You are given a multimodal question with {num_images} image(s), and a list of atomic facts derived from the problem text.

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
{pruned_question}
[Question End]

[Facts Begin]
{facts_numbered}
[Facts End]

Your output should strictly follow the format below:
[Labels Begin]
["Text", "Image", "None", ...]
[Labels End]

The JSON array must have exactly {num_facts} elements, one per fact above.
'''


# ---------------------------------------------------------------------------
# atomic caption
# ---------------------------------------------------------------------------

def build_Atomic_Extraction() -> str:
    return (
    "Do not solve the problem. Output four sections:\n\n"
    "Section 0: Problem Summary "
    "Write 2-3 sentences describing: what kind of diagram or figure this is (geometry, chemistry reaction, graph, etc.), "
    "what the problem is asking you to find or determine, and any key constraints or conditions stated.\n\n"
    "Section 1: Exact Values (from problem text) "
    "List every coordinate, equation, length, angle, and geometric relationship explicitly stated in the problem text. These are ground truth.\n\n"
    "Section 2: Topology (from figure) "
    "Describe relationships as chains and intersections, not isolated facts. For each element state:\n"
    "- What it passes through or lies on, in order (e.g. Line L passes through A, then X, then B from left to right)\n"
    "- What it intersects and where in the sequence (e.g. Line L and Line M intersect at X, which is between A and B on Line L)\n"
    "- Every arrow in the diagram: what it points FROM and TO, its direction (left/right/up/down), and its position relative to other elements\n"
    "- Every labeled region, box, or enclosed area and what it contains\n"
    "- Every connection, bond, or edge between elements and what they link\n"
    "- Spatial ordering: left-to-right or top-to-bottom ordering of all major elements\n\n"
    "Section 3: Visual Estimates (figure only) "
    "For anything not covered above:\n"
    "- Relative sizes: which segment/region appears longer, larger, or smaller than another\n"
    "- Approximate angles: describe each visible angle as acute, right, obtuse, or reflex\n"
    "- Approximate ratios: e.g. segment AB appears roughly twice as long as segment CD\n"
    "- Relative positions: e.g. point P appears closer to the left edge than the right edge\n"
    "- Any spatial property not otherwise described"
)

def build_Atomic_Convert_to_JSON(raw_atomic_captions: str) -> str:
    """
    Stage 1 (three_stage_revise.py): Reformat raw annotated captions into a structured
    JSON array of atomic fact objects.

    Args:
        raw_atomic_captions: the raw caption string for a single image (item['atomic_captions'][img_id]).
    """
    return (
        f'''{raw_atomic_captions}'''
        + r'''

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
'''
    )


def build_Atomic_Cross_Model_Feedback(
    question: str,
    part1_items: list,
    part2_items: list,
    part3_items: list,
) -> str:
    """
    Stage 2 (three_stage_revise.py): Verify and correct structured atomic captions
    against the figure and the question.

    Args:
        question: the problem question text.
        part1_items: list of strings for Part 1 (Exact Values from problem text).
        part2_items: list of strings for Part 2 (Topology from figure).
        part3_items: list of strings for Part 3 (Visual Estimates from figure).
    """
    def _numbered(items):
        return '\n'.join(f'{i+1}. {c}' for i, c in enumerate(items))

    return (
        f'''You are given a question, and one figure related to the question. Also, human annotated atomic captions are provided. Your task is to verify and correct the atomic captions based on the figure and the question.

[Question Begin]
{question}
[Question End]

[Atomic Captions Begin]
Part 1: Exact Values (from problem text), {len(part1_items)} items
{_numbered(part1_items)}

Part 2: Topology (from figure), {len(part2_items)} items
{_numbered(part2_items)}

Part 3: Visual Estimates (figure only), {len(part3_items)} items
{_numbered(part3_items)}
[Atomic Captions End]
'''
        + r'''
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
'''
    )


def build_Atomic_Aggregate_Feedback(
    question: str,
    part1_items: list,
    part2_items: list,
    part3_items: list,
    expert_feedbacks: str,
) -> str:
    """
    Stage 3 (three_stage_revise.py): Revise atomic captions based on expert feedback
    from multiple models, producing an updated JSON array.

    Args:
        question: the problem question text.
        part1_items: list of strings for Part 1 (Exact Values from problem text).
        part2_items: list of strings for Part 2 (Topology from figure).
        part3_items: list of strings for Part 3 (Visual Estimates from figure).
        expert_feedbacks: concatenated expert feedback blocks
                          (formatted as "[Expert N Feedback Begin]...[Expert N Feedback End]").
    """
    def _numbered(items):
        return '\n'.join(f'{i+1}. {c}' for i, c in enumerate(items))

    return (
        f'''You are given a question, and one figure related to the question. Original annotated atomic captions used to decribe the figure are provided. And, expert feedbacks on the captions are also provided. Your task is to revise the atomic captions based on the figure, the question, and the expert feedbacks.

[Question Begin]
{question}
[Question End]

[Atomic Captions Begin]
Part 1: Exact Values (from problem text), {len(part1_items)} items
{_numbered(part1_items)}

Part 2: Topology (from figure), {len(part2_items)} items
{_numbered(part2_items)}

Part 3: Visual Estimates (figure only), {len(part3_items)} items
{_numbered(part3_items)}
[Atomic Captions End]

{expert_feedbacks}
'''
        + r'''
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
'''
    )
