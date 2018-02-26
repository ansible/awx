const columns = ['Name', 'Kind', 'Owners', 'Actions'];
const sortable = ['Name'];

module.exports = {
    before: (client, done) => {
        const credentials = client.page.credentials();

        client.login();
        client.resizeWindow(1200, 800);
        client.waitForAngular();

        credentials
            .load()
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        credentials.waitForElementVisible('#credentials_table', done);
    },
    'expected table columns are visible': client => {
        const credentials = client.page.credentials();
        const { table } = credentials.section.list.section;

        columns.forEach(label => {
            table.section.header.findColumnByText(label)
                .expect.element('@self').visible;
        });
    },
    'only fields expected to be sortable show sort icon': client => {
        const credentials = client.page.credentials();
        const { table } = credentials.section.list.section;

        sortable.forEach(label => {
            table.section.header.findColumnByText(label)
                .expect.element('@sortable').visible;
        });
    },
    'sort all columns expected to be sortable': client => {
        const credentials = client.page.credentials();
        const { table } = credentials.section.list.section;

        sortable.forEach(label => {
            const column = table.section.header.findColumnByText(label);

            column.click('@self');

            credentials
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            column.expect.element('@sorted').visible;
        });

        client.end();
    }
};
