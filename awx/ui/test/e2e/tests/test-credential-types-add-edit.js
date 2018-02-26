module.exports = {
    before: (client, done) => {
        const credentialTypes = client.page.credentialTypes();

        client.login();
        client.waitForAngular();

        credentialTypes.navigateTo(`${credentialTypes.url()}/add/`);

        credentialTypes.section.add
            .waitForElementVisible('@title', done);
    },
    'expected fields are present and enabled': client => {
        const credentialTypes = client.page.credentialTypes();
        const { details } = credentialTypes.section.add.section;

        details.expect.element('@name').visible;
        details.expect.element('@description').visible;
        details.section.inputConfiguration.expect.element('.CodeMirror').visible;
        details.section.injectorConfiguration.expect.element('.CodeMirror').visible;

        details.expect.element('@name').enabled;
        details.expect.element('@description').enabled;
        details.expect.element('@inputConfiguration').enabled;
        details.expect.element('@injectorConfiguration').enabled;

        client.end();
    }
};
