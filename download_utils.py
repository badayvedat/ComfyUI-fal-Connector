import os
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import fal
from fal.toolkit.utils.download_utils import (
    FAL_MODEL_WEIGHTS_DIR,
    DownloadError,
    _hash_url,
)

FAL_VERSION = getattr(fal, "__version__", "<1.0.0")
_REQUEST_HEADERS = {"User-Agent": f"fal-client ({FAL_VERSION}/python)"}


def get_civitai_headers() -> dict[str, str]:
    headers: dict[str, str] = {}

    civitai_token = os.getenv("CIVITAI_TOKEN", None)

    if not civitai_token:
        print("CIVITAI_TOKEN is not set in the environment variables.")
        return headers

    headers["Authorization"] = f"Bearer {civitai_token}"

    return headers


def get_huggingface_headers() -> dict[str, str]:
    headers: dict[str, str] = {}

    hf_token = os.getenv("HF_TOKEN", None)

    if not hf_token:
        print("HF_TOKEN is not set in the environment variables.")
        return headers

    headers["Authorization"] = f"Bearer {hf_token}"

    return headers


def get_local_file_content_length(file_path: Path) -> int:
    return file_path.stat().st_size


def download_url_to_file(
    url: str,
    dst: str | Path,
    progress: bool = True,
    headers: dict[str, str] = None,
    chunk_size_in_mb=16,
    file_integrity_check_callback=None,
) -> Path:
    """Download object at the given URL to a local path.

    Args:
        url (str): URL of the object to download
        dst (str): Full path where object will be saved, e.g. ``/tmp/temporary_file``
        progress (bool, optional): whether or not to display a progress bar to stderr
            Default: True
        headers (dict, optional): HTTP headers to include with the request
            Default: None
        chunk_size_in_mb (int, optional): size of each chunk in MB
            Default: 16
        file_integrity_check_callback (callable, optional): callback function to check file integrity
            Default: None

    """
    from tqdm import tqdm

    file_size = None

    request_headers = {
        **_REQUEST_HEADERS,
        **(headers or {}),
    }

    import requests

    req = requests.get(url, headers=request_headers, stream=True, allow_redirects=True)
    req.raise_for_status()

    headers = req.headers  # type: ignore
    content_length = headers.get("Content-Length", None)  # type: ignore
    if content_length is not None and len(content_length) > 0:
        file_size = int(content_length[0])

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        file_path = temp_file.name
        try:
            with tqdm(
                total=file_size,
                disable=not progress,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar, open(file_path, "wb") as f:
                for chunk in req.iter_content(
                    chunk_size=chunk_size_in_mb * 1024 * 1024
                ):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            if file_integrity_check_callback:
                file_integrity_check_callback(file_path)

            # Move the file when the file is downloaded completely. Since the
            # file used is temporary, in a case of an interruption, the downloaded
            # content will be lost. So, it is safe to redownload the file in such cases.
            shutil.move(file_path, dst)
        except Exception as error:
            raise error
        finally:
            Path(temp_file.name).unlink(missing_ok=True)

    return Path(dst)


def download_model_weights(url: str, force: bool = False) -> Path:
    parsed_url = urlparse(url)

    headers = {}
    if parsed_url.netloc == "civitai.com":
        headers.update(get_civitai_headers())
    elif parsed_url.netloc == "huggingface.co":
        headers.update(get_huggingface_headers())

    return download_model_weights_fal(url, request_headers=headers, force=force)


def download_model_weights_fal(
    url: str, force: bool = False, request_headers: dict[str, str] | None = None
) -> Path:
    weights_dir = Path(FAL_MODEL_WEIGHTS_DIR / _hash_url(url))

    if weights_dir.exists() and not force:
        try:
            weights_path = next(weights_dir.glob("*"))
            return weights_path

        # The model weights directory is empty, so we need to download the weights
        except StopIteration:
            pass

    try:
        file_name, file_content_length = _get_remote_file_properties(
            url, request_headers=request_headers
        )
    except Exception as e:
        print(e)
        raise DownloadError(f"Failed to get remote file properties for {url}")

    target_path = weights_dir / file_name

    if (
        target_path.exists()
        and get_local_file_content_length(target_path) == file_content_length
        and not force
    ):
        return target_path

    # Make sure the parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        download_url_to_file(
            url,
            target_path,
            progress=True,
            headers=request_headers,
            file_integrity_check_callback=is_safetensors_file,
        )
    except Exception as e:
        print(e)
        raise DownloadError(f"Failed to download {url}")

    return target_path


def _get_filename_from_content_disposition(cd: str | None) -> str | None:
    if not cd:
        return None

    filenames = re.findall('filename="(.+)"', cd)

    if len(filenames) == 0:
        filenames = re.findall("filename=(.+)", cd)

    if len(filenames) == 0:
        return None

    return unquote(filenames[0])


def _parse_filename(url: str, cd: str | None) -> str:
    file_name = _get_filename_from_content_disposition(cd)

    if not file_name:
        parsed_url = urlparse(url)

        if parsed_url.scheme == "data":
            file_name = _hash_url(url)
        else:
            url_path = parsed_url.path
            file_name = Path(url_path).name or _hash_url(url)

    return file_name  # type: ignore


def _get_remote_file_properties(
    url: str, request_headers: dict[str, str] = None
) -> tuple[str, int]:
    import requests

    headers = {
        **_REQUEST_HEADERS,
        **(request_headers or {}),
    }

    req = requests.get(
        url, headers=headers, stream=True, allow_redirects=True, verify=False
    )
    req.raise_for_status()

    headers = req.headers  # type: ignore
    content_disposition = headers.get("Content-Disposition", None)
    file_name = _parse_filename(url, content_disposition)
    content_length = int(headers.get("Content-Length", -1))

    return file_name, content_length


def is_safetensors_file(path: str | Path):
    from safetensors import safe_open

    path = str(path)

    if not path.endswith(".safetensors"):
        raise ValueError(f"File {path} is not a .safetensors file")

    try:
        with safe_open(path, framework="pt"):
            pass
    except Exception as e:
        print(e)
        error_mesage = e.args[0]
        if error_mesage == "Error while deserializing header: HeaderTooLarge":
            raise ValueError(f"File {path} is not a .safetensors file")
        else:
            raise e
