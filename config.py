import os


class Config:
    # ── Models ──────────────────────────────────────────
    PRIMARY_MODEL = "black-forest-labs/FLUX.1-dev"
    FALLBACK_MODEL = "black-forest-labs/FLUX.1-schnell"
    OPTIONAL_MODEL = "Tongyi-MAI/Z-Image-Turbo"

    # ── Generation defaults ─────────────────────────────
    WIDTH = 1024
    HEIGHT = 1024
    STEPS_PRIMARY = 20
    STEPS_FALLBACK = 4
    FLUX_FP8 = True
    GUIDANCE_SCALE = 3.5
    BATCH_SIZE = 1
    SEED = 42
    OUTPUT_FORMAT = "PNG"
    METADATA_FORMAT = "JSON"

    # ── Paths ───────────────────────────────────────────
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(BASE_DIR, "input")
    OUTPUT_DIR = os.path.join(BASE_DIR, "output")
    IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
    METADATA_DIR = os.path.join(OUTPUT_DIR, "metadata")
    GRIDS_DIR = os.path.join(OUTPUT_DIR, "grids")

    # Drive path used inside Colab
    DRIVE_BASE = "/content/drive/MyDrive/text_to_image_factory"
    DRIVE_OUTPUT = os.path.join(DRIVE_BASE, "output")
    MODEL_CACHE_DIR = os.path.join(DRIVE_BASE, "model_cache")

    # ── Hugging Face ────────────────────────────────────
    HF_TOKEN = os.environ.get("HF_TOKEN", None)

    # ── Device ──────────────────────────────────────────
    DEVICE = None
    DTYPE = None
    MODEL_VARIANT = "fp16"

    @classmethod
    def get_device(cls):
        if cls.DEVICE is not None:
            return cls.DEVICE
        try:
            import torch
            cls.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
            cls.DTYPE = torch.float16 if cls.DEVICE == "cuda" else torch.float32
        except ImportError:
            cls.DEVICE = "cpu"
            cls.DTYPE = None
        return cls.DEVICE

    @classmethod
    def get_dtype(cls):
        if cls.DTYPE is None:
            cls.get_device()
        return cls.DTYPE

    # ── Style presets ───────────────────────────────────
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

    @classmethod
    def ensure_dirs(cls, base_dir=None):
        if base_dir is None:
            base_dir = cls.BASE_DIR
        for d in [cls.INPUT_DIR, cls.IMAGES_DIR, cls.METADATA_DIR, cls.GRIDS_DIR]:
            os.makedirs(d, exist_ok=True)

    @classmethod
    def ensure_cache_dirs(cls):
        os.makedirs(cls.MODEL_CACHE_DIR, exist_ok=True)

    @classmethod
    def setup_cache(cls):
        if cls.is_colab():
            cls.ensure_cache_dirs()
            os.environ["HF_HOME"] = cls.MODEL_CACHE_DIR
            os.environ["HF_HUB_CACHE"] = os.path.join(cls.MODEL_CACHE_DIR, "hub")
            os.environ["XDG_CACHE_HOME"] = cls.MODEL_CACHE_DIR

    @classmethod
    def is_colab(cls):
        try:
            import google.colab
            return True
        except ImportError:
            return False
