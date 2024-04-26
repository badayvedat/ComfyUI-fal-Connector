import random
import string


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


class ComboInput:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": f"combo_{get_random_short_id()}"}),
                "value": ([],),
                "options": ([],),
            },
        }

    RETURN_TYPES = ("COMBO",)
    FUNCTION = "get_value"

    def get_value(self, name, value, options):
        print("value:", value)
        print("options:", options)
        return (value,)

    @classmethod
    def VALIDATE_INPUTS(cls, value, options):
        return True


def get_random_short_id():
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=8))


NODE_CLASS_MAPPINGS = {
    "IntegerInput_fal": IntegerInput,
    "FloatInput_fal": FloatInput,
    "BooleanInput_fal": BooleanInput,
    "StringInput_fal": StringInput,
    # "ComboInput_fal": ComboInput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IntegerInput_fal": "Integer Input (fal)",
    "FloatInput_fal": "Float Input (fal)",
    "BooleanInput_fal": "Boolean Input (fal)",
    "StringInput_fal": "String Input (fal)",
    # "ComboInput_fal": "Combo Input (fal)",
}
