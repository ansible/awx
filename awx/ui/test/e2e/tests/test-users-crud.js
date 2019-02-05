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
        users.section.list.section.search
            .setValue('@input', store.user.username)
            .click('@searchButton');
        client.waitForSpinny();
        users.waitForElementNotPresent(`${row}:nth-of-type(2)`);
        users.expect.element('.List-titleBadge').text.to.contain('1');
        users.expect.element(row).text.contain(store.user.username);
    },
    'edit an user': client => {
        const users = client.page.users();
        users.load();
        client.waitForSpinny();
        users.section.list.section.search
            .setValue('@input', store.user.username)
            .click('@searchButton');
        client.waitForSpinny();
        users.waitForElementNotPresent(`${row}:nth-of-type(2)`);
        users.expect.element('.List-titleBadge').text.to.contain('1');
        users.expect.element(row).text.contain(store.user.username);
        const editButton = `${row} i[class*="fa-pencil"]`;
        users.waitForElementVisible(editButton).click(editButton);
        users.section.edit
            .waitForElementVisible('@title')
            .setValue('@firstName', store.user.firstName)
            .setValue('@lastName', store.user.lastName)
            .click('@save');
        client.waitForSpinny();
        users.section.list.section.search
            .setValue('@input', store.user.username)
            .click('@searchButton');
        client.waitForSpinny();
        users.waitForElementNotPresent(`${row}:nth-of-type(2)`);
        users.expect.element(row).text.contain(`${store.user.username}\n${store.user.firstName[0].toUpperCase() + store.user.firstName.slice(1)}\n${store.user.lastName}`);
    },
    after: client => {
        client.end();
    },
};
