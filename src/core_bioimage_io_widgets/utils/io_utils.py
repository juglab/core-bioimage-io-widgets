import json
from typing import List, Dict

from core_bioimage_io_widgets.resources import SPDX_LICENSES, SITE_CONFIG


def get_spdx_licenses():
    """Read the SPDX licenses identifier from the json file.

    aquired from: https://github.com/spdx/license-list-data/tree/main/json
    """
    with open(SPDX_LICENSES) as f:
        licenses: List[Dict] = json.load(f).get("licenses", [])
    return [lic["licenseId"] for lic in licenses]


def get_predefined_tags():
    """Extract tags out of the site.config.json file."""
    defined_tags = []
    with open(SITE_CONFIG) as f:
        resources_categories = json.load(f).get("resource_categories", [])
    if len(resources_categories) > 0:
        tag_categories = resources_categories[0].get("tag_categories", {})
        for cat, tags in tag_categories.items():
            defined_tags.extend(tags)

    return defined_tags
