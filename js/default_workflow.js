const DEFAULT_WORKFLOW = {
    "prompt": {
        "3": {
            "inputs": {
                "seed": [
                    "12",
                    0
                ],
                "steps": 20,
                "cfg": [
                    "13",
                    0
                ],
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": [
                    "4",
                    0
                ],
                "positive": [
                    "6",
                    0
                ],
                "negative": [
                    "7",
                    0
                ],
                "latent_image": [
                    "5",
                    0
                ]
            },
            "class_type": "KSampler",
            "_meta": {
                "title": "KSampler"
            }
        },
        "4": {
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.ckpt"
            },
            "class_type": "CheckpointLoaderSimple",
            "_meta": {
                "title": "Load Checkpoint"
            }
        },
        "5": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage",
            "_meta": {
                "title": "Empty Latent Image"
            }
        },
        "6": {
            "inputs": {
                "text": [
                    "10",
                    0
                ],
                "clip": [
                    "4",
                    1
                ]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "7": {
            "inputs": {
                "text": [
                    "11",
                    0
                ],
                "clip": [
                    "4",
                    1
                ]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "8": {
            "inputs": {
                "samples": [
                    "3",
                    0
                ],
                "vae": [
                    "4",
                    2
                ]
            },
            "class_type": "VAEDecode",
            "_meta": {
                "title": "VAE Decode"
            }
        },
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": [
                    "8",
                    0
                ]
            },
            "class_type": "SaveImage",
            "_meta": {
                "title": "Save Image"
            }
        },
        "10": {
            "inputs": {
                "name": "prompt",
                "value": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,"
            },
            "class_type": "StringInput_fal",
            "_meta": {
                "title": "String Input (fal)"
            }
        },
        "11": {
            "inputs": {
                "name": "negative_prompt",
                "value": "text, watermark"
            },
            "class_type": "StringInput_fal",
            "_meta": {
                "title": "String Input (fal)"
            }
        },
        "12": {
            "inputs": {
                "name": "ksampler_seed",
                "number": 156680208700286,
                "min": 0,
                "max": 18446744073709552000,
                "step": 1
            },
            "class_type": "IntegerInput_fal",
            "_meta": {
                "title": "Integer Input (fal)"
            }
        },
        "13": {
            "inputs": {
                "name": "guidance_scale",
                "number": 8,
                "min": 0,
                "max": 100,
                "step": 0.1
            },
            "class_type": "FloatInput_fal",
            "_meta": {
                "title": "Float Input (fal)"
            }
        }
    },
    "extra_data": {},
    "fal_inputs_dev_info": {
        "ksampler_seed": {
            "key": [
                "12",
                "inputs",
                "number"
            ],
            "class_type": "IntegerInput_fal"
        },
        "guidance_scale": {
            "key": [
                "13",
                "inputs",
                "number"
            ],
            "class_type": "FloatInput_fal"
        },
        "prompt": {
            "key": [
                "10",
                "inputs",
                "value"
            ],
            "class_type": "StringInput_fal"
        },
        "negative_prompt": {
            "key": [
                "11",
                "inputs",
                "value"
            ],
            "class_type": "StringInput_fal"
        }
    },
    "fal_inputs": {
        "ksampler_seed": 156680208700286,
        "guidance_scale": 8,
        "prompt": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,",
        "negative_prompt": "text, watermark"
    }
}

export async function getDefaultWorkflow() {
    return DEFAULT_WORKFLOW;
}
