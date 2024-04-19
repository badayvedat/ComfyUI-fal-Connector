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

const hideSaveButton = async () => {
  const saveButton = document.getElementById("comfy-dialog-save-button");
  if (saveButton) {
    saveButton.style.display = "none";
  }
};

const showSaveButton = async (content) => {
  const saveButton = document.getElementById("comfy-dialog-save-button");
  if (saveButton && content) {
    saveButton._prompt_content = content;
    saveButton.style.display = "inline-block";
  }
};

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
      hideSaveButton();
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

api.addEventListener("fal-node-timings", async ({ detail }) => {});

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

const saveComfyPrompt = async (promptJson) => {
  let filename = "fal_api_workflow.json";
  filename = prompt("Save workflow (API) as:", filename);
  if (!filename) return;
  if (!filename.toLowerCase().endsWith(".json")) {
    filename += ".json";
  }

  const json = JSON.stringify(promptJson, null, 2);
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

const registerSaveFalFormatButton = async () => {
  const falFormatButton = document.createElement("button");
  falFormatButton.id = "save-fal-format-button";
  falFormatButton.textContent = "Save as fal format";
  falFormatButton.style.background =
    "linear-gradient(90deg, #192A51 0%, #6B3E9B 50%, #0099FF 100%)";
  falFormatButton.style.display = "inline-block";
  falFormatButton.style.color = "#fefefe";
  falFormatButton.style.display = "block";

  const closeButton = app.ui.dialog.textElement.nextSibling;
  const saveButton = $el("button", {
    id: "comfy-dialog-save-button",
    type: "button",
    textContent: "Save",
    display: "none",
  });

  saveButton._prompt_content = null;
  saveButton.onclick = () => {
    saveComfyPrompt(saveButton._prompt_content);
  };

  closeButton.before(saveButton);

  const originalCloseHandler = closeButton.onclick;
  closeButton.onclick = () => {
    hideSaveButton();
    originalCloseHandler();
  };

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

      showSaveButton(responseJSON);
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
      hideSaveButton();
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

// Based on https://github.com/comfyanonymous/ComfyUI/blob/4b9005e949224782236a8b914eae48bc503f1f18/web/extensions/core/widgetInputs.js
const CONVERTED_TYPE = "converted-widget";

function getWidgetType(config) {
  // Special handling for COMBO so we restrict links based on the entries
  let type = config[0];
  if (type instanceof Array) {
    type = "COMBO";
  }
  return { type };
}

// 'combo' is a problem because it has a list of options rendered in the widget
// and has a constant value obtained from the py class itself.
// we can modify to render a combo widget with the same options as the original
// however, backend will not be able to get the value from the widget itself
// because the py class will always return the default value
// const VALID_TYPES = ["STRING", "combo", "number", "BOOLEAN"];

const VALID_TYPES = ["STRING", "number", "BOOLEAN"];
const INVALID_OPTIONS = ["control_after_generate"];

const FAL_INPUT_NODES = [
  "IntegerInput_fal",
  "FloatInput_fal",
  "BooleanInput_fal",
  "StringInput_fal",
  // "ComboInput_fal",
];

// create a map to keep track of the number of converted widgets
const convertedWidgetsMap = new Map();

function getConfig(widgetName) {
  const { nodeData } = this.constructor;
  return (
    nodeData?.input?.required[widgetName] ??
    nodeData?.input?.optional?.[widgetName]
  );
}

function isConvertableWidget(widget, config) {
  const isValid =
    VALID_TYPES.includes(widget.type) || VALID_TYPES.includes(config[0]);
  const isUnvalidOption = INVALID_OPTIONS.includes(widget.name);
  const isFalNode = FAL_INPUT_NODES.includes(widget.type);

  return (
    isValid && !isUnvalidOption && !widget.options?.forceInput && !isFalNode
  );
}

function hideWidget(node, widget, suffix = "") {
  if (widget.type?.startsWith(CONVERTED_TYPE)) return;
  widget.origType = widget.type;
  widget.origComputeSize = widget.computeSize;
  widget.origSerializeValue = widget.serializeValue;
  widget.computeSize = () => [0, -4]; // -4 is due to the gap litegraph adds between widgets automatically
  widget.type = CONVERTED_TYPE + suffix;
  widget.serializeValue = () => {
    // Prevent serializing the widget if we have no input linked
    if (!node.inputs) {
      return undefined;
    }
    let node_input = node.inputs.find((i) => i.widget?.name === widget.name);

    if (!node_input || !node_input.link) {
      return undefined;
    }
    return widget.origSerializeValue
      ? widget.origSerializeValue()
      : widget.value;
  };

  // Hide any linked widgets, e.g. seed+seedControl
  if (widget.linkedWidgets) {
    for (const w of widget.linkedWidgets) {
      hideWidget(node, w, ":" + widget.name);
    }
  }
}

function convertTofalInput(node, widget, config) {
  hideWidget(node, widget);
  let widgetName = widget.name;

  const nodeType = node.type.toLowerCase();
  widgetName = `${nodeType}_${widgetName}`;

  const count = convertedWidgetsMap.has(widgetName)
    ? convertedWidgetsMap.get(widgetName) + 1
    : 0;
  convertedWidgetsMap.set(widgetName, count);

  if (count > 0) {
    widgetName = `${widgetName}_${count}`;
  }

  const { type } = getWidgetType(config);

  // Add input and store widget config for creating on primitive node
  const sz = node.size;
  node.addInput(widget.name, type, {
    widget: { name: widget.name, config },
  });

  for (const widget of node.widgets) {
    widget.last_y += LiteGraph.NODE_SLOT_HEIGHT;
  }

  // Restore original size but grow if needed
  node.setSize([Math.max(sz[0], node.size[0]), Math.max(sz[1], node.size[1])]);

  const originalValue = widget.value;

  let newNode = null;
  if (type === "COMBO") {
    const widgetOptions = widget?.options?.values || [];
    newNode = LiteGraph.createNode("ComboInput_fal");

    newNode.widgets[1].value = originalValue;
    newNode.widgets[1].options.values = widgetOptions;

    newNode.widgets[2].value = widgetOptions[0];
    newNode.widgets[2].options.values = widgetOptions;
  } else if (type === "INT") {
    newNode = LiteGraph.createNode("IntegerInput_fal");

    newNode.widgets[1].value = originalValue;

    const minValue = widget?.options?.min;
    const maxValue = widget?.options?.max;
    newNode.widgets[2].value = config[1]?.min ?? minValue;
    newNode.widgets[3].value = config[1]?.max ?? maxValue;
    newNode.widgets[4].value = config[1]?.step ?? 1;
  } else if (type === "FLOAT") {
    newNode = LiteGraph.createNode("FloatInput_fal");

    newNode.widgets[1].value = originalValue;

    const minValue = widget?.options?.min;
    const maxValue = widget?.options?.max;
    newNode.widgets[2].value = config[1]?.min ?? minValue;
    newNode.widgets[3].value = config[1]?.max ?? maxValue;
    newNode.widgets[4].value = config[1]?.step ?? 0.1;
  } else if (type === "BOOLEAN") {
    newNode = LiteGraph.createNode("BooleanInput_fal");
    newNode.widgets[1].value = originalValue;
  } else if (type === "STRING") {
    newNode = LiteGraph.createNode("StringInput_fal");
    newNode.widgets[1].value = originalValue;
  }

  if (!newNode) {
    return;
  }

  newNode.widgets[0].value = widgetName;
  app.graph.add(newNode);

  // connect nodes
  newNode.connect(0, node, node.inputs.length - 1);
}

app.registerExtension({
  name: "Comfy.falConnector",
  async setup() {
    await registerFalConnectButton();
    await registerFalInfoLabel();
    await hideUnusedElements();
    await registerSaveFalFormatButton();
  },
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    nodeType.prototype.getExtraMenuOptions = function (_, options) {
      if (this.widgets) {
        let toInput = [];
        let toWidget = [];

        for (const widget of this.widgets) {
          if (widget.options?.forceInput) {
            continue;
          }
          if (widget.type !== CONVERTED_TYPE) {
            const config = getConfig.call(this, widget.name) ?? [
              widget.type,
              widget.options || {},
            ];
            if (isConvertableWidget(widget, config)) {
              toInput.push({
                content: `Convert ${widget.name} to fal input`,
                className: "litemenu-entry-fal",
                callback: () => convertTofalInput(this, widget, config),
              });
            }
          }
        }
        if (toInput.length) {
          options.push(...toInput, null);
        }

        if (toWidget.length) {
          options.push(...toWidget, null);
        }
      }
    };
  },
});

var styleElement = document.createElement("style");
const cssCode = `
.litemenu-entry-fal
{
    color: #fefefe;
    background: linear-gradient(90deg, #192A51 0%, #6B3E9B 50%, #0099FF 100%);
}
`;
styleElement.innerHTML = cssCode;
document.head.appendChild(styleElement);
