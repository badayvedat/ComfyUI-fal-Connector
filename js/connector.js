import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { APPLICATION_NAME } from "./fal-env.js";
import { FAL_KEY } from "./fal-env.js";

const apiBase = `fal.run/${APPLICATION_NAME}`;

const processPrompt = async (prompt) => {
    const fal_endpoint = `https://${apiBase}`;

    console.log(FAL_KEY);
    if (!FAL_KEY || FAL_KEY === "your_fal_key_here") {
        alert("FAL key not provided. Please provide a key in the fal-env.js file.");
        return;
    }

    const response = await fetch(fal_endpoint, {
        method: 'POST',
        body: JSON.stringify(prompt),
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Key ${FAL_KEY}`,
        }
      })

    // if response is 401, then the key is invalid
    if (response.status === 401) {
        alert("Invalid FAL key provided. Please check the key in the fal-env.js file.");
        return;
    }
    const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
    
    while (true) {
      const {value, done} = await reader.read();
      if (done) break;

        const lines = value.split('\n');
        lines.forEach((line) => {
            if (line.startsWith('data:')) {
                const jsonDataStr = line.substring(line.indexOf('data: ') + 'data: '.length);
                const event = new MessageEvent('message', {data: jsonDataStr});
                api.socket.dispatchEvent(event);
            }
        });

    }
}



api.addEventListener("executed-fal", async ({ detail }) => {
    const files = detail.files;
    const originalMessage = detail.original_message;
    console.log("files", files);

    api.fetchApi("/fal/download", { method: "POST", body: JSON.stringify({ files: files }), headers: { "Content-Type": "application/json" } });
    console.log("original message", originalMessage);
    api.socket.dispatchEvent(new MessageEvent("message", { data: originalMessage }));
});

app.registerExtension({
    name: "Comfy.falConnector",
    async setup() {
        const falConnectButton = document.createElement("button");
        falConnectButton.id = "fal-connect-button";
        falConnectButton.textContent = "Run on fal";
        falConnectButton.style.background = "linear-gradient(90deg, #192A51 0%, #6B3E9B 50%, #0099FF 100%)";
        falConnectButton.style.display = "inline-block";
        falConnectButton.style.color = "#fefefe";

        falConnectButton.onclick = () => {
            app.graphToPrompt().then(({ output, workflow }) => {
                const body = {
                    client_id: api.clientId,
                    prompt: output,
                    extra_data: { extra_pnginfo: { workflow } },
                };

                processPrompt(body);
            });

        };
        
        const queue_prompt_button = document.getElementById("queue-button")
        const options_menu = queue_prompt_button.parentElement
        options_menu.insertBefore(falConnectButton, queue_prompt_button);
    },
});

