import { range } from 'lodash';

import { getOrganization } from '../fixtures';

module.exports = {
    before: (client, done) => {
        const resources = range(100).map(n => getOrganization(`test-lookup-${n}`));

        Promise.all(resources)
            .then(() => {
                const credentials = client.page.credentials();
                const { details } = credentials.section.add.section;

                client.login();
                client.waitForAngular();

                credentials.section.navigation.waitForElementVisible('@credentials');
                credentials.section.navigation.click('@credentials');

                credentials.waitForElementVisible('div.spinny');
                credentials.waitForElementNotVisible('div.spinny');

                credentials.section.list.waitForElementVisible('@add');
                credentials.section.list.click('@add');

                details.waitForElementVisible('@save');

                done();
            });
    },
    'open the lookup modal': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { lookupModal } = credentials.section;

        details.expect.element('@organization').visible;
        details.expect.element('@organization').enabled;

        details.section.organization.expect.element('@lookup').visible;
        details.section.organization.expect.element('@lookup').enabled;

        details.section.organization.click('@lookup');

        credentials.expect.section('@lookupModal').present;

        const expected = 'SELECT ORGANIZATION';
        lookupModal.expect.element('@title').visible;
        lookupModal.expect.element('@title').text.equal(expected);
    },
    'select button is disabled until item is selected': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { lookupModal } = credentials.section;
        const { table } = lookupModal.section;

        details.section.organization.expect.element('@lookup').visible;
        details.section.organization.expect.element('@lookup').enabled;

        details.section.organization.click('@lookup');

        credentials.expect.section('@lookupModal').present;

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(6) input[type="radio"]').not.present;

        lookupModal.expect.element('@select').visible;
        lookupModal.expect.element('@select').not.enabled;

        table.click('tbody tr:nth-child(2)');
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').selected;

        lookupModal.expect.element('@select').visible;
        lookupModal.expect.element('@select').enabled;
    },
    'sort and unsort the table by name with an item selected': client => {
        const credentials = client.page.credentials();
        const { lookupModal } = credentials.section;
        const { table } = lookupModal.section;

        const column = table.section.header.findColumnByText('Name');

        column.expect.element('@self').visible;
        column.expect.element('@sortable').visible;

        column.click('@self');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;

        column.click('@self');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;
    },
    'use the pagination controls with an item selected': client => {
        const credentials = client.page.credentials();
        const { lookupModal } = credentials.section;
        const { table } = lookupModal.section;
        const { pagination } = lookupModal.section;

        pagination.click('@next');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;

        pagination.click('@previous');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;

        pagination.click('@last');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        pagination.click('@previous');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;

        pagination.click('@first');
        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        table.expect.element('tbody tr:nth-child(1) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(2) input[type="radio"]').selected;
        table.expect.element('tbody tr:nth-child(3) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(4) input[type="radio"]').not.selected;
        table.expect.element('tbody tr:nth-child(5) input[type="radio"]').not.selected;

        client.end();
    }
};
