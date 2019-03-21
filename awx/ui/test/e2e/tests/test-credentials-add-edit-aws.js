import uuid from 'uuid';

const testID = uuid().substr(0, 8);

const store = {
    organization: {
        name: `org-${testID}`
    },
    credential: {
        name: `cred-${testID}`
    },
};

module.exports = {
    before: (client, done) => {
        const credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        client.inject(
            [store, 'OrganizationModel'],
            (_store_, Model) => new Model().http.post({ data: _store_.organization }),
            ({ data }) => { store.organization = data; }
        );

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
    'expected fields are visible and enabled': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

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
    'required fields display \'*\'': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const required = [
            details.section.name,
            details.section.type,
            details.section.aws.section.accessKey,
            details.section.aws.section.secretKey
        ];

        required.forEach(s => {
            s.expect.element('@label').text.to.contain('*');
        });
    },
    'save button becomes enabled after providing required fields': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        details
            .clearAndSelectType('Amazon Web Services')
            .setValue('@name', store.credential.name);

        details.expect.element('@save').not.enabled;
        details.section.aws.setValue('@accessKey', 'AAAAAAAAAAAAA');
        details.section.aws.setValue('@secretKey', 'AAAAAAAAAAAAA');
        details.expect.element('@save').enabled;
    },
    'create aws credential': client => {
        const credentials = client.page.credentials();
        const { add } = credentials.section;
        const { edit } = credentials.section;

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
    'edit details panel remains open after saving': client => {
        const credentials = client.page.credentials();

        credentials.section.edit.expect.section('@details').visible;
    },
    'credential is searchable after saving': client => {
        const credentials = client.page.credentials();
        const row = '#credentials_table .List-tableRow';

        const { search } = credentials.section.list.section;

        search
            .waitForElementVisible('@input')
            .setValue('@input', `name:${store.credential.name}`)
            .click('@searchButton');

        credentials.waitForElementNotPresent(`${row}:nth-of-type(2)`);
        credentials.expect.element(row).text.contain(store.credential.name);

        client.end();
    }
};
