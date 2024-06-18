from ..download_utils import download_model_weights
import folder_paths


class RemoteLoraLoader:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_url": (
                    "STRING",
                    {
                        "default": "https://huggingface.co/nerijs/pixel-art-xl/resolve/main/pixel-art-xl.safetensors"
                    },
                ),
                "strength_model": (
                    "FLOAT",
                    {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01},
                ),
                "strength_clip": (
                    "FLOAT",
                    {"default": 1.0, "min": -20.0, "max": 20.0, "step": 0.01},
                ),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    FUNCTION = "load_lora"

    CATEGORY = "loaders"

    def load_lora(self, model, clip, lora_url, strength_model, strength_clip):
        import comfy.utils
        import comfy.sd

        if strength_model == 0 and strength_clip == 0:
            return (model, clip)

        lora_path = str(download_model_weights(lora_url))

        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                temp = self.loaded_lora
                self.loaded_lora = None
                del temp

        if lora is None:
            lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        model_lora, clip_lora = comfy.sd.load_lora_for_models(
            model, clip, lora, strength_model, strength_clip
        )
        return (model_lora, clip_lora)


class RemoteCheckpointLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ckpt_url": (
                    "STRING",
                    {
                        "default": "https://huggingface.co/nerijs/pixel-art-xl/resolve/main/pixel-art-xl.safetensors"
                    },
                ),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    FUNCTION = "load_checkpoint"

    CATEGORY = "loaders"

    def load_checkpoint(self, ckpt_url, output_vae=True, output_clip=True):
        import comfy.sd

        ckpt_path = str(download_model_weights(ckpt_url))
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        return out[:3]


NODE_CLASS_MAPPINGS = {

    "RemoteLoraLoader_fal": RemoteLoraLoader,
    "RemoteCheckpointLoader_fal": RemoteCheckpointLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RemoteLoraLoader_fal": "Load LoRA from URL (fal)",
    "RemoteCheckpointLoader_fal": "Load Checkpoint from URL (fal)",
}
