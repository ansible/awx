import { post } from '../api';
import {
    getInventoryScript,
    getInventorySource,
    getJobTemplate,
    getOrCreate,
    getOrganization,
    getProject,
    getUser,
    getWorkflowTemplate,
} from '../fixtures';

let data;

const promptHeader = '#prompt-header';
const promptWarning = '#prompt-body';
const promptResource = 'span[class="Prompt-warningResourceTitle"]';
const promptResourceCount = 'span[class="badge List-titleBadge"]';
const promptCancelButton = '#prompt_cancel_btn';
const promptActionButton = '#prompt_action_btn';
const promptCloseButton = '#prompt-header + div i[class*="times-circle"]';

module.exports = {
    before: (client, done) => {
        const resources = [
            getUser('test-warnings'),
            getOrganization('test-warnings'),
            getWorkflowTemplate('test-warnings'),
            getProject('test-warnings'),
            getJobTemplate('test-warnings'),
            getInventoryScript('external-org'),
            getInventorySource('external-org'),
        ];

        Promise.all(resources)
            .then(([user, org, workflow, project, template, script, source]) => {
                const unique = 'unified_job_template';
                const nodes = workflow.related.workflow_nodes;
                const nodePromise = getOrCreate(nodes, { [unique]: source.id }, [unique]);

                const permissions = [
                    [org, 'admin_role'],
                    [workflow, 'admin_role'],
                    [project, 'admin_role'],
                    [template, 'admin_role'],
                    [script, 'read_role'],
                ];

                const assignments = permissions
                    .map(([resource, name]) => resource.summary_fields.object_roles[name])
                    .map(role => `/api/v2/roles/${role.id}/users/`)
                    .map(url => post(url, { id: user.id }))
                    .concat([nodePromise]);

                Promise.all(assignments)
                    .then(() => { data = { user, project, source, template, workflow }; })
                    .then(done);
            });
    },
    'verify job template delete warning': client => {
        const templates = client.page.templates();

        client.useCss();
        client.login();
        client.waitForAngular();

        templates.load();
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
        templates.expect.element('i[class*="trash"]').visible;
        templates.expect.element('i[class*="trash"]').enabled;

        templates.click('i[class*="trash"]');

        templates.expect.element(promptHeader).visible;
        templates.expect.element(promptWarning).visible;
        templates.expect.element(promptResource).visible;
        templates.expect.element(promptResourceCount).visible;
        templates.expect.element(promptCancelButton).visible;
        templates.expect.element(promptActionButton).visible;
        templates.expect.element(promptCloseButton).visible;

        templates.expect.element(promptCancelButton).enabled;
        templates.expect.element(promptActionButton).enabled;
        templates.expect.element(promptCloseButton).enabled;

        templates.expect.element(promptHeader).text.contain('DELETE');
        templates.expect.element(promptHeader).text.contain(`${data.template.name.toUpperCase()}`);

        templates.expect.element(promptWarning).text.contain('job template');

        templates.expect.element(promptResource).text.contain('Workflow Job Template Nodes');
        templates.expect.element(promptResourceCount).text.contain('1');

        templates.click(promptCancelButton);

        templates.expect.element(promptHeader).not.visible;

        client.end();
    },
    'verify workflow template delete warning': client => {
        const templates = client.page.templates();

        client.useCss();
        client.login();
        client.waitForAngular();

        templates.load();
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
        templates.expect.element('i[class*="trash"]').visible;
        templates.expect.element('i[class*="trash"]').enabled;

        templates.click('i[class*="trash"]');

        templates.expect.element(promptHeader).visible;
        templates.expect.element(promptWarning).visible;
        templates.expect.element(promptCancelButton).visible;
        templates.expect.element(promptActionButton).visible;
        templates.expect.element(promptCloseButton).visible;

        templates.expect.element(promptCancelButton).enabled;
        templates.expect.element(promptActionButton).enabled;
        templates.expect.element(promptCloseButton).enabled;

        templates.expect.element(promptHeader).text.contain('DELETE');
        templates.expect.element(promptHeader).text.contain(`${data.workflow.name.toUpperCase()}`);

        templates.expect.element(promptWarning).text.contain('workflow template');

        templates.click(promptCancelButton);

        templates.expect.element(promptHeader).not.visible;

        client.end();
    },
    'verify workflow restricted copy warning': client => {
        const templates = client.page.templates();

        client.useCss();
        client.login(data.user.username);
        client.waitForAngular();

        templates.load();
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

        templates.click('i[class*="copy"]');

        templates.expect.element(promptHeader).visible;
        templates.expect.element(promptWarning).visible;
        templates.expect.element(promptCancelButton).visible;
        templates.expect.element(promptActionButton).visible;
        templates.expect.element(promptCloseButton).visible;

        templates.expect.element(promptCancelButton).enabled;
        templates.expect.element(promptActionButton).enabled;
        templates.expect.element(promptCloseButton).enabled;

        templates.expect.element(promptHeader).text.contain('COPY');
        templates.expect.element(promptHeader).text.contain(`${data.workflow.name.toUpperCase()}`);
        templates.expect.element(promptWarning).text.contain('Unified Job Templates');
        templates.expect.element(promptWarning).text.contain(`${data.source.name}`);

        templates.click(promptCancelButton);

        templates.expect.element(promptHeader).not.visible;

        client.end();
    },
};
