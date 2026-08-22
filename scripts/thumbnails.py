#!/usr/bin/env python3
import json
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_PATH = ROOT / "src/generated/thumbnail-config.json"
FORMATS = {
    "vertical": "ThumbnailVertical",
}
VARIANTS = {"silhouette", "pixelated", "roulette"}
DEFAULT_DESIGN_VARIANT = "default"
TYPE_ASSET_DIR = ROOT / "public/images/guess-types/visible"
HIDDEN_TYPE_ASSET_DIR = ROOT / "public/images/guess-types/hidden"


def type_names() -> list[str]:
    return sorted(path.stem for path in TYPE_ASSET_DIR.glob("*.png"))


def type_slug(answer_type: str) -> str:
    return answer_type.casefold().replace(" ", "_")


def category_icon_path(answer_type: str) -> str:
    hidden = HIDDEN_TYPE_ASSET_DIR / f"{answer_type}.png"
    return f"images/guess-types/{'hidden' if hidden.is_file() else 'visible'}/{answer_type}.png"


def type_thumbnail_path(
    answer_type: str,
    platform: str,
    root: Path = ROOT,
    design_variant: str = DEFAULT_DESIGN_VARIANT,
) -> Path:
    type_dir = root / "out/thumbnails" / type_slug(answer_type) / design_variant
    return type_dir / f"{type_slug(answer_type)}.{platform}.jpg"


def _write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def copy_thumbnail_config(episode: dict) -> dict:
    answer_type = episode["answer"]["guessType"]
    thumbnail = deepcopy(episode["thumbnail"])
    thumbnail["platforms"] = {"vertical": thumbnail["platforms"]["vertical"]}
    return {
        "thumbnail": thumbnail,
        "answerType": answer_type,
        "categoryIcon": category_icon_path(answer_type),
        "rouletteIcons": deepcopy(episode["hook"]["rouletteIcons"]),
        "hintCount": len(episode["clues"]),
    }


def validate_config(config: dict) -> None:
    thumbnail = config["thumbnail"]
    answer_type = config.get("answerType")
    category_icon = config.get("categoryIcon")
    if not isinstance(answer_type, str) or not answer_type:
        raise RuntimeError("La miniatura requiere answerType")
    if category_icon != category_icon_path(answer_type):
        raise RuntimeError("categoryIcon debe ser el asset del tipo de respuesta")
    if "vertical" not in thumbnail.get("platforms", {}):
        raise RuntimeError("thumbnail.platforms debe definir vertical")
    if not set(thumbnail["platforms"].values()) <= VARIANTS:
        raise RuntimeError("thumbnail.platforms contiene una variante desconocida")
    if len(config.get("rouletteIcons", [])) != 7:
        raise RuntimeError("La miniatura requiere 7 iconos de ruleta")
    if config.get("hintCount") != 3:
        raise RuntimeError("La plantilla definitiva requiere exactamente 3 pistas")
    for src in [thumbnail["background"], category_icon, thumbnail["icon"], *config["rouletteIcons"]]:
        if not (ROOT / "public" / src).is_file():
            raise RuntimeError(f"Falta el asset de miniatura: {src}")


def write_config(config: dict) -> None:
    validate_config(config)
    _write_json(GENERATED_PATH, config)


def render_thumbnails(config: dict, stem: str | None = None) -> list[Path]:
    validate_config(config)
    write_config(config)
    if stem:
        output = (
            ROOT
            / config["thumbnail"]["outputDir"]
            / type_slug(config["answerType"])
            / DEFAULT_DESIGN_VARIANT
            / f"{stem}.vertical.jpg"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "node",
                "node_modules/@remotion/cli/remotion-cli.js",
                "still",
                FORMATS["vertical"],
                str(output),
                f"--props={json.dumps({'variant': config['thumbnail']['platforms']['vertical']})}",
            ],
            cwd=ROOT,
            check=True,
        )
        return [output]
    answer_types = type_names()
    outputs = [type_thumbnail_path(answer_type, "vertical") for answer_type in answer_types]
    if outputs and all(path.is_file() for path in outputs):
        write_config(config)
        return outputs

    for answer_type in answer_types:
        type_config = deepcopy(config)
        type_config["answerType"] = answer_type
        type_config["categoryIcon"] = category_icon_path(answer_type)
        write_config(type_config)
        for platform, composition in {"vertical": FORMATS["vertical"]}.items():
            output = type_thumbnail_path(answer_type, platform)
            output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    "node",
                    "node_modules/@remotion/cli/remotion-cli.js",
                    "still",
                    composition,
                    str(output),
                    f"--props={json.dumps({'variant': type_config['thumbnail']['platforms'][platform]})}",
                ],
                cwd=ROOT,
                check=True,
            )
    write_config(config)
    return outputs
