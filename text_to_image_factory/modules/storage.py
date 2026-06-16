import json
import logging
import os
from datetime import datetime

from PIL import Image

logger = logging.getLogger(__name__)


def save_image(image: Image.Image, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, "PNG")
    logger.info(f"Image saved: {path}")
    return path


def save_metadata(meta: dict, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    logger.info(f"Metadata saved: {path}")
    return path


def build_metadata(result: dict, output_path: str) -> dict:
    return {
        "model": result.get("model", "unknown"),
        "prompt": result.get("prompt", ""),
        "negative_prompt": result.get("negative_prompt", ""),
        "seed": result.get("seed"),
        "steps": result.get("steps"),
        "width": result.get("width"),
        "height": result.get("height"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "generation_time_s": result.get("time_s"),
        "output_path": output_path,
    }


def save_result(result: dict, output_dir: str, scene_index: int = 1) -> dict:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"scene_{scene_index:03d}_{timestamp}"
    image_path = os.path.join(output_dir, "images", f"{filename}.png")
    meta_path = os.path.join(output_dir, "metadata", f"{filename}.json")

    save_image(result["image"], image_path)
    meta = build_metadata(result, image_path)
    meta["scene_index"] = scene_index
    save_metadata(meta, meta_path)

    return {"image_path": image_path, "metadata_path": meta_path, "metadata": meta}
