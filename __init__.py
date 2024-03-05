from pathlib import Path
import folder_paths
import os
from server import PromptServer
from aiohttp import web
import aiohttp
import asyncio
import os

COMFY_PATH = Path(os.path.dirname(folder_paths.__file__))
CUSTOM_NODES_PATH = COMFY_PATH / "custom_nodes"
FAL_CONNECTOR_PATH = CUSTOM_NODES_PATH / "ComfyUI-fal-Connector"
FAL_JS_PATH = FAL_CONNECTOR_PATH / "js"

WEB_DIRECTORY = "js"

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


async def download_file(url: str, path: str, chunk_size_mb: int = 10 * 1024 * 1024):
    print(f"Downloading {url} to {path}")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                with open(path, "wb") as f:
                    while True:
                        chunk = await response.content.read(chunk_size_mb)
                        if not chunk:
                            break
                        f.write(chunk)
                print(f"Downloaded {url} to {path}")
            else:
                print(f"Failed to download {url}")


@PromptServer.instance.routes.post("/fal/download")
async def download(request):
    json_data = await request.json()
    for file in json_data.get("files", []):
        filename = file["filename"]
        subfolder = file["subfolder"]
        type = file["type"]
        url = file["url"]

        filename, output_dir = folder_paths.annotated_filepath(filename)

        if filename[0] == "/" or ".." in filename:
            return web.Response(status=400)

        if output_dir is None:
            type = type or "output"
            output_dir = folder_paths.get_directory_by_type(type)

        if output_dir is None:
            return web.Response(status=400)

        full_output_dir = os.path.join(output_dir, subfolder)
        if (
            os.path.commonpath((os.path.abspath(full_output_dir), output_dir))
            != output_dir
        ):
            return web.Response(status=403)
        output_dir = full_output_dir

        filename = os.path.basename(filename)
        file = os.path.join(output_dir, filename)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"Downloading {url} to {file} ss")
        await download_file(url, file)

        await asyncio.sleep(0.1)

    return web.Response(status=200)
