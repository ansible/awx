import { post, patch } from '../api';
import {
    getOrCreate,
    getUpdatedProject,
    getInventory
} from '../fixtures';

let templateReferences = {};

module.exports = {
    before: (client, done) => {
        const resources = [
            getUpdatedProject('test-launch-jt'),
            getInventory('test-launch-jt')
        ];

        Promise.all(resources)
            .then(([project, inventory]) => {
                const noPromptPromise = getOrCreate('/job_templates/', {
                    name: 'test-launch-jt-no-prompts',
                    inventory: inventory.id,
                    project: project.id,
                    playbook: 'hello_world.yml',
                });

                const promptNoPassPromise = getOrCreate('/job_templates/', {
                    name: 'test-launch-jt-prompts-no-pass',
                    inventory: inventory.id,
                    ask_inventory_on_launch: true,
                    project: project.id,
                    playbook: 'hello_world.yml',
                    ask_diff_mode_on_launch: true,
                    ask_variables_on_launch: true,
                    ask_limit_on_launch: true,
                    ask_tags_on_launch: true,
                    ask_skip_tags_on_launch: true,
                    ask_job_type_on_launch: true,
                    ask_verbosity_on_launch: true,
                    ask_credential_on_launch: true
                });

                Promise.all([noPromptPromise, promptNoPassPromise])
                    .then(([noPrompt, promptNoPass]) => {
                        templateReferences = { noPrompt, promptNoPass };
                        const surveyPost = post(promptNoPass.related.survey_spec, {
                            name: '',
                            description: '',
                            spec: [{
                                question_name: 'Foo',
                                question_description: '',
                                required: true,
                                type: 'text',
                                variable: 'foo',
                                min: 0,
                                max: 1024,
                                default: 'bar',
                                choices: '',
                                new_question: true
                            }]
                        });

                        surveyPost
                            .then(() => patch(promptNoPass.url, { survey_enabled: true }))
                            .then(done);
                    });
            });
    },
    'login to awx': client => {
        client.login();
        client.waitForAngular();
    },
    'expected jt launch with no prompts to navigate to job details': client => {
        const templates = client.page.templates();
        templates.load();
        templates.waitForElementVisible('input[class*="SmartSearch-input"]');
        templates.section.list.section.search
            .sendKeys('@input', `id:${templateReferences.noPrompt.id}`);
        templates.section.list.section.search.getValue('@input', (result) => {
            client.assert.equal(result.value, `id:${templateReferences.noPrompt.id}`);
        });
        client.pause(1000).waitForElementNotVisible('div.spinny');
        templates.waitForElementVisible('i[class$="search"]');
        templates.section.list.section.search.click('i[class$="search"]');
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');
        templates.expect.element('.at-Panel-headingTitleBadge').text.equal('1');
        templates.expect.element(`#templates_list .at-Row[id="row-${templateReferences.noPrompt.id}"]`).visible;
        templates.expect.element('i[class*="icon-launch"]').visible;
        templates.expect.element('i[class*="icon-launch"]').enabled;
        templates.click('i[class*="icon-launch"]');
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');
        client.waitForElementVisible('at-job-details', 10000);

        client.useXpath();
        client.waitForElementVisible('.//span[normalize-space(text())=\'"msg": "Hello World!"\']', 60000);
        client.useCss();
    },
    'expected jt launch with prompts but no changes to navigate to job details': client => {
        const templates = client.page.templates();
        templates.load();
        templates.waitForElementVisible('input[class*="SmartSearch-input"]');
        templates.section.list.section.search
            .sendKeys('@input', `id:${templateReferences.promptNoPass.id}`);
        templates.section.list.section.search.getValue('@input', (result) => {
            client.assert.equal(result.value, `id:${templateReferences.promptNoPass.id}`);
        });
        client.pause(1000).waitForElementNotVisible('div.spinny');
        templates.waitForElementVisible('i[class$="search"]');
        templates.section.list.section.search.click('i[class$="search"]');
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');
        templates.expect.element('.at-Panel-headingTitleBadge').text.equal('1');
        templates.expect.element(`#templates_list .at-Row[id="row-${templateReferences.promptNoPass.id}"]`).visible;
        templates.expect.element('i[class*="icon-launch"]').visible;
        templates.expect.element('i[class*="icon-launch"]').enabled;
        templates.click('i[class*="icon-launch"]');
        templates.waitForElementVisible('#prompt-inventory');
        templates.expect.element('#prompt_inventory_tab').visible;
        templates.expect.element('#prompt_inventory_tab').to.have.attribute('class').which.contains('at-Tab--active');
        templates.expect.element('#prompt_inventory_next').visible;
        templates.expect.element('#prompt_inventory_next').enabled;
        templates.waitForElementNotVisible('div.spinny');
        templates.click('#prompt_inventory_next');
        templates.waitForElementVisible('#prompt_credential_step');
        templates.expect.element('#prompt_credential_tab').visible;
        templates.expect.element('#prompt_credential_tab').to.have.attribute('class').which.contains('at-Tab--active');
        templates.expect.element('#prompt_credential_next').visible;
        templates.expect.element('#prompt_credential_next').enabled;
        templates.waitForElementNotVisible('div.spinny');
        templates.click('#prompt_credential_next');
        templates.waitForElementVisible('#prompt_other_prompts_step');
        templates.expect.element('#prompt_other_prompts_tab').visible;
        templates.expect.element('#prompt_other_prompts_tab').to.have.attribute('class').which.contains('at-Tab--active');
        templates.expect.element('#prompt_other_prompts_next').visible;
        templates.expect.element('#prompt_other_prompts_next').enabled;
        templates.waitForElementNotVisible('div.spinny');
        templates.click('#prompt_other_prompts_next');
        templates.waitForElementVisible('#prompt_survey_step');
        templates.expect.element('#prompt_survey_tab').visible;
        templates.expect.element('#prompt_survey_tab').to.have.attribute('class').which.contains('at-Tab--active');
        templates.expect.element('#prompt_survey_next').visible;
        templates.expect.element('#prompt_survey_next').enabled;
        templates.waitForElementNotVisible('div.spinny');
        templates.click('#prompt_survey_next');
        templates.waitForElementVisible('#prompt_preview_step');
        templates.expect.element('#prompt_preview_tab').visible;
        templates.expect.element('#prompt_preview_tab').to.have.attribute('class').which.contains('at-Tab--active');
        templates.expect.element('#prompt_finish').visible;
        templates.expect.element('#prompt_finish').enabled;
        templates.waitForElementNotVisible('div.spinny');
        templates.click('#prompt_finish');
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');
        client.waitForElementVisible('at-job-details', 10000);

        client.useXpath();
        client.waitForElementVisible('.//span[normalize-space(text())=\'"msg": "Hello World!"\']', 60000);
        client.useCss();

        client.end();
    }
};
