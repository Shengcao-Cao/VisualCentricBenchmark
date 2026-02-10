import argparse
import json
import json_repair

from gpt import GPT


def build_judge_prompt(data):
    samples = []
    for sample in data:
        prompt_text = "Please extract the final answer from the model's response and compare it with the correct answer.\n"
        prompt_text += "Focus on the final answer provided by the model and its correctness, ignoring any intermediate reasoning steps or specific formatting.\n\n"
        prompt_text += "Here is the model's response:\n"
        prompt_text += sample["model_response"] + "\n\n"
        if len(sample["answer"]) == 1:
            prompt_text += "The correct answer is:\n"
            prompt_text += sample["answer"][0] + "\n\n"
        else:
            prompt_text += "The sequence of correct answers is:\n"
            prompt_text += ", ".join(sample["answer"]) + "\n\n"
        prompt_text += "Based on the above, provide your response in JSON format as follows:\n"
        prompt_text += '```\n'
        prompt_text += '{ "extracted_model_answer": "<final answer extracted from the model response>",\n'
        prompt_text += '  "is_correct": <true if the model answer matches the correct answer, false otherwise> }\n'
        prompt_text += '```\n'
        samples.append([{"type": "text", "text": prompt_text}])
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str)
    parser.add_argument("--output", type=str)
    parser.add_argument("--model", type=str, default="gpt-5.2")
    parser.add_argument("--api_key", type=str, default=None)
    args = parser.parse_args()

    problems = json.load(open(args.input, "r", encoding="utf-8"))
    prompts = build_judge_prompt(problems)

    if args.model.startswith("gpt-"):
        judger = GPT(model=args.model, api_key=args.api_key)
    else:
        raise ValueError(f"Unsupported model: {args.model}")

    responses = judger.generate_batch(prompts)
    correct_count = 0
    total_count = 0
    for i in range(len(problems)):
        try:
            repaired_response = json_repair.repair_json(responses[i])
            judge_result = json.loads(repaired_response)
            problems[i]["judge_response"] = repaired_response
            is_correct = judge_result.get("is_correct", False)
            problems[i]["extracted_model_answer"] = judge_result.get("extracted_model_answer", "")
            problems[i]["is_correct"] = is_correct
            if is_correct:
                correct_count += 1
            total_count += 1
        except Exception as e:
            print(f"Error processing response for problem {i}: {e}")

    accuracy = correct_count / total_count if total_count > 0 else 0.0
    print(f"Accuracy: {accuracy:.2%} ({correct_count}/{total_count})")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
