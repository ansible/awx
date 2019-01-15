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

        details.waitForElementVisible('@save', done);
    },
    'common fields are visible and enabled': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        details.expect.element('@name').visible;
        details.expect.element('@description').visible;
        details.expect.element('@organization').visible;
        details.expect.element('@type').visible;

        details.expect.element('@name').enabled;
        details.expect.element('@description').enabled;
        details.expect.element('@organization').enabled;
        details.expect.element('@type').enabled;
    },
    'required common fields display \'*\'': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        details.section.name.expect.element('@label').text.to.contain('*');
        details.section.type.expect.element('@label').text.to.contain('*');
    },
    'save button becomes enabled after providing required fields': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        details.expect.element('@save').not.enabled;

        details
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name)
            .setValue('@type', 'Network');

        details.section.network
            .waitForElementVisible('@username')
            .setValue('@username', 'sgrimes');

        details.expect.element('@save').enabled;
    },
    'network credential fields are visible after choosing type': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { network } = details.section;

        network.expect.element('@username').visible;
        network.expect.element('@password').visible;
        network.expect.element('@authorizePassword').visible;
        network.expect.element('@sshKeyData').visible;
        network.expect.element('@sshKeyUnlock').visible;
    },
    'error displayed for invalid ssh key data': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { sshKeyData } = details.section.network.section;

        details
            .clearAndSelectType('Network')
            .setValue('@name', store.credential.name);

        details.section.network
            .setValue('@username', 'sgrimes')
            .setValue('@sshKeyData', 'invalid');

        details.click('@save');

        sshKeyData.expect.element('@error').visible;
        sshKeyData.expect.element('@error').text.to.contain('Invalid certificate or key');

        details.section.network.clearValue('@sshKeyData');
        sshKeyData.expect.element('@error').not.present;
    },
    'error displayed for unencrypted ssh key with passphrase': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { sshKeyUnlock } = details.section.network.section;

        details
            .clearAndSelectType('Network')
            .setValue('@name', store.credential.name);

        details.section.network
            .setValue('@username', 'sgrimes')
            .setValue('@sshKeyUnlock', 'password')
            .sendKeys('@sshKeyData', '-----BEGIN RSA PRIVATE KEY-----')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', 'AAAA')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', '-----END RSA PRIVATE KEY-----');

        details.click('@save');

        sshKeyUnlock.expect.element('@error').visible;
        sshKeyUnlock.expect.element('@error').text.to.contain('not encrypted');

        details.section.network.clearValue('@sshKeyUnlock');
        sshKeyUnlock.expect.element('@error').not.present;
    },
    'error displayed for authorize password without authorize enabled': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { authorizePassword } = details.section.network.section;

        details
            .clearAndSelectType('Network')
            .setValue('@name', store.credential.name);

        details.section.network
            .setValue('@username', 'sgrimes')
            .setValue('@authorizePassword', 'ovid');

        details.click('@save');

        const expected = 'cannot be set unless "Authorize" is set';
        authorizePassword.expect.element('@error').visible;
        authorizePassword.expect.element('@error').text.to.equal(expected);

        details.section.network.clearValue('@authorizePassword');
        authorizePassword.expect.element('@error').not.present;
    },
    'create network credential': client => {
        const credentials = client.page.credentials();
        const { add } = credentials.section;
        const { edit } = credentials.section;

        add.section.details
            .clearAndSelectType('Network')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name);

        add.section.details.section.network
            .setValue('@username', 'sgrimes')
            .setValue('@password', 'ovid')
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
