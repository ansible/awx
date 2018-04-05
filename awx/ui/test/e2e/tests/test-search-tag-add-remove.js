import { range } from 'lodash';

import { getAdminMachineCredential } from '../fixtures';

const spinny = 'div.spinny';
const searchInput = 'smart-search input';
const searchSubmit = 'smart-search i[class*="search"]';
const searchTags = 'smart-search .SmartSearch-tagContainer';
const searchClearAll = 'smart-search .SmartSearch-clearAll';
const searchTagDelete = 'i[class*="fa-times"]';

const createTagSelector = n => `${searchTags}:nth-of-type(${n})`;
const createTagDeleteSelector = n => `${searchTags}:nth-of-type(${n}) ${searchTagDelete}`;

const checkTags = (client, tags) => {
    const strategy = 'css selector';

    const countReached = createTagSelector(tags.length);
    const countExceeded = createTagSelector(tags.length + 1);

    if (tags.length > 0) {
        client.waitForElementVisible(countReached);
        client.waitForElementNotPresent(countExceeded);
    }

    client.elements(strategy, searchTags, tagElements => {
        client.assert.equal(tagElements.value.length, tags.length);

        let n = -1;
        tagElements.value.map(o => o.ELEMENT).forEach(id => {
            client.elementIdText(id, ({ value }) => {
                client.assert.equal(value, tags[++n]);
            });
        });
    });
};

module.exports = {
    before: (client, done) => {
        const resources = range(25).map(n => getAdminMachineCredential(`test-search-${n}`));

        Promise.all(resources).then(done);
    },
    'add and remove search tags': client => {
        const credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        credentials.section.navigation.waitForElementVisible('@credentials');
        credentials.section.navigation.click('@credentials');

        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        client.waitForElementVisible(searchInput);
        client.waitForElementVisible(searchSubmit);

        client.expect.element(searchInput).enabled;
        client.expect.element(searchSubmit).enabled;

        checkTags(client, []);

        client.setValue(searchInput, 'foo');
        client.click(searchSubmit);
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, ['foo']);

        client.setValue(searchInput, 'bar e2e');
        client.click(searchSubmit);
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, ['foo', 'bar', 'e2e']);

        client.click(searchClearAll);
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, []);

        client.setValue(searchInput, 'fiz name:foo');
        client.click(searchSubmit);
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, ['fiz', 'name:foo']);

        client.click(searchClearAll);
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, []);

        client.setValue(searchInput, 'hello name:world fiz');
        client.click(searchSubmit);
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, ['hello', 'fiz', 'name:world']);

        client.click(createTagDeleteSelector(2));
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, ['hello', 'name:world']);

        client.click(createTagDeleteSelector(1));
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, ['name:world']);

        client.click(createTagDeleteSelector(1));
        client.waitForElementVisible(spinny);
        client.waitForElementNotVisible(spinny);

        checkTags(client, []);

        client.end();
    },
};
