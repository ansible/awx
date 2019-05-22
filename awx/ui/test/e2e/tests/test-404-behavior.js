import {
    AWX_E2E_URL,
    AWX_E2E_TIMEOUT_MEDIUM
} from '../settings';

module.exports = {
    before: (client) => {
        client
            .login()
            .waitForAngular();
    },
    'Test that default the 404 behavior redirects to the dashboard': client => {
        client.navigateTo(`${AWX_E2E_URL}#/brokenurl`, false);
        client.useXpath().waitForElementVisible('//job-status-graph');
        client.assert.urlContains('#/home');
    },
    'Test 404 modal for job templates': client => {
        client.navigateTo(`${AWX_E2E_URL}#/templates/job_template/99999`, false);
        client.expect.element('//*[@id="alert-modal"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.findThenClick('//*[@id="alert_ok_btn"]');
    },
    'Test 404 modal for workflow job templates': client => {
        client.navigateTo(`${AWX_E2E_URL}#/templates/workflow_job_template/99999`, false);
        client.expect.element('//*[@id="alert-modal"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.findThenClick('//*[@id="alert_ok_btn"]');
    },
    'Test 404 modal for credentials': client => {
        client.navigateTo(`${AWX_E2E_URL}#/credentials/99999`, false);
        client.expect.element('//*[@id="alert-modal"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.findThenClick('//*[@id="alert_ok_btn"]');
    },
    'Test 404 modal for projects': client => {
        client.navigateTo(`${AWX_E2E_URL}#/projects/99999`, false);
        client.expect.element('//*[@id="alert-modal"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.findThenClick('//*[@id="alert_ok_btn"]');
    },
    after: client => {
        client.end();
    }
};
