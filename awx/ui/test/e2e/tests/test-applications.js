/* Tests for applications. */
import uuid from 'uuid';

const row = '.at-List-container .at-Row';
const testID = uuid().substr(0, 8);

const store = {
    organization: {
        name: `org-${testID}`
    },
    application: {
        name: `name-${testID}`,
        description: `description-${testID}`,
        // authorizationGrantType: `authorization-grand-type-${testID}`,
        redirectUris: `https://example.com/${testID}/`,
        // clientType: `client-type-${testID}`,
    },
};

module.exports = {
    before: (client, done) => {
        client.login();
        client.waitForAngular();

        client.inject(
            [store, 'OrganizationModel'],
            (_store_, Model) => new Model().http.post({ data: _store_.organization }),
            ({ data }) => {
                store.organization = data;
                done();
            }
        );
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
        const editLink = `${row} a.ng-binding`;
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
