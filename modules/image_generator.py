import gc
import logging
import time
import torch

from diffusers import DiffusionPipeline, FluxPipeline, FluxTransformer2DModel
from transformers import T5EncoderModel
from huggingface_hub import login

logger = logging.getLogger(__name__)


class ImageGenerator:
    def __init__(self, config):
        self.config = config
        self.pipe = None
        self.model_name = None
        self.device = config.get_device()
        self._load_model()

    def _load_model(self):
        model = self.config.PRIMARY_MODEL
        logger.info(f"Loading model: {model}")
        logger.info(f"Device: {self.device}")

        self.config.setup_cache()

        try:
            if self.config.HF_TOKEN:
                login(token=self.config.HF_TOKEN)

            is_flux_dev = "flux" in model.lower() and "dev" in model.lower()

            if is_flux_dev and self.config.FLUX_FP8:
                self._load_flux_fp8(model)
                return

            for attempt, variant in enumerate([self.config.MODEL_VARIANT, None]):
                try:
                    kwargs = dict(
                        torch_dtype=self.config.DTYPE,
                        use_safetensors=True,
                        cache_dir=self.config.MODEL_CACHE_DIR,
                    )
                    if variant:
                        kwargs["variant"] = variant

                    if "flux" in model.lower() or "schnell" in model.lower():
                        self.pipe = FluxPipeline.from_pretrained(model, **kwargs)
                    else:
                        self.pipe = DiffusionPipeline.from_pretrained(model, **kwargs)

                    if self.device == "cuda":
                        self.pipe.enable_model_cpu_offload()
                        if hasattr(self.pipe, "enable_attention_slicing"):
                            self.pipe.enable_attention_slicing()
                        if hasattr(self.pipe.vae, "enable_slicing"):
                            self.pipe.vae.enable_slicing()
                        if hasattr(self.pipe.vae, "enable_tiling"):
                            self.pipe.vae.enable_tiling()
                    else:
                        self.pipe = self.pipe.to(self.device)

                    self.model_name = model
                    variant_tag = f" (variant={variant})" if variant else ""
                    logger.info(f"Model loaded: {model}{variant_tag}")
                    break
                except KeyboardInterrupt:
                    if attempt == 0 and variant is not None:
                        logger.warning("Interrupted during model load, retrying without variant...")
                        continue
                    logger.error("Interrupted during model load, all attempts exhausted")
                    raise
                except Exception as e:
                    if attempt == 0 and variant is not None:
                        logger.warning(f"Failed with variant={variant}, retrying without variant: {e}")
                        continue
                    raise

        except KeyboardInterrupt:
            logger.error("Model loading interrupted by user")
            raise
        except Exception as e:
            logger.error(f"Failed to load primary model {model}: {e}")
            self._load_fallback()

    def _load_flux_fp8(self, model):
        from optimum.quanto import freeze, qfloat8, quantize

        dtype = torch.bfloat16
        logger.info("Loading FLUX.1-dev with FP8 quantization...")

        transformer = FluxTransformer2DModel.from_single_file(
            "https://huggingface.co/Kijai/flux-fp8/blob/main/flux1-dev-fp8.safetensors",
            torch_dtype=dtype,
        )
        quantize(transformer, weights=qfloat8)
        freeze(transformer)

        text_encoder_2 = T5EncoderModel.from_pretrained(
            model, subfolder="text_encoder_2", torch_dtype=dtype,
            cache_dir=self.config.MODEL_CACHE_DIR,
        )
        quantize(text_encoder_2, weights=qfloat8)
        freeze(text_encoder_2)

        self.pipe = FluxPipeline.from_pretrained(
            model,
            transformer=None,
            text_encoder_2=None,
            torch_dtype=dtype,
            cache_dir=self.config.MODEL_CACHE_DIR,
        )
        self.pipe.transformer = transformer
        self.pipe.text_encoder_2 = text_encoder_2

        if self.device == "cuda":
            self.pipe.enable_model_cpu_offload()
            self.pipe.vae.enable_slicing()
            self.pipe.vae.enable_tiling()

        self.model_name = model
        logger.info("FLUX.1-dev FP8 loaded successfully")

    def _load_fallback(self):
        model = self.config.FALLBACK_MODEL
        logger.warning(f"Falling back to: {model}")
        self.config.setup_cache()
        try:
            for attempt, variant in enumerate([self.config.MODEL_VARIANT, None]):
                try:
                    kwargs = dict(
                        torch_dtype=self.config.DTYPE,
                        use_safetensors=True,
                        cache_dir=self.config.MODEL_CACHE_DIR,
                    )
                    if variant:
                        kwargs["variant"] = variant

                    if "flux" in model.lower() or "schnell" in model.lower():
                        self.pipe = FluxPipeline.from_pretrained(model, **kwargs)
                    else:
                        self.pipe = DiffusionPipeline.from_pretrained(model, **kwargs)

                    if self.device == "cuda":
                        self.pipe.enable_model_cpu_offload()
                        if hasattr(self.pipe, "enable_attention_slicing"):
                            self.pipe.enable_attention_slicing()
                        if hasattr(self.pipe.vae, "enable_slicing"):
                            self.pipe.vae.enable_slicing()
                        if hasattr(self.pipe.vae, "enable_tiling"):
                            self.pipe.vae.enable_tiling()
                    else:
                        self.pipe = self.pipe.to(self.device)
                    break
                except Exception as e:
                    if attempt == 0 and variant is not None:
                        logger.warning(f"Fallback: failed with variant={variant}, retrying: {e}")
                        continue
                    raise
            self.model_name = model
            logger.info(f"Fallback model loaded: {model}")
        except Exception as e2:
            logger.error(f"Fallback model also failed: {e2}")
            raise RuntimeError("Both primary and fallback models failed to load")

    def _get_steps(self):
        model = self.model_name.lower()
        if "schnell" in model:
            return self.config.STEPS_FALLBACK
        if "flux" in model:
            return self.config.STEPS_PRIMARY
        return self.config.STEPS_PRIMARY

    def generate(self, prompt: str, negative_prompt: str = "", seed: int = None, width: int = None,
                 height: int = None, steps: int = None, num_images: int = 1) -> list[dict]:
        if self.pipe is None:
            raise RuntimeError("No model loaded")

        if seed is None:
            seed = self.config.SEED
        if width is None:
            width = self.config.WIDTH
        if height is None:
            height = self.config.HEIGHT
        if steps is None:
            steps = self._get_steps()

        generator = torch.Generator(device="cpu").manual_seed(seed)

        logger.info(f"Generating {num_images} image(s) | prompt: {prompt[:60]}... | "
                    f"size: {width}x{height} | steps: {steps} | seed: {seed}")

        results = []

        for i in range(num_images):
            current_seed = seed + i
            gen = torch.Generator(device="cpu").manual_seed(current_seed)
            start = time.time()

            try:
                kwargs = {
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "num_inference_steps": steps,
                    "generator": gen,
                    "num_images_per_prompt": 1,
                }

                is_flux = "flux" in self.model_name.lower()
                if is_flux:
                    guidance = self.config.GUIDANCE_SCALE if "dev" in self.model_name.lower() else 0.0
                    kwargs["guidance_scale"] = guidance
                else:
                    kwargs["negative_prompt"] = negative_prompt if negative_prompt else None

                output = self.pipe(**kwargs)
                image = output.images[0]
                elapsed = time.time() - start

                logger.info(f"Image {i+1}/{num_images} generated in {elapsed:.2f}s")

                results.append({
                    "image": image,
                    "seed": current_seed,
                    "steps": steps,
                    "width": width,
                    "height": height,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "model": self.model_name,
                    "time_s": round(elapsed, 2),
                })

            except torch.cuda.OutOfMemoryError:
                logger.error("CUDA OOM — clearing cache and retrying with lower settings")
                torch.cuda.empty_cache()
                gc.collect()
                reduced_width = min(width, 768)
                reduced_height = min(height, 768)
                reduced_steps = max(steps // 2, 2)

                kwargs["width"] = reduced_width
                kwargs["height"] = reduced_height
                kwargs["num_inference_steps"] = reduced_steps
                kwargs["num_images_per_prompt"] = 1

                try:
                    output = self.pipe(**kwargs)
                    image = output.images[0]
                    elapsed = time.time() - start
                    logger.info(f"Image {i+1}/{num_images} generated (OOM recovery) in {elapsed:.2f}s")
                    results.append({
                        "image": image,
                        "seed": current_seed,
                        "steps": reduced_steps,
                        "width": reduced_width,
                        "height": reduced_height,
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "model": self.model_name,
                        "time_s": round(elapsed, 2),
                    })
                except Exception as e:
                    logger.error(f"OOM recovery also failed: {e}")
                    raise

            except Exception as e:
                logger.error(f"Generation failed for image {i+1}: {e}")
                raise

        return results

    def cleanup(self):
        if self.pipe is not None:
            del self.pipe
            self.pipe = None
        torch.cuda.empty_cache()
        gc.collect()
        logger.info("VRAM cleaned up")
