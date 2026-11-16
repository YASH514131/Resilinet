import os
import shutil
import glob
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASETS_DIR = BASE_DIR / "datasets"
OUTPUT_DIR = DATASETS_DIR / "unified_incidents"

UNIFIED_CLASSES = ["car_accident", "fire", "smoke", "flood"]

CLASS_MAPPINGS = {
    "car_accident": {
        0: 0,
        1: 0,
        2: 0,
    },
    "fire_accident": {
        0: 1,
        1: 2,
    },
    "flood_accident": {
        0: 3,
    }
}


def create_directory_structure():
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    for split in ["train", "valid", "test"]:
        (OUTPUT_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)


def process_dataset(dataset_name: str, train_limit: int = 2200, val_limit: int = 400, test_limit: int = 250):
    mapping = CLASS_MAPPINGS.get(dataset_name)
    if not mapping:
        return

    source_path = DATASETS_DIR / dataset_name
    split_map = {"train": "train", "val": "valid", "valid": "valid", "test": "test"}
    limit_map = {"train": train_limit, "valid": val_limit, "test": test_limit}

    for split_dir in source_path.iterdir():
        if not split_dir.is_dir() or split_dir.name not in split_map:
            continue

        target_split = split_map[split_dir.name]
        split_max = limit_map.get(target_split, 400)
        img_dir = split_dir / "images"
        lbl_dir = split_dir / "labels"

        if not img_dir.exists() or not lbl_dir.exists():
            continue

        label_files = list(lbl_dir.glob("*.txt"))
        random.seed(42)
        random.shuffle(label_files)

        copied_count = 0
        for lbl_file in label_files:
            if split_max and copied_count >= split_max:
                break

            img_candidates = list(img_dir.glob(f"{lbl_file.stem}.*"))
            if not img_candidates:
                continue
            src_img = img_candidates[0]

            new_lines = []
            with open(lbl_file, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    src_cls = int(parts[0])
                    target_cls = mapping.get(src_cls)
                    if target_cls is not None:
                        new_lines.append(f"{target_cls} " + " ".join(parts[1:]))

            if new_lines:
                unique_name = f"{dataset_name}_{src_img.name}"
                unique_lbl_name = f"{dataset_name}_{lbl_file.name}"

                dest_img = OUTPUT_DIR / "images" / target_split / unique_name
                dest_lbl = OUTPUT_DIR / "labels" / target_split / unique_lbl_name

                shutil.copy2(src_img, dest_img)
                with open(dest_lbl, "w") as out_f:
                    out_f.write("\n".join(new_lines) + "\n")

                copied_count += 1

        print(f"Processed {dataset_name} ({target_split}): {copied_count} items")


def create_unified_yaml():
    yaml_text = f"""path: {OUTPUT_DIR.as_posix()}
train: images/train
val: images/valid
test: images/test

names:
  0: car_accident
  1: fire
  2: smoke
  3: flood
"""
    yaml_path = OUTPUT_DIR / "data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_text)


if __name__ == "__main__":
    create_directory_structure()
    for ds in ["car_accident", "fire_accident", "flood_accident"]:
        process_dataset(ds, train_limit=2200, val_limit=400, test_limit=250)
    create_unified_yaml()
