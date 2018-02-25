import { getInventory } from '../fixtures';

const data = {};

module.exports = {
    before: (client, done) => {
        getInventory('test-actions')
            .then(obj => { data.inventory = obj; })
            .then(done);
    },
    'copy inventory': client => {
        const inventories = client.page.inventories();

        client.useCss();
        client.resizeWindow(1200, 800);
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

        inventories.expect.element(`#inventories_table tr[id="${data.inventory.id}"]`).visible;
        inventories.expect.element('i[class*="copy"]').visible;
        inventories.expect.element('i[class*="copy"]').enabled;

        inventories.click('i[class*="copy"]');
        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.expect.element('#inventory_form').visible;
        inventories.section.editStandardInventory.expect.element('@title').visible;
        inventories.section.editStandardInventory.expect.element('@title').text.contain(data.inventory.name);
        inventories.section.editStandardInventory.expect.element('@title').text.not.equal(data.inventory.name);
        inventories.expect.element('@save').visible;
        inventories.expect.element('@save').enabled;

        client.end();
    }
};
