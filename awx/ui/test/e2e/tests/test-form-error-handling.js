/* Tests for validation checks during form creation and editing. */

import {
    getJobTemplate
} from '../fixtures';

import {
    AWX_E2E_TIMEOUT_MEDIUM,
    AWX_E2E_TIMEOUT_SHORT
} from '../settings';

let data;

const templatesNavTab = '//at-side-nav-item[contains(@name, "TEMPLATES")]';
const orgsNavTab = '//at-side-nav-item[contains(@name, "ORGANIZATIONS")]';

module.exports = {
    before: (client, done) => {
        const resources = [
            getJobTemplate('test-form-error-handling'),
            getJobTemplate('test-form-error-handling-2')
        ];

        Promise.all(resources)
            .then(([jt, jt2]) => {
                data = { jt, jt2 };
                // We login and load the test page *after* data setup is finished.
                // This helps avoid flakiness due to unpredictable spinners, etc.
                // caused by first-time project syncs when creating the job templates.
                client
                    .login()
                    .waitForAngular()
                    .useXpath()
                    .findThenClick(templatesNavTab)
                    .findThenClick('//*[@id="button-add"]')
                    .findThenClick('//a[@ui-sref="templates.addJobTemplate"]');
                done();
            });
    },
    'Test max character limit when creating a job template': client => {
        client
            .waitForElementVisible('//input[@id="job_template_name"]')
            .setValue(
                '//input[@id="job_template_name"]',
                ['a'.repeat(513), client.Keys.ENTER]
            )
            .setValue(
                '//input[@name="inventory_name"]',
                ['test-form-error-handling-inventory', client.Keys.ENTER]
            )
            .setValue(
                '//input[@name="project_name"]',
                ['test-form-error-handling-project', client.Keys.ENTER]
            )
            // After the test sets a value for the project, a few seconds are
            // needed while the UI fetches the playbooks names with a network
            // call. There's no obvious dom element here to poll, so we wait a
            // reasonably safe amount of time for the form to settle down
            // before proceeding.
            .pause(AWX_E2E_TIMEOUT_MEDIUM)
            .waitForElementNotVisible('//*[contains(@class, "spinny")]')
            .findThenClick('//*[@id="select2-playbook-select-container"]')
            .findThenClick('//li[text()="hello_world.yml"]')
            .findThenClick('//*[@id="job_template_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]');

        client.expect.element('//div[@id="job_template_name_group"]' +
            '//div[@id="job_template-name-api-error"]').to.be.visible;
    },
    'Test duplicate template name handling when creating a job template': client => {
        client
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]')
            .waitForElementVisible('//div[contains(@class, "Form-title")]')
            .clearValue('//input[@id="job_template_name"]')
            .setValue(
                '//input[@id="job_template_name"]',
                ['test-form-error-handling-job-template', client.Keys.ENTER]
            )
            .findThenClick('//*[@id="job_template_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]');
    },

    'Test incorrect format when creating a job template': client => {
        client
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]')
            .waitForElementVisible('//div[contains(@class, "Form-title")]')
            .clearValue('//input[@name="inventory_name"]')
            .setValue(
                '//input[@name="inventory_name"]',
                ['invalid inventory name', client.Keys.ENTER]
            )
            .clearValue('//input[@name="project_name"]')
            .setValue(
                '//input[@name="project_name"]',
                ['invalid project', client.Keys.ENTER]
            );

        client.expect.element('//*[@id="job_template-inventory-notfound-error"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_SHORT);
        client.expect.element('//*[@id="job_template-project-notfound-error"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_SHORT);
    },

    'Test max character limit when editing a job template': client => {
        client
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]')
            .setValue(
                '//input[contains(@class, "SmartSearch-input")]',
                ['name.iexact:test-form-error-handling-job-template', client.Keys.ENTER]
            )
            // double click to make field active
            .findThenClick('//a[text()="test-form-error-handling-job-template"]')
            .findThenClick('//a[text()="test-form-error-handling-job-template"]')
            .findThenClick('//div[contains(@class, "Form-title") and text()="test-form-error-handling-job-template"]')
            .clearValue('//input[@id="job_template_name"]')
            .setValue(
                '//input[@id="job_template_name"]',
                ['a'.repeat(513), client.Keys.ENTER]
            )
            .findThenClick('//*[@id="job_template_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]');

        client.expect.element('//div[@id="job_template_name_group"]' +
            '//div[@id="job_template-name-api-error"]').to.be.visible.after(AWX_E2E_TIMEOUT_SHORT);
    },

    'Test duplicate template name handling when editing a job template': client => {
        client
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]')
            .findThenClick('//div[contains(@class, "Form-title")]')
            .clearValue('//input[@id="job_template_name"]')
            .setValue(
                '//input[@id="job_template_name"]',
                ['test-form-error-handling-2-job-template', client.Keys.ENTER]
            )
            .findThenClick('//*[@id="job_template_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]');
    },

    'Test incorrect format when editing a job template': client => {
        client
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]')
            .waitForElementVisible('//div[contains(@class, "Form-title")]')
            .clearValue('//input[@name="inventory_name"]')
            .setValue(
                '//input[@name="inventory_name"]',
                ['invalid inventory name', client.Keys.ENTER]
            )
            .clearValue('//input[@name="project_name"]')
            .setValue(
                '//input[@name="project_name"]',
                ['invalid project', client.Keys.ENTER]
            );

        client.expect.element('//*[@id="job_template-inventory-notfound-error"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_SHORT);
        client.expect.element('//*[@id="job_template-project-notfound-error"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_SHORT);
    },

    'Test max character limit when creating an organization': client => {
        client
            .findThenClick(orgsNavTab)
            .findThenClick('//*[@id="button-add"]')
            .waitForElementVisible('//div[contains(@class, "Form-title")]')
            .setValue(
                '//input[@id="organization_name"]',
                ['a'.repeat(513), client.Keys.ENTER]
            )
            .findThenClick('//*[@id="organization_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]')
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]');
    },

    'Test duplicate template name handling when creating an organization': client => {
        client
            .setValue(
                '//input[@id="organization_name"]',
                ['test-form-error-handling-2-organization)', client.Keys.ENTER]
            )
            .findThenClick('//*[@id="organization_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]')
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]');
    },

    'Test max character limit when editing an organization': client => {
        client
            .setValue(
                '//input[contains(@class, "SmartSearch-input")]',
                ['name.iexact:test-form-error-handling-organization', client.Keys.ENTER]
            )
            // double click to make field active
            .findThenClick('//a[normalize-space(text())= "test-form-error-handling-organization"]')
            .findThenClick('//a[normalize-space(text())= "test-form-error-handling-organization"]')
            .findThenClick('//*[contains(@class, "Form-title") and text()="test-form-error-handling-organization"]')
            .clearValue('//input[@id="organization_name"]')
            .setValue(
                '//input[@id="organization_name"]',
                ['a'.repeat(513), client.Keys.ENTER]
            )
            .findThenClick('//*[@id="organization_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]')
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]');
    },

    'Test duplicate template name handling when editing an organization': client => {
        client
            .clearValue('//input[@id="organization_name"]')
            .setValue(
                '//input[@id="organization_name"]',
                ['test-form-error-handling-2-organization', client.Keys.ENTER]
            )
            .findThenClick('//*[@id="organization_save_btn"]')
            .findThenClick('//*[@id="alert_ok_btn"]')
            .waitForElementNotVisible('//*[@id="alert_ok_btn"]');
    },

    after: client => {
        client.end();
    }
};
