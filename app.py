#!/usr/bin/env python3
"""
Text-to-Image Factory
A Colab-ready system for converting text, prompts, or story scenes
into high-quality AI images using Tongyi-MAI/Z-Image-Turbo (primary)
with FLUX.1-schnell fallback.
"""

import logging
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from modules import scene_splitter, prompt_builder, image_generator, storage, utils

logger = logging.getLogger(__name__)


def run_single(cfg, prompt_text: str, style: str = None, seed: int = None,
               width: int = None, height: int = None, steps: int = None,
               num_images: int = 1, output_dir: str = None):
    if output_dir is None:
        output_dir = cfg.OUTPUT_DIR
    cfg.ensure_dirs()

    prompt_data = prompt_builder.build_prompt(prompt_text, style)
    final_prompt = prompt_data["prompt"]
    neg = prompt_data["negative_prompt"]

    logger.info(f"Single mode | Final prompt: {final_prompt[:80]}...")
    gen = image_generator.ImageGenerator(cfg)
    results = gen.generate(final_prompt, negative_prompt=neg, seed=seed,
                           width=width, height=height, steps=steps,
                           num_images=num_images)

    saved = []
    for i, result in enumerate(results):
        info = storage.save_result(result, output_dir, scene_index=i + 1)
        saved.append(info)
        logger.info(f"[{i+1}/{len(results)}] image -> {info['image_path']}")

    gen.cleanup()
    return saved


def run_batch(cfg, prompts_file: str, style: str = None, seed: int = None,
              width: int = None, height: int = None, steps: int = None,
              output_dir: str = None):
    if output_dir is None:
        output_dir = cfg.OUTPUT_DIR
    cfg.ensure_dirs()

    prompts = scene_splitter.read_prompts_file(prompts_file)
    if not prompts:
        logger.error("No prompts found in file")
        return []

    logger.info(f"Batch mode | {len(prompts)} prompts loaded")
    gen = image_generator.ImageGenerator(cfg)
    saved = []

    for i, p in enumerate(prompts):
        prompt_data = prompt_builder.build_prompt(p, style)
        logger.info(f"Prompt {i+1}/{len(prompts)}: {prompt_data['prompt'][:60]}...")
        try:
            results = gen.generate(
                prompt_data["prompt"],
                negative_prompt=prompt_data["negative_prompt"],
                seed=(seed or cfg.SEED) + i,
                width=width, height=height, steps=steps, num_images=1
            )
            info = storage.save_result(results[0], output_dir, scene_index=i + 1)
            saved.append(info)
            logger.info(f"  -> {info['image_path']}")
        except Exception as e:
            logger.error(f"Batch item {i+1} failed: {e}")
            continue

    gen.cleanup()
    return saved


def run_story(cfg, story_file: str, style: str = None, seed: int = None,
              width: int = None, height: int = None, steps: int = None,
              output_dir: str = None):
    if output_dir is None:
        output_dir = cfg.OUTPUT_DIR
    cfg.ensure_dirs()

    text = scene_splitter.read_story_file(story_file)
    scenes = scene_splitter.split_story_into_scenes(text)

    if not scenes:
        logger.error("No scenes extracted from story")
        return []

    logger.info(f"Story mode | {len(scenes)} scenes")
    gen = image_generator.ImageGenerator(cfg)
    saved = []

    for scene in scenes:
        prompt_data = prompt_builder.scene_to_prompt(scene, style)
        logger.info(f"Scene {scene['index']}: {prompt_data['scene_text'][:60]}...")
        try:
            results = gen.generate(
                prompt_data["prompt"],
                negative_prompt=prompt_data["negative_prompt"],
                seed=(seed or cfg.SEED) + scene["index"],
                width=width, height=height, steps=steps, num_images=1
            )
            info = storage.save_result(results[0], output_dir, scene_index=scene["index"])

            info["metadata"]["scene_text"] = prompt_data["scene_text"]
            info["metadata"]["generated_prompt"] = prompt_data["prompt"]
            storage.save_metadata(info["metadata"], info["metadata_path"])

            saved.append(info)
            logger.info(f"  -> {info['image_path']}")
        except Exception as e:
            logger.error(f"Scene {scene['index']} failed: {e}")
            continue

    gen.cleanup()
    return saved


