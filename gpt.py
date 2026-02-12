import base64
import concurrent.futures
import time
import os
from openai import OpenAI
from tqdm import tqdm


def encode_image(image_path):
    ext = image_path.split('.')[-1].lower()
    if ext == 'jpg':
        prefix = 'data:image/jpeg;base64,'
    elif ext == 'png':
        prefix = 'data:image/png;base64,'
    else:
        raise ValueError(f"Unsupported image format: {ext}")
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return prefix + encoded_string


class GPT:
    def __init__(self, model="gpt-5.2", api_key=None, max_attempts=5, max_workers=80):
        self.model = model
        if api_key is None:
            print("api_key not found, using system env variable OPENAI_API_KEY")
            api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.max_attempts = max_attempts
        self.max_workers = max_workers

    def generate_single(self, prompt):
        encoded_prompt = []
        for seg in prompt:
            if seg["type"] == "text":
                encoded_prompt.append({"type": "input_text", "text": seg["text"]})
            elif seg["type"] == "image":
                encoded_prompt.append({
                    "type": "input_image",
                    "image_url": encode_image(seg["image_url"])
                })
            else:
                raise ValueError(f"Unsupported segment type: {seg['type']}")

        attempt_count = 0
        while attempt_count < self.max_attempts:
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=[{"role": "user", "content": encoded_prompt}],
                    reasoning={"effort": "medium"},
                    text={"verbosity": "medium"},
                )
                return response.output_text
            except Exception as e:
                attempt_count += 1
                print(f"Error occurred when calling OpenAI API! {e}")
                time.sleep(5)
        return None

    def generate_batch(self, prompts):
        results = [None] * len(prompts)
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {}
            for index, prompt in enumerate(prompts):
                future = executor.submit(self.generate_single, prompt)
                future_to_index[future] = index
            for future in tqdm(concurrent.futures.as_completed(future_to_index),
                           total=len(prompts),
                           desc="Generating Responses",
                           unit="response"):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as exc:
                    print(f"Generated exception for {prompts[index]}: {exc}")
        return results
