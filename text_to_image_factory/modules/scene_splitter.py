import re
import logging

logger = logging.getLogger(__name__)


def split_story_into_scenes(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        logger.warning("Empty story text provided")
        return []

    scenes = []

    numbered = re.split(r"\n\s*(?=\d+[.\)]\s)", text)
    if len(numbered) > 1:
        for i, block in enumerate(numbered):
            block = block.strip()
            if block:
                scenes.append({"index": i + 1, "text": block})
        logger.info(f"Split story into {len(scenes)} numbered scenes")
        return scenes

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) > 1:
        for i, para in enumerate(paragraphs):
            scenes.append({"index": i + 1, "text": para})
        logger.info(f"Split story into {len(scenes)} paragraph scenes")
        return scenes

    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > 1:
        for i, sent in enumerate(sentences):
            if sent.strip():
                scenes.append({"index": i + 1, "text": sent.strip()})
        logger.info(f"Split story into {len(scenes)} sentence scenes")
        return scenes

    scenes.append({"index": 1, "text": text})
    logger.info("Story treated as single scene")
    return scenes


def read_story_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_prompts_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    prompts = []
    current = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                prompts.append(" ".join(current))
                current = []
        else:
            current.append(stripped)
    if current:
        prompts.append(" ".join(current))
    logger.info(f"Read {len(prompts)} prompts from {path}")
    return prompts
