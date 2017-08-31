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

        credentials.section.add.section.details
            .waitForElementVisible('@save')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name)
            .setValue('@type', 'Amazon Web Services', done);
    },
    'expected fields are visible and enabled': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;

        details.expect.element('@name').visible;
        details.expect.element('@description').visible;
        details.expect.element('@organization').visible;
        details.expect.element('@type').visible;
        details.section.aws.expect.element('@accessKey').visible;
        details.section.aws.expect.element('@secretKey').visible;
        details.section.aws.expect.element('@securityToken').visible;

        details.expect.element('@name').enabled;
        details.expect.element('@description').enabled;
        details.expect.element('@organization').enabled;
        details.expect.element('@type').enabled;
        details.section.aws.expect.element('@accessKey').enabled;
        details.section.aws.expect.element('@secretKey').enabled;
        details.section.aws.expect.element('@securityToken').enabled;
    },
    'required fields display \'*\'': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;
        const required = [
            details.section.name,
            details.section.type,
            details.section.aws.section.accessKey,
            details.section.aws.section.secretKey
        ]
        required.map(s => s.expect.element('@label').text.to.contain('*'));
    },
    'save button becomes enabled after providing required fields': function(client) {
        const credentials = client.page.credentials();
        const details = credentials.section.add.section.details;

        details
            .clearAndSelectType('Amazon Web Services')
            .setValue('@name', store.credential.name);

        details.expect.element('@save').not.enabled;
        details.section.aws.setValue('@accessKey', 'AAAAAAAAAAAAA');
        details.section.aws.setValue('@secretKey', 'AAAAAAAAAAAAA');
        details.expect.element('@save').enabled;
    },
   'create aws credential': function(client) {
        const credentials = client.page.credentials();
        const add = credentials.section.add;
        const edit = credentials.section.edit;

        add.section.details
            .clearAndSelectType('Amazon Web Services')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name);

        add.section.details.section.aws
            .setValue('@accessKey', 'ABCD123456789')
            .setValue('@secretKey', '987654321DCBA');

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

        const search = credentials.section.list.section.search;
        const table = credentials.section.list.section.table;

        search
            .waitForElementVisible('@input')
            .setValue('@input', `name:${store.credential.name}`)
            .click('@searchButton');

        table.waitForRowCount(1);
        table.findRowByText(store.credential.name)
            .waitForElementVisible('@self');

        client.end();
    }
};
