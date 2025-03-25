import configparser
import functools
import os

from fal_client.auth import MissingCredentialsError, FAL_RUN_HOST

@functools.cache
def get_fal_config():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    fal_config_path = os.path.join(curr_dir, "fal-config.ini")
    config = configparser.ConfigParser()
    config.read(fal_config_path)
    return config


@functools.cache
def get_fal_endpoint():
    config = get_fal_config()
    endpoint = os.environ.get("FAL_COMFY_ENDPOINT", config["fal"]["application_name"])
    return f"https://{FAL_RUN_HOST}/{endpoint}"


@functools.cache
def get_headers():
    api_key = get_fal_api_key()
    return {"Authorization": f"Key {api_key}"}


def get_fal_api_key():
    from fal_client.auth import fetch_credentials

    try:
        api_key = fetch_credentials()
    except MissingCredentialsError:
        api_key = None

    try:
        if not api_key:
            config = get_fal_config()
            api_key = config["fal"]["api_key"]
    except Exception as e:
        print(e)

    if not api_key:
        raise MissingCredentialsError("No FAL API key found.")

    return api_key

def get_hf_token():
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        try:
            config = get_fal_config()
            if "huggingface" in config:
                hf_token = config["huggingface"].get("token")
        except Exception as e:
            print(f"Error reading HF token from config: {e}")
    
    return hf_token


def set_fal_credentials():
    api_key = get_fal_api_key()
    os.environ["FAL_KEY"] = api_key

    # Backwards compatibility
    key_id, key_secret = api_key.split(":")
    os.environ["FAL_KEY_ID"] = key_id
    os.environ["FAL_KEY_SECRET"] = key_secret
    
    # Set HF token if available
    hf_token = get_hf_token()
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
