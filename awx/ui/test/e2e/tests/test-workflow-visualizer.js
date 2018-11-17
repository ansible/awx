import {
    getInventorySource,
    getJobTemplate,
    getProject,
    getWorkflowTemplate
} from '../fixtures';

let data;
const spinny = "//*[contains(@class, 'spinny')]";
const workflowTemplateNavTab = "//at-side-nav-item[contains(@name, 'TEMPLATES')]";
const workflowSelector = "//a[contains(text(), 'test-actions-workflow-template')]";
const workflowVisualizerBtn = "//button[contains(@id, 'workflow_job_template_workflow_visualizer_btn')]";
const workflowSearchBar = "//input[contains(@class, 'SmartSearch-input')]";
const workflowText = 'name.iexact:"test-actions-workflow-template"';
const workflowSearchBadgeCount = '//span[contains(@class, "at-Panel-headingTitleBadge") and contains(text(), "1")]';

const rootNode = "//*[@id='node-2']";
const childNode = "//*[@id='node-3']";
const newChildNode = "//*[@id='node-5']";
const leafNode = "//*[@id='node-6']";
const nodeAdd = "//*[contains(@class, 'nodeAddCross')]";
const nodeRemove = "//*[contains(@class, 'nodeRemoveCross')]";

// one of the jobs or projects or inventories
const testActionsProject = "//td[contains(text(), 'test-actions-project')]";
const testActionsJob = "//td[contains(text(), 'test-actions-job')]";
const testActionsProjectText = 'name.iexact:"test-actions-project"';
const testActionsJobText = 'name.iexact:"test-actions-job-template"';

// search bar for visualizer templates
const jobSearchBar = "//*[contains(@id, 'workflow-jobs-list')]//input[contains(@class, 'SmartSearch-input')]";
const projectSearchBar = "//*[contains(@id, 'workflow-project-sync-list')]//input[contains(@class, 'SmartSearch-input')]";

// dropdown bar which lets you select edge type
const edgeTypeDropdownBar = "//span[contains(@id, 'select2-workflow_node_edge-container')]";
const alwaysDropdown = "//li[contains(@id, 'select2-workflow_node_edge') and text()='Always']";
const successDropdown = "//li[contains(@id, 'select2-workflow_node_edge') and text()='On Success']";
const failureDropdown = "//li[contains(@id, 'select2-workflow_node_edge') and text()='On Failure']";
const selectButton = "//*[@id='workflow_maker_select_btn']";
const deleteConfirmation = "//button[@ng-click='confirmDeleteNode()']";

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
            .pause(1500)
            .waitForElementNotVisible(spinny)
            .clearValue(workflowSearchBar)
            .setValue(workflowSearchBar, [workflowText, client.Keys.ENTER])
            .waitForElementVisible(workflowSearchBadgeCount)
            .waitForElementNotVisible(spinny)
            .findThenClick(workflowSelector)
            .findThenClick(workflowVisualizerBtn);
    },
    'verify that workflow visualizer root node can only be set to always': client => {
        client
            .useXpath()
            .findThenClick(rootNode)
            .clearValue(projectSearchBar)
            .setValue(projectSearchBar, [testActionsProjectText, client.Keys.ENTER])
            .pause(1000)
            .findThenClick(testActionsProject)
            .findThenClick(edgeTypeDropdownBar)
            .waitForElementNotPresent(successDropdown)
            .waitForElementNotPresent(failureDropdown)
            .waitForElementPresent(alwaysDropdown);
    },
    'verify that a non-root node can be set to always/success/failure': client => {
        client
            .useXpath()
            .findThenClick(childNode)
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .findThenClick(edgeTypeDropdownBar)
            .waitForElementPresent(successDropdown)
            .waitForElementPresent(failureDropdown)
            .waitForElementPresent(alwaysDropdown)
            .findThenClick(edgeTypeDropdownBar);
    },
    'verify that a sibling node can be any edge type': client => {
        client
            .useXpath()
            .moveToElement(childNode, 0, 0, () => {
                client.pause(500);
                client.waitForElementNotVisible(spinny);
                // Concatenating the xpaths lets us click the proper node
                client.click(childNode + nodeAdd);
            })
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .clearValue(jobSearchBar)
            .setValue(jobSearchBar, [testActionsJobText, client.Keys.ENTER])
            .pause(1000)
            .findThenClick(testActionsJob)
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .findThenClick(edgeTypeDropdownBar)
            .waitForElementPresent(successDropdown)
            .waitForElementPresent(failureDropdown)
            .waitForElementPresent(alwaysDropdown)
            .findThenClick(alwaysDropdown)
            .click(selectButton);
    },
    'Verify node-shifting behavior upon deletion': client => {
        client
            .findThenClick(newChildNode)
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .findThenClick(edgeTypeDropdownBar)
            .findThenClick(successDropdown)
            .click(selectButton)
            .moveToElement(newChildNode, 0, 0, () => {
                client.pause(500);
                client.waitForElementNotVisible(spinny);
                client.click(newChildNode + nodeAdd);
            })
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .clearValue(jobSearchBar)
            .setValue(jobSearchBar, [testActionsJobText, client.Keys.ENTER])
            .pause(1000)
            .findThenClick(testActionsJob)
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .findThenClick(edgeTypeDropdownBar)
            .waitForElementPresent(successDropdown)
            .waitForElementPresent(failureDropdown)
            .waitForElementPresent(alwaysDropdown)
            .findThenClick(alwaysDropdown)
            .click(selectButton)
            .moveToElement(newChildNode, 0, 0, () => {
                client.pause(500);
                client.waitForElementNotVisible(spinny);
                client.click(newChildNode + nodeRemove);
            })
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .findThenClick(deleteConfirmation)
            .findThenClick(leafNode)
            .pause(1000)
            .waitForElementNotVisible(spinny)
            .findThenClick(edgeTypeDropdownBar)
            .waitForElementPresent(successDropdown)
            .waitForElementPresent(failureDropdown)
            .waitForElementPresent(alwaysDropdown);
    },
    after: client => {
        client.end();
    }
};
