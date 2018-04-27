module.exports = {
    'expected LDAP codemirror fields are rendered when returning from another tab': client => {
        const authTab = '#auth_tab';
        const authView = 'div[ui-view="auth"]';
        const ldapForm = '#configuration_ldap_template_form';
        const systemTab = '#system_tab';
        const systemView = 'div[ui-view="system"]';

        const { navigation } = client.page.dashboard().section;
        const configuration = client.page.configuration();

        client.login();
        client.waitForAngular();

        navigation
            .waitForElementVisible('@settings')
            .click('@settings');

        configuration.waitForElementVisible(authView);

        configuration.waitForElementVisible(systemTab);
        configuration.click(systemTab);
        configuration.waitForElementNotVisible(authView);
        configuration.waitForElementVisible(systemView);

        configuration.waitForElementVisible(authTab);
        configuration.click(authTab);
        configuration.waitForElementNotVisible(systemView);
        configuration.waitForElementVisible(authView);

        configuration.selectSubcategory('LDAP');
        configuration.waitForElementVisible(ldapForm);

        const expectedCodemirrorFields = [
            'AUTH_LDAP_USER_SEARCH',
            'AUTH_LDAP_GROUP_SEARCH',
            'AUTH_LDAP_USER_ATTR_MAP',
            'AUTH_LDAP_GROUP_TYPE_PARAMS',
            'AUTH_LDAP_USER_FLAGS_BY_GROUP',
            'AUTH_LDAP_ORGANIZATION_MAP',
            'AUTH_LDAP_TEAM_MAP',
        ];

        const ldapCodeMirrors = `${ldapForm} div[class^="CodeMirror"] textarea`;

        client.elements('css selector', ldapCodeMirrors, ({ value }) => {
            client.assert.equal(value.length, expectedCodemirrorFields.length);
        });

        expectedCodemirrorFields.forEach(fieldName => {
            const codemirror = `#cm-${fieldName}-container div[class^="CodeMirror"]`;

            configuration.expect.element(codemirror).visible;
            configuration.expect.element(codemirror).enabled;
        });

        client.end();
    },
};
