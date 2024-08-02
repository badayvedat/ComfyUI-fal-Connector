import io
import os

import numpy as np
import requests
from fal_client import submit
from PIL import Image


class FluxPro:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image_size": (
                    [
                        "square_hd",
                        "square",
                        "portrait_4_3",
                        "portrait_16_9",
                        "landscape_4_3",
                        "landscape_16_9",
                    ],
                    {"default": "landscape_4_3"},
                ),
                "num_inference_steps": ("INT", {"default": 28, "min": 1, "max": 100}),
                "guidance_scale": ("FLOAT", {"default": 3.5, "min": 0.0, "max": 20.0}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 10}),
                "safety_tolerance": (["1", "2", "3", "4", "5", "6"], {"default": "2"}),
            },
            "optional": {
                "seed": ("INT", {"default": -1}),
                "api_key": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "FAL"

    def generate_image(
        self,
        prompt,
        image_size,
        num_inference_steps,
        guidance_scale,
        num_images,
        safety_tolerance,
        seed=-1,
        api_key="",
    ):
        if api_key:
            os.environ["FAL_KEY"] = api_key

        arguments = {
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_images": num_images,
            "safety_tolerance": safety_tolerance,
        }
        if seed != -1:
            arguments["seed"] = seed

        try:
            handler = submit("fal-ai/flux-pro", arguments=arguments)
            result = handler.get()
            return self.process_result(result)
        except Exception as e:
            print(f"Error generating image with FluxPro: {str(e)}")
            return self.create_blank_image()


class FluxDev:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image_size": (
                    [
                        "square_hd",
                        "square",
                        "portrait_4_3",
                        "portrait_16_9",
                        "landscape_4_3",
                        "landscape_16_9",
                    ],
                    {"default": "landscape_4_3"},
                ),
                "num_inference_steps": ("INT", {"default": 28, "min": 1, "max": 100}),
                "guidance_scale": ("FLOAT", {"default": 3.5, "min": 0.0, "max": 20.0}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 10}),
                "enable_safety_checker": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "seed": ("INT", {"default": -1}),
                "api_key": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "FAL"

    def generate_image(
        self,
        prompt,
        image_size,
        num_inference_steps,
        guidance_scale,
        num_images,
        enable_safety_checker,
        seed=-1,
        api_key="",
    ):
        if api_key:
            os.environ["FAL_KEY"] = api_key

        arguments = {
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_images": num_images,
            "enable_safety_checker": enable_safety_checker,
        }
        if seed != -1:
            arguments["seed"] = seed

        try:
            handler = submit("fal-ai/flux/dev", arguments=arguments)
            result = handler.get()
            return self.process_result(result)
        except Exception as e:
            print(f"Error generating image with FluxDev: {str(e)}")
            return self.create_blank_image()


class FluxSchnell:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "image_size": (
                    [
                        "square_hd",
                        "square",
                        "portrait_4_3",
                        "portrait_16_9",
                        "landscape_4_3",
                        "landscape_16_9",
                    ],
                    {"default": "landscape_4_3"},
                ),
                "num_inference_steps": ("INT", {"default": 4, "min": 1, "max": 100}),
                "num_images": ("INT", {"default": 1, "min": 1, "max": 10}),
                "enable_safety_checker": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "seed": ("INT", {"default": -1}),
                "api_key": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate_image"
    CATEGORY = "FAL"

    def generate_image(
        self,
        prompt,
        image_size,
        num_inference_steps,
        num_images,
        enable_safety_checker,
        seed=-1,
        api_key="",
    ):
        if api_key:
            os.environ["FAL_KEY"] = api_key

        arguments = {
            "prompt": prompt,
            "image_size": image_size,
            "num_inference_steps": num_inference_steps,
            "num_images": num_images,
            "enable_safety_checker": enable_safety_checker,
        }
        if seed != -1:
            arguments["seed"] = seed

        try:
            handler = submit("fal-ai/flux/schnell", arguments=arguments)
            result = handler.get()
            return self.process_result(result)
        except Exception as e:
            print(f"Error generating image with FluxSchnell: {str(e)}")
            return self.create_blank_image()


# Common methods for all classes
def process_result(self, result):
    import torch

    images = []
    for img_info in result["images"]:
        img_url = img_info["url"]
        img_response = requests.get(img_url)
        img = Image.open(io.BytesIO(img_response.content))
        img_array = np.array(img).astype(np.float32) / 255.0
        images.append(img_array)

    # Stack the images along a new first dimension
    stacked_images = np.stack(images, axis=0)

    # Convert to PyTorch tensor
    img_tensor = torch.from_numpy(stacked_images)

    return (img_tensor,)


def create_blank_image(self):
    import torch

    blank_img = Image.new("RGB", (512, 512), color="black")
    img_array = np.array(blank_img).astype(np.float32) / 255.0
    img_tensor = torch.from_numpy(img_array)[None,]
    return (img_tensor,)


# Add common methods to all classes
for cls in [FluxPro, FluxDev, FluxSchnell]:
    cls.process_result = process_result
    cls.create_blank_image = create_blank_image

# Node class mappings
NODE_CLASS_MAPPINGS = {
    "FluxPro_fal": FluxPro,
    "FluxDev_fal": FluxDev,
    "FluxSchnell_fal": FluxSchnell,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "FluxPro_fal": "Flux Pro (fal)",
    "FluxDev_fal": "Flux Dev (fal)",
    "FluxSchnell_fal": "Flux Schnell (fal)",
}
