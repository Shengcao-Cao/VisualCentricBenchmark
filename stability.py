import argparse
import json
import numpy as np


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()

    correctness_all = []
    accuracy_all = []
    for run in range(args.runs):
        path = args.input.replace(".json", f"_r{run+1}.json")
        problems = json.load(open(path, "r", encoding="utf-8"))
        problems.sort(key=lambda x: x["id"])
        correctness = [problem["is_correct"] for problem in problems]
        accuracy = sum(correctness) / len(correctness)
        correctness_all.append(correctness)
        accuracy_all.append(accuracy)

    accuracy_mean = np.mean(accuracy_all)
    accuracy_std = np.std(accuracy_all)
    print(f"Accuracy over {args.runs} runs: {accuracy_all} ({accuracy_mean*100:.2f}% ± {accuracy_std*100:.2f}%)")

    correctness_all = np.array(correctness_all)
    correctness_all = correctness_all.sum(axis=0)
    for i in range(args.runs + 1):
        num_problems = (correctness_all == i).sum()
        print(f"Number of problems with correctness {i}/{args.runs}: {num_problems}")
    instable_problems = (correctness_all > 0) & (correctness_all < args.runs)
    print(f"Number of instable problems: {instable_problems.sum()}")

    print("IDs of stable problems:")
    print([problems[i]["id"] for i in range(len(problems)) if correctness_all[i] == args.runs])
