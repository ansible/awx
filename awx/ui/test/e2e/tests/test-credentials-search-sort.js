module.exports = {
    before: (client, done) => {
        const credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        credentials
            .load()
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        credentials.waitForElementVisible('#credentials_table', done);
    },
    'expected table columns are visible': client => {
        const credentials = client.page.credentials();

        credentials.expect.element('#credential-name-header').visible;
        credentials.expect.element('#credential-kind-header').visible;
        credentials.expect.element('#credential-owners-header').visible;
        credentials.expect.element('#credential-actions-header').visible;
    },
    'only fields expected to be sortable show sort icon': client => {
        const credentials = client.page.credentials();

        credentials.expect.element('#credential-name-header > i.columnSortIcon').visible;
    },
    'sort all columns expected to be sortable': client => {
        const credentials = client.page.credentials();

        credentials.expect.element('#credential-name-header > i.columnSortIcon.fa-sort-up').visible;
        credentials.click('#credential-name-header');
        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');
        credentials.expect.element('#credential-name-header > i.columnSortIcon.fa-sort-down').visible;

        client.end();
    }
};
