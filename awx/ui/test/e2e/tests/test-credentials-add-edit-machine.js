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
            .setValue('@type', 'Machine');

        details.expect.element('@save').enabled;
    },
    'machine credential fields are visible after choosing type': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { machine } = details.section;

        machine.expect.element('@username').visible;
        machine.expect.element('@password').visible;
        machine.expect.element('@becomeUsername').visible;
        machine.expect.element('@becomePassword').visible;
        machine.expect.element('@sshKeyData').visible;
        machine.expect.element('@sshKeyUnlock').visible;
    },
    'error displayed for invalid ssh key data': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { sshKeyData } = details.section.machine.section;

        details
            .clearAndSelectType('Machine')
            .setValue('@name', store.credential.name);

        details.section.machine.setValue('@sshKeyData', 'invalid');

        details.click('@save');

        sshKeyData.expect.element('@error').visible;
        sshKeyData.expect.element('@error').text.to.contain('Invalid certificate or key');

        details.section.machine.clearValue('@sshKeyData');
        sshKeyData.expect.element('@error').not.present;
    },
    'error displayed for unencrypted ssh key with passphrase': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;
        const { sshKeyUnlock } = details.section.machine.section;

        details
            .clearAndSelectType('Machine')
            .setValue('@name', store.credential.name);

        details.section.machine
            .setValue('@sshKeyUnlock', 'password')
            .sendKeys('@sshKeyData', '-----BEGIN RSA PRIVATE KEY-----')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', 'AAAA')
            .sendKeys('@sshKeyData', client.Keys.ENTER)
            .sendKeys('@sshKeyData', '-----END RSA PRIVATE KEY-----');

        details.click('@save');

        sshKeyUnlock.expect.element('@error').visible;
        sshKeyUnlock.expect.element('@error').text.to.contain('not encrypted');

        details.section.machine.clearValue('@sshKeyUnlock');
        sshKeyUnlock.expect.element('@error').not.present;
    },
    'create machine credential': client => {
        const credentials = client.page.credentials();
        const { add } = credentials.section;
        const { edit } = credentials.section;

        add.section.details
            .clearAndSelectType('Machine')
            .setValue('@name', store.credential.name)
            .setValue('@organization', store.organization.name);

        add.section.details.section.machine
            .setValue('@username', 'dsarif')
            .setValue('@password', 'freneticpny')
            .setValue('@becomeMethod', 'sudo')
            .setValue('@becomeUsername', 'dsarif')
            .setValue('@becomePassword', 'freneticpny')
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
    'change the password after saving': client => {
        const credentials = client.page.credentials();
        const { edit } = credentials.section;
        const { machine } = edit.section.details.section;

        machine.section.password.expect.element('@replace').visible;
        machine.section.password.expect.element('@replace').enabled;
        machine.section.password.expect.element('@revert').not.visible;

        machine.expect.element('@password').not.enabled;

        machine.section.password.click('@replace');

        machine.section.password.expect.element('@replace').not.visible;
        machine.section.password.expect.element('@revert').visible;

        machine.expect.element('@password').enabled;
        machine.setValue('@password', 'newpassword');

        edit.section.details.click('@save');

        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');
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
    },
};
