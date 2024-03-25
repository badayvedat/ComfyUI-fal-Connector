import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { $el } from "../../scripts/ui.js";

let processingQueue = false;

// Based on https://github.com/comfyanonymous/ComfyUI/blob/4b9005e949224782236a8b914eae48bc503f1f18/web/scripts/app.js#L1991-L2014
const formatPromptError = async (error) => {
  if (error == null) {
    return "(unknown error)";
  } else if (typeof error === "string") {
    return error;
  } else if (error.stack && error.message) {
    return error.toString();
  } else if (error.response) {
    let message = error.response.error.message;
    if (error.response.error.details)
      message += ": " + error.response.error.details;
    if (error.response.node_errors) {
      for (const [nodeID, nodeError] of Object.entries(
        error.response.node_errors,
      )) {
        message += "\n" + nodeError.class_type + ":";
        for (const errorReason of nodeError.errors) {
          message +=
            "\n    - " + errorReason.message + ": " + errorReason.details;
        }
      }
    }
    return message;
  }
  return "(unknown error)";
};

// const formatWorkflowAPIFormat = async (workflow) => {

const queuePrompt = async () => {
  // Only have one action process the items so each one gets a unique seed correctly
  if (processingQueue) {
    return;
  }

  processingQueue = true;
  app.lastNodeErrors = null;

  try {
    try {
      await app.graphToPrompt().then(async (prompt) => {
        await api
          .fetchApi("/fal/execute", {
            method: "POST",
            body: JSON.stringify({ ...prompt, client_id: api.clientId }),
            headers: { "Content-Type": "application/json" },
          })
          .then(async (res) => {
            if (res.status !== 200) {
              throw {
                response: await res.json(),
              };
            }

            for (const n of prompt.workflow.nodes) {
              const node = app.graph.getNodeById(n.id);
              if (node.widgets) {
                for (const widget of node.widgets) {
                  // Allow widgets to run callbacks after a prompt has been queued
                  // e.g. random seed after every gen
                  if (widget.afterQueued) {
                    widget.afterQueued();
                  }
                }
              }
            }
          });
      });
    } catch (error) {
      const formattedError = await formatPromptError(error);
      app.ui.dialog.show(formattedError);
      if (error.response) {
        app.lastNodeErrors = error.response.node_errors;
        app.canvas.draw(true, true);
      }
    }

    app.canvas.draw(true, true);
  } finally {
    processingQueue = false;
  }
};

api.addEventListener("fal-info", async ({ detail }) => {
  const elem = document.getElementById("fal-info-label");
  if (!elem || !detail.message) {
    return;
  }

  elem.textContent = `${detail.message}`;
  elem.style.display = "block";
});

const registerFalConnectButton = async () => {
  const falConnectButton = document.createElement("button");
  falConnectButton.id = "fal-connect-button";
  falConnectButton.textContent = "Execute on fal";
  falConnectButton.style.background =
    "linear-gradient(90deg, #192A51 0%, #6B3E9B 50%, #0099FF 100%)";
  falConnectButton.style.display = "inline-block";
  falConnectButton.style.color = "#fefefe";

  falConnectButton.onclick = () => queuePrompt();

  const queue_prompt_button = document.getElementById("queue-button");
  const options_menu = queue_prompt_button.parentElement;
  options_menu.insertBefore(falConnectButton, queue_prompt_button);
};

const registerFalInfoLabel = async () => {
  const infoLabel = document.createElement("label");
  infoLabel.id = "fal-info-label";
  infoLabel.style.display = "none";
  infoLabel.style.margin = "0.5em auto 0";

  const queue_prompt_button = document.getElementById("queue-button");
  const options_menu = queue_prompt_button.parentElement;
  options_menu.insertBefore(infoLabel, queue_prompt_button);
};

const hideUnusedElements = async () => {
  const queue_prompt_button = document.getElementById("queue-button");

  queue_prompt_button.style.display = "none";
  // 'Extra Options' element
  queue_prompt_button.nextSibling.style.display = "none";

  const element_ids_to_hide = [
    "extraOptions",
    "comfy-view-history-button",
    "comfy-view-queue-button",
    "queue-front-button",
  ];
  for (const id of element_ids_to_hide) {
    const element = document.getElementById(id);
    if (element) {
      element.style.display = "none";
    }
  }
};

const saveComfyPrompt = async (comfyPrompt) => {
  let filename = "fal_api_workflow.json";
  filename = prompt("Save workflow (API) as:", filename);
  if (!filename) return;
  if (!filename.toLowerCase().endsWith(".json")) {
    filename += ".json";
  }
  const responseJSON = await res.json();
  const json = JSON.stringify(responseJSON, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = $el("a", {
    href: url,
    download: filename,
    style: { display: "none" },
    parent: document.body,
  });
  a.click();
  setTimeout(() => {
    a.remove();
    window.URL.revokeObjectURL(url);
  }, 0);
};

const showSaveFalFormatButton = async () => {
  const falFormatButton = document.createElement("button");
  falFormatButton.id = "save-fal-format-button";
  falFormatButton.textContent = "Save as fal format";
  falFormatButton.style.background =
    "linear-gradient(90deg, #192A51 0%, #6B3E9B 50%, #0099FF 100%)";
  falFormatButton.style.display = "inline-block";
  falFormatButton.style.color = "#fefefe";

  falFormatButton.style.display = "block";
  falFormatButton.onclick = async () => {
    try {
      const comfyPrompt = await app.graphToPrompt();
      const response = await api.fetchApi("/fal/save", {
        method: "POST",
        body: JSON.stringify({ ...comfyPrompt, client_id: api.clientId }),
        headers: { "Content-Type": "application/json" },
      });
      if (response.status !== 200) {
        throw {
          response: await response.json(),
        };
      }
      const responseJSON = await response.json();
      const json = JSON.stringify(responseJSON, null, 2);
      const closeButton = app.ui.dialog.textElement.nextSibling;
      const saveButton = $el("button", {
        type: "button",
        textContent: "Save",
        onclick: () => saveComfyPrompt(json),
      });
      closeButton.before(saveButton);

      app.ui.dialog.show(
        $el("div", {}, [
          $el("pre", {
            style: {
              color: "white",
            },
            textContent: json,
          }),
        ]),
      );
    } catch (error) {
      const formattedError = await formatPromptError(error);
      app.ui.dialog.show(formattedError);
      if (error.response) {
        app.lastNodeErrors = error.response.node_errors;
        app.canvas.draw(true, true);
      }
    }
  };

  const falConnectButton = document.getElementById("fal-connect-button");
  falConnectButton.after(falFormatButton);
};

app.registerExtension({
  name: "Comfy.falConnector",
  async setup() {
    await registerFalConnectButton();
    await registerFalInfoLabel();
    await hideUnusedElements();
    await showSaveFalFormatButton();
  },
});
