import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";


api.addEventListener("fal-execution-time", async ({ detail }) => {
  console.log(detail);
});

app.registerExtension({
  name: "Comfy.falConnector",
  async setup() {
    const falConnectButton = document.createElement("button");
    falConnectButton.id = "fal-connect-button";
    falConnectButton.textContent = "Execute on fal";
    falConnectButton.style.background =
      "linear-gradient(90deg, #192A51 0%, #6B3E9B 50%, #0099FF 100%)";
    falConnectButton.style.display = "inline-block";
    falConnectButton.style.color = "#fefefe";

    falConnectButton.onclick = () => {
      app.graphToPrompt().then((prompt) => {
        api
          .fetchApi("/fal/execute", {
            method: "POST",
            body: JSON.stringify({ ...prompt, client_id: api.clientId }),
            headers: { "Content-Type": "application/json" },
          })
          .catch((error) => {
            console.error("Error executing the workflow:", error);
            alert("Error executing the workflow");
            return;
          });
      });
    };

    const queue_prompt_button = document.getElementById("queue-button");
    const options_menu = queue_prompt_button.parentElement;
    options_menu.insertBefore(falConnectButton, queue_prompt_button);
  },
});
