import {
    getInventorySource,
    getJobTemplate,
    getProject,
    getWorkflowTemplate
} from '../fixtures';

let data;

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
    },
    'copy job template': client => {
        const templates = client.page.templates();

        client.useCss();
        client.resizeWindow(1200, 800);
        client.login();
        client.waitForAngular();

        templates.navigate();
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.expect.element('smart-search').visible;
        templates.expect.element('smart-search input').enabled;

        templates
            .sendKeys('smart-search input', `id:>${data.template.id - 1} id:<${data.template.id + 1}`)
            .sendKeys('smart-search input', client.Keys.ENTER);

        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.expect.element('.at-Panel-headingTitleBadge').text.equal('1');
        templates.expect.element(`#row-${data.template.id}`).visible;
        templates.expect.element('i[class*="copy"]').visible;
        templates.expect.element('i[class*="copy"]').enabled;

        templates.click('i[class*="copy"]');
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.expect.element('#job_template_form').visible;
        templates.section.addJobTemplate.expect.element('@title').visible;
        templates.section.addJobTemplate.expect.element('@title').text.contain(data.template.name);
        templates.section.addJobTemplate.expect.element('@title').text.not.equal(data.template.name);
        templates.expect.element('@save').visible;
        templates.expect.element('@save').enabled;

        client.end();
    },
    'copy workflow template': client => {
        const templates = client.page.templates();

        client.useCss();
        client.resizeWindow(1200, 800);
        client.login();
        client.waitForAngular();

        templates.navigate();
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.expect.element('smart-search').visible;
        templates.expect.element('smart-search input').enabled;

        templates
            .sendKeys('smart-search input', `id:>${data.workflow.id - 1} id:<${data.workflow.id + 1}`)
            .sendKeys('smart-search input', client.Keys.ENTER);

        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.expect.element('.at-Panel-headingTitleBadge').text.equal('1');
        templates.expect.element(`#row-${data.workflow.id}`).visible;
        templates.expect.element('i[class*="copy"]').visible;
        templates.expect.element('i[class*="copy"]').enabled;

        templates
            .click('i[class*="copy"]')
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny')
            .waitForAngular();

        templates.expect.element('#workflow_job_template_form').visible;
        templates.section.editWorkflowJobTemplate.expect.element('@title').visible;
        templates.section.editWorkflowJobTemplate.expect.element('@title').text.contain(data.workflow.name);
        templates.section.editWorkflowJobTemplate.expect.element('@title').text.not.equal(data.workflow.name);

        templates.expect.element('@save').visible;
        templates.expect.element('@save').enabled;

        client
            .useXpath()
            .pause(1000)
            .waitForElementVisible('//*[text()=" Workflow Editor"]')
            .click('//*[text()=" Workflow Editor"]')
            .useCss()
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny')
            .waitForAngular();

        client.expect.element('#workflow-modal-dialog').visible;
        client.expect.element('#workflow-modal-dialog span[class^="badge"]').visible;
        client.expect.element('#workflow-modal-dialog span[class^="badge"]').text.equal('3');
        client.expect.element('div[class="WorkflowMaker-title"]').visible;
        client.expect.element('div[class="WorkflowMaker-title"]').text.contain(data.workflow.name);
        client.expect.element('div[class="WorkflowMaker-title"]').text.not.equal(data.workflow.name);

        client.expect.element('#workflow-modal-dialog i[class*="fa-cog"]').visible;
        client.expect.element('#workflow-modal-dialog i[class*="fa-cog"]').enabled;

        client.click('#workflow-modal-dialog i[class*="fa-cog"]');

        client.waitForElementVisible('workflow-controls');
        client.waitForElementVisible('div[class*="-zoomPercentage"]');

        client.click('i[class*="fa-home"]').expect.element('div[class*="-zoomPercentage"]').text.equal('100%');
        client.click('i[class*="fa-minus"]').expect.element('div[class*="-zoomPercentage"]').text.equal('90%');
        client.click('i[class*="fa-minus"]').expect.element('div[class*="-zoomPercentage"]').text.equal('80%');
        client.click('i[class*="fa-minus"]').expect.element('div[class*="-zoomPercentage"]').text.equal('70%');
        client.click('i[class*="fa-minus"]').expect.element('div[class*="-zoomPercentage"]').text.equal('60%');

        client.expect.element('#node-1').visible;
        client.expect.element('#node-2').visible;
        client.expect.element('#node-3').visible;
        client.expect.element('#node-4').visible;

        client.expect.element('#node-1 text').text.not.equal('').after(5000);
        client.expect.element('#node-2 text').text.not.equal('').after(5000);
        client.expect.element('#node-3 text').text.not.equal('').after(5000);
        client.expect.element('#node-4 text').text.not.equal('').after(5000);

        const checkNodeText = (selector, text) => client.getText(selector, ({ value }) => {
            client.assert.equal(text.indexOf(value.replace('...', '')) >= 0, true);
        });

        checkNodeText('#node-1 text', 'START');
        checkNodeText('#node-2 text', data.project.name);
        checkNodeText('#node-3 text', data.template.name);
        checkNodeText('#node-4 text', data.source.name);

        templates.expect.element('@save').visible;
        templates.expect.element('@save').enabled;

        client.end();
    }
};
