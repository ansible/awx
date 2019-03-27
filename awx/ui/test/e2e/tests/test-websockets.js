/* Websocket tests. These tests verify that items like the sparkline (colored box rows which
 * display job status) and other status icons update correctly as the jobs progress.
 */

import {
    getInventorySource,
    getOrganization,
    getProject,
    getJob,
    getUpdatedProject
} from '../fixtures';

import {
    AWX_E2E_URL,
    AWX_E2E_TIMEOUT_ASYNC,
    AWX_E2E_TIMEOUT_LONG,
    AWX_E2E_TIMEOUT_MEDIUM,
} from '../settings';

let data;

// Xpath selectors for recently run job templates on the dashboard.
const successfulJt = '//a[contains(text(), "test-websockets-successful")]/../..';
const failedJt = '//a[contains(text(), "test-websockets-failed")]/../..';
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
            getJob('test-websockets', 'debug.yml', 'test-websockets-successful', done),
            getJob('test-websockets', 'fail_unless.yml', 'test-websockets-failed', done)
        ];

        Promise.all(resources)
            .then(([inventory, project, org, jt1, jt2]) => {
                data = { inventory, project, org, jt1, jt2 };
                done();
            });

        client
            .login()
            .waitForAngular()
            .resizeWindow(1200, 1000);
    },

    'Test job template status updates for a successful job on dashboard': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/home`);
        getJob('test-websockets', 'debug.yml', 'test-websockets-successful', false);

        client.expect.element('.spinny')
            .to.not.be.visible.before(AWX_E2E_TIMEOUT_MEDIUM);
        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
        client.useXpath().expect.element(`${successfulJt}${sparklineIcon}[1]${success}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_LONG);
    },

    'Test job template status updates for a failed job on dashboard': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/home`);
        getJob('test-websockets', 'fail_unless.yml', 'test-websockets-failed', false);

        client.expect.element('.spinny')
            .to.not.be.visible.before(AWX_E2E_TIMEOUT_MEDIUM);
        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
        client.useXpath().expect.element(`${failedJt}${sparklineIcon}[1]${fail}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_LONG);
    },

    'Test projects list blinking icon': client => {
        client
            .useCss()
            .findThenClick('[ui-sref=projects]', 'css')
            .waitForElementVisible('.SmartSearch-input')
            .clearValue('.SmartSearch-input')
            .setValue(
                '.SmartSearch-input',
                ['name.iexact:"test-websockets-project"', client.Keys.ENTER]
            );
        getUpdatedProject('test-websockets');

        client.expect.element('i.icon-job-running')
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
        client.expect.element('i.icon-job-success')
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
    },

    'Test successful job within an organization view': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/organizations/${data.org.id}/job_templates`)
            .waitForElementVisible('[ui-view=templatesList] .SmartSearch-input')
            .clearValue('[ui-view=templatesList] .SmartSearch-input')
            .setValue(
                '[ui-view=templatesList] .SmartSearch-input',
                ['test-websockets-successful', client.Keys.ENTER]
            );
        getJob('test-websockets', 'debug.yml', 'test-websockets-successful', false);

        client.expect.element('.spinny')
            .to.not.be.visible.before(AWX_E2E_TIMEOUT_MEDIUM);
        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
        client.useXpath().expect.element(`${sparklineIcon}[1]${success}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_LONG);
    },
    'Test failed job within an organization view': client => {
        client
            .useCss()
            .navigateTo(`${AWX_E2E_URL}/#/organizations/${data.org.id}/job_templates`)
            .waitForElementVisible('[ui-view=templatesList] .SmartSearch-input')
            .clearValue('[ui-view=templatesList] .SmartSearch-input')
            .setValue(
                '[ui-view=templatesList] .SmartSearch-input',
                ['test-websockets-failed', client.Keys.ENTER]
            );
        getJob('test-websockets', 'debug.yml', 'test-websockets-failed', false);

        client.expect.element('.spinny')
            .to.not.be.visible.before(AWX_E2E_TIMEOUT_MEDIUM);
        client.useXpath().expect.element(`${sparklineIcon}[1]${running}`)
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
        client.useXpath().expect.element(`${sparklineIcon}[1]${fail}`)
            .to.be.present.before(AWX_E2E_TIMEOUT_LONG);
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
        getUpdatedProject('test-websockets');

        client.expect.element('i.icon-job-running')
            .to.be.visible.before(AWX_E2E_TIMEOUT_LONG);
        client.expect.element('i.icon-job-success')
            .to.be.visible.before(AWX_E2E_TIMEOUT_ASYNC);
    },

    after: client => {
        client.end();
    }
};
