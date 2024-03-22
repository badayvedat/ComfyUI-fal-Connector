import json
from pathlib import Path
from typing import Any
import functools
import httpx
from aiohttp import web
from fal.toolkit import File
from httpx_sse import SSEError, aconnect_sse
from server import PromptServer

from .config import get_fal_endpoint, get_headers


class ComfyClientError(Exception):
    pass


async def get_comfy_error_response(
    type: str,
    message: str,
    details: str | None,
    extra_info: dict[str, Any] | None = None,
    node_errors: dict[str, Any] | None = None,
):
    return {
        "error": {
            "type": type,
            "message": message,
            "details": details or "",
            "extra_info": extra_info or {},
        },
        "node_errors": node_errors or {},
    }


@functools.lru_cache(maxsize=128)
def _upload_file(file_path: Path, md5_hash: str):
    return File.from_path(file_path).url

def _calculate_file_hash(file_path: Path):
    import hashlib

    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

def upload_file(file_path: Path):
    file_hash = _calculate_file_hash(file_path)
    return _upload_file(file_path, file_hash)

async def upload_file_load_image(node_id, node_data):
    import folder_paths

    image = node_data["inputs"]["image"]
    image_path = Path(folder_paths.get_annotated_filepath(image))
    fal_file_url = upload_file(image_path)
    return {"key": [node_id, "inputs", "image"], "url": fal_file_url}


async def upload_file_load_video(node_id, node_data):
    import folder_paths

    video = node_data["inputs"]["video"]
    video_path = Path(folder_paths.get_annotated_filepath(video))
    fal_file_url = upload_file(video_path)
    return {"key": [node_id, "inputs", "video"], "url": fal_file_url}


async def upload_input_files(prompt_data: dict[str, dict[str, Any]]):
    file_urls = []

    for node_id, node_data in prompt_data.items():
        if node_data["class_type"] == "LoadImage":
            file_data = await upload_file_load_image(node_id, node_data)
            file_urls.append(file_data)
        elif node_data["class_type"] == "VHS_LoadVideo":
            file_data = await upload_file_load_video(node_id, node_data)
            file_urls.append(file_data)

    return file_urls


@PromptServer.instance.routes.post("/fal/execute")
async def execute_prompt(request):
    prompt_data = await request.json()

    api_workflow = prompt_data["output"]
    ui_workflow = prompt_data["workflow"]
    client_id = prompt_data["client_id"]

    try:
        await emit_event("fal-info", {"message": "Uploading files"}, client_id)
        fal_files = await upload_input_files(api_workflow)
        await emit_event("fal-info", {"message": "Files uploaded"}, client_id)
    except Exception as err:
        error_response = await get_comfy_error_response(
            "file_upload_failed",
            "File upload failed",
            str(err),
        )
        return web.json_response(
            status=400,
            data=error_response,
        )

    payload = {
        "prompt": api_workflow,
        "extra_data": {"extra_pnginfo": ui_workflow, "fal_files": fal_files},
    }

    with open("payload.json", "w") as f:
        json.dump(payload, f, indent=4)

    async with httpx.AsyncClient() as client:
        try:
            await emit_event("fal-info", {"message": "Executing the workflow"}, client_id)
            await emit_events(client, payload, client_id)
            return web.json_response(status=200)

        except httpx.HTTPStatusError as error:
            error_response = {"error": f"HTTP error occurred: {str(error)}"}
            return web.json_response(
                status=error.response.status_code,
                data=error_response,
            )

        except httpx.RequestError as error:
            # A fix to handle incomplete chunked read error
            # We are not sure why this error occurs, but it seems to be harmless
            if (
                str(error)
                == "peer closed connection without sending complete message body (incomplete chunked read)"
            ):
                return web.json_response(status=200)

            error_response = {"error": f"Request error occurred: {str(error)}"}
            return web.json_response(
                status=500,
                data=error_response,
            )

        except ComfyClientError as error:
            error_data = error.args[0]
            error_code = error_data.get("code", 500)
            error_message = error_data.get("error", "An unexpected error occurred")
            return web.json_response(
                status=error_code,
                data=error_message,
            )

        except Exception as error:
            error_response = {"error": f"An unexpected error occurred: {str(error)}"}
            return web.json_response(
                status=500,
                data=error_response,
            )


async def emit_events(client: httpx.AsyncClient, payload: dict, client_id: str):
    headers = get_headers()
    fal_endpoint = get_fal_endpoint()

    async with aconnect_sse(
        client,
        method="POST",
        url=fal_endpoint,
        json=payload,
        headers=headers,
        timeout=60,
    ) as event_source:
        try:
            async for event in event_source.aiter_sse():
                message = json.loads(event.data)
                await emit_event(message["type"], message["data"], client_id)
        except SSEError:
            response = event_source.response
            response_body = await response.aread()
            error_message = response_body.decode()
            error_response = await get_comfy_error_response(
                "fal-execution-error",
                "fal execution error",
                error_message,
            )
            raise ComfyClientError({"code": 400, "error": error_response})


async def emit_event(type, data, client_id):
    if type == "fal-execution-error":
        raise ComfyClientError(data)

    await PromptServer.instance.send(type, data, client_id)
