function CredentialsStrings (BaseString) {
    BaseString.call(this, 'credentials');
    
    let t = this.t;
    let ns = this.credentials;

    ns.state = {
        ADD_BREADCRUMB_LABEL: t('CREATE CREDENTIAL'),
        EDIT_BREADCRUMB_LABEL: t('EDIT CREDENTIAL')
    };

    ns.tab = {
        DETAILS: t('Details'),
        PERMISSIONS: t('Permissions')
    };

    ns.inputs = {
        GROUP_TITLE: t('Type Details'),
        ORGANIZATION_PLACEHOLDER: t('SELECT AN ORGANIZATION'),
        CREDENTIAL_TYPE_PLACEHOLDER: t('SELECT A CREDENTIAL TYPE')
    };

    ns.add = {
        PANEL_TITLE: t('NEW CREDENTIAL')
    };

    ns.permissions = {
        TITLE: t('CREDENTIALS PERMISSIONS')
    };
}

CredentialsStrings.$inject = ['BaseStringService'];

export default CredentialsStrings;
