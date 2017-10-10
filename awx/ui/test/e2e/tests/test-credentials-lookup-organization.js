module.exports = {
    before: function(client, done) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;

        client.login();
        client.waitForAngular();

        credentials.section.navigation
            .waitForElementVisible('@credentials')
            .click('@credentials');

        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        credentials.section.list
            .waitForElementVisible('@add')
            .click('@add');

        details
            .waitForElementVisible('@save', done);

    },
    'open the lookup modal': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;
        const lookupModal = credentials.section.lookupModal;

        details.expect.element('@organization').visible;
        details.expect.element('@organization').enabled;

        details.section.organization.expect.element('@lookup').visible;
        details.section.organization.expect.element('@lookup').enabled;

        details.section.organization.click('@lookup');

        credentials.expect.section('@lookupModal').present;

        let expected = 'SELECT ORGANIZATION';
        lookupModal.expect.element('@title').visible;
        lookupModal.expect.element('@title').text.equal(expected);
    },
    'select button is disabled until item is selected': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;
        const lookupModal = credentials.section.lookupModal;
        const table = lookupModal.section.table;

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
    'sort and unsort the table by name with an item selected': function(client) {
        const credentials = client.page.credentials();
        const lookupModal = credentials.section.lookupModal;
        const table = lookupModal.section.table;

        let column = table.section.header.findColumnByText('Name');

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
    'use the pagination controls with an item selected': function(client) {
        const credentials = client.page.credentials();
        const lookupModal = credentials.section.lookupModal;
        const table = lookupModal.section.table;
        const pagination = lookupModal.section.pagination;

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
