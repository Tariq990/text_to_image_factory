import logging

logger = logging.getLogger(__name__)


STYLE_PRESETS = {
    "cinematic realistic": {
        "quality": "cinematic, volumetric lighting, 8K, ultra-detailed, photorealistic",
        "negative": "cartoon, painting, illustration, 2D, flat lighting, low quality, blurry, distorted faces, extra limbs, bad anatomy",
    },
    "dark fantasy book cover": {
        "quality": "dark fantasy, intricate details, epic composition, dramatic shadows, gothic, mystical glow, oil painting texture",
        "negative": "bright, cheerful, cartoon, anime, oversaturated, low contrast, blurry, distorted faces, bad anatomy",
    },
    "historical realistic": {
        "quality": "historical realism, authentic period details, natural lighting, textured fabrics, documentary photography style",
        "negative": "fantasy, sci-fi, anachronistic, modern elements, cartoon, oversaturated, blurry, distorted faces",
    },
    "photorealistic YouTube thumbnail": {
        "quality": "photorealistic, hyper-detached, vibrant colors, sharp focus, high contrast, professional photography, 8K",
        "negative": "blurry, dark, low resolution, text, watermark, cluttered, distorted faces, bad anatomy",
    },
    "epic fantasy concept art": {
        "quality": "epic fantasy concept art, sweeping vistas, dramatic sky, magical atmosphere, intricate architecture, detailed textures",
        "negative": "modern, sci-fi, low detail, flat, blurry, distorted faces, extra limbs, bad anatomy",
    },
    "anime cinematic": {
        "quality": "anime style, cinematic composition, vibrant colors, detailed background, beautiful lighting, Makoto Shinkai aesthetic",
        "negative": "3D render, photorealistic, western comic, horror, gore, blurry, distorted faces, bad anatomy",
    },
    "mystery noir": {
        "quality": "film noir, high contrast, deep shadows, moody atmosphere, monochromatic with selective color, rain, smoke, city lights",
        "negative": "bright, cheerful, colorful, fantasy, oversaturated, cartoon, blurry, distorted faces",
    },
    "horror atmosphere": {
        "quality": "horror, dark atmospheric, eerie lighting, desaturated colors, grainy texture, abandoned, unsettling, dread",
        "negative": "bright, cheerful, cute, cartoon, colorful, comedy, blurry, distorted faces, bad anatomy",
    },
}


def build_prompt(scene_text: str, style: str = None, subject: str = None) -> dict:
    parts = []

    if subject:
        parts.append(subject)

    parts.append(scene_text)

    if style and style in STYLE_PRESETS:
        parts.append(STYLE_PRESETS[style]["quality"])
    else:
        parts.append("cinematic quality, ultra-detailed, professional photography")

    final_prompt = ", ".join(parts)

    if style and style in STYLE_PRESETS:
        negative_prompt = STYLE_PRESETS[style]["negative"]
    else:
        negative_prompt = "blurry, distorted faces, extra limbs, bad anatomy, low quality, watermark, text"

    return {"prompt": final_prompt, "negative_prompt": negative_prompt, "style": style or "none"}


def scene_to_prompt(scene: dict, style: str = None) -> dict:
    text = scene["text"]
    prompt_data = build_prompt(text, style)
    prompt_data["scene_index"] = scene["index"]
    prompt_data["scene_text"] = text
    return prompt_data
