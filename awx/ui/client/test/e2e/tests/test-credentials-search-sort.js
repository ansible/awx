const columns = ['Name', 'Kind', 'Owners', 'Actions'];
const sortable = ['Name'];
const defaultSorted = ['Name'];


module.exports = {
    before: function(client, done) {
        const credentials = client.page.credentials();

        client.login();
        client.resizeWindow(1200, 800);
        client.waitForAngular();

        credentials
            .navigate()
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        credentials.waitForElementVisible('#credentials_table', done);
    },
    'expected table columns are visible': function(client) {
        const credentials = client.page.credentials();
        const table = credentials.section.list.section.table;

        columns.map(label => {
            table.section.header.findColumnByText(label)
                .expect.element('@self').visible;
        });
    },
    'only fields expected to be sortable show sort icon': function(client) {
        const credentials = client.page.credentials();
        const table = credentials.section.list.section.table;

        sortable.map(label => {
            table.section.header.findColumnByText(label)
                .expect.element('@sortable').visible;
        });
    },
    'sort all columns expected to be sortable': function(client) {
        const credentials = client.page.credentials();
        const table = credentials.section.list.section.table;

        sortable.map(label => {
            let column = table.section.header.findColumnByText(label);

            column.click('@self');

            credentials
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            column.expect.element('@sorted').visible;
        });

        client.end();
    }
};
