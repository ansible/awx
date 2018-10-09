import {
    getInventorySource,
    getJobTemplate,
    getProject,
    getWorkflowTemplate
} from '../fixtures';

let data;
const workflowTemplateNavTab = "//at-side-nav-item[contains(@name, 'TEMPLATES')]";
const workflowSelector = "//a[contains(text(), 'test-actions-workflow-template')]";
const workflowVisualizerBtn = "//button[contains(@id, 'workflow_job_template_workflow_visualizer_btn')]";

const rootNode = "//*[@id='node-2']";
const childNode = "";
const leafNode = "//g[contains(@id, 'node-1')]";
const project = "//td[contains(text(), 'test-actions-project')]";
const edgeTypeDropdown = "//span[contains(@id, 'select2-workflow_node_edge-container')]";
const alwaysDropdown = "//*[@id='select2-workflow_node_edge-result-elm7-always']"
const successDropdown = "//*[@id='select2-workflow_node_edge-result-veyc-success']"
const failureDropdown = "//*[@id='select2-workflow_node_edge-result-xitr-failure']"

module.exports = {
    before: (client, done) => {
        const resources = [
            getInventorySource('test-actions'),
            getJobTemplate('test-actions'),
            getProject('test-actions'),
            getWorkflowTemplate('test-actions'),
        ];

        Promise.all(resources)
            .then(([source, template, project, workflow]) => {
                data = { source, template, project, workflow };
                done();
            });
        client
            .login()
            .waitForAngular()
            .resizeWindow(1200, 1000)
            .useXpath()
            .findThenClick(workflowTemplateNavTab)
            .pause(1000)
            .findThenClick(workflowSelector)
            .findThenClick(workflowVisualizerBtn);
    },
    'verify that workflow visualizer root node can only be set to always': client => {
        client
            .useXpath()
            .findThenClick(rootNode)
            .findThenClick(project)
            .findThenClick(edgeTypeDropdown);
    },
};
