import gc
import logging
import os
import sys
import torch


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    return logging.getLogger(__name__)


def clear_vram():
    torch.cuda.empty_cache()
    gc.collect()


def ensure_colab_drive():
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        return True
    except ImportError:
        return False


def resolve_output_dir(config, use_drive: bool = False):
    if use_drive and config.is_colab():
        d = config.DRIVE_OUTPUT
    else:
        d = config.OUTPUT_DIR
    os.makedirs(os.path.join(d, "images"), exist_ok=True)
    os.makedirs(os.path.join(d, "metadata"), exist_ok=True)
    os.makedirs(os.path.join(d, "grids"), exist_ok=True)
    return d


def parse_cli_args():
    import argparse
    parser = argparse.ArgumentParser(description="Text-to-Image Factory")
    parser.add_argument("--mode", choices=["single", "batch", "story", "gradio"], default="gradio")
    parser.add_argument("--model", default=None)
    parser.add_argument("--fallback-model", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--num-images", type=int, default=1)
    parser.add_argument("--variant", default=None)
    parser.add_argument("--style", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--prompts", default=None)
    parser.add_argument("--story", default=None)
    return parser.parse_args()
