import random
import string
import os
import json
import random

from PIL import Image, ImageOps, ImageSequence
from PIL.PngImagePlugin import PngInfo
import numpy as np
from comfy.cli_args import args
import folder_paths
from ..download_utils import download_file_temp


class IntegerInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": f"int_{get_random_short_id()}"}),
                "number": ("INT", {"default": 0}),
                "min": ("INT", {"default": -(2**31)}),
                "max": ("INT", {"default": 2**31 - 1}),
                "step": ("INT", {"default": 1}),
            }
        }

    RETURN_TYPES = ("INT",)
    FUNCTION = "get_number"

    def get_number(self, name, number, min, max, step):
        return (number,)


class FloatInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": f"float_{get_random_short_id()}"}),
                "number": ("FLOAT", {"default": 0}),
                "min": ("FLOAT", {"default": -float(2**31)}),
                "max": ("FLOAT", {"default": float(2**31)}),
                "step": ("FLOAT", {"default": 0.1}),
            }
        }

    RETURN_TYPES = ("FLOAT",)
    FUNCTION = "get_number"

    def get_number(self, name, number, min, max, step):
        return (number,)


class BooleanInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": f"bool_{get_random_short_id()}"}),
                "value": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "get_value"

    def get_value(self, name, value):
        return (value,)


class StringInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": f"str_{get_random_short_id()}"}),
                "value": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_value"

    def get_value(self, name, value):
        return (value,)


class SaveImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                 "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "output_name": (
                    "STRING",
                    {"default": f"output_{get_random_short_id()}"},
                ),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "image"

    def save_images(
        self, images, output_name, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None
    ):
        if not output_name:
            raise ValueError("Output name is required")

        filename_prefix += self.prefix_append
        (
            full_output_folder,
            filename,
            counter,
            subfolder,
            filename_prefix,
        ) = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )
        results = list()
        for batch_number, image in enumerate(images):
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"
            img.save(
                os.path.join(full_output_folder, file),
                pnginfo=metadata,
                compress_level=self.compress_level,
            )
            results.append(
                {"filename": file, "subfolder": subfolder, "type": self.type}
            )
            counter += 1

        return {"ui": {"images": results}}
    

# Based on https://github.com/comfyanonymous/ComfyUI/blob/04e8798c37d958d74ea6bda506b86f51356d6caf/nodes.py#L1471-L1526
class LoadImageFromURL:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "default": "https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/input/example.png"
                    },
                ),
            }
        }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"

    def load_image(self, url: string):
        import torch

        with download_file_temp(url) as image_path:
            img = Image.open(image_path)

        output_images = []
        output_masks = []
        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)

            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))

            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]

            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")

            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))

        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        return (output_image, output_mask)


def get_random_short_id():
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=8))


NODE_CLASS_MAPPINGS = {
    "IntegerInput_fal": IntegerInput,
    "FloatInput_fal": FloatInput,
    "BooleanInput_fal": BooleanInput,
    "StringInput_fal": StringInput,
    "SaveImage_fal": SaveImage,
    "LoadImageFromURL_fal": LoadImageFromURL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IntegerInput_fal": "Integer Input (fal)",
    "FloatInput_fal": "Float Input (fal)",
    "BooleanInput_fal": "Boolean Input (fal)",
    "StringInput_fal": "String Input (fal)",
    "SaveImage_fal": "Save Image (fal)",
    "LoadImageFromURL_fal": "Load Image From URL (fal)",
}