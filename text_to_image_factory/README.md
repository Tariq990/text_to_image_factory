# Text-to-Image Factory

A Colab-ready system for converting text, prompts, or story scenes into high-quality AI images.

**Primary model:** Tongyi-MAI/Z-Image-Turbo  
**Fallback:** black-forest-labs/FLUX.1-schnell  
**Optional (future):** Qwen-VL-Chat (for images with readable text)

## Quick Start (Colab)

1. Open `notebooks/Run_Text_To_Image_Factory.ipynb` in Google Colab.
2. Run cells in order:
   - Mount Drive
   - Install dependencies
   - Set Hugging Face token (get one at https://huggingface.co/settings/tokens)
   - Clone the project
   - Run single/batch/story mode or launch Gradio

## Local Installation

```bash
pip install -r requirements.txt
```

## Usage

### Single prompt

```bash
python app.py --mode single --prompt "A cinematic old library at night" --style "cinematic realistic"
```

### Batch generation

```bash
python app.py --mode batch --prompts input/prompts.txt --style "epic fantasy concept art"
```

### Story mode

```bash
python app.py --mode story --story input/story.txt --style "dark fantasy book cover"
```

### Gradio UI

```bash
python app.py --mode gradio
```

## CLI Arguments

| Argument         | Description                          |
|------------------|--------------------------------------|
| `--mode`         | single, batch, story, gradio         |
| `--model`        | Override primary model               |
| `--fallback-model` | Override fallback model           |
| `--output-dir`   | Custom output directory              |
| `--width`        | Image width (default: 1024)          |
| `--height`       | Image height (default: 1024)         |
| `--steps`        | Inference steps                      |
| `--seed`         | Random seed                          |
| `--num-images`   | Number of images to generate         |
| `--style`        | Style preset (see config.py)         |
| `--prompt`       | Prompt text (single mode)            |
| `--prompts`      | Prompts file (batch mode)            |
| `--story`        | Story file (story mode)              |

## Style Presets

- cinematic realistic
- dark fantasy book cover
- historical realistic
- photorealistic YouTube thumbnail
- epic fantasy concept art
- anime cinematic
- mystery noir
- horror atmosphere

## Output Structure

```
output/
├── images/          # Generated PNG images
├── metadata/        # JSON metadata per image
└── grids/           # (future) composite grids
```

Each image has a matching metadata JSON file with: model name, prompt, final prompt, seed, steps, dimensions, timestamp, output path.

## Troubleshooting

### CUDA Out of Memory

- Clear cache: `torch.cuda.empty_cache()`
- Reduce width/height to 768 or 512
- Reduce steps (4 for FLUX, 6 for Z-Image-Turbo)
- Set `batch_size=1`
- The system auto-reduces on OOM

### Model fails to load

The system automatically falls back to FLUX.1-schnell. Make sure you're logged in to Hugging Face for gated models.

### Colab Free tier

Recommended settings:
- Width/Height: 768x768 or 1024x1024
- Steps: 6-8 for Z-Image-Turbo, 4 for FLUX
- Batch size: 1
- Use fp16 (enabled by default)

## Project Structure

```
text_to_image_factory/
├── app.py                # Main CLI and Gradio entry point
├── config.py             # Configuration and defaults
├── requirements.txt      # Dependencies
├── README.md             # This file
├── input/                # Input text files
│   ├── story.txt
│   └── prompts.txt
├── output/               # Generated outputs
│   ├── images/
│   ├── metadata/
│   └── grids/
├── modules/
│   ├── scene_splitter.py # Story text → scene splitting
│   ├── prompt_builder.py # Prompt construction with style presets
│   ├── image_generator.py # Model loading and image generation
│   ├── storage.py        # Save images and metadata
│   └── utils.py          # Logging, VRAM, Colab helpers
└── notebooks/
    └── Run_Text_To_Image_Factory.ipynb
```

## Extending

To add Qwen-Image support later:
- Add the model to `config.py`
- Add a `QwenImageGenerator` class in `modules/image_generator.py`
- Add a fallback chain in the existing generator

To add video generation:
- Add `modules/video_generator.py`
- Extend `app.py` with a `--mode video` option
