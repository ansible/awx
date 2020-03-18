import {
    getInventory,
    getInventoryNoSource,
    getInventorySource,
} from '../fixtures';

let data;

module.exports = {
    before: (client, done) => {
        const resources = [
            getInventory('test-actions'),
            getInventoryNoSource('test-actions'),
            getInventorySource('test-actions'),
        ];

        Promise.all(resources)
            .then(([inventory, inventoryNoSource]) => {
                data = { inventory, inventoryNoSource };
                done();
            });
    },
    'copy inventory': client => {
        const inventories = client.page.inventories();

        client.useCss();
        client.login();
        client.waitForAngular();

        inventories.load();
        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.section.list.expect.element('smart-search').visible;
        inventories.section.list.section.search.expect.element('@input').enabled;

        inventories.section.list.section.search
            .sendKeys('@input', `id:>${data.inventoryNoSource.id - 1} id:<${data.inventoryNoSource.id + 1}`)
            .sendKeys('@input', client.Keys.ENTER);

        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.expect.element(`#inventories_table .List-tableRow[id="${data.inventoryNoSource.id}"]`).visible;
        inventories.expect.element('i[class*="copy"]').visible;
        inventories.expect.element('i[class*="copy"]').enabled;

        inventories.click('i[class*="copy"]');
        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        const activityStream = 'bread-crumb > div i[class$="icon-activity-stream"]';
        const activityRow = '#activities_table .List-tableCell[class*="description-column"] a';
        const toast = 'div[class="Toast-icon"]';

        inventories.waitForElementNotPresent(toast);
        inventories.expect.element(activityStream).visible;
        inventories.expect.element(activityStream).enabled;
        inventories.click(activityStream);
        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        client
            .waitForElementVisible(activityRow)
            .click(activityRow);

        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.expect.element('#inventory_form').visible;
        inventories.section.editStandardInventory.expect.element('@title').visible;
        inventories.section.editStandardInventory.expect.element('@title').text.contain(data.inventoryNoSource.name);
        inventories.section.editStandardInventory.expect.element('@title').text.not.equal(data.inventoryNoSource.name);
        inventories.expect.element('@save').visible;
        inventories.expect.element('@save').enabled;

        client.end();
    },
    'verify inventories with sources cannot be copied': client => {
        const inventories = client.page.inventories();

        client.useCss();
        client.login();
        client.waitForAngular();

        inventories.load();
        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.section.list.expect.element('smart-search').visible;
        inventories.section.list.section.search.expect.element('@input').enabled;

        inventories.section.list.section.search
            .sendKeys('@input', `id:>${data.inventory.id - 1} id:<${data.inventory.id + 1}`)
            .sendKeys('@input', client.Keys.ENTER);

        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.expect.element(`#inventories_table .List-tableRow[id="${data.inventory.id}"]`).visible;
        inventories.expect.element(`#inventory-${data.inventory.id}-copy-action`).visible;
        inventories.expect.element(`#inventory-${data.inventory.id}-copy-action[class*="btn-disabled"]`).present;

        client.end();
    }
};
