"""
Metadata Module
Handles loading and generating video metadata for uploads.
"""

import json
import yaml


def load_template(path):
    """
    Load metadata template from JSON or YAML file.
    Args:
        path: Path to template file
    Returns:
        Dict with template data
    """
    # TODO: Load JSON/YAML template
    pass


def generate_metadata(template, dynamic_values=None):
    """
    Generate metadata dict from template and dynamic values.
    Args:
        template: Dict with template fields
        dynamic_values: Optional dict to override/add fields
    Returns:
        Dict with final metadata (title, description, tags)
    """
    # TODO: Merge template and dynamic values
    pass
