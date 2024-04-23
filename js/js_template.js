export const getJSTemplate = (promptJSON) => {
  const indent = 2;
  const promptStringified = JSON.stringify(promptJSON, null, indent);

  let getWorkflowTemplate = "getWorkflow({}),";
  // check if there are any fal_inputs
  if (promptJSON.fal_inputs && Object.keys(promptJSON.fal_inputs).length > 0) {
    let exampleObject = JSON.stringify(promptJSON.fal_inputs, null, indent * 3);
    // remove the first and last curly braces
    exampleObject = exampleObject.substring(2, exampleObject.length - 2);

    getWorkflowTemplate = `getWorkflow({
${exampleObject}
  }),`;
  }

  return `
import * as fal from "@fal-ai/serverless-client";

// This is a simple example of how to use the fal-js SDK to execute a workflow.
const result = fal.subscribe("fal-ai/fast-sdxl", {
  input: ${getWorkflowTemplate}
  logs: true,
  onQueueUpdate: (update) => {
    if (update.status === "IN_PROGRESS") {
      update.logs.map((log) => log.message).forEach(console.log);
    }
  },
});

// This workflow is generated with ComfyUI-fal
const WORKFLOW = ${promptStringified}

function getWorkflow(object: any) {
  let newWorkflow = JSON.parse(JSON.stringify(WORKFLOW));
  newWorkflow.fal_inputs = {
    ...newWorkflow.fal_inputs,
    ...object,
  };

  return newWorkflow;
}

`;
};
