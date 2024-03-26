# ComfyUI-fal-Connector

## Installation
```bash
git clone --recursive https://github.com/badayvedat/ComfyUI-fal.git

cd ComfyUI-fal

pip install -r requirements.txt
```

## Set up fal key
1. Go to [fal dashboard](https://fal.ai/dashboard/keys) and generate an API key.
2. Navigate to the `custom_nodes/ComfyUI-fal-Connector` directory.
3. Copy and paste the generated API key into the `api_key` section within the `fal-config.ini` file.

## Start Comfy Server
```bash
python main.py
```

## TODO
- [] Easier deployment procedure
- [] Document payload format usage
