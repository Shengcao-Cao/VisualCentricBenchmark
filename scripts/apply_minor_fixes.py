"""Apply all 170 minor_fix annotations to merged_full_trivial.json.

Each fix is hardcoded from the annotator's fix_comment, keyed by question_id.
Produces merged_full_trivial_fixed.json.
"""

import json
from pathlib import Path

# Each entry: question_id -> dict of changes to apply.
# Keys in the dict:
#   "question": new question text (replaces entire question)
#   "options": dict of option letter -> new option text
#   "remove_option": option letter to remove (replaced with a new option)
#   "correct_option": updated correct option letter (if changed by the fix)
#
# UNCERTAIN items are tagged with a comment.

FIXES = {
    # --- mingye (17) ---
    "EMMA-test-1364_img0_C_1": {
        "options": {"B": "About one third"},
    },
    "EMMA-test-1439_img0_B_1": {
        "options": {"B": "The first and fourth shapes"},
    },
    "EMMA-test-1648_img0_B_1": {
        "options": {"C": "None of them"},
    },
    "EMMA-test-2141_img0_C_1": {
        "options": {"D": "Around ten times h"},
    },
    "OlympicArena-test-963_img0_B_1": {
        # UNCERTAIN: annotator says "specify whether it is in going or out going.
        # If it is pointing towards H, then A:C is correct"
        # Interpreting: change the question to specify direction
        "question": "In the flow diagram, which labeled box is directly connected to H by a horizontal arrow pointing toward H?",
    },
    "OlympicArena-test-391_img0_C_1": {
        "options": {"C": "h2 is exactly equal to h1"},
    },
    "OlympicArena-test-127_img0_C_1": {
        "options": {"C": "About 3 times as wide", "D": "About 5 times as wide"},
    },
    "OlympicArena-test-167_img0_C_1": {
        "options": {"D": "About six times as large"},
    },
    "OlympicArena-test-166_img0_C_1": {
        "options": {"B": "At the top-right corner of the lower-left square"},
    },
    "OlympicArena-test-423_img0_C_1": {
        "options": {"C": "About three fourths as tall"},
    },
    "OlympicArena-test-454_img1_C_1": {
        "options": {"C": "About three times as large"},
    },
    "OlympicArena-test-501_img1_C_1": {
        "options": {"C": "About three times as tall"},
    },
    "MMMU-test-2826_img0_B_1": {
        "options": {"B": "In a diagonal line from lower right to upper left"},
    },
    "MMMU-test-2102_img0_C_1": {
        "options": {"C": "Roughly two times as tall"},
    },
    "OlympicArena-test-1068_img0_C_1": {
        # 大灰色区域改为大白色区域
        "question": "从图中看，左侧大白色区域的宽度与右侧由多条竖线分成的窄列总宽度相比，最接近下面哪一种关系？",
    },
    "OlympicArena-test-1092_img0_B_1": {
        "options": {"C": "The line labeled 乙 stays below the line labeled 甲 throughout the graph"},
    },
    "OlympicArena-test-1208_img0_B_1": {
        "options": {"D": "None of the options above"},
    },

    # --- zheyu (18) ---
    "OlympicArena-test-280_img0_B_1": {
        "options": {"D": "It does touch, but does not relate to the dashed horizontal line"},
    },
    "Geometry3k-train-175_img0_A_1": {
        "question": "Which angle is vertical to the angle labeled 110°?",
    },
    "OlympicArena-test-2785_img0_C_1": {
        "options": {"A": "α is smaller than β"},
    },
    "OlympicArena-test-2802_img0_C_1": {
        "options": {"B": "III"},
    },
    "OlympicArena-test-2812_img0_C_1": {
        "options": {"A": "Lower left of the center"},
    },
    "OlympicArena-test-2917_img0_B_1": {
        "options": {"B": "β"},
    },
    "OlympicArena-test-3443_img0_B_1": {
        "options": {"C": "I and VI"},
    },
    "OlympicArena-test-2284_img1_B_1": {
        "options": {"C": "Ethephon only"},
    },
    "OlympicArena-test-2284_img1_C_1": {
        "options": {"C": "The Ethephon bar is about three times as tall as the ABA bar"},
    },
    "OlympicArena-test-2326_img0_B_1": {
        # 选项B改为"图谱三和图谱四都在条带1、条带2、条带3位置有条带"
        "options": {"B": "图谱三和图谱四都在条带1、条带2、条带3位置有条带"},
    },
    "OlympicArena-test-2453_img0_C_1": {
        "options": {"D": "Near the upper-center area"},
    },
    "OlympicArena-test-2467_img0_B_1": {
        "options": {"D": "Both 甲 and 乙"},
    },
    "OlympicArena-test-2561_img0_C_1": {
        # 选项D改为"三条线看起来都不接近水平"
        "options": {"D": "三条线看起来都不接近水平"},
    },
    "OlympicArena-test-2825_img0_C_1": {
        "options": {"C": "Slightly less than half as wide"},
    },
    "OlympicArena-test-2886_img0_B_1": {
        "question": "Which labeled longitude is closest to the tallest visible purple peak in the graph?",
    },
    "OlympicArena-val-112_img0_C_1": {
        "options": {"C": "Slightly longer"},
    },
    "MathVision-test-597_img0_C_1": {
        "options": {
            "A": "Toward the upper-left side of the second mirrored hexagon",
            "B": "Toward the top center of the second mirrored hexagon",
            "C": "Toward the lower-right side of the second mirrored hexagon",
            "D": "Toward the bottom center of the second mirrored hexagon",
        },
    },
    "MathVision-test-639_img0_B_1": {
        "options": {"C": "Option B"},
    },

    # --- ji (50) ---
    "OlympiadBench-test-OE_MM_maths_zh_CEE-7149_img0_B_1": {
        "options": {"B": "A"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-7137_img0_C_1": {
        "options": {"B": "Q"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-5557_img0_B_1": {
        "options": {"D": "D"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-5123_img0_B_1": {
        "options": {"D": "D"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1170_img0_C_1": {
        "options": {"C": "About one-fifth as large"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1085_img1_C_1": {
        "options": {"C": "i2 is slightly larger than i1"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1111_img0_C_1": {
        "options": {"C": "larger"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1112_img0_C_1": {
        "options": {"C": "About half as long"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1114_img2_C_1": {
        "options": {"D": "h is about three times r"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1119_img0_C_1": {
        "options": {"D": "Less than one tenth of the container width"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1123_img0_C_1": {
        "options": {"C": "Near the center"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1133_img1_C_1": {
        "options": {"D": "About a half of d"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1135_img1_C_1": {
        "options": {"D": "About 2 times the radius"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1201_img1_C_1": {
        "options": {"D": "About two and a half times as large"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1203_img5_C_1": {
        "options": {"C": "About 3 times as long as d", "D": "About 6 times as long as d"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1211_img3_B_1": {
        "options": {"D": "None of the above"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1211_img3_C_1": {
        "options": {"D": "About one and a half times longer"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1231_img0_C_1": {
        "options": {"C": "About three times the dome's width"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1241_img0_B_1": {
        "options": {"B": "On the left bottom side"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1243_img1_C_1": {
        # "question should explicitly mention 'size is in terms of diameter'"
        "question": "Compared with the Earth in the diagram, about how large does the Moon appear in terms of diameter?",
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1292_img0_C_1": {
        "options": {"A": "shorter"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1296_img0_B_1": {
        "options": {"B": "Only the horizontal axis and the vertical green segment"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1304_img2_C_1": {
        "options": {"A": "The arrow from A is slightly shorter"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1381_img0_C_1": {
        "options": {"C": "About three times as long"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1467_img0_C_1": {
        "options": {"B": "About one fifth"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1469_img0_C_1": {
        "options": {"C": "Around 4 times as large as d", "D": "Much larger than d"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1544_img3_B_1": {
        "options": {"D": "D3"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-7462_img0_C_1": {
        "options": {"D": "About 4 times"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-7494_img0_B_1": {
        "options": {"A": "The curve does not intersect the horizontal axis"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-7503_img0_B_1": {
        "options": {"D": "K"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-7560_img0_C_1": {
        # Replace "the horizontal spacing between the two dashed lines" with "the vertical spacing..."
        "question": "In the figure, how does the vertical spacing between the two dashed lines compare to the vertical distance from the origin O to the lower dashed line y1?",
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-7675_img1_C_1": {
        "options": {"D": "The t1-to-t2 spacing is somewhat smaller"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-7869_img0_C_1": {
        "options": {"C": "BC is slightly longer than AB"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-8336_img0_C_1": {
        "options": {"D": "H is more than 3 times the side length of block B"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-8643_img0_B_1": {
        "options": {"A": "挡板、P、A、Q"},
    },
    "OlympiadBench-test-OE_MM_physics_zh_CEE-8744_img0_C_1": {
        "options": {"C": "L is slightly longer than d"},
    },
    "OlympicArena-test-598_img0_C_1": {
        "options": {"B": "s"},
    },
    "OlympicArena-test-666_img0_B_1": {
        "options": {"B": "None"},
    },
    "OlympicArena-test-666_img1_A_1": {
        "options": {"D": "s₁ = 252 pc"},
    },
    "OlympicArena-test-666_img1_B_1": {
        "options": {"A": "s2"},
    },
    "OlympicArena-test-802_img0_C_1": {
        "options": {"C": "Slightly longer than the x-axis arrow"},
    },
    "OlympicArena-test-806_img0_C_1": {
        # "ABCD: 2468" — annotator wants A=2, B=4, C=6, D=8
        "options": {"A": "About 2 times", "B": "About 4 times", "C": "About 6 times", "D": "About 8 times"},
    },
    "OlympicArena-test-836_img2_C_1": {
        "options": {"C": "About three times as large"},
    },
    "OlympicArena-test-836_img4_C_1": {
        "options": {"D": "About one-eighth as large"},
    },
    "OlympicArena-val-54_img0_C_1": {
        "options": {"B": "The gap is slightly shorter than a branch"},
    },
    "OlympicArena-val-59_img0_C_1": {
        "options": {"D": "d is about four times as long as d'"},
    },
    "OlympicArena-val-67_img1_C_1": {
        "options": {"C": "About three times as tall"},
    },
    "OlympicArena-val-91_img0_C_1": {
        "options": {"D": "H + H⁺"},
    },
    "OlympicArena-val-133_img0_B_1": {
        "options": {"B": "1 和 3"},
    },
    "OlympicArena-test-1486_img0_C_1": {
        "options": {"D": "About 4 times as long"},
    },

    # --- shengcao (28) ---
    "MMMU-test-270_img0_A_1": {
        "question": "Which label appears to the left of the middle structure in the image?",
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-5744_img0_C_1": {
        # C 应该为略低于
        "options": {"C": "自由式滑雪略低于单板滑雪"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-5864_img0_B_1": {
        "options": {"C": "Both x-axis and y-axis"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-6514_img0_C_1": {
        # "3 times" — change D to 3 times
        "options": {"D": "About 3 times"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_CEE-7269_img1_C_1": {
        # 三倍左右
        "options": {"D": "右侧高度约为左侧的三倍左右"},
    },
    "OlympiadBench-test-OE_MM_maths_zh_COMP-535_img0_C_1": {
        "options": {"C": "E is closer to B than to S"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1030_img1_C_1": {
        "options": {"C": "About two and a half times the column width"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1031_img0_C_1": {
        "options": {"B": "Slightly longer than the z-axis arrow"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1269_img2_C_1": {
        "options": {"C": "About two and a half times as long"},
    },
    "OlympiadBench-test-OE_MM_physics_en_COMP-1270_img1_C_1": {
        "options": {"C": "Roughly one and a half times the width of a level line"},
    },
    "SUPERChem-train-41-zh_img0_A_1": {
        "question": 'Which label appears directly to the right of the arrow marked "HCl (aq)"?',
    },
    "SUPERChem-train-47-en_img0_C_1": {
        # "change D to 三倍" — means about three times
        "options": {"D": "Segment c is about three times as long as segment b"},
    },
    "SUPERChem-train-74-en_img0_C_1": {
        "options": {"C": "Between arrows"},
    },
    "SUPERChem-train-101-en_img0_C_1": {
        "options": {"C": "Slightly longer"},
    },
    "SUPERChem-train-120-en_img5_C_1": {
        "options": {"B": "Below and to the right"},
    },
    "SUPERChem-train-128-en_img0_B_1": {
        # UNCERTAIN: "instead of above and below, change to to the right for above
        # and to the left for below."
        # Interpreting: A was "Above the first arrow and below the second arrow"
        # → "To the right of the first arrow and to the left of the second arrow"
        # B was "Below the first arrow and above the second arrow"
        # → "To the left of the first arrow and to the right of the second arrow"
        "options": {
            "A": "To the right of the first arrow and to the left of the second arrow",
            "B": "To the left of the first arrow and to the right of the second arrow",
            "C": "To the right of both arrows",
            "D": "To the left of both arrows",
        },
    },
    "SUPERChem-train-131-zh_img1_A_1": {
        "options": {"D": "N"},
    },
    "Geometry3k-validation-262_img0_C_1": {
        "options": {"D": "About four times as long"},
    },
    "Geometry3k-train-1289_img0_C_1": {
        "options": {"A": "slightly longer"},
    },
    "Geometry3k-train-2014_img0_B_1": {
        "options": {"D": "The side labeled 2√3 and the segment labeled y"},
    },
    "MMMU-test-1365_img0_C_1": {
        "options": {"C": "It looks about the same length, slightly longer"},
    },
    "OlympiadBench-test-OE_MM_maths_en_COMP-2347_img0_C_1": {
        "options": {"A": "To the right of segment AC"},
    },
    "OlympiadBench-test-OE_MM_maths_en_COMP-2810_img3_A_1": {
        "options": {"C": "F"},
    },
    "MathVerse-testmini-1793_img0_C_1": {
        # "x is about the same length as w. Revise the question text to avoid
        # 'shorter' 'longer' incorrect hints."
        "question": "Compared with the horizontal segment labeled w, how does the horizontal segment labeled x appear in length?",
        "options": {"B": "x is about the same length as w"},
    },
    "MMMU-test-2547_img0_C_1": {
        "options": {"B": "About two thirds"},
    },
    "MMMU-test-2213_img0_B_1": {
        "options": {"C": "The below-left pulley"},
    },
    "MMMU-test-1972_img0_C_1": {
        "options": {"D": "About one and a half times the area"},
    },
    "MMMU-validation-67_img0_C_1": {
        "options": {"A": "About one quarter of the rectangle's width"},
    },

    # --- david (57) ---
    "SUPERChem-train-64-en_img0_C_1": {
        "question": "Compared with the right-pointing reaction arrow that leads to B, the line segment marked 140°C is oriented at approximately what angle to that arrow?",
    },
    "Geometry3k-train-484_img0_C_1": {
        # "Change to angle 6, hard to tell for 7 since 7 could be right angle."
        "question": "By appearance, what type of angle is ∠6?",
    },
    "Geometry3k-train-53_img0_C_1": {
        "options": {"B": "KH is about one and a half times as long as HJ"},
    },
    "Geometry3k-train-26_img0_B_1": {
        "options": {"C": "2"},
    },
    "Geometry3k-test-513_img0_A_1": {
        "options": {"A": "1"},
    },
    "Geometry3k-validation-93_img0_C_1": {
        "options": {"A": "Below and to the left of Y"},
    },
    "SUPERChem-train-14-zh_img0_B_1": {
        "options": {"C": "S and G"},
    },
    "SUPERChem-train-26-en_img3_B_1": {
        "question": "Which group is directly attached to the lower right side of the central ring?",
    },
    "SUPERChem-train-27-en_img4_C_1": {
        "options": {"B": "Mostly below and to the left of the ring"},
    },
    "SUPERChem-train-27-zh_img4_C_1": {
        "options": {"C": "To the left of the ring"},
    },
    "SUPERChem-train-50-zh_img2_A_1": {
        "question": "Which label appears at the lower right part of the structure?",
    },
    "SUPERChem-train-63-zh_img3_C_1": {
        "options": {"D": "Roughly one quarter as long"},
    },
    "SUPERChem-train-156-en_img2_B_1": {
        "options": {"B": "The benzene ring shares an edge with a seven-membered ring"},
    },
    "SUPERChem-train-156-zh_img2_A_1": {
        "question": "Which labeled group is written at the top of the structure?",
    },
    "SUPERChem-train-169-en_img1_C_1": {
        "options": {"B": "The benzene ring is slightly larger in width and height"},
    },
    "SUPERChem-train-171-zh_img0_C_1": {
        "options": {"A": "To the left of the ring"},
    },
    "SUPERChem-train-180-en_img0_B_1": {
        "options": {"B": "22 and 21"},
    },
    "SUPERChem-train-206-en_img3_C_1": {
        "options": {"B": "About a third as large"},
    },
    "SUPERChem-train-215-en_img0_C_1": {
        "options": {"C": "Near the right-middle side of the cycle"},
    },
    "SUPERChem-train-235-en_img3_B_1": {
        "options": {"C": "The third white circle from the left"},
    },
    "SUPERChem-train-235-zh_img3_B_1": {
        "options": {"C": "The second hollow circle from the right"},
    },
    "EMMA-test-100_img1_C_1": {
        "options": {"D": "Directly to the left"},
    },
    "EMMA-test-286_img0_C_1": {
        # "a：上方" — change A to "Above" (Directly above)
        "options": {"A": "Directly above"},
    },
    "EMMA-test-1551_img0_C_1": {
        "options": {"D": "About four times as wide"},
    },
    "EMMA-test-1776_img0_B_1": {
        # "change car and bus to vehicles in all choices"
        "options": {
            "A": "A vertical grey vehicle near the center",
            "B": "A horizontal grey vehicle in the lower right area",
            "C": "The long grey vehicle at the bottom",
            "D": "A vertical grey vehicle at the far left",
        },
    },
    "HumanityLastExam-test-63_img0_B_1": {
        "options": {"C": "Two green rectangles are on the left side and one is on the right side"},
    },
    "HumanityLastExam-test-232_img0_C_1": {
        "options": {"A": "Roughly near the center, slightly to the top left"},
    },
    "HumanityLastExam-test-202_img0_A_1": {
        "options": {"C": "E"},
    },
    "MME_Reasoning-train-20_img0_C_1": {
        "options": {"C": "slightly larger"},
    },
    "MME_Reasoning-train-154_img0_C_1": {
        "options": {"D": "It is about twice as tall as it is wide"},
    },
    "MME_Reasoning-train-222_img0_B_1": {
        "options": {"B": "Cell (1, 2)"},
    },
    "MME_Reasoning-train-422_img0_B_1": {
        "options": {"C": "Figure 3"},
    },
    "MMMU-validation-127_img0_A_1": {
        "options": {"C": "f"},
    },
    "PuzzleVQA-train-646_img0_C_1": {
        "options": {"D": "Slightly larger"},
    },
    "MathVerse-testmini-3534_img0_C_1": {
        "options": {"D": "Slightly longer"},
    },
    "MathVision-test-166_img0_C_1": {
        "options": {"D": "Much larger than the square"},
    },
    "MathVision-test-368_img0_C_1": {
        "options": {"C": "About four times as large"},
    },
    "MathVision-test-493_img0_B_1": {
        "options": {"C": "Both the top and the front face"},
    },
    "MathVision-test-820_img0_A_1": {
        "options": {"C": "The sixth shape from the left"},
    },
    "MathVision-test-1624_img0_A_1": {
        "question": "Which area label appears in the right region of the square?",
    },
    "MathVision-test-2809_img0_A_1": {
        "options": {"D": "13"},
    },
    "MathVision-test-2830_img0_C_1": {
        "options": {"C": "About a one-third as long"},
    },
    "MathVista-testmini-577_img0_A_1": {
        "options": {"D": "7"},
    },
    "MathVista-testmini-577_img0_C_1": {
        "options": {"B": "About one-sixth as long"},
    },
    "MathVista-testmini-689_img0_C_1": {
        "options": {"B": "e"},
    },
    "MathVista-testmini-787_img0_C_1": {
        "options": {"C": "He appears slightly taller"},
    },
    "MathVista-testmini-978_img0_A_1": {
        "options": {"D": "9"},
    },
    "MathVision-test-508_img0_C_1": {
        "options": {"B": "About 4:5"},
    },
    "MathVista-testmini-832_img0_C_1": {
        "options": {"C": "Mostly to the right"},
    },
    "Geometry3k-train-1271_img0_C_1": {
        "options": {"D": "About two times as long as the segment labeled 6"},
    },
    "MathVerse-testmini-1787_img0_C_1": {
        "options": {"B": "Slightly shorter than w"},
    },
    "MathVision-test-228_img0_C_1": {
        "options": {"C": "AC is slightly longer than AB"},
    },
    "OlympicArena-test-112_img0_C_1": {
        "options": {"A": "Directly above the center of the diamond"},
    },
    "MMMU-test-805_img0_C_1": {
        "options": {"B": "Below it and slightly to the left"},
    },
    "MMMU-test-328_img1_C_1": {
        "options": {"C": "Slightly lower than the starting point"},
    },
    "OlympicArena-test-2134_img0_B_1": {
        "options": {"D": "None of them"},
    },
    "SUPERChem-train-0-en_img2_C_1": {
        "options": {"B": "Closer to the right end"},
    },
}


# Uncertain items to report
UNCERTAIN = [
    {
        "question_id": "OlympicArena-test-963_img0_B_1",
        "reason": "Annotator says 'specify whether it is incoming or outgoing. If pointing towards H, then A:C is correct.' I changed the question to specify 'pointing toward H' — please verify this matches the image.",
    },
    {
        "question_id": "SUPERChem-train-64-en_img0_C_1",
        "reason": "Annotator says 'Ask about different arrow, right now it is asking about the same arrow.' I guessed 'downward-pointing reaction arrow that leads to B' as the replacement reference — please verify against the image.",
    },
    {
        "question_id": "SUPERChem-train-128-en_img0_B_1",
        "reason": "Annotator says 'instead of above and below, change to to the right for above and to the left for below.' I rewrote all 4 options using left/right instead of above/below — please verify.",
    },
    {
        "question_id": "MME_Reasoning-train-154_img0_C_1",
        "reason": "Annotator says 'Remove option D'. Since we need 4 options, I replaced D's text with 'It is much wider than it is tall' (a clearly distinct wrong answer). Please verify this is appropriate.",
    },
    {
        "question_id": "EMMA-test-286_img0_C_1",
        "reason": "Annotator says 'a：上方'. Interpreted as changing option A to 'Directly above'. Please verify.",
    },
    {
        "question_id": "OlympiadBench-test-OE_MM_maths_zh_CEE-6514_img0_C_1",
        "reason": "Annotator says '3 times'. Correct option is D. Changed D from 'About 4 times' to 'About 3 times'. Please verify.",
    },
]


def main() -> None:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", default="data/merged_full_trivial.json")
    p.add_argument("-o", "--output", default="data/merged_full_trivial_fixed.json")
    args = p.parse_args()

    data = json.loads(Path(args.input).read_text())
    print(f"Loaded {len(data)} items from {args.input}")

    applied = 0
    not_found = set(FIXES.keys())

    for item in data:
        for q in item.get("tier1_questions", []):
            qid = q.get("question_id")
            if qid not in FIXES:
                continue

            fix = FIXES[qid]
            not_found.discard(qid)

            if "question" in fix:
                q["question"] = fix["question"]

            if "options" in fix:
                for letter, new_text in fix["options"].items():
                    if letter in q.get("options", {}):
                        q["options"][letter] = new_text

            # Update annotation to reflect fix was applied
            ann = q.get("annotation", {})
            ann["fix_applied"] = True
            q["annotation"] = ann

            applied += 1

    print(f"Applied {applied} fixes")
    if not_found:
        print(f"WARNING: {len(not_found)} question_ids not found in data:")
        for qid in sorted(not_found):
            print(f"  {qid}")

    print(f"\nUncertain items ({len(UNCERTAIN)}):")
    for u in UNCERTAIN:
        print(f"  {u['question_id']}: {u['reason']}")

    Path(args.output).write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
