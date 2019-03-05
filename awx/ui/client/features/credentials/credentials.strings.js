function CredentialsStrings (BaseString) {
    BaseString.call(this, 'credentials');

    const { t } = this;
    const ns = this.credentials;

    ns.state = {
        ADD_BREADCRUMB_LABEL: t.s('CREATE CREDENTIAL'),
        EDIT_BREADCRUMB_LABEL: t.s('EDIT CREDENTIAL')
    };

    ns.tab = {
        DETAILS: t.s('Details'),
        PERMISSIONS: t.s('Permissions'),
    };

    ns.inputs = {
        GROUP_TITLE: t.s('Type Details'),
        ORGANIZATION_PLACEHOLDER: t.s('SELECT AN ORGANIZATION'),
        CREDENTIAL_TYPE_PLACEHOLDER: t.s('SELECT A CREDENTIAL TYPE'),
        GCE_FILE_INPUT_LABEL: t.s('Service Account JSON File'),
        GCE_FILE_INPUT_HELP_TEXT: t.s('Provide account information using Google Compute Engine JSON credentials file.')
    };

    ns.externalTest = {
        TITLE: t.s('Test External Credential')
    };

    ns.inputSources = {
        TITLE: t.s('Set Input Source'),
        CREDENTIAL: t.s('CREDENTIAL'),
        METADATA: t.s('METADATA'),
        NO_MATCH: t.s('No records matched your search.'),
        NO_RECORDS: t.s('No external credentials available.'),
        SELECTED: t.s('selected'),
        NONE_SELECTED: t.s('No credential selected'),
    };

    ns.add = {
        PANEL_TITLE: t.s('NEW CREDENTIAL')
    };

    ns.edit = {
        TEST_PASSED: t.s('Test passed.'),
        TEST_FAILED: t.s('Test failed.')
    };

    ns.permissions = {
        TITLE: t.s('CREDENTIALS PERMISSIONS')
    };
}

CredentialsStrings.$inject = ['BaseStringService'];

export default CredentialsStrings;
