import {
    getInventorySource,
    getJobTemplate,
    getProject,
    getWorkflowTemplate
} from '../fixtures';

const spinny = 'div.spinny';
const workflowTemplateNavTab = 'at-side-nav-item i[class*="pencil"]';
const workflowTemplateVisualizerBtn = '#workflow_job_template_workflow_visualizer_btn';
const workflowSearchBar = 'div[ui-view="templatesList"] smart-search input';
const workflowText = 'name.iexact:"test-actions-workflow-template"';
const templatesListBadge = '.at-Panel-headingTitleBadge';

const rootNode = '#node-1';
const childNode = '#node-3';
const newChildNode = '#node-5';
const leafNode = "#node-6";
const nodeAdd = 'circle[class*="nodeAddCircle"]';
const nodeRemove = 'circle[class*="nodeRemoveCircle"]';

const testActionsProjectText = 'name.iexact:"test-actions-project"';
const testActionsJobTemplateText = 'name.iexact:"test-actions-job-template"';

// search bar for visualizer templates
const jobTemplateSearchBar = '#workflow-jobs-list smart-search input';
const projectSearchBar = '#workflow-project-sync-list smart-search input';

// node selection buttons
const selectButton = '#workflow_maker_select_btn';
const cancelButton = '#workflow_maker_cancel_btn';
const deleteConfirmation = '#workflow-modal-dialog button[ng-click="confirmDeleteNode()"]';

// dropdown bar which lets you select edge type
const edgeTypeDropdownBar = "//span[contains(@id, 'select2-workflow_node_edge') and contains(@class, 'selection')]";
const alwaysDropdown = "//li[contains(@id, 'select2-workflow_node_edge') and text()='Always']";
const successDropdown = "//li[contains(@id, 'select2-workflow_node_edge') and text()='On Success']";
const failureDropdown = "//li[contains(@id, 'select2-workflow_node_edge') and text()='On Failure']";

// one of the job templates, projects or inventories - these selectors are dynamically generated
// below during test setup
let testActionsWorkflowtemplateLink;
let testActionsProject;
let testActionsJobTemplate;

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
                testActionsWorkflowtemplateLink = `a[href="/#/templates/workflow_job_template/${workflow.id}"]`;
                testActionsProject = `#projects_table tr[id="${project.id}"]`;
                testActionsJobTemplate = `#templates_table tr[id="${template.id}"]`;

                console.log(testActionsWorkflowtemplateLink);

                done();
            });
    },
    'navigate to the workflow template visualizer': client => {
        client
            .login()
            .waitForAngular()
            .resizeWindow(1200, 1000)
            .findThenClick(workflowTemplateNavTab)
            .pause(1500)
            .waitForElementNotVisible(spinny)
            .search(workflowSearchBar, workflowText)
            .waitForElementPresent(templatesListBadge)
            .waitForElementVisible(templatesListBadge);

        client.expect.element(templatesListBadge).text.to.equal('1').before(10000);

        client
            .findThenClick(testActionsWorkflowtemplateLink)
            .findThenClick(workflowTemplateVisualizerBtn);
    },
    'verify that workflow visualizer root node can only be set to always': client => {
        client
            .findThenClick(rootNode)
            .search(jobTemplateSearchBar, testActionsJobTemplateText)
            .findThenClick(testActionsJobTemplate);

        client
            .useXpath()
            .findThenClick(edgeTypeDropdownBar)
            .waitForElementNotPresent(successDropdown)
            .waitForElementNotPresent(failureDropdown)
            .waitForElementPresent(alwaysDropdown)
            .useCss()
            .click(cancelButton)
            .waitForElementNotPresent(cancelButton)
            .waitForElementNotPresent('#node-6');
    },
    'verify that a non-root node can be set to always/success/failure': client => {
        client
            .waitForElementVisible('#link-3-4')
            .click('#link-3-4') // TODO: find a way to click the link and not the + icon
    //         .waitForElementNotVisible(spinny)
    //         .pause();

    //     client
    //         .useXpath()
    //         .findThenClick(edgeTypeDropdownBar)
    //         .pause()
    //         .waitForElementPresent(successDropdown)
    //         .waitForElementPresent(failureDropdown)
    //         .waitForElementPresent(alwaysDropdown)
    //         .findThenClick(edgeTypeDropdownBar)
    //         .useCss();
    // },
    // 'verify that a sibling node can be any edge type': client => {
    //     client
    //         .moveToElement(childNode, 0, 0, () => {
    //             client.pause(500);
    //             client.waitForElementNotVisible(spinny);
    //             // Concatenating the selectors lets us click the proper node
    //             client.click(childNode + ' ' + nodeAdd);
    //         })
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny)
    //         .search(jobTemplateSearchBar, testActionsJobTemplateText)
    //         .findThenClick(testActionsJobTemplate)
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny);

    //     client
    //         .useXpath()
    //         .findThenClick(edgeTypeDropdownBar)
    //         .waitForElementPresent(successDropdown)
    //         .waitForElementPresent(failureDropdown)
    //         .waitForElementPresent(alwaysDropdown)
    //         .findThenClick(alwaysDropdown)
    //         .useCss();

    //     client.click(selectButton);
    },
    // 'Verify node-shifting behavior upon deletion': client => {
    //     client
    //         .findThenClick(newChildNode)
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny)


    //     client
    //         .useXpath()
    //         .findThenClick(edgeTypeDropdownBar)
    //         .findThenClick(successDropdown)
    //         .useCss();

    //     client
    //         .click(selectButton)
    //         .moveToElement(newChildNode, 0, 0, () => {
    //             client.pause(500);
    //             client.waitForElementNotVisible(spinny);
    //             client.click(newChildNode + ' ' + nodeAdd);
    //         })
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny)
    //         .search(jobTemplateSearchBar, testActionsJobTemplateText)
    //         .pause(1000)
    //         .findThenClick(testActionsJobTemplate)
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny);

    //     client
    //         .useXpath()
    //         .findThenClick(edgeTypeDropdownBar)
    //         .waitForElementPresent(successDropdown)
    //         .waitForElementPresent(failureDropdown)
    //         .waitForElementPresent(alwaysDropdown)
    //         .findThenClick(alwaysDropdown)
    //         .useCss();

    //     client
    //         .click(selectButton)
    //         .moveToElement(newChildNode, 0, 0, () => {
    //             client.pause(500);
    //             client.waitForElementNotVisible(spinny);
    //             client.click(newChildNode + ' ' + nodeRemove);
    //         })
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny)
    //         .findThenClick(deleteConfirmation)
    //         .findThenClick(leafNode)
    //         .pause(1000)
    //         .waitForElementNotVisible(spinny);

    //     client
    //         .useXpath()
    //         .findThenClick(edgeTypeDropdownBar)
    //         .waitForElementPresent(successDropdown)
    //         .waitForElementPresent(failureDropdown)
    //         .waitForElementPresent(alwaysDropdown)
    //         .useCss();
    },
    after: client => {
        client.end();
    }
};
