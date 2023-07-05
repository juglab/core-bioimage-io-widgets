import json
from pathlib import Path
from typing import Dict, List

from bioimageio.core.build_spec import build_model

from core_bioimage_io_widgets.resources import SITE_CONFIG, SPDX_LICENSES
from core_bioimage_io_widgets.utils.constants import PYTORCH_STATE_DICT
from core_bioimage_io_widgets.utils.schemas import model


def get_spdx_licenses() -> List[str]:
    """Read the SPDX licenses identifier from the json file.

    aquired from: https://github.com/spdx/license-list-data/tree/main/json
    """
    with open(SPDX_LICENSES) as f:
        licenses: List[Dict] = json.load(f).get("licenses", [])
    return [lic["licenseId"] for lic in licenses]


def get_predefined_tags() -> List[str]:
    """Extract tags out of the site.config.json file."""
    defined_tags = []
    with open(SITE_CONFIG) as f:
        resources_categories = json.load(f).get("resource_categories", [])
    if len(resources_categories) > 0:
        tag_categories = resources_categories[0].get("tag_categories", {})
        for _cat, tags in tag_categories.items():
            defined_tags.extend(tags)

    return defined_tags


def build_model_zip(model_data: dict, zip_file_path: str) -> model.Model:
    """Build bioimage model zip file from model specification data."""
    weight_type = list(model_data["weights"].keys())[0]
    weight_uri = model_data["weights"][weight_type]["source"]
    pytorch_state_dict_args = {}
    if weight_type == PYTORCH_STATE_DICT:
        pytorch_state_dict_args = {
            k: v for k, v in model_data["weight"][weight_type].items() if k != "source"
        }

    raw_model = build_model(
        output_path=zip_file_path,
        name=model_data["name"],
        weight_type=weight_type,
        weight_uri=weight_uri,
        architecture=pytorch_state_dict_args.get("architecture"),
        model_kwargs=pytorch_state_dict_args,
        test_inputs=model_data["test_inputs"],
        test_outputs=model_data["test_outputs"],
        input_names=[_input["name"] for _input in model_data["inputs"]],
        input_axes=[_input["axes"] for _input in model_data["inputs"]],
        preprocessing=[_input.get("preprocessing") for _input in model_data["inputs"]],
        output_names=[output["name"] for output in model_data["outputs"]],
        output_axes=[output["axes"] for output in model_data["outputs"]],
        halo=[output.get("halo") for output in model_data["outputs"]],
        postprocessing=[
            output.get("postprocessing") for output in model_data["outputs"]
        ],
        authors=model_data["authors"],
        cite=model_data["cite"],
        documentation=model_data["documentation"],
        description=model_data["description"],
        license=model_data["license"],
        # optionals
        covers=model_data.get("covers"),
        tags=model_data.get("tags"),
        root=Path(zip_file_path).parent,
    )

    return raw_model
