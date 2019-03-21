import uuid from 'uuid';

import { AWX_E2E_TIMEOUT_LONG } from '../settings';

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
        const { details } = credentials.section.add.section;

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

        details
            .waitForElementVisible('@save')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name)
            .setValue('@type', 'Google Compute Engine', done);
    },
    'expected fields are visible and enabled': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        details.expect.element('@name').visible;
        details.expect.element('@description').visible;
        details.expect.element('@organization').visible;
        details.expect.element('@type').visible;
        details.section.gce.expect.element('@email').visible;
        details.section.gce.expect.element('@sshKeyData').visible;
        details.section.gce.expect.element('@project').visible;

        details.expect.element('@name').enabled;
        details.expect.element('@description').enabled;
        details.expect.element('@organization').enabled;
        details.expect.element('@type').enabled;
        details.section.gce.expect.element('@email').enabled;
        details.section.gce.expect.element('@sshKeyData').enabled;
        details.section.gce.expect.element('@project').enabled;

        details.section.organization.expect.element('@lookup').visible;
    },
    'required fields display \'*\'': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const required = [
            details.section.name,
            details.section.type,
            details.section.gce.section.email,
            details.section.gce.section.sshKeyData
        ];

        required.forEach(s => {
            s.expect.element('@label').text.to.contain('*');
        });
    },
    'save button becomes enabled after providing required fields': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        details
            .clearAndSelectType('Google Compute Engine')
            .setValue('@name', store.credential.name);

        details.expect.element('@save').not.enabled;

        details.section.gce
            .setValue('@email', 'abc@123.com')
            .sendKeys('@sshKeyData', '-----BEGIN RSA PRIVATE KEY-----')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', 'AAAA')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', '-----END RSA PRIVATE KEY-----');

        details.expect.element('@save').enabled;
    },
    'error displayed for invalid ssh key data': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { sshKeyData } = details.section.gce.section;

        details
            .clearAndSelectType('Google Compute Engine')
            .setValue('@name', store.credential.name);

        details.section.gce
            .setValue('@email', 'abc@123.com')
            .setValue('@sshKeyData', 'invalid');

        details.click('@save');

        sshKeyData.expect.element('@error').visible;
        sshKeyData.expect.element('@error').text.to.contain('Invalid certificate or key');

        details.section.gce.clearValue('@sshKeyData');

        sshKeyData.expect.element('@error').visible;
        sshKeyData.expect.element('@error').text.to.contain('Please enter a value');

        details.section.gce.setValue('@sshKeyData', 'AAAA');
        sshKeyData.expect.element('@error').not.present;
    },
    'create gce credential': client => {
        const credentials = client.page.credentials();
        const { add } = credentials.section;
        const { edit } = credentials.section;

        add.section.details
            .clearAndSelectType('Google Compute Engine')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name);

        add.section.details.section.gce
            .setValue('@email', 'abc@123.com')
            .sendKeys('@sshKeyData', '-----BEGIN RSA PRIVATE KEY-----')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', 'AAAA')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', '-----END RSA PRIVATE KEY-----');

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

        credentials.section.list.section.search
            .waitForElementVisible('@input', AWX_E2E_TIMEOUT_LONG)
            .setValue('@input', `name:${store.credential.name}`)
            .click('@searchButton');

        credentials.waitForElementNotPresent(`${row}:nth-of-type(2)`);
        credentials.expect.element(row).text.contain(store.credential.name);

        client.end();
    }
};
