"""
Metadata Module
Handles loading and generating video metadata for uploads.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class UploadMetadata:
    """Strongly typed metadata structure for uploads."""

    title: str
    description: str
    tags: list[str]
    visibility: str
    made_for_kids: bool

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "visibility": self.visibility,
            "made_for_kids": self.made_for_kids,
        }


def load_template(path: str) -> dict:
    """Load metadata template from JSON or YAML file."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Metadata template not found: {path}")

    suffix = config_path.suffix.lower()
    with open(config_path, "r", encoding="utf-8") as fh:
        if suffix == ".json":
            return json.load(fh)
        if suffix in {".yml", ".yaml"}:
            return yaml.safe_load(fh)
    raise ValueError("Unsupported metadata template format; use .json or .yaml")


def _parse_tags(raw_tags) -> list[str]:
    if not raw_tags:
        return []
    if isinstance(raw_tags, list):
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    return [tag.strip() for tag in str(raw_tags).split(",") if tag.strip()]


def generate_metadata(template: dict | None, dynamic_values: dict | None = None) -> UploadMetadata:
    """Combine template defaults with runtime overrides."""

    template = template or {}
    overrides = dynamic_values or {}

    merged = {**template, **overrides}

    return UploadMetadata(
        title=str(merged.get("title", "")),
        description=str(merged.get("description", "")),
        tags=_parse_tags(merged.get("tags")),
        visibility=str(merged.get("visibility", "unlisted")).lower(),
        made_for_kids=bool(merged.get("made_for_kids", False)),
    )


def build_metadata_from_form(
    title: str,
    description: str,
    tags: str,
    visibility: str,
    made_for_kids: bool,
    template: dict | None = None
) -> UploadMetadata:
    """Helper for GUIs to create metadata without duplication."""

    dynamic = {
        "title": title,
        "description": description,
        "tags": tags,
        "visibility": visibility,
        "made_for_kids": made_for_kids,
    }

    return generate_metadata(template, dynamic)


def save_metadata(metadata: UploadMetadata, path: str) -> None:
    """Export metadata to a JSON file."""
    
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(metadata.as_dict(), fh, indent=2, ensure_ascii=False)


def save_metadata_template(
    title: str = "",
    description: str = "",
    tags: list[str] | None = None,
    visibility: str = "unlisted",
    made_for_kids: bool = False,
    path: str = "metadata_template.json"
) -> None:
    """Generate and save a metadata template file for reuse."""
    
    template_data = {
        "title": title,
        "description": description,
        "tags": tags or [],
        "visibility": visibility,
        "made_for_kids": made_for_kids,
    }
    
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(template_data, fh, indent=2, ensure_ascii=False)
