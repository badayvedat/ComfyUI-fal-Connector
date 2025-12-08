import io
import base64
import os
import numpy as np
from PIL import Image

import fal_client


class FalAITextLLM:
    """
    Fal.AI Text LLM Node
    Run any LLM (Large Language Model) with fal, powered by OpenRouter
    Endpoint: openrouter/router
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fal_api_key": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Write a short story (under 200 words) about an AI that learns to dream. Use vivid sensory details and end with a surprising twist that makes the reader feel both awe and melancholy."
                }),
                "model": ([
                    "google/gemini-2.5-flash-lite",
                    "google/gemini-2.5-flash",
                    "google/gemini-2.5-pro",
                    "google/gemini-2.0-flash-001",
                    "google/gemini-flash-1.5",
                    "google/gemini-flash-1.5-8b",
                    "google/gemini-pro-1.5",
                    "anthropic/claude-3.7-sonnet",
                    "anthropic/claude-3.5-sonnet",
                    "anthropic/claude-3-5-haiku",
                    "anthropic/claude-3-haiku",
                    "openai/gpt-4o",
                    "openai/gpt-4o-mini",
                    "openai/gpt-4.1",
                    "openai/gpt-5-chat",
                    "openai/gpt-5-mini",
                    "openai/gpt-5-nano",
                    "openai/o3",
                    "openai/gpt-oss-120b",
                    "meta-llama/llama-3.1-70b-instruct",
                    "meta-llama/llama-3.1-8b-instruct",
                    "meta-llama/llama-3.2-1b-instruct",
                    "meta-llama/llama-3.2-3b-instruct",
                    "meta-llama/llama-4-maverick",
                    "meta-llama/llama-4-scout",
                    "deepseek/deepseek-r1",
                ], {
                    "default": "google/gemini-2.5-flash-lite"
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful assistant."
                }),
            },
            "optional": {
                "max_tokens": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 4096,
                    "step": 1
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("generated_text",)
    FUNCTION = "generate_text"
    CATEGORY = "fal/llm"

    def generate_text(
        self,
        fal_api_key,
        prompt, 
        model, 
        system_prompt,
        max_tokens=512, 
        temperature=0.7
    ):
        """
        Generate text using Fal.AI OpenRouter API
        
        Args:
            fal_api_key: Fal.AI API key (REQUIRED - environment variables are ignored)
            prompt: The user prompt
            model: The LLM model to use
            system_prompt: System instructions for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            
        Returns:
            Tuple containing the generated text
        """
        # Validate API key is provided
        if not fal_api_key or not fal_api_key.strip():
            error_msg = "ERROR: Fal.AI API key is required. Please provide your API key in the 'fal_api_key' field."
            print(f"[FalAI Text LLM] {error_msg}")
            return (error_msg,)
        
        # Set the API key for this call ONLY (never use environment)
        original_key = os.environ.get("FAL_KEY")
        os.environ["FAL_KEY"] = fal_api_key.strip()
        
        try:
            # Prepare the request payload
            arguments = {
                "prompt": prompt,
                "model": model,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Call the Fal.AI OpenRouter API
            result = fal_client.subscribe(
                "openrouter/router",
                arguments=arguments
            )

            # Extract the generated text
            generated_text = result.get("output", "")
            
            if not generated_text:
                generated_text = "Error: No output received from the API"
                print(f"[FalAI Text LLM] Warning: Empty response from API")
            else:
                print(f"[FalAI Text LLM] Generated text: {generated_text[:100]}...")

            return (generated_text,)

        except Exception as e:
            error_msg = f"Error generating text: {str(e)}"
            print(f"[FalAI Text LLM] {error_msg}")
            return (error_msg,)
        
        finally:
            # Always restore original environment state (security critical!)
            if original_key:
                os.environ["FAL_KEY"] = original_key
            else:
                os.environ.pop("FAL_KEY", None)


class FalAIVisionLLM:
    """
    Fal.AI Vision LLM Node
    Run any VLM (Vision Language Model) with fal
    Endpoint: fal-ai/any-llm/vision (kept for backward compatibility)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fal_api_key": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "image": ("IMAGE",),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "Caption this image for a text-to-image model with as much detail as possible."
                }),
                "model": ([
                    "google/gemini-2.5-flash-lite",
                    "google/gemini-2.5-flash",
                    "google/gemini-2.5-pro",
                    "google/gemini-2.0-flash-001",
                    "google/gemini-flash-1.5",
                    "google/gemini-flash-1.5-8b",
                    "google/gemini-pro-1.5",
                    "anthropic/claude-3.7-sonnet",
                    "anthropic/claude-3.5-sonnet",
                    "anthropic/claude-3-haiku",
                    "openai/gpt-4o",
                    "openai/gpt-4.1",
                    "openai/gpt-5-chat",
                    "meta-llama/llama-3.2-90b-vision-instruct",
                    "meta-llama/llama-4-maverick",
                    "meta-llama/llama-4-scout",
                ], {
                    "default": "google/gemini-2.5-flash-lite"
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "Only answer the question, do not provide any additional information or add any prefix/suffix other than the answer of the original question. Don't use markdown."
                }),
            },
            "optional": {
                "max_tokens": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 4096,
                    "step": 1
                }),
                "temperature": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("description",)
    FUNCTION = "analyze_image"
    CATEGORY = "fal/llm"

    def tensor_to_base64(self, image_tensor):
        """
        Convert ComfyUI image tensor to base64 data URI
        
        Args:
            image_tensor: ComfyUI image tensor [batch, height, width, channels] with values 0-1
            
        Returns:
            Base64 encoded data URI
        """
        # Convert tensor to numpy array (0-255 range)
        image_np = (image_tensor.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_np)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"

    def analyze_image(
        self,
        fal_api_key,
        image, 
        prompt, 
        model, 
        system_prompt,
        max_tokens=512,
        temperature=1.0
    ):
        """
        Analyze image using Fal.AI Vision API
        
        Args:
            fal_api_key: Fal.AI API key (REQUIRED - environment variables are ignored)
            image: ComfyUI image tensor
            prompt: The question or instruction about the image
            model: The vision-language model to use
            system_prompt: System instructions for the model
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            
        Returns:
            Tuple containing the generated description
        """
        # Validate API key is provided
        if not fal_api_key or not fal_api_key.strip():
            error_msg = "ERROR: Fal.AI API key is required. Please provide your API key in the 'fal_api_key' field."
            print(f"[FalAI Vision LLM] {error_msg}")
            return (error_msg,)
        
        # Set the API key for this call ONLY (never use environment)
        original_key = os.environ.get("FAL_KEY")
        os.environ["FAL_KEY"] = fal_api_key.strip()
        
        try:
            # Convert image to base64 data URI
            image_data_uri = self.tensor_to_base64(image)

            # Prepare the request payload (keeping single image for compatibility)
            arguments = {
                "image_url": image_data_uri,  # Keep single image format for backward compatibility
                "prompt": prompt,
                "model": model,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Call the Fal.AI Vision API (keeping old endpoint for compatibility)
            result = fal_client.subscribe(
                "fal-ai/any-llm/vision",
                arguments=arguments
            )

            # Extract the generated description
            description = result.get("output", "")
            
            if not description:
                description = "Error: No output received from the API"
                print(f"[FalAI Vision LLM] Warning: Empty response from API")
            else:
                print(f"[FalAI Vision LLM] Generated description: {description[:100]}...")

            return (description,)

        except Exception as e:
            error_msg = f"Error analyzing image: {str(e)}"
            print(f"[FalAI Vision LLM] {error_msg}")
            return (error_msg,)
        
        finally:
            # Always restore original environment state (security critical!)
            if original_key:
                os.environ["FAL_KEY"] = original_key
            else:
                os.environ.pop("FAL_KEY", None)


NODE_CLASS_MAPPINGS = {
    "FalAITextLLM_fal": FalAITextLLM,
    "FalAIVisionLLM_fal": FalAIVisionLLM,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FalAITextLLM_fal": "Text LLM (fal)",
    "FalAIVisionLLM_fal": "Vision LLM (fal)",
}



