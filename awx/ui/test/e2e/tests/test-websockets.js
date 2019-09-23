/* Websocket tests. These tests verify that items like the sparkline (colored box rows which
 * display job status) and other status icons update correctly as the jobs progress.
 */
import {
    getInventorySource,
    getOrganization,
    getProject,
    getJob,
    getJobTemplate,
    getUpdatedProject
} from '../fixtures';

import {
    AWX_E2E_URL,
    AWX_E2E_TIMEOUT_ASYNC,
    AWX_E2E_TIMEOUT_LONG
} from '../settings';

let data;

// Xpath selectors for recently run job templates on the dashboard.
const successfulJt = '//a[contains(text(), "test-websockets-successful")]/../..';
const failedJt = '//a[contains(text(), "test-websockets-failed")]/../..';
const splitJt = '//a[contains(text(), "test-ws-split-job-template")]/../..';
const sparklineIcon = '//div[contains(@class, "SmartStatus-iconContainer")]';

// Xpath selectors for sparkline icon statuses.
const running = '//div[@ng-show="job.status === \'running\'"]';
const success = '//div[contains(@class, "SmartStatus-iconIndicator--success")]';
const fail = '//div[contains(@class, "SmartStatus-iconIndicator--failed")]';

module.exports = {

    before: (client, done) => {
        const resources = [
            getInventorySource('test-websockets'),
            getProject('test-websockets', 'https://github.com/ansible/test-playbooks'),
            getOrganization('test-websockets'),
            // launch job templates once before running tests so that they appear on the dashboard.
            getJob('test-websockets', 'debug.yml', 'test-websockets-successful', true, done),
            getJob('test-websockets', 'fail_unless.yml', 'test-websockets-failed', true, done),
            getJobTemplate('test-websockets', 'debug.yml', 'test-ws-split-job-template', true, '2'),
            getJob('test-websockets', 'debug.yml', 'test-ws-split-job-template', false, done)
        ];

        Promise.all(resources)
            .then(([inventory, project, org, jt1, jt2, sjt, sj]) => {
                data = { inventory, project, org, jt1, jt2, sjt, sj };
                done();
            });

        client
            .login()
            .waitForAngular();
    },

    'Test job template status updates for a successful job on dashboard': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/home`, false);
        getJob('test-websockets', 'debug.yml', 'test-websockets-successful', false);
        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
        client.useXpath().expect.element(`${successfulJt}${sparklineIcon}[1]${success}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },

    'Test job template status updates for a failed job on dashboard': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/home`, false);
        getJob('test-websockets', 'fail_unless.yml', 'test-websockets-failed', false);
        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
        client.useXpath().expect.element(`${failedJt}${sparklineIcon}[1]${fail}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },

    'Test projects list blinking icon': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/projects`)
            .waitForElementVisible('.SmartSearch-input')
            .clearValue('.SmartSearch-input')
            .setValue(
                '.SmartSearch-input',
                ['name.iexact:"test-websockets-project"', client.Keys.ENTER]
            );
        getUpdatedProject('test-websockets');
        getUpdatedProject('test-websockets'); // occasionally 1st update is too quick

        client.expect.element('i.icon-job-running')
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
        client.expect.element('i.icon-job-success')
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },

    'Test successful job within an organization view': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/organizations/${data.org.id}/job_templates`, false)
            .waitForElementVisible('[ui-view=templatesList] .SmartSearch-input')
            .clearValue('[ui-view=templatesList] .SmartSearch-input')
            .setValue(
                '[ui-view=templatesList] .SmartSearch-input',
                ['test-websockets-successful', client.Keys.ENTER]
            );
        getJob('test-websockets', 'debug.yml', 'test-websockets-successful', false);

        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_ASYNC);
        client.useXpath().expect.element(`${sparklineIcon}[1]${success}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },
    'Test failed job within an organization view': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/organizations/${data.org.id}/job_templates`, false)
            .waitForElementVisible('[ui-view=templatesList] .SmartSearch-input')
            .clearValue('[ui-view=templatesList] .SmartSearch-input')
            .setValue(
                '[ui-view=templatesList] .SmartSearch-input',
                ['test-websockets-failed', client.Keys.ENTER]
            );
        getJob('test-websockets', 'debug.yml', 'test-websockets-failed', false);

        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_ASYNC);
        client.useXpath().expect.element(`${sparklineIcon}[1]${fail}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },
    'Test project blinking icon within an organization view': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/organizations/${data.org.id}/projects`)
            .waitForElementVisible('.projectsList .SmartSearch-input')
            .clearValue('.projectsList .SmartSearch-input')
            .setValue(
                '.projectsList .SmartSearch-input',
                ['test-websockets-project', client.Keys.ENTER]
            );
        client.useXpath().waitForElementVisible('//i[contains(@class, "icon-job")]');
        client.useCss();
        getUpdatedProject('test-websockets');
        getUpdatedProject('test-websockets'); // sometimes project update is too fast

        client.expect.element('i.icon-job-running')
            .to.be.visible.before(AWX_E2E_TIMEOUT_ASYNC);
        client.expect.element('i.icon-job-success')
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },
    'Test job slicing sparkline behavior': client => {
        client.navigateTo(`${AWX_E2E_URL}/#/home`, false);
        getJob('test-websockets', 'debug.yml', 'test-ws-split-job-template', false);

        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_ASYNC);
        client.useXpath().expect.element(`${splitJt}${sparklineIcon}[1]${success}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_ASYNC);
    },
    after: client => {
        client.end();
    }
};
