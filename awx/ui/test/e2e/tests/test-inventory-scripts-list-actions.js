import { getInventoryScript } from '../fixtures';

const data = {};

module.exports = {
    before: (client, done) => {
        getInventoryScript('test-actions')
            .then(obj => { data.inventoryScript = obj; })
            .then(done);
    },
    'copy inventory script': client => {
        const inventoryScripts = client.page.inventoryScripts();

        client.useCss();
        client.login();
        client.waitForAngular();

        inventoryScripts.load();
        inventoryScripts.waitForElementVisible('div.spinny');
        inventoryScripts.waitForElementNotVisible('div.spinny');

        inventoryScripts.section.list.expect.element('smart-search').visible;
        inventoryScripts.section.list.expect.element('smart-search input').enabled;

        inventoryScripts.section.list
            .sendKeys('smart-search input', `id:>${data.inventoryScript.id - 1} id:<${data.inventoryScript.id + 1}`)
            .sendKeys('smart-search input', client.Keys.ENTER);

        inventoryScripts.waitForElementVisible('div.spinny');
        inventoryScripts.waitForElementNotVisible('div.spinny');

        inventoryScripts.expect.element(`#inventory_scripts_table .List-tableRow[id="${data.inventoryScript.id}"]`).visible;
        inventoryScripts.expect.element('i[class*="copy"]').visible;
        inventoryScripts.expect.element('i[class*="copy"]').enabled;

        inventoryScripts.click('i[class*="copy"]');
        inventoryScripts.waitForElementVisible('div.spinny');
        inventoryScripts.waitForElementNotVisible('div.spinny');

        const activityStream = 'bread-crumb > div i[class$="icon-activity-stream"]';
        const activityRow = '#activities_table .List-tableCell[class*="description-column"] a';
        const toast = 'div[class="Toast-icon"]';

        inventoryScripts.waitForElementNotPresent(toast);
        inventoryScripts.expect.element(activityStream).visible;
        inventoryScripts.expect.element(activityStream).enabled;
        inventoryScripts.click(activityStream);
        inventoryScripts.waitForElementVisible('div.spinny');
        inventoryScripts.waitForElementNotVisible('div.spinny');

        client
            .waitForElementVisible(activityRow)
            .click(activityRow);

        inventoryScripts.waitForElementVisible('div.spinny');
        inventoryScripts.waitForElementNotVisible('div.spinny');

        inventoryScripts.expect.element('#inventory_script_form').visible;
        inventoryScripts.section.edit.expect.element('@title').visible;
        inventoryScripts.section.edit.expect.element('@title').text.contain(data.inventoryScript.name);
        inventoryScripts.section.edit.expect.element('@title').text.not.equal(data.inventoryScript.name);
        inventoryScripts.expect.element('@save').visible;
        inventoryScripts.expect.element('@save').enabled;

        client.end();
    }
};
