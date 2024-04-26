import os
from pathlib import Path

import folder_paths

from .config import set_fal_credentials
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from .routes import *

COMFY_PATH = Path(os.path.dirname(folder_paths.__file__))
CUSTOM_NODES_PATH = COMFY_PATH / "custom_nodes"
FAL_CONNECTOR_PATH = CUSTOM_NODES_PATH / "ComfyUI-fal-Connector"
FAL_JS_PATH = FAL_CONNECTOR_PATH / "js"

WEB_DIRECTORY = "js"


set_fal_credentials()
