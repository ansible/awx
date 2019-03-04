import {
    AWX_E2E_URL
} from '../settings';

module.exports = {
    before: (client) => {

        client
            .login()
            .waitForAngular()
            .resizeWindow(1200, 1000);
    },
    'Verify 404 page behavior': client => {
        client.navigateTo(AWX_E2E_URL + '#/brokenurl', false);
        client.useXpath().waitForElementVisible('//job-status-graph');
        client.assert.urlContains('#/home');
    },

    after: client => {
        client.end();
    }
};
