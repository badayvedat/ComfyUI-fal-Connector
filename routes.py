import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from aiohttp import web
from fal.toolkit import File
from httpx_sse import aconnect_sse
from server import PromptServer

from .config import get_fal_endpoint, get_headers


async def upload_file_load_image(node_id, node_data):
    import folder_paths

    image = node_data["inputs"]["image"]
    image_path = Path(folder_paths.get_annotated_filepath(image))
    fal_file_url = File.from_path(image_path).url
    return {"key": [node_id, "inputs", "image"], "url": fal_file_url}


async def upload_input_files(prompt_data: dict[str, dict[str, Any]]):
    file_urls = []

    for node_id, node_data in prompt_data.items():
        if node_data["class_type"] == "LoadImage":
            file_data = await upload_file_load_image(node_id, node_data)
            file_urls.append(file_data)

    return file_urls


@PromptServer.instance.routes.post("/fal/execute")
async def execute_prompt(request):
    prompt_data = await request.json()

    api_workflow = prompt_data["output"]
    ui_workflow = prompt_data["workflow"]
    client_id = prompt_data["client_id"]

    try:
        fal_files = await upload_input_files(api_workflow)
    except Exception as err:
        print(err)
        error_response = {"error": f"An unexpected error occurred: {str(err)}"}
        return web.Response(
            status=500,
            body=json.dumps(error_response),
            content_type="application/json",
        )

    payload = {
        "prompt": api_workflow,
        "extra_data": {"extra_pnginfo": ui_workflow, "fal_files": fal_files},
    }

    async with httpx.AsyncClient() as client:
        try:
            await emit_events(client, payload, client_id)
            return web.Response(status=200)

        except httpx.HTTPStatusError as err:
            print(err)
            error_response = {"error": f"HTTP error occurred: {str(err)}"}
            return web.Response(
                status=err.response.status_code,
                body=json.dumps(error_response),
                content_type="application/json",
            )

        except httpx.RequestError as err:
            print(err)
            error_response = {"error": f"Request failed: {str(err)}"}
            return web.Response(
                status=500,
                body=json.dumps(error_response),
                content_type="application/json",
            )

        except Exception as err:
            print(err)
            error_response = {"error": f"An unexpected error occurred: {str(err)}"}
            return web.Response(
                status=500,
                body=json.dumps(error_response),
                content_type="application/json",
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
    ) as event_source:
        async for event in event_source.aiter_sse():
            message = json.loads(event.data)
            await emit_event(message["type"], message["data"], client_id)


async def emit_event(type, data, client_id):
    await PromptServer.instance.send(type, data, client_id)
