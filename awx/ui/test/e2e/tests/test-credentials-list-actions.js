import { getAdminMachineCredential } from '../fixtures';

const data = {};

module.exports = {
    before: (client, done) => {
        getAdminMachineCredential('test-actions')
            .then(obj => { data.credential = obj; })
            .then(done);
    },
    'copy credential': client => {
        const credentials = client.page.credentials();

        client.useCss();
        client.login();
        client.waitForAngular();

        credentials.load();
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        credentials.section.list.expect.element('smart-search').visible;
        credentials.section.list.expect.element('smart-search input').enabled;

        credentials.section.list
            .sendKeys('smart-search input', `id:>${data.credential.id - 1} id:<${data.credential.id + 1}`)
            .sendKeys('smart-search input', client.Keys.ENTER);

        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        credentials.expect.element(`#credentials_table .List-tableRow[id="${data.credential.id}"]`).visible;
        credentials.expect.element('i[class*="copy"]').visible;
        credentials.expect.element('i[class*="copy"]').enabled;

        credentials.click('i[class*="copy"]');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        const activityStream = 'bread-crumb > div i[class$="icon-activity-stream"]';
        const activityRow = '#activities_table .List-tableCell[class*="description-column"] a';
        const toast = 'div[class="Toast-icon"]';

        credentials.waitForElementNotPresent(toast);
        credentials.expect.element(activityStream).visible;
        credentials.expect.element(activityStream).enabled;
        credentials.click(activityStream);
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        client
            .waitForElementVisible(activityRow)
            .click(activityRow);

        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        credentials.expect.element('div[ui-view="edit"] form').visible;
        credentials.section.edit.expect.element('@title').visible;
        credentials.section.edit.expect.element('@title').text.contain(data.credential.name);
        credentials.section.edit.expect.element('@title').text.not.equal(data.credential.name);
        credentials.section.edit.section.details.expect.element('@save').visible;
        credentials.section.edit.section.details.expect.element('@save').enabled;

        client.end();
    }
};
