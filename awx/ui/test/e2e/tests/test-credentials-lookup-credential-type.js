module.exports = {
    before: (client, done) => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        client.login();
        client.waitForAngular();

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
            .waitForElementVisible('@save', done);
    },
    'open the lookup modal': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        const modal = 'div[class="modal-body"]';
        const title = 'div[class^="Form-title"]';

        details.expect.element('@type').visible;
        details.expect.element('@type').enabled;

        details.section.type.expect.element('@lookup').visible;
        details.section.type.expect.element('@lookup').enabled;

        details.section.type.click('@lookup');

        client.expect.element(modal).present;

        const expected = 'SELECT CREDENTIAL TYPE';
        client.expect.element(title).visible;
        client.expect.element(title).text.equal(expected);

        client.end();
    }
};