def launch_gradio(cfg):
    import gradio as gr

    cfg.ensure_dirs()

    def generate(prompt, style, seed, width, height, steps, num_images, mode, file_input):
        try:
            if mode == "Single":
                results = run_single(cfg, prompt, style=style, seed=seed,
                                     width=width, height=height, steps=steps,
                                     num_images=num_images)
            elif mode == "Batch":
                if not file_input:
                    return [], "No file provided", "", ""
                results = run_batch(cfg, file_input, style=style, seed=seed,
                                    width=width, height=height, steps=steps)
            elif mode == "Story":
                if not file_input:
                    return [], "No file provided", "", ""
                results = run_story(cfg, file_input, style=style, seed=seed,
                                    width=width, height=height, steps=steps)
            else:
                return [], "Unknown mode", "", ""

            paths = [r["image_path"] for r in results]
            prompts_text = "\n---\n".join([r["metadata"].get("prompt", "") for r in results])
            seeds_text = ", ".join([str(r["metadata"].get("seed", "")) for r in results])
            return paths, f"Generated {len(results)} images", prompts_text, seeds_text

        except Exception as e:
            logger.error(f"Gradio error: {traceback.format_exc()}")
            return [], f"Error: {e}", "", ""

    style_list = list(cfg.STYLE_PRESETS.keys()) + ["none"]

    with gr.Blocks(title="Text-to-Image Factory", theme=gr.themes.Soft()) as ui:
        gr.Markdown("# Text-to-Image Factory")
        gr.Markdown(f"Primary model: `{cfg.PRIMARY_MODEL}` | Fallback: `{cfg.FALLBACK_MODEL}`")

        with gr.Row():
            mode = gr.Radio(["Single", "Batch", "Story"], label="Mode", value="Single")
            style = gr.Dropdown(style_list, label="Style", value="cinematic realistic")

        with gr.Row():
            prompt = gr.Textbox(label="Prompt (Single mode)", lines=3, placeholder="Enter your prompt here...")
            file_input = gr.File(label="File (Batch/Story mode)", file_types=[".txt"], type="filepath")

        with gr.Row():
            seed = gr.Number(label="Seed (-1 for random)", value=-1, precision=0)
            num_images = gr.Number(label="Number of images", value=1, precision=0, minimum=1, maximum=8)
            steps = gr.Number(label="Steps", value=cfg.STEPS_PRIMARY, precision=0, minimum=1, maximum=50)

        with gr.Row():
            width = gr.Number(label="Width", value=cfg.WIDTH, precision=0, minimum=512, maximum=2048, step=64)
            height = gr.Number(label="Height", value=cfg.HEIGHT, precision=0, minimum=512, maximum=2048, step=64)

        btn = gr.Button("Generate", variant="primary")

        with gr.Row():
            status = gr.Textbox(label="Status", interactive=False)

        gallery = gr.Gallery(label="Output Images", columns=4, height="auto")
        out_prompts = gr.Textbox(label="Final Prompts", lines=5, interactive=False)
        out_seeds = gr.Textbox(label="Seeds", lines=1, interactive=False)

        btn.click(
            generate,
            inputs=[prompt, style, seed, width, height, steps, num_images, mode, file_input],
            outputs=[gallery, status, out_prompts, out_seeds],
        )

    ui.launch(share=True, debug=False)


def cli_main():
    args = utils.parse_cli_args()
    utils.setup_logging()

    cfg = Config

    if args.model:
        cfg.PRIMARY_MODEL = args.model
    if args.fallback_model:
        cfg.FALLBACK_MODEL = args.fallback_model
    if args.variant:
        cfg.MODEL_VARIANT = args.variant

    seed = args.seed if args.seed is not None else None

    if args.mode == "single":
        if not args.prompt:
            logger.error("--prompt required for single mode")
            sys.exit(1)
        run_single(cfg, args.prompt, style=args.style, seed=seed,
                   width=args.width, height=args.height, steps=args.steps,
                   num_images=args.num_images, output_dir=args.output_dir)

    elif args.mode == "batch":
        if not args.prompts:
            logger.error("--prompts file required for batch mode")
            sys.exit(1)
        run_batch(cfg, args.prompts, style=args.style, seed=seed,
                  width=args.width, height=args.height, steps=args.steps,
                  output_dir=args.output_dir)

    elif args.mode == "story":
        if not args.story:
            logger.error("--story file required for story mode")
            sys.exit(1)
        run_story(cfg, args.story, style=args.style, seed=seed,
                  width=args.width, height=args.height, steps=args.steps,
                  output_dir=args.output_dir)

    elif args.mode == "gradio":
        launch_gradio(cfg)

    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
