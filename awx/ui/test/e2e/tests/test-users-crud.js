/* Tests for the user CRUD operations. */
import uuid from 'uuid';

const row = '#users_table .List-tableRow';
const testID = uuid().substr(0, 8);

const store = {
    organization: {
        name: `org-${testID}`
    },
    user: {
        email: `email-${testID}@example.com`,
        firstName: `first-${testID}`,
        lastName: `last-${testID}`,
        password: `${testID}`,
        username: `user-${testID}`,
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
    'create an user': client => {
        const users = client.page.users();
        users.load();
        client.waitForSpinny();
        users.section.list
            .waitForElementVisible('@add')
            .click('@add');
        users.section.add
            .waitForElementVisible('@title')
            .setValue('@organization', store.organization.name)
            .setValue('@email', store.user.email)
            .setValue('@username', store.user.username)
            .setValue('@password', store.user.password)
            .setValue('@confirmPassword', store.user.password)
            .click('@save');
        client.waitForSpinny();
        users.search(store.user.username);
    },
    'edit an user': client => {
        const users = client.page.users();
        users.load();
        client.waitForSpinny();
        users.search(store.user.username);
        const editButton = `${row} i[class*="fa-pencil"]`;
        users.waitForElementVisible(editButton).click(editButton);
        users.section.edit
            .waitForElementVisible('@title')
            .setValue('@firstName', store.user.firstName)
            .setValue('@lastName', store.user.lastName)
            .click('@save');
        client.waitForSpinny();
        users.search(store.user.username);
        users.expect.element(row).text.contain(`${store.user.username}\n${store.user.firstName[0].toUpperCase() + store.user.firstName.slice(1)}\n${store.user.lastName}`);
    },
    'check if the new user can login': (client) => {
        client.logout();
        client.login(store.user.username, store.user.password);
        client.logout();
        client.login();
    },
    'delete the user': (client) => {
        const users = client.page.users();
        users.load();
        client.waitForSpinny();
        users.search(store.user.username);
        const deleteButton = `${row} i[class*="fa-trash-o"]`;
        const modalAction = '.modal-dialog #prompt_action_btn';
        users
            .waitForElementVisible(deleteButton)
            .click(deleteButton)
            .waitForElementVisible(modalAction)
            .click(modalAction)
            .waitForSpinny();
        const searchResults = '.List-searchNoResults';
        users
            .waitForElementVisible(searchResults)
            .expect.element(searchResults).text.contain('No records matched your search.');
    },
    after: client => {
        client.end();
    },
};
