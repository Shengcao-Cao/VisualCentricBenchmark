"""Task 4: Generate structured captions for each image in each question."""

import copy
import json
from pathlib import Path

from client import VLMClient
from utils import run_batch


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

CAPTION_PROMPT = en_structured

def extract_structured_captions(response: str) -> dict:
    """Extract structured captions from the model response."""
    # The structured caption is included in a ```json``` block. Extract the content in between.
    start = response.find("```json")
    if start == -1:
        raise ValueError("No ```json block found in the response.")
    start += len("```json")
    end = response.find("```", start)
    if end == -1:
        raise ValueError("No closing ``` found in the response.")
    json_str = response[start:end].strip()
    return json.loads(json_str)

async def run_structured(
    data: list[dict],
    client: VLMClient,
    model_key: str,
    base_dir: str | Path,
    concurrency: int = 10,
    max_retries: int = 3,
) -> list[dict]:
    """Caption each image and store under item["model"][model_key]["captions"]."""
    base_dir = Path(base_dir)

    async def process(item: dict) -> dict:
        item = copy.deepcopy(item)
        captions = []

        for img_path in item["images"]:
            image_part = client.encode_image(base_dir / img_path)
            messages = [
                {
                    "role": "user",
                    "content": [
                        image_part,
                        {"type": "text", "text": CAPTION_PROMPT},
                    ],
                }
            ]
            # Retry a few times if the model fails to respond with a valid caption.
            for _ in range(max_retries):
                try:
                    caption = await client.chat(messages)
                    # Try to extract the structured caption from the model response. If it fails, retry.
                    caption = extract_structured_captions(caption)
                    break
                except Exception as e:
                    print(f"Error processing {img_path}: {e}. Retrying...")
            else:
                print(f"Failed to process {img_path} after {max_retries} retries. Skipping.")
                caption = None
            captions.append(caption)

        item.setdefault("model", {}).setdefault(model_key, {})["captions"] = captions
        return item

    return await run_batch(data, process, concurrency=concurrency, desc="Captioning")
