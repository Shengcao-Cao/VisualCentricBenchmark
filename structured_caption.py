import argparse
import json
import os

from gpt import GPT

cn_structured = """
你是一个得力的助手，负责将提供的图像转换为详细且结构化的描述。请遵循以下步骤：

1. 列出所有基础对象：
列出图像中出现的所有基础对象，并为它们分配唯一的名称。例如，对于电路图，最佳实践是列出所有电子元件以及导线的交叉点，并分别命名为"电阻1"、"电阻2"、"电容1"等。

2. 详细描述每个对象：
针对上一步列出的每个对象，进行尽可能详尽的描述。每个对象的描述需独立成段，以其分配的唯一名称开头，且至少包含以下要点：对象的类别；该对象在图像中的整体位置、朝向、尺寸和颜色（如果有的话）；它与图像中其他基础对象的关系。

3. 转换为 JSON 格式：
将上述详细描述转换为 JSON 格式。具体要求是将对象的属性（attributes）和关系（relation）提取为独立的条目，并将剩余信息保留在简明扼要的说明（description）中。请参考以下示例：

```
{
    "name": "电阻5",
    "category": "电阻",
    "description": "位于电路第二行的电阻",
    "attributes": {
        "position": "middle-left", 
        "orientation": "horizontal", 
        "color": "black", 
        "size": "standard"
    },
    "relation": {
        "part of": "电路", 
        "connecting": ["点A", "点B"]
    }
}
```
"""

en_structured = """
You are a helpful assistant that converts the provided image into a detailed, structured description. Follow the below steps:

1. List all basic objects in the image, and assign them unique names. For example, for a circuit diagram, a good practice is to list all electronic components as well as the intersection points of the wires, and then name them as "resistor-1", "resistor-2", "capacitor-1" and so on.

2. For each object listed before, describe the object with as many details as possible. Respond in one comprehensive paragraph starting with its unique name assigned, and at least include the below points: the category of the object; the overall position, orientation, size and color (if applicable) of the object in the image; its relation with other basic objects in the image.

3. Convert the detailed description into json format. Specifically, extract the attributes and relation of the object as separate entries, and keep the remaining information in a concise caption. Take the below as an example:
```
{
    "name": "resistor-5",
    "category": "resistor",
    "description": "a resistor placed in the second row of the circuit",
    "attributes": {"position": "middle-left", "orientation": "horizontal"}, // "color": "black", "size": "standard"
    "relation": {"part of": "circuit", "connecting": ["point-A", "point-B"]} //"contains": []
}
```
"""

def build_caption_prompt(data, image_dir):
    samples = []
    for sample in data:
        for figure_path in sample["figure_local_paths"]:
            content = [{"type": "image", "image_url": os.path.join(image_dir, figure_path)}]
            if sample["language"] == "ZH":
                content += [{"type": "text", "text": cn_structured}]
            else:
                content += [{"type": "text", "text": en_structured}]
            samples.append(content)
    return samples


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="mm_dataset")
    parser.add_argument("--model", type=str, default="gpt-5.2")
    parser.add_argument("--api_key", type=str, default=None)
    parser.add_argument("--n_limit", type=int, default=10)
    parser.add_argument("--output", type=str, default="saves/gpt_5_2_structured.json")
    args = parser.parse_args()

    problems = json.load(open(os.path.join(args.data, "problems.json"), "r", encoding="utf-8"))
    if args.n_limit > 0:
        problems = problems[:args.n_limit]

    image_dir = os.path.join(args.data, "images")
    prompts = build_caption_prompt(problems, image_dir)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    if args.model.startswith("gpt-"):
        model = GPT(model=args.model, api_key=args.api_key)
    else:
        raise ValueError(f"Unsupported model: {args.model}")

    responses = model.generate_batch(prompts)
    caption_index = 0
    for i in range(len(problems)):
        problems[i]["figure_captions"] = []
        for _ in problems[i]["figure_local_paths"]:
            problems[i]["figure_captions"].append(responses[caption_index])
            caption_index += 1
    assert caption_index == len(responses)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=2)
