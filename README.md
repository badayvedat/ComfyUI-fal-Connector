# ComfyUI-fal-Connector
The ComfyUI-fal-Connector is a tool designed to provide an integration between
`ComfyUI` and `fal`. This extension allows users to execute their ComfyUI
workflows directly on `fal.ai`. This enables users to leverage the
computational power and resources provided by `fal.ai` for running their
ComfyUI workflows.


## Usage
### Installation:
1. **Cloning the required repositories:** Clone the [ComfyUI-fal](https://github.com/badayvedat/ComfyUI-fal.git) and install the required dependencies using the
provided requirements.txt file. `ComfyUI-fal` repository includes all the necessary custom extensions including this one.
```bash
git clone --recursive https://github.com/badayvedat/ComfyUI-fal.git

cd ComfyUI-fal

pip install -r requirements.txt
```

2. **Set up a `fal` API key:** Generate an API key from
[fal dashboard](https://fal.ai/dashboard/keys) and add it to 
the `fal-config.ini` file in the `ComfyUI-fal/custom_nodes/ComfyUI-fal-Connector`
directory.
> [!WARNING]
> The `fal-config.ini` file is not in the root directory of the `ComfyUI-fal`
repository, but in the `ComfyUI-fal/custom_nodes/ComfyUI-fal-Connector` directory.

4. **Start the Comfy Server:** Run the `main.py` file to start the Comfy server and
initiate the connector.

5. **Execute Workflows:** Use ComfyUI to create and configure your AI workflows.
When ready, execute the workflows directly on `fal` using the connector.

## How to use it outside of ComfyUI?
After you set up a workflow, and made sure it is working properly. You can generate a
"fal format" using `Save as fal format` button. Then you can post the generated JSON
to `https://fal.run/fal-ai/comfy-server` to execute it and obtain the results.