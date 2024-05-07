import functools
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import fal_client
import httpx
from aiohttp import web
from httpx_sse import SSEError, aconnect_sse
from server import PromptServer

from .config import get_fal_endpoint, get_headers
from .nodes import NODE_CLASS_MAPPINGS as FAL_NODES


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
    return fal_client.upload_file(file_path)


def _calculate_file_hash(file_path: Path):
    import hashlib

    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash


def upload_file(file_path: Path):
    file_hash = _calculate_file_hash(file_path)
    return _upload_file(file_path, file_hash)


async def upload_file_load_image(node_id, node_data, dry_run=False):
    import folder_paths

    image = node_data["inputs"]["image"]
    image_path = Path(folder_paths.get_annotated_filepath(image))

    fal_file_url = "example_url"
    if not dry_run:
        fal_file_url = upload_file(image_path)

    return {"key": [node_id, "inputs", "image"], "url": fal_file_url}


async def upload_file_load_video(node_id, node_data, dry_run=False):
    import folder_paths

    video = node_data["inputs"]["video"]
    video_path = Path(folder_paths.get_annotated_filepath(video))

    fal_file_url = "example_url"
    if not dry_run:
        fal_file_url = upload_file(video_path)

    return {"key": [node_id, "inputs", "video"], "url": fal_file_url}


async def upload_file_load_audio(node_id, node_data, dry_run=False):
    import folder_paths

    audio = node_data["inputs"]["audio"]
    audio_path = Path(folder_paths.get_annotated_filepath(audio))

    fal_file_url = "example_url"
    if not dry_run:
        fal_file_url = upload_file(audio_path)

    return {"key": [node_id, "inputs", "audio"], "url": fal_file_url}


async def upload_input_files(
    prompt_data: dict[str, dict[str, Any]], dry_run: bool = False
):
    load_image_nodes = ["LoadImage"]
    load_video_nodes = ["VHS_LoadVideo"]
    load_audio_nodes = ["LoadAudio", "LoadVHSAudio", "VHS_LoadAudio"]
    load_nodes = load_image_nodes + load_video_nodes + load_audio_nodes

    file_urls = []

    for node_id, node_data in prompt_data.items():
        node_class_type = node_data["class_type"]
        file_data = None

        if node_class_type not in load_nodes:
            continue

        if node_class_type in load_image_nodes:
            file_data = await upload_file_load_image(
                node_id, node_data, dry_run=dry_run
            )
        elif node_class_type in load_video_nodes:
            file_data = await upload_file_load_video(
                node_id, node_data, dry_run=dry_run
            )
        elif node_class_type in load_audio_nodes:
            file_data = await upload_file_load_audio(
                node_id, node_data, dry_run=dry_run
            )

        file_data["class_type"] = node_class_type
        file_urls.append(file_data)

    return file_urls


@PromptServer.instance.routes.post("/fal/execute")
async def execute_prompt(request):
    prompt_data = await request.json()

    try:
        client_id = prompt_data["client_id"]
    except KeyError:
        error_response = await get_comfy_error_response(
            type="client_id_missing",
            message="Client ID is missing",
            details="Client is not initialized yet. Please try again in a few seconds.",
        )
        return web.json_response(
            status=400,
            data=error_response,
        )

    try:
        payload = await build_payload(prompt_data)
    except ComfyClientError as err:
        error_data = err.args[0]
        error_code = error_data.get("code", 500)
        error_message = error_data.get("error", "An unexpected error occurred")
        return web.json_response(
            status=error_code,
            data=error_message,
        )

    async with httpx.AsyncClient() as client:
        try:
            await emit_event(
                "fal-info", {"message": "Executing the workflow"}, client_id
            )
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


@PromptServer.instance.routes.post("/fal/save")
async def save_prompt(request):
    prompt_data = await request.json()

    try:
        payload = await build_payload(prompt_data, dry_run=True)
    except ComfyClientError as err:
        error_data = err.args[0]
        error_code = error_data.get("code", 500)
        error_message = error_data.get("error", "An unexpected error occurred")
        return web.json_response(
            status=error_code,
            data=error_message,
        )

    payload["extra_data"].pop("extra_pnginfo", None)

    return web.json_response(status=200, data=payload)


