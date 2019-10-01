/* Tests for applications. */
import uuid from 'uuid';
import {
    getOrganization,
    getUser
} from '../fixtures';

const row = '.at-List-container .at-Row';
const editLink = `${row} a.ng-binding`;
const testID = uuid().substr(0, 8);
const namespace = 'test-applications';

const store = {
    organization: {
        name: `${namespace}-organization`
    },
    application: {
        name: `name-${testID}`,
        description: `description-${testID}`,
        // authorizationGrantType: `authorization-grand-type-${testID}`,
        redirectUris: `https://example.com/${testID}/`,
        // clientType: `client-type-${testID}`,
    },
    adminUser: {
        username: `admin-${testID}`,
        password: `admin-${testID}`,
        isSuperuser: true,
    },
};

let data;

module.exports = {
    before: (client, done) => {
        const resources = [
            getOrganization(store.organization.name),
            getUser(
                namespace,
                store.adminUser.username,
                store.adminUser.password,
                store.adminUser.isSuperuser
            ),
        ];
        Promise.all(resources)
            .then(([org]) => {
                data = { org };
                done();
            });

        client.login();
        client.waitForAngular();
    },
    'create an application': client => {
        const applications = client.page.applications();
        applications.load();
        client.waitForSpinny();
        const newApplication = {
            name: store.application.name,
            redirectUris: store.application.redirectUris,
            authorizationGrantType:
                applications.props.authorizationGrantTypeOptions.authorizationCode,
            clientType: applications.props.clientTypeOptions.confidential,
        };
        applications.create(newApplication, store.organization);
        applications.search(store.application.name);
    },
    'edit an application': client => {
        // Given the application created on the previous test
        const applications = client.page.applications();
        applications.load();
        client.waitForSpinny();
        applications.search(store.application.name);
        client
            .waitForElementVisible(editLink)
            .expect.element(editLink).text.to.equal(store.application.name);
        client.click(editLink);
        applications.section.edit
            .waitForElementVisible('@description')
            .setValue('@description', store.application.description)
            .click('@save');
        client.waitForSpinny();
        applications.load();
        client.waitForSpinny();
        applications.search(store.application.name);
        client
            .waitForElementVisible(editLink)
            .expect.element(editLink).text.to.equal(store.application.name);
        client.click(editLink);
        applications.section.edit
            .waitForElementVisible('@description')
            .expect.element('@description').value.to.equal(store.application.description);
    },
    'add a read scoped application token': client => {
        client.logout();
        client.login(store.adminUser.username, store.adminUser.password);

        // Given the application created on the previous test
        const token = {
            application: store.application.name,
            description: `Read scoped token for ${store.application.name}`,
            scope: 'Read',
        };
        const users = client.page.users();
        users.load();
        client.waitForSpinny();
        users.createToken(store.adminUser.username, token, (tokenInfo) => {
            const applications = client.page.applications();
            applications.load();
            client.waitForSpinny();
            applications.search(store.application.name);
            client.findThenClick(editLink, 'css');
            applications.section.edit
                .waitForElementVisible('@tokensTab')
                .click('@tokensTab')
                .waitForSpinny();
            // FIXME: Search is not properly working, update this when it is working.
            applications.section.tokens.expect.element('@list').text.to.contain(`${store.adminUser.username}\n${token.description}\nEXPIRATION ${tokenInfo.expires}`);
        });
    },
    'add a write scoped application token': client => {
        // Given the application created on the previous test
        const token = {
            application: store.application.name,
            description: `Write scoped token for ${store.application.name}`,
            scope: 'Write',
        };

        const users = client.page.users();
        users.load();
        client.waitForSpinny();
        users.createToken(store.adminUser.username, token, (tokenInfo) => {
            const applications = client.page.applications();
            applications.load();
            client.waitForSpinny();
            applications.search(store.application.name);
            client.findThenClick(editLink, 'css');
            applications.section.edit
                .waitForElementVisible('@tokensTab')
                .click('@tokensTab')
                .waitForSpinny();
            // FIXME: Search is not properly working, update this when it is working.
            applications.section.tokens.expect.element('@list').text.to.contain(`${store.adminUser.username}\n${token.description}\nEXPIRATION ${tokenInfo.expires}`);
        });

        client.logout();
        client.login();
    },
    'delete an application': client => {
        // Given the application created on the create application test
        const applications = client.page.applications();
        applications.load();
        client.waitForSpinny();
        applications.delete(store.application.name);
    },
    after: client => {
        client.end();
    },
};
