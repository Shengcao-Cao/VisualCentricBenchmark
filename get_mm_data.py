import json
import os
import re
import requests
from datasets import load_dataset, concatenate_datasets
from tqdm import tqdm

hf_data_path = "GAIR/OlympicArena"
split = "val"
subjects = ["Math", "Physics", "Chemistry", "Biology", "Geography", "Astronomy", "CS"]
save_dir = "mm_dataset"
save_json_path = f"{save_dir}/problems.json"
save_image_dir = f"{save_dir}/images"

dataset = []
for subject in subjects:
    dataset.append(load_dataset(hf_data_path, subject, split=split))

dataset = concatenate_datasets(dataset)
mm_dataset = [sample for sample in dataset if sample["figure_urls"] and sample["subject"] != "CS"]

count_by_subject = {}
for subject in subjects:
    count_by_subject[subject] = len([sample for sample in mm_dataset if sample["subject"] == subject])

# {'Math': 31, 'Physics': 59, 'Chemistry': 39, 'Biology': 35, 'Geography': 63, 'Astronomy': 65, 'CS': 0}
print(count_by_subject)

os.makedirs(save_image_dir, exist_ok=True)

valid_mm_dataset = []
for sample in tqdm(mm_dataset, desc="Processing samples"):
    if sample["language"] == "ZH":
        segments = re.split(r'(\[图\d+\])', sample["prompt"])
    else:
        segments = re.split(r'(\[figure\d+\])', sample["prompt"])
    n_image_segments = len([seg for seg in segments if seg.startswith('[')])
    if n_image_segments == 0:
        continue
    all_images_accessible = True
    images = []
    for image_index, url in enumerate(sample["figure_urls"]):
        try:
            response = requests.head(url, timeout=5)
            if response.status_code != 200:
                all_images_accessible = False
                print(f"Image not accessible: {url}")
                break
            if not response.headers.get('Content-Type', '').startswith('image/'):
                all_images_accessible = False
                print(f"URL does not point to an image: {url}")
                break
            image_response = requests.get(url, timeout=10)
            if image_response.status_code == 200:
                image_extension = url.split('.')[-1].split('?')[0]
                image_filename = f"{sample['id']}_fig{image_index + 1}.{image_extension}"
                image_path = os.path.join(save_image_dir, image_filename)
                with open(image_path, 'wb') as f:
                    f.write(image_response.content)
                images.append(image_filename)
            else:
                all_images_accessible = False
                print(f"Failed to download image: {url}")
                break
        except requests.RequestException:
            all_images_accessible = False
            print(f"Image not accessible: {url}")
            break
    if all_images_accessible:
        sample["figure_local_paths"] = images
        valid_mm_dataset.append(sample)

with open(save_json_path, "w", encoding="utf-8") as f:
    json.dump(valid_mm_dataset, f, ensure_ascii=False, indent=2)

count_by_subject = {}
for subject in subjects:
    count_by_subject[subject] = len([sample for sample in valid_mm_dataset if sample["subject"] == subject])

# {'Math': 14, 'Physics': 55, 'Chemistry': 38, 'Biology': 35, 'Geography': 63, 'Astronomy': 63, 'CS': 0}
print(count_by_subject)

# valid_mm_dataset = json.load(open(save_json_path, "r", encoding="utf-8"))
# for sample in valid_mm_dataset:
#     if sample["language"] == "ZH":
#         segments = re.split(r'(\[图\d+\])', sample["prompt"])
#     else:
#         segments = re.split(r'(\[figure\d+\])', sample["prompt"])
#     n_image_segments = len([seg for seg in segments if seg.startswith('[')])
#     if not (n_image_segments == len(sample["figure_local_paths"]) and n_image_segments == len(sample["figure_urls"])):
#         print(f"Mismatch in number of images for sample ID {sample['id']}: {n_image_segments} image segments, {len(sample['figure_local_paths'])} local paths, {len(sample['figure_urls'])} URLs.")

# id_to_sample = {sample["id"]: sample for sample in valid_mm_dataset}
# problemetic_ids = ["Physics_1346", "Chemistry_811", "Biology_493", "Geography_583", "Astronomy_2"]
# for id in problemetic_ids:
#     print(id)
#     print(id_to_sample[id]["problem"])
#     print(id_to_sample[id]["solution"])
#     print("#" * 40)
