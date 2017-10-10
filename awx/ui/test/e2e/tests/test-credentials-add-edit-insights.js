import uuid from 'uuid';


let testID = uuid().substr(0,8);

let store = {
    organization: {
        name: `org-${testID}`
    },
    credential: {
        name: `cred-${testID}`
    },
};

module.exports = {
    before: function(client, done) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;

        client.login();
        client.waitForAngular();

        client.inject([store, 'OrganizationModel'], (store, model) => {
            return new model().http.post(store.organization);
        },
        ({ data }) => {
            store.organization = data;
        });

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
            .waitForElementVisible('@save')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name)
            .setValue('@type', 'Insights', done);
    },
    'expected fields are visible and enabled': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;

        details.expect.element('@name').visible;
        details.expect.element('@description').visible;
        details.expect.element('@organization').visible;
        details.expect.element('@type').visible;
        details.section.insights.expect.element('@username').visible;
        details.section.insights.expect.element('@password').visible;

        details.expect.element('@name').enabled;
        details.expect.element('@description').enabled;
        details.expect.element('@organization').enabled;
        details.expect.element('@type').enabled;
        details.section.insights.expect.element('@username').enabled;
        details.section.insights.expect.element('@password').enabled;
    },
    'required fields display \'*\'': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;
        const required = [
            details.section.name,
            details.section.type,
            details.section.insights.section.username,
            details.section.insights.section.password
        ]
        required.map(s => s.expect.element('@label').text.to.contain('*'));
    },
    'save button becomes enabled after providing required fields': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;

        details
            .clearAndSelectType('Insights')
            .setValue('@name', store.credential.name);

        details.expect.element('@save').not.enabled;

        details.section.insights
            .setValue('@username', 'wrosellini')
            .setValue('@password', 'quintus');

        details.expect.element('@save').enabled;
    },
   'create insights credential': function(client) {
        const credentials = client.page.credentials();
        const add = credentials.section.add;
        const edit = credentials.section.edit;

        add.section.details
            .clearAndSelectType('Insights')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name);

        add.section.details.section.insights
            .setValue('@username', 'wrosellini')
            .setValue('@password', 'quintus');

        add.section.details.click('@save');

        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        edit.expect.element('@title').text.equal(store.credential.name);
    },
    'edit details panel remains open after saving': function(client) {
        const credentials = client.page.credentials();

        credentials.section.edit.expect.section('@details').visible;
    },
    'credential is searchable after saving': function(client) {
        const credentials = client.page.credentials();
        const row = '#credentials_table tbody tr';

        credentials.section.list.section.search
            .waitForElementVisible('@input', client.globals.longWait)
            .setValue('@input', `name:${store.credential.name}`)
            .click('@searchButton');

        credentials.waitForElementNotPresent(`${row}:nth-of-type(2)`);
        credentials.expect.element(row).text.contain(store.credential.name);

        client.end();
    }
};