async def build_payload(prompt_data: dict[str, dict[str, Any]], dry_run: bool = False):
    api_workflow = prompt_data["output"]
    ui_workflow = prompt_data["workflow"]

    try:
        if not dry_run:
            await emit_event(
                "fal-info",
                {"message": "Uploading input files"},
                prompt_data["client_id"],
            )
        fal_files = await upload_input_files(api_workflow, dry_run=dry_run)
    except Exception as err:
        error_response = await get_comfy_error_response(
            "file_upload_failed",
            "File upload failed",
            str(err),
        )
        raise ComfyClientError({"code": 400, "error": error_response})

    fal_inputs = {}
    fal_inputs_dev_info = {}
    file_input_type_counter = defaultdict(int)

    for file_data in fal_files:
        file_input_class_name = file_data["class_type"].lower()
        file_input_type_counter[file_input_class_name] += 1

        file_input_name = (
            f"{file_input_class_name}_{file_input_type_counter[file_input_class_name]}"
        )
        fal_inputs[file_input_name] = file_data["url"]
        fal_inputs_dev_info[file_input_name] = {
            "key": file_data["key"],
            "class_type": file_data["class_type"],
        }

    api_inputs_counter = {}
    async for _, _, api_node_data, ui_node_data in get_node_data(
        api_workflow, ui_workflow
    ):
        api_inputs, _ = await get_node_inputs(api_node_data, ui_node_data)

        for _, api_input_data in api_inputs.items():
            if not isinstance(api_input_data, list):
                continue

            upstream_node_id = api_input_data[0]
            upstream_node_data = api_workflow[upstream_node_id]
            upstream_node_inputs = upstream_node_data["inputs"]
            upstream_node_class_type = upstream_node_data["class_type"]

            if upstream_node_class_type not in FAL_NODES:
                continue

            input_name = upstream_node_inputs["name"]

            if input_name in api_inputs_counter:
                (
                    previous_upstream_node_id,
                    previous_upstream_node_class_type,
                ) = api_inputs_counter[input_name]

                error_response = await get_comfy_error_response(
                    "duplicate_input_name",
                    "Duplicate input name",
                    details=f"Found duplicate input name '{input_name}' in the workflow",
                    node_errors={
                        previous_upstream_node_id: {
                            "class_type": previous_upstream_node_class_type,
                            "errors": [
                                {
                                    "message": f"Duplicate input name '{input_name}'",
                                    "details": "",
                                }
                            ],
                        },
                        upstream_node_id: {
                            "class_type": upstream_node_class_type,
                            "errors": [
                                {
                                    "message": f"Duplicate input name '{input_name}'",
                                    "details": "",
                                }
                            ],
                        },
                    },
                )
                raise ComfyClientError(
                    {
                        "code": 400,
                        "error": error_response,
                    }
                )

            api_inputs_counter[input_name] = (
                upstream_node_id,
                upstream_node_class_type,
            )

            if upstream_node_class_type == "StringInput_fal":
                input_key = [upstream_node_id, "inputs", "value"]
                fal_inputs[input_name] = upstream_node_inputs["value"]

            elif upstream_node_class_type == "IntegerInput_fal":
                input_key = [upstream_node_id, "inputs", "number"]
                fal_inputs[input_name] = upstream_node_inputs["number"]

            elif upstream_node_class_type == "FloatInput_fal":
                input_key = [upstream_node_id, "inputs", "number"]
                fal_inputs[input_name] = upstream_node_inputs["number"]

            elif upstream_node_class_type == "BooleanInput_fal":
                input_key = [upstream_node_id, "inputs", "value"]
                fal_inputs[input_name] = upstream_node_inputs["value"]

            fal_inputs_dev_info[input_name] = {
                "key": input_key,
                "class_type": upstream_node_class_type,
            }

    payload = {
        "prompt": api_workflow,
        "extra_data": {"extra_pnginfo": ui_workflow},
        "fal_inputs_dev_info": fal_inputs_dev_info,
        "fal_inputs": fal_inputs,
    }

    return payload


async def get_node_data(api_workflow: dict[str, Any], ui_workflow: dict[str, Any]):
    ui_nodes = {str(node["id"]): node for node in ui_workflow["nodes"]}

    for node_id, api_node_data in api_workflow.items():
        ui_node_data = ui_nodes[node_id]
        node_class_type = api_node_data["class_type"]
        yield node_id, node_class_type, api_node_data, ui_node_data


async def get_node_inputs(api_node_data: dict[str, Any], ui_node_data: dict[str, Any]):
    api_inputs = {
        input: input_data
        for input, input_data in api_node_data.get("inputs", {}).items()
    }

    ui_inputs = {
        input_data["name"]: input_data["widget"]
        for input_data in ui_node_data.get("inputs", [])
        if "widget" in input_data
    }

    return api_inputs, ui_inputs


async def emit_events(client: httpx.AsyncClient, payload: dict, client_id: str):
    headers = get_headers()
    fal_endpoint = get_fal_endpoint()

    async with aconnect_sse(
        client,
        method="POST",
        url=fal_endpoint,
        json=payload,
        headers=headers,
        timeout=120,
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
